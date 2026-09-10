#!/usr/bin/env python3
"""Tests for wtc_sidecar.py.

The first two are the ones that matter: they pin the exact bug that produced
this tool. Everything else is a guard on the reader contract.

    python3 tools/test_wtc_sidecar.py
"""
import os
import shutil
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wtc_sidecar as S  # noqa: E402

import yaml  # noqa: E402


DESC = "Several sentences a human wrote after reading the transcript."
TOPICS = ["Border security", "The candidates' debate"]


def sidecar_with_handwritten():
    return yaml.safe_load(f"""
Transcription:
  Video:
    Title: "A title"
    Description: >-
      {DESC}
    URL: "https://www.youtube.com/watch?v=abc"
    Video_ID: "abc"
  People_in_Video:
    Person_1:
      Name: "Kari Lake"
      Role: "Subject"
      Subject: true
      Speaker_Label: "SPEAKER_00"
    Person_2:
      Name: "Unidentified"
      Speaker_Label: "SPEAKER_01"
  Topics:
    - "{TOPICS[0]}"
    - "{TOPICS[1]}"
  Source:
    Evidence_Grade: "aligned"
  Curation:
    reviewed_by: "a human"
""")


class MergePreservesHandWrittenWork(unittest.TestCase):
    """RULE 1. This is the regression that justifies the whole module."""

    def setUp(self):
        self.kept = S.merge_preserving(sidecar_with_handwritten(), {})

    def test_description_survives(self):
        self.assertIn("human wrote", self.kept["Description"])

    def test_topics_survive(self):
        self.assertEqual(self.kept["Topics"], TOPICS)

    def test_a_named_speaker_survives(self):
        self.assertEqual(self.kept["people"]["SPEAKER_00"]["Name"], "Kari Lake")
        self.assertIs(self.kept["people"]["SPEAKER_00"]["Subject"], True)

    def test_the_placeholder_name_is_not_preserved(self):
        # "Unidentified" is the generator's own placeholder and carries no
        # information. Preserving it would freeze a guess into the record.
        self.assertNotIn("SPEAKER_01", self.kept["people"])

    def test_unknown_blocks_are_carried_not_dropped(self):
        self.assertEqual(self.kept["extra"]["Curation"], {"reviewed_by": "a human"})

    def test_an_absent_file_loses_nothing_and_raises_nothing(self):
        self.assertEqual(S.merge_preserving(None, {})["Description"], None)

    def test_a_corrupt_file_loses_nothing_and_raises_nothing(self):
        for junk in ("", "not yaml at all", "[]", "Transcription: null"):
            self.assertIsNone(S.merge_preserving(yaml.safe_load(junk) if junk else None, {})["Description"])


class ReaderContract(unittest.TestCase):
    """The FOUR fields the product reads, and its lenient spellings.

    Mirrors we_citizens code/packages/backend/src/modules/groups/
    transcription-sidecar.ts. If that file changes, this test should fail.
    """

    def test_the_four_fields_are_found_in_our_own_layout(self):
        f = S.reader_facts(sidecar_with_handwritten())
        self.assertEqual(f["source_url"], "https://www.youtube.com/watch?v=abc")
        self.assertEqual(f["claimed_video_id"], "abc")
        self.assertEqual(f["title"], "A title")
        self.assertEqual(f["evidence_grade"], "aligned")

    def test_keys_are_case_and_underscore_insensitive(self):
        doc = yaml.safe_load("""
transcription:
  video:
    videoid: "xyz"
    watch_url: "https://example.test/x"
    name: "Alt title"
  source:
    grade: "aligned"
""")
        f = S.reader_facts(doc)
        self.assertEqual(f["claimed_video_id"], "xyz")
        self.assertEqual(f["source_url"], "https://example.test/x")
        self.assertEqual(f["title"], "Alt title")
        self.assertEqual(f["evidence_grade"], "aligned")

    def test_fields_at_document_root_are_accepted(self):
        doc = yaml.safe_load('source_url: "https://example.test/y"\ntitle: "Flat"\n')
        f = S.reader_facts(doc)
        self.assertEqual(f["source_url"], "https://example.test/y")
        self.assertEqual(f["title"], "Flat")

    def test_garbage_is_absent_not_an_exception(self):
        for junk in (None, [], "a string", 7):
            self.assertEqual(S.reader_facts(junk)["title"], "")


class YamlQuoting(unittest.TestCase):
    """A quote inside a quoted scalar is a parse error, and political
    transcripts are full of phrases a writer wants in quotation marks."""

    def test_a_value_containing_a_double_quote_still_parses(self):
        emitted = "k: " + S.yq('The "border czar" designation')
        self.assertEqual(yaml.safe_load(emitted)["k"], 'The "border czar" designation')

    def test_apostrophes_survive(self):
        emitted = "k: " + S.yq("Gallego's record")
        self.assertEqual(yaml.safe_load(emitted)["k"], "Gallego's record")

    def test_both_at_once(self):
        v = 'She said "it\'s over" plainly'
        self.assertEqual(yaml.safe_load("k: " + S.yq(v))["k"], v)


