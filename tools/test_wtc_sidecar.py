#!/usr/bin/env python3
"""Tests for wtc_sidecar.py.

The first two are the ones that matter: they pin the exact bug that produced
this tool. Everything else is a guard on the reader contract.

    python3 tools/test_wtc_sidecar.py
"""
import os
import sys
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