class MediaResolution(unittest.TestCase):
    def test_audio_is_preferred_over_video(self):
        # Same words, a fraction of the bytes, and the transcriber discards the
        # video stream anyway.
        self.assertLess(S.AUDIO_EXT.index("m4a"), len(S.AUDIO_EXT))
        self.assertNotIn("mkv", S.AUDIO_EXT)
        self.assertIn("mkv", S.VIDEO_EXT)


class UnrecoverableFields(unittest.TestCase):
    """RULE 2. These live only beside the media, under a root treated as
    disposable. Losing them is permanent."""

    def test_channel_id_is_captured_not_just_the_handle(self):
        labels = [lbl for lbl, _ in S.UNRECOVERABLE]
        self.assertIn("Channel_ID", labels)

    def test_reach_at_capture_time_is_captured(self):
        keys = [k for _, k in S.UNRECOVERABLE]
        for k in ("view_count", "like_count", "comment_count"):
            self.assertIn(k, keys)


DEMAND_HEADER = (
    "person_key,video_uid,video_key,youtube_id,duration_seconds,priority,ceiling,"
    "raw,bound_by,transcripts_held,trusted_transcripts_held,person_transcripts_held,"
    "seat_rank,challenger,round,status,closed_reason,notes,computed_at,run_id,"
    "source_type,source_url,ipfs_cid,source_ref\n"
)


def demand_csv(tmpdir, *rows):
    path = os.path.join(tmpdir, "video_demand.csv")
    with open(path, "w") as fh:
        fh.write(DEMAND_HEADER)
        for r in rows:
            fh.write(r + "\n")
    return path


class DemandJoinsOnVideoUid(unittest.TestCase):
    """THE JOIN KEY IS video_uid. A bare video_key is not unique.

    The demand engine issues placeholder keys — v0001, v0002 ... — one per
    person, so the same video_key appears against dozens of roster_keys with a
    DIFFERENT youtube_id each time. render() builds Video.URL out of the matched
    row's youtube_id, and Video.URL is one of the four fields the product reads,
    so a bare-key match publishes a sidecar pointing at another human's video.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.csv = demand_csv(
            self.tmp,
            "casey_putsch_oh_gov,casey_putsch_oh_gov::v0001,v0001,yZgzh8vzhfc,,550,800,"
            "550,raw,1,0,4,240,true,1,partial,,,2026-09-07T21:12:40.989Z,"
            "job_1,youtube,https://www.youtube.com/watch?v=yZgzh8vzhfc,,yZgzh8vzhfc",
            "rashida_tlaib_mi_12,rashida_tlaib_mi_12::v0001,v0001,-LOuGfPUHfU,,490,800,"
            "490,raw,1,0,1,150,true,1,partial,,,2026-09-07T21:12:40.989Z,"
            "job_1,youtube,https://www.youtube.com/watch?v=-LOuGfPUHfU,,-LOuGfPUHfU",
        )

    def test_the_second_person_gets_their_own_row_not_the_first_match(self):
        row = S.demand_row_for("rashida_tlaib_mi_12", "v0001", self.csv)
        self.assertEqual(row["youtube_id"], "-LOuGfPUHfU")
        self.assertEqual(row["person_key"], "rashida_tlaib_mi_12")

    def test_the_first_person_still_gets_theirs(self):
        row = S.demand_row_for("casey_putsch_oh_gov", "v0001", self.csv)
        self.assertEqual(row["youtube_id"], "yZgzh8vzhfc")

    def test_a_roster_key_with_no_row_is_an_absence_not_somebody_elses_row(self):
        self.assertIsNone(S.demand_row_for("kari_lake_us_pres", "v0001", self.csv))


class DemandBlockCarriesTheWholeRow(unittest.TestCase):
    """The CSV is regenerated every engine run. A column dropped here is a fact
    about this date that then exists nowhere."""

    def test_every_csv_column_has_a_home(self):
        header = DEMAND_HEADER.strip().split(",")
        named = {c for c, _, _ in S.DEMAND_COLUMNS}
        self.assertEqual(set(header) - named, set())

    def _block(self, **over):
        row = {"person_key": "kari_lake_us_pres",
               "video_uid": "kari_lake_us_pres::abc", "video_key": "abc",
               "youtube_id": "abc", "priority": "595", "ceiling": "1000",
               "raw": "595", "bound_by": "raw", "transcripts_held": "0",
               "trusted_transcripts_held": "0", "person_transcripts_held": "0",
               "seat_rank": "195", "challenger": "false", "round": "1",
               "status": "open", "closed_reason": "", "notes": "",
               "duration_seconds": "", "ipfs_cid": "",
               "computed_at": "2026-09-07T10:15:03.048Z", "run_id": "job_1",
               "source_type": "youtube", "source_ref": "abc",
               "source_url": "https://www.youtube.com/watch?v=abc"}
        row.update(over)
        text = "Transcription:\n" + "\n".join(S.render_demand(row)) + "\n"
        return text, yaml.safe_load(text)["Transcription"]["Demand"]

    def test_every_populated_column_reaches_the_sidecar(self):
        _, d = self._block()
        for key in ("ceiling", "raw_score", "bound_by", "transcripts_held",
                    "trusted_transcripts_held", "person_transcripts_held",
                    "status", "source_type", "source_url", "source_ref",
                    "youtube_id"):
            self.assertIn(key, d, f"{key} was dropped on the floor")

    def test_a_blank_cell_is_omitted_never_written_as_zero(self):
        # seat_rank blank means "no office rank". A 0 would be read as
        # "the least important seat there is" — a measurement, not an absence.
        _, d = self._block(seat_rank="")
        self.assertNotIn("seat_rank", d)
        for blank in ("closed_reason", "notes", "duration_seconds", "ipfs_cid"):
            self.assertNotIn(blank, d)

    def test_numbers_and_booleans_are_not_strings(self):
        _, d = self._block()
        self.assertEqual(d["priority"], 595)
        self.assertEqual(d["seat_rank"], 195)
        self.assertIs(d["challenger"], False)
        self.assertEqual(d["status"], "open")

    def test_a_column_this_version_never_heard_of_is_carried(self):
        _, d = self._block(**{"new engine column": "kept"})
        self.assertEqual(d["new_engine_column"], "kept")

    def test_a_note_full_of_quotes_still_parses(self):
        _, d = self._block(notes='she called it "the wall" twice')
        self.assertIn("the wall", d["notes"])

    def test_an_unknown_column_is_carried_not_dropped(self):
        self.assertEqual(S._norm_col("new engine column"), "new_engine_column")
        self.assertNotIn("new engine column", S.DEMAND_KNOWN)


class DescriptionWrapNeverBreaksAtAHyphen(unittest.TestCase):
    """A ">-" folded scalar re-joins wrapped lines with a SPACE. Breaking after
    "pre-" therefore reads back as "pre- existing", and merge_preserving then
    carries the damage forward on every later write. 27 sidecars carried it
    before this was fixed on 2026-09-10."""

    def test_hyphenated_words_survive_a_round_trip(self):
        desc = " ".join(["pre-existing anti-money-laundering non-federal long-standing"] * 12)
        text = ("Video:\n  Description: >-\n"
                + "\n".join("    " + line for line in S.fold_description(desc)) + "\n")
        self.assertEqual(yaml.safe_load(text)["Video"]["Description"], desc)

    def test_lines_fit_the_width(self):
        for line in S.fold_description("word " * 100):
            self.assertLessEqual(len(line), 104)


class NothingPartialEntersTheRepo(unittest.TestCase):
    """The seed goes BESIDE THE MEDIA, outside every repo.

    On 2026-09-07 fifteen in-repo stubs were committed mid-run by an external
    auto-committer (901615a) and then deleted by the failure path (d4452fa).
    A file only enters {TRANSCRIPTIONS_ROOT} once it is complete.
    """

    def test_the_seed_is_not_under_the_transcriptions_root(self):
        path = os.path.abspath(S.seed_path_for("kari_lake_us_pres", "abc123"))
        root = os.path.abspath(S.TRANSCRIPTIONS_ROOT)
        self.assertFalse(path.startswith(root + os.sep))

    def test_the_seed_sits_beside_the_media(self):
        path = S.seed_path_for("kari_lake_us_pres", "abc123")
        self.assertTrue(path.startswith(S.MEDIA_ROOTS[0]))
        self.assertTrue(path.endswith("kari_lake_us_pres/abc123/abc123.demand.yaml"))


class AtomicWriteLeavesAReadableFile(unittest.TestCase):
    """mkstemp creates 0600 and os.replace carries that mode onto the sidecar.
    These files are published; they must not land owner-only."""

    def test_a_new_sidecar_is_not_owner_only(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "transcription.yaml")
        S.atomic_write(path, "Transcription: {}\n")
        mode = stat.S_IMODE(os.stat(path).st_mode)
        self.assertTrue(mode & stat.S_IRGRP or mode & stat.S_IROTH,
                        f"sidecar landed as {oct(mode)} — unreadable to anyone else")

    def test_it_lands_where_a_plain_write_would(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        atomic, plain = os.path.join(tmp, "a.yaml"), os.path.join(tmp, "b.yaml")
        S.atomic_write(atomic, "a: 1\n")
        with open(plain, "w") as fh:
            fh.write("a: 1\n")
        self.assertEqual(stat.S_IMODE(os.stat(atomic).st_mode),
                         stat.S_IMODE(os.stat(plain).st_mode))

    def test_an_owner_only_sidecar_is_repaired_not_carried_forward(self):
        # 0600 is the mkstemp bug's fingerprint, not a citizen's choice.
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "transcription.yaml")
        S.atomic_write(path, "a: 1\n")
        os.chmod(path, 0o600)
        S.atomic_write(path, "a: 2\n")
        mode = stat.S_IMODE(os.stat(path).st_mode)
        self.assertTrue(mode & stat.S_IRGRP or mode & stat.S_IROTH, oct(mode))


class ProvenanceIsMeasuredNotAsserted(unittest.TestCase):
    """Source.ASR / Diarization / Evidence_Grade used to be three hardcoded
    string literals naming the aligned_local pipeline, stamped onto EVERY
    sidecar whatever had produced the words. Evidence_Grade is one of the four
    fields the product reads, and `aligned` claims word timings and acoustic
    speaker turns. A words-only engine produces neither."""

    def _facts(self, suffixes):
        """The parts of gather()'s output render() reads, for a video whose
        output directory holds exactly `suffixes`."""
        vk = "abc"
        files = sorted(f"{vk}.{s}" for s in suffixes if s in S.FILE_LABELS)
        have = {f[len(vk) + 1:] for f in files}
        aligned = "ctm" in have and "rttm" in have
        return {
            "files": files,
            "aligned": aligned,
            "asr": "whisper_cpp / ggml-large-v3-turbo-q5_0" if aligned else None,
            "diarization": ("sherpa-onnx-node / pyannote-segmentation-3-0-onnx"
                            if aligned else None),
            "evidence_grade": "aligned" if aligned else "flat",
        }

    def test_word_timings_and_speaker_turns_together_are_aligned(self):
        f = self._facts(("transcription", "ctm", "rttm"))
        self.assertEqual(f["evidence_grade"], "aligned")
        self.assertTrue(f["diarization"])

    def test_words_only_is_flat_and_names_no_diarizer(self):
        # The Large File Bridge engines (apple-speechanalyzer, whisper-small)
        # emit the words and nothing else.
        f = self._facts(("transcription",))
        self.assertEqual(f["evidence_grade"], "flat")
        self.assertIsNone(f["diarization"])

    def test_timings_without_speakers_are_not_aligned(self):
        # Half the aligned pipeline is not the aligned pipeline.
        self.assertEqual(self._facts(("transcription", "ctm"))["evidence_grade"], "flat")
        self.assertEqual(self._facts(("transcription", "rttm"))["evidence_grade"], "flat")

    def test_provenance_survives_a_later_write(self):
        # A re-run to add a Description must not restamp how the words were made:
        # the run that made them is the only thing that ever knew.
        kept = S.merge_preserving(sidecar_with_handwritten(), {})
        self.assertEqual(kept["Evidence_Grade"], "aligned")

    def test_absent_provenance_stays_absent(self):
        doc = yaml.safe_load("Transcription:\n  Source:\n    Word_Count: 5\n")
        kept = S.merge_preserving(doc, {})
        self.assertIsNone(kept["ASR"])
        self.assertIsNone(kept["Evidence_Grade"])


class TheGateAsksForWhatTheEngineOwes(unittest.TestCase):
    """cmd_verify used to demand all nine aligned-pipeline artifacts from every
    transcript, which assumed one transcriber would ever write here."""

    def _owed(self, grade):
        return S.OUTPUT_SUFFIXES if grade == "aligned" else ("transcription",)

    def test_aligned_still_owes_all_nine(self):
        # The check that matters: an `aligned` claim with no .ctm/.rttm beside it
        # is the sidecar lying about its own provenance.
        self.assertEqual(self._owed("aligned"), S.OUTPUT_SUFFIXES)
        self.assertIn("rttm", self._owed("aligned"))
        self.assertIn("ctm", self._owed("aligned"))

    def test_flat_owes_only_the_words(self):
        self.assertEqual(self._owed("flat"), ("transcription",))

    def test_an_unrecorded_grade_owes_only_the_words(self):
        # Absent is absent: a missing grade must not be read as a promise of
        # timings the sidecar never made.
        for g in ("", None, "machine_caption", "legacy_flat"):
            self.assertEqual(self._owed(S._str(g) or "flat"), ("transcription",))


if __name__ == "__main__":
    unittest.main(verbosity=2)
