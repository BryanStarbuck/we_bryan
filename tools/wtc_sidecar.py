#!/usr/bin/env python3
"""
wtc_sidecar.py — build and verify transcription.yaml sidecars.

WHY THIS FILE EXISTS AT ALL
---------------------------
Before this existed, the sidecar writer was improvised fresh in /tmp on every
run of prompts/p_download_videos.md. The outputs were committed and auditable
forever; the program that produced them was deleted by the next /tmp sweep. That
is backwards, and it is the reason this file is checked in.

WHAT A SIDECAR IS FOR
---------------------
It is the human-readable record of WHAT was transcribed and FROM WHERE.

It is NOT evidence. Per we_citizens pm/calc_engine_user_repo_ingest.mdx §17.R5,
the sidecar's bytes are never hashed into content_sha256, never landed, never
published, and read by no contract. Editing it does not make a transcript new.
The words are authenticated separately, by the manifest's text_sha256 over the
.transcription file.

The product reads exactly FOUR fields out of it — see reader_facts() below,
which mirrors transcription-sidecar.ts key-for-key. Everything else in the file
is for humans. That is not a reason to be sloppy with it; it is the reason the
verify pass has to check the human parts explicitly, because no contract will.

THE TWO RULES THAT SHAPE THE CODE
---------------------------------
1. NEVER DESTROY HAND-WRITTEN WORK. Description and Topics cannot be derived
   from anything on disk — they require reading the transcript. A generator that
   opens the file "w" and rebuilds it wipes them, and the result still parses and
   still carries a correct hash, so nothing downstream can tell. This module
   merges instead: it rebuilds the mechanical fields and carries the written ones
   forward untouched. See merge_preserving().

2. CAPTURE WHAT IS NOT RECOVERABLE LATER. The .info.json lives only beside the
   media, under a root the prompt calls "disposable once the words exist". A
   handful of facts in it are cheap to keep and impossible to recover once that
   directory is cleared or the video is edited, made private or deleted. They go
   in the Capture block. See UNRECOVERABLE.

USAGE
    python3 tools/wtc_sidecar.py seed   <roster_key>/<video_key> [...]
    python3 tools/wtc_sidecar.py write  <roster_key>/<video_key> [...]
    python3 tools/wtc_sidecar.py verify [--all | <roster_key>/<video_key> ...]

`seed` records the demand row beside the media, OUTSIDE every repo. NOTHING is
written into {TRANSCRIPTIONS_ROOT} until `write` has a complete sidecar to put
there — see seed_path_for() for the incident that rule comes from.

`verify` exits non-zero if anything is missing. It is the gate before Stage 8.

Requires: PyYAML. ffprobe and shasum on PATH for `write`.
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import textwrap

try:
    import yaml
except ImportError:
    sys.exit("wtc_sidecar: PyYAML is required.  pip3 install pyyaml")


# ---------------------------------------------------------------------------
# Locations. Resolved from this file so the tool works from any directory.
# ---------------------------------------------------------------------------

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPTIONS_ROOT = os.path.join(ROOT_DIR, "videos", "transcriptions")
MEDIA_ROOTS = [
    os.path.expanduser("~/T/_we_citizens/download/videos"),
    os.path.expanduser("~/T/_we_citizens/videos"),
]
DEFAULT_DEMAND_CSV = os.path.expanduser(
    "~/BGit/act3/data_we_citizens/video_demand.csv"
)

# The transcriber's own allowlist, from we_citizens
# code/packages/backend/src/modules/machine/machine-transcription.controller.ts
# ALLOWED_EXTENSIONS. Audio containers first: same words, a fraction of the bytes.
AUDIO_EXT = ("m4a", "opus", "mp3", "wav", "flac", "ogg")
VIDEO_EXT = ("mp4", "mov", "mkv", "webm", "avi")

# The nine files the CLI writes into --out with --also rttm,ctm.
OUTPUT_SUFFIXES = (
    "transcription", "segments.json", "segments.jsonl", "srt", "vtt",
    "script.txt", "fountain", "ctm", "rttm",
)

# Pretty names for the Files: mapping. Files is a MAPPING, never a sequence: it
# holds Transcript_SHA256 alongside the filenames and a YAML block cannot be both.
FILE_LABELS = {
    "transcription": "Plain_Text",
    "script.txt": "As_Broadcast_Script",
    "fountain": "Fountain",
    "segments.json": "Segments_JSON",
    "segments.jsonl": "Segments_JSONL",
    "ctm": "Word_Timings_CTM",
    "rttm": "Diarization_RTTM",
    "srt": "Subtitles_SRT",
    "vtt": "Subtitles_VTT",
}

# RULE 2. Cheap, and gone forever once the media root is cleared or the video
# changes. A political clip's reach at capture time is a real datum and it is
# never recoverable for a past date; a channel handle can be renamed or
# reassigned to a different human, a UC id cannot.
UNRECOVERABLE = [
    ("Channel_ID",    "channel_id"),
    ("Uploader_ID",   "uploader_id"),
    ("View_Count",    "view_count"),
    ("Like_Count",    "like_count"),
    ("Comment_Count", "comment_count"),
    ("Availability",  "availability"),
    ("Published_At",  "timestamp"),
]

# RULE 1. Written by a human from the transcript. Nothing on disk contains them.
HAND_WRITTEN = ("Description", "Topics")


# ---------------------------------------------------------------------------
# The product's reader, mirrored. Keep in lockstep with:
#   we_citizens/code/packages/backend/src/modules/groups/transcription-sidecar.ts
# ---------------------------------------------------------------------------

def _norm(key: str) -> str:
    return re.sub(r"[_\s-]", "", key.lower())


def _pick(obj, names):
    """Case- and underscore-insensitive lookup, first match in caller's order."""
    if not isinstance(obj, dict):
        return None
    table = {_norm(k): v for k, v in obj.items()}
    for name in names:
        hit = table.get(_norm(name))
        if hit is not None:
            return hit
    return None


def _as_object(v):
    return v if isinstance(v, dict) else None


def _str(v):
    return v.strip() if isinstance(v, str) else ""


def reader_facts(doc) -> dict:
    """The FOUR fields the product actually reads. Everything else is for humans.

    Mirrors parseTranscriptionSidecar() including its lenient spellings, so a
    file that passes here passes there.
    """
    if not isinstance(doc, dict):
        return {"source_url": "", "claimed_video_id": "", "title": "", "evidence_grade": ""}
    body = _as_object(_pick(doc, ["transcription"])) or doc
    video = _as_object(_pick(body, ["video"])) or body
    source = _as_object(_pick(body, ["source"])) or body
    return {
        "source_url": _str(_pick(video, ["url", "source_url", "video_url", "youtube_url", "watch_url"])),
        "claimed_video_id": _str(_pick(video, ["video_id", "youtube_id", "platform_id"])),
        "title": _str(_pick(video, ["title", "name"])),
        "evidence_grade": _str(_pick(source, ["evidence_grade", "grade"])),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sh(*args) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=120).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def media_file_for(roster_key: str, video_key: str):
    """Absolute path to the file that was transcribed, or None.

    Audio containers win over video ones: a directory may hold both after an
    older full-video run, and the transcriber discards the video stream anyway.
    A .fNNN pre-merge part is never a hit.
    """
    for root in MEDIA_ROOTS:
        d = os.path.join(root, roster_key, video_key)
        if not os.path.isdir(d):
            continue
        for ext in AUDIO_EXT + VIDEO_EXT:
            candidate = os.path.join(d, f"{video_key}.{ext}")
            if os.path.exists(candidate):
                return candidate
    return None


def demand_row_for(roster_key: str, video_key: str, csv_path: str):
    """Find this video's demand row. THE JOIN KEY IS video_uid, NEVER video_key.

    A bare video_key is NOT unique across the CSV and matching on it silently
    attaches another politician's row. The demand engine issues placeholder keys
    — v0001, v0002 ... — one per person, so `v0001` appears against dozens of
    roster_keys, each carrying a DIFFERENT youtube_id. render() builds Video.URL
    out of the matched row's youtube_id, and Video.URL is one of the four fields
    the product actually reads, so a bare-key match publishes a sidecar whose URL
    points at a different human's video. data_we_citizens/prompts/
    p_transcriptions_speakers_to_people.md states the same rule: join on
    video_uid — <person_key>::<video_key> — never on a bare video_key.

    Returns None when the row is absent, which is an absence, not a zero.
    """
    if not os.path.exists(csv_path):
        return None
    uid = f"{roster_key}::{video_key}"
    with open(csv_path, newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("video_uid") == uid:
                return row
            # Older snapshots predate the video_uid column. Fall back to the
            # PAIR, which is still unique; never to video_key alone.
            if (not row.get("video_uid")
                    and row.get("person_key") == roster_key
                    and row.get("video_key") == video_key):
                return row
    return None


def out_dir_for(roster_key: str, video_key: str) -> str:
    return os.path.join(TRANSCRIPTIONS_ROOT, roster_key, video_key)


def yq(value) -> str:
    """Quote a scalar for YAML.

    Political transcripts are full of phrases a writer wants in quotation marks.
    A double quote inside a double-quoted scalar is a parse error, so anything
    containing one is emitted as a single-quoted scalar instead.
    """
    s = str(value)
    if '"' in s:
        return "'" + s.replace("'", "''") + "'"
    return '"' + s.replace("\\", "\\\\") + '"'


def load_existing(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path) as fh:
            return yaml.safe_load(fh)
    except (OSError, yaml.YAMLError):
        return None


def _default_file_mode() -> int:
    """0666 minus the umask — exactly what open(path, "w") would have produced.

    The atomic write must be indistinguishable from a plain one in every way a
    reader can observe, and the mode is one of those ways. The mode of the file
    being replaced is deliberately NOT preserved: an owner-only sidecar is the
    fingerprint of the mkstemp bug this function fixes, not a citizen's choice,
    and preserving it would carry the bug forward on every re-run.
    """
    cur = os.umask(0)
    os.umask(cur)
    return 0o666 & ~cur


def atomic_write(path: str, text: str) -> None:
    """Write via a temp file in the same directory, then rename.

    A crash mid-write must not leave a truncated sidecar that still parses.
    """
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".sidecar-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        # mkstemp creates 0600 and os.replace carries that mode onto the sidecar,
        # so an unfixed atomic write silently makes this one file unreadable to
        # everyone but the owner while every hand-written sidecar beside it is
        # 0644. These files are meant to be published; give them the mode a
        # normal `open(path, "w")` would have produced.
        os.chmod(tmp, _default_file_mode())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ---------------------------------------------------------------------------
# Gathering the mechanical facts
# ---------------------------------------------------------------------------

def gather(roster_key: str, video_key: str, demand_csv: str) -> dict:
    out = out_dir_for(roster_key, video_key)
    media = media_file_for(roster_key, video_key)
    if media is None:
        raise FileNotFoundError(f"no media on disk for {roster_key}/{video_key}")

    facts = {"roster_key": roster_key, "video_key": video_key,
             "media": media, "media_dir": os.path.dirname(media)}

    # --- media
    facts["sha256"] = (sh("shasum", "-a", "256", media) or " ").split()[0]
    facts["bytes"] = os.path.getsize(media)
    probe = {}
    raw = sh("ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", media)
    if raw:
        try:
            probe = json.loads(raw)
        except json.JSONDecodeError:
            probe = {}
    dur = probe.get("format", {}).get("duration")
    facts["duration"] = int(float(dur)) if dur else None
    streams = probe.get("streams", [])
    facts["acodec"] = next((s.get("codec_name") for s in streams if s.get("codec_type") == "audio"), None)
    facts["vcodec"] = next((s.get("codec_name") for s in streams if s.get("codec_type") == "video"), None)
    facts["container"] = media.rsplit(".", 1)[1]
    facts["kind"] = "video" if facts["vcodec"] else "audio"

    # --- metadata beside the media
    info, info_name = {}, None
    ij = os.path.join(facts["media_dir"], f"{video_key}.info.json")
    if os.path.exists(ij):
        try:
            with open(ij) as fh:
                info = json.load(fh)
            info_name = f"{video_key}.info.json"
        except (OSError, json.JSONDecodeError):
            info = {}
    legacy = {}
    vy = os.path.join(facts["media_dir"], f"{video_key}.video.yaml")
    if os.path.exists(vy):
        try:
            with open(vy) as fh:
                legacy = yaml.safe_load(fh) or {}
            info_name = info_name or f"{video_key}.video.yaml"
        except (OSError, yaml.YAMLError):
            legacy = {}

    facts["metadata_from"] = info_name
    facts["title"] = info.get("title") or legacy.get("title")
    facts["channel"] = info.get("uploader") or info.get("channel")
    upload = info.get("upload_date")
    if upload and len(str(upload)) == 8:
        u = str(upload)
        facts["recorded"] = f"{u[0:4]}-{u[4:6]}-{u[6:8]}"
    else:
        pub = legacy.get("published_at")
        facts["recorded"] = str(pub)[:10] if pub else None
    facts["downloader"] = (
        f"yt-dlp {sh('yt-dlp', '--version')}".strip()
        if not legacy.get("yt_dlp_version")
        else f"yt-dlp {legacy['yt_dlp_version']}"
    )

    # RULE 2 — the unrecoverable handful.
    facts["capture"] = []
    for label, key in UNRECOVERABLE:
        if key in info and info[key] not in (None, ""):
            v = info[key]
            if key == "timestamp":
                try:
                    v = datetime.datetime.fromtimestamp(
                        int(v), datetime.timezone.utc).isoformat()
                except (OSError, ValueError, OverflowError):
                    v = str(v)
            facts["capture"].append((label, v))
    if facts["capture"]:
        facts["captured_at"] = datetime.datetime.fromtimestamp(
            os.path.getmtime(ij if info_name else media)).astimezone().replace(microsecond=0).isoformat()

    # --- transcription outputs
    seg = {}
    segp = os.path.join(out, f"{video_key}.segments.json")
    if os.path.exists(segp):
        try:
            with open(segp) as fh:
                seg = json.load(fh)
        except (OSError, json.JSONDecodeError):
            seg = {}
    facts["language"] = seg.get("language") or "en"
    facts["canonical_id"] = seg.get("canonical_id") or seg.get("id")
    facts["segments"] = len(seg.get("segments") or seg.get("Segments") or [])

    tp = os.path.join(out, f"{video_key}.transcription")
    with open(tp, "rb") as fh:
        blob = fh.read()
    facts["words"] = len(blob.decode("utf-8", "replace").split())
    facts["transcript_sha256"] = hashlib.sha256(blob).hexdigest()
    facts["finished"] = datetime.datetime.fromtimestamp(
        os.path.getmtime(tp)).astimezone().isoformat()
    facts["downloaded"] = datetime.datetime.fromtimestamp(
        os.path.getmtime(media)).astimezone().isoformat()

    # --- speakers, from the rttm
    turns, secs = collections.Counter(), collections.Counter()
    rttm = os.path.join(out, f"{video_key}.rttm")
    if os.path.exists(rttm):
        with open(rttm) as fh:
            for line in fh:
                p = line.split()
                if len(p) >= 8 and p[0] == "SPEAKER":
                    turns[p[7]] += 1
                    try:
                        secs[p[7]] += float(p[4])
                    except ValueError:
                        pass
    facts["turns"], facts["secs"] = turns, secs

    facts["files"] = sorted(
        f for f in os.listdir(out)
        if f.startswith(video_key + ".") and f[len(video_key) + 1:] in FILE_LABELS
    )

    # --- PROVENANCE, DERIVED FROM WHAT IS ACTUALLY ON DISK.
    # These three fields used to be three hardcoded string literals naming the
    # aligned_local pipeline, written onto EVERY sidecar regardless of what had
    # produced the words. That is a fabricated provenance claim, and it is the
    # one kind of error this file exists to refuse: Source.Evidence_Grade is one
    # of the FOUR fields the product actually reads (reader_facts()), and
    # `aligned` tells a scorer it is holding word timings and acoustic speaker
    # turns. A transcript made by a words-only engine has neither, and stamping
    # `aligned` on it inflates confidence on a claim nothing can support.
    #
    # The evidence is on disk and needs no configuration: the aligned pipeline
    # is the only thing that emits BOTH a .ctm (word timings) and a .rttm
    # (speaker turns), so their presence IS the grade. Words alone are `flat`
    # (transcription.mdx §5.1 — a closed vocabulary; `flat` is the entry for
    # "words only"). A lower grade lowers stated confidence and renders a
    # caveat; §5.1 is explicit that it NEVER blocks an award, so recording the
    # true one costs the movement nothing and buys it an honest read.
    have = {f[len(video_key) + 1:] for f in facts["files"]}
    facts["aligned"] = "ctm" in have and "rttm" in have
    if facts["aligned"]:
        facts["asr"] = "whisper_cpp / ggml-large-v3-turbo-q5_0"
        facts["diarization"] = "sherpa-onnx-node / pyannote-segmentation-3-0-onnx"
        facts["evidence_grade"] = "aligned"
    else:
        facts["asr"] = None            # supplied by --asr, or kept from the file
        facts["diarization"] = None    # absent is absent: nothing diarized this
        facts["evidence_grade"] = "flat"
    # The CSV is regenerated every engine run, so a long batch can reach here
    # after its row changed or closed. The selection-time seed is what the row
    # actually said when the work started; prefer the live row, fall back to it.
    facts["demand"] = (demand_row_for(roster_key, video_key, demand_csv)
                       or load_seed(roster_key, video_key))
    return facts


# ---------------------------------------------------------------------------
# RULE 1 — merge, never clobber
# ---------------------------------------------------------------------------

def merge_preserving(existing, facts) -> dict:
    """Pull every hand-written value out of the file already on disk.

    Returns {"Description":..., "Topics":[...], "people":{label:{...}}, "extra":{...}}
    Anything returned here is written back verbatim.
    """
    kept = {"Description": None, "Topics": None, "people": {}, "extra": {},
            "ASR": None, "Diarization": None, "Evidence_Grade": None}
    if not isinstance(existing, dict):
        return kept
    body = existing.get("Transcription")
    if not isinstance(body, dict):
        return kept

    video = body.get("Video") if isinstance(body.get("Video"), dict) else {}
    if _str(video.get("Description")):
        kept["Description"] = video["Description"]

    # Provenance is established once, by the run that made the words, and can
    # never be re-derived afterwards from a repo directory alone. A later
    # `write` (to add a Description, say) must not silently restamp it.
    source = body.get("Source") if isinstance(body.get("Source"), dict) else {}
    for f in ("ASR", "Diarization", "Evidence_Grade"):
        if _str(source.get(f)):
            kept[f] = source[f]
    topics = body.get("Topics")
    if isinstance(topics, list) and topics:
        kept["Topics"] = topics

    # A human may have identified a speaker. "Unidentified" is the generator's
    # own placeholder and carries no information, so it is not preserved.
    people = body.get("People_in_Video")
    if isinstance(people, dict):
        for _, entry in people.items():
            if not isinstance(entry, dict):
                continue
            label = entry.get("Speaker_Label")
            name = _str(entry.get("Name"))
            if label and name and name.lower() != "unidentified":
                kept["people"][label] = {
                    "Name": name,
                    "Role": entry.get("Role"),
                    "Subject": entry.get("Subject"),
                }

    # Forward compatibility: any top-level block this version does not know
    # about is a fact somebody added deliberately. Carry it rather than drop it.
    known = {"Video", "Media", "People_in_Video", "Topics", "Source",
             "Timestamps", "Files", "Demand", "Capture"}
    for k, v in body.items():
        if k not in known:
            kept["extra"][k] = v
    return kept


# ---------------------------------------------------------------------------
# The demand row
# ---------------------------------------------------------------------------

# Every column of {DATA_REPO}/video_demand.csv, in CSV order, with the name it
# takes in the sidecar and whether it is emitted bare (numbers, booleans) or
# quoted. The whole row is carried: the CSV is regenerated each engine run, so
# a column dropped here is a fact that can never be recovered for this date.
# "bare" values are written unquoted so a reader gets a number or a boolean
# rather than a string; anything free-text is quoted.
DEMAND_COLUMNS = [
    ("person_key",               "roster_key",               "quoted"),
    ("video_uid",                "video_uid",                "quoted"),
    ("video_key",                "video_key",                "quoted"),
    ("youtube_id",               "youtube_id",               "quoted"),
    ("duration_seconds",         "duration_seconds",         "bare"),
    ("priority",                 "priority",                 "bare"),
    ("ceiling",                  "ceiling",                  "bare"),
    ("raw",                      "raw_score",                "bare"),
    ("bound_by",                 "bound_by",                 "quoted"),
    ("transcripts_held",         "transcripts_held",         "bare"),
    ("trusted_transcripts_held", "trusted_transcripts_held", "bare"),
    ("person_transcripts_held",  "person_transcripts_held",  "bare"),
    ("seat_rank",                "seat_rank",                "bare"),
    ("challenger",               "challenger",               "bare"),
    ("round",                    "round",                    "bare"),
    ("status",                   "status",                   "quoted"),
    ("closed_reason",            "closed_reason",            "quoted"),
    ("notes",                    "notes",                    "quoted"),
    ("computed_at",              "demand_generated_at",      "quoted"),
    ("run_id",                   "demand_run_id",            "quoted"),
    ("source_type",              "source_type",              "quoted"),
    ("source_url",               "source_url",               "quoted"),
    ("ipfs_cid",                 "ipfs_cid",                 "quoted"),
    ("source_ref",               "source_ref",               "quoted"),
]

DEMAND_KNOWN = {c for c, _, _ in DEMAND_COLUMNS}


def _norm_col(col: str) -> str:
    """A CSV header this table has no name for, made safe as a YAML key."""
    return re.sub(r"[^A-Za-z0-9_]+", "_", col.strip()).strip("_") or "unnamed_column"


def fold_description(text) -> list:
    """Wrap a hand-written Description into lines for a ">-" folded scalar.

    Never break at a hyphen: a folded scalar re-joins lines with a SPACE, so a
    break after "pre-" reads back as "pre- existing", and merge_preserving then
    carries the damage forward on every later write.
    """
    body = " ".join(str(text).split())
    return textwrap.wrap(body, width=104, break_on_hyphens=False,
                         break_long_words=False) or [""]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_demand(row) -> list:
    """The Demand block: THE WHOLE CSV ROW, not a selection from it.

    video_demand.csv is REGENERATED every engine run. Today's priority,
    transcripts_held and status are overwritten by tomorrow's, and the values
    that were true WHEN THIS TRANSCRIPT WAS MADE then exist nowhere else. This
    block is the only record of why this video was worked on.

    ABSENT IS ABSENT: a blank cell is omitted, never written as 0. seat_rank is
    the one that bites — blank means "no office rank", and a 0 would be read as
    "the least important seat there is", which is a measurement, not an absence.
    """
    L = ["  Demand:   # the join back to the server: which request this answers",
         "    # The WHOLE demand row. The CSV is regenerated every engine run, so",
         "    # this is the only record of what it said when the work was done.",
         f"    roster_key: {yq(row['person_key'])}"]
    for col, key, kind in DEMAND_COLUMNS:
        if col == "person_key":
            continue
        raw = (row.get(col) or "").strip()
        if raw == "":
            continue
        L.append(f"    {key}: " + (raw if kind == "bare" else yq(raw)))
    # Any column a newer engine added that DEMAND_COLUMNS has no name for. The
    # schema is expandable and a dropped column is a fact destroyed.
    for col, val in row.items():
        if col in DEMAND_KNOWN or col is None:
            continue
        val = (val or "").strip()
        if val:
            L.append(f"    {_norm_col(col)}: {yq(val)}")
    return L


def render(facts, kept) -> str:
    vk = facts["video_key"]
    yid = (facts["demand"] or {}).get("youtube_id") or vk
    url = f"https://www.youtube.com/watch?v={yid}"
    L = []
    A = L.append

    A("# transcription.yaml — the human-readable record of WHAT was transcribed")
    A("# and FROM WHERE. Written by tools/wtc_sidecar.py; see that file for why")
    A("# this is checked-in code and not an improvisation.")
    A("#")
    A("# NOT EVIDENCE (pm/calc_engine_user_repo_ingest.mdx §17.R5): these bytes are")
    A("# never hashed into content_sha256, never landed, never published. The words")
    A("# are authenticated by the manifest's text_sha256 over the .transcription.")
    A("# The product reads only Video.URL, Video.Video_ID, Video.Title and")
    A("# Source.Evidence_Grade. The rest is for humans.")
    A("#")
    A("# ABSENT IS ABSENT: a field this run could not establish is omitted. There")
    A("# are no placeholders, because a zero read later is a measurement.")
    A("Transcription:")
    A("")

    A("  Video:")
    if facts["title"]:
        A(f"    Title: {yq(facts['title'])}")
    if kept["Description"]:
        # A ">-" folded scalar comes back from the parser as ONE long line, so
        # re-emitting it verbatim collapses the wrapping a little more on every
        # run until the description is a single 900-character line. Re-wrap it.
        # This is the one block a human is actually meant to read.
        A("    Description: >-")
        for line in fold_description(kept["Description"]):
            A("      " + line)
    A(f"    URL: {yq(url)}")
    A(f"    Video_ID: {yq(vk)}")
    if facts["channel"]:
        A(f"    Show: {yq(facts['channel'])}")
    if facts["duration"]:
        d = facts["duration"]
        A(f"    Runtime: \"{d // 3600:02d}:{d % 3600 // 60:02d}:{d % 60:02d}\"")
    A(f"    Language: {yq(facts['language'])}")
    A("")

    A("  Media:")
    A(f"    File: {yq(os.path.basename(facts['media']))}")
    A(f"    SHA256: {yq(facts['sha256'])}")
    A(f"    Bytes: {facts['bytes']}")
    if facts["duration"]:
        A(f"    Duration_Seconds: {facts['duration']}")
    A(f"    Container: {yq(facts['container'])}")
    if facts["acodec"]:
        A(f"    Audio_Codec: {yq(facts['acodec'])}")
    if facts["vcodec"]:
        A(f"    Video_Codec: {yq(facts['vcodec'])}")
    A(f"    Media_Kind: {yq(facts['kind'])}")
    A(f"    Source_URL: {yq(url)}")
    if facts["downloader"]:
        A(f"    Downloader: {yq(facts['downloader'])}")
    if facts["metadata_from"]:
        A(f"    Metadata_From: {yq(facts['metadata_from'])}")
    A(f"    Stored_At: {yq(facts['media_dir'] + '/')}")
    A("")

    if facts["capture"]:
        A("  # CAPTURE — facts about the posting AT THE MOMENT IT WAS FETCHED.")
        A("  # These live nowhere else. The .info.json they came from sits beside the")
        A("  # media, outside every repo, under a root that is treated as disposable")
        A("  # once the words exist. View counts change hourly and are never")
        A("  # recoverable for a past date; a video can be edited, made private or")
        A("  # deleted; a channel handle can be renamed or reassigned to a different")
        A("  # human, which is why Channel_ID is kept and not just the handle.")
        A("  Capture:")
        for label, value in facts["capture"]:
            A(f"    {label}: {yq(value) if isinstance(value, str) else value}")
        if facts.get("captured_at"):
            A(f"    Captured_At: {yq(facts['captured_at'])}")
        A("")

    turns = facts["turns"]
    if turns:
        total = sum(facts["secs"].values()) or 1.0
        named = kept["people"]
        if not named:
            A("  # No cluster is matched to a named human: the transcript does not")
            A("  # identify who is speaking. Subject is therefore OMITTED rather than")
            A("  # assigned to whichever label sorted first — that is the one field a")
            A("  # scorer trusts, and a default there is a fabricated attribution.")
        A("  People_in_Video:")
        for i, (label, n) in enumerate(sorted(turns.items()), start=1):
            A(f"    Person_{i}:")
            hand = named.get(label)
            if hand:
                A(f"      Name: {yq(hand['Name'])}")
                if hand.get("Role"):
                    A(f"      Role: {yq(hand['Role'])}")
                if hand.get("Subject") is not None:
                    A(f"      Subject: {'true' if hand['Subject'] else 'false'}")
            else:
                A('      Name: "Unidentified"')
                A('      Role: "Diarized speaker cluster; the transcript does not name it"')
            A(f"      Speaker_Label: {yq(label)}")
            A(f"      Share_Of_Speech: \"{facts['secs'][label] / total * 100:.1f}%\"")
            A(f"      Turns: {n}")
        A("")

    if kept["Topics"]:
        A("  Topics:")
        for t in kept["Topics"]:
            A(f"    - {yq(t)}")
        A("")

    A("  Source:")
    if facts["canonical_id"]:
        A(f"    Canonical_ID: {yq(facts['canonical_id'])}")
    A(f"    Transcribed: {yq(facts['finished'])}")
    # Precedence: what this run was TOLD (--asr / --evidence-grade) > what the
    # file already says (the run that made the words) > what the artifacts on
    # disk prove. Diarization is omitted entirely when nothing diarized this
    # recording — absent is absent, and an empty string reads as a measurement.
    asr = facts.get("asr_override") or kept.get("ASR") or facts.get("asr")
    diar = facts.get("diarization_override") or kept.get("Diarization") or facts.get("diarization")
    grade = (facts.get("evidence_grade_override") or kept.get("Evidence_Grade")
             or facts.get("evidence_grade"))
    if asr:
        A(f"    ASR: {yq(asr)}")
    if diar:
        A(f"    Diarization: {yq(diar)}")
    A(f"    Evidence_Grade: {yq(grade)}")
    A(f"    Word_Count: {facts['words']}")
    if facts["segments"]:
        A(f"    Segments: {facts['segments']}")
    A("")

    A("  Timestamps:")
    A(f"    Downloaded_At: {yq(facts['downloaded'])}")
    A(f"    Transcription_Finished: {yq(facts['finished'])}")
    if facts["recorded"]:
        A(f"    Recorded: {yq(facts['recorded'])}   # from upload_date. NEVER the decode date.")
    A("")

    A("  Files:")
    for f in facts["files"]:
        A(f"    {FILE_LABELS[f[len(vk) + 1:]]}: {yq(f)}")
    A(f"    Transcript_SHA256: {yq(facts['transcript_sha256'])}")
    A("")

    if facts["demand"]:
        for line in render_demand(facts["demand"]):
            A(line)
        A("")

    if kept["extra"]:
        A("  # Blocks this version of the tool does not know about, carried forward")
        A("  # verbatim rather than dropped.")
        for k, v in kept["extra"].items():
            dumped = yaml.safe_dump({k: v}, sort_keys=False, allow_unicode=True,
                                    default_flow_style=False, width=100)
            for line in dumped.rstrip().splitlines():
                A("  " + line)
        A("")

    return "\n".join(L).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def seed_path_for(roster_key: str, video_key: str) -> str:
    """Where the selection-time demand snapshot goes: BESIDE THE MEDIA, OUTSIDE
    THE REPO.

    It is deliberately not {TRANSCRIPTIONS_ROOT}. A file placed in the repo
    before the words exist is a partial transcript, and the machine running this
    is swept by an external auto-committer that knows nothing about this run: it
    will commit the stub, the transcription will then fail, and the failure path
    will delete a file that is by then part of the repo's history. That is
    exactly what happened on 2026-09-07 — fifteen stubs committed by
    "Bryan 26 Tower" (901615a) and removed again by d4452fa. Nothing enters the
    repo until it is complete.
    """
    return os.path.join(MEDIA_ROOTS[0], roster_key, video_key,
                        f"{video_key}.demand.yaml")


def load_seed(roster_key: str, video_key: str):
    """The demand row as it read AT SELECTION TIME, if a seed was written.

    The demand CSV is regenerated every engine run, so by the time a long batch
    reaches Stage 7 the row it selected may have a different priority, a
    different status, or be gone. The seed is what that row actually said.
    """
    doc = load_existing(seed_path_for(roster_key, video_key))
    if isinstance(doc, dict):
        row = doc.get("demand_row")
        if isinstance(row, dict):
            return {k: ("" if v is None else str(v)) for k, v in row.items()}
    return None


def cmd_seed(args) -> int:
    rc = 0
    for target in args.targets:
        roster_key, video_key = split_target(target, must_exist=False)
        row = demand_row_for(roster_key, video_key, args.demand_csv)
        if row is None:
            print(f"  FAIL  {roster_key}/{video_key}: no row in {args.demand_csv} "
                  f"for video_uid {roster_key}::{video_key}")
            rc = 1
            continue
        path = seed_path_for(roster_key, video_key)
        # Belt and braces: this must never land in the repo, whatever the roots
        # are set to. A seed inside {TRANSCRIPTIONS_ROOT} is the bug this
        # command exists to remove.
        if os.path.abspath(path).startswith(os.path.abspath(TRANSCRIPTIONS_ROOT) + os.sep):
            print(f"  FAIL  {roster_key}/{video_key}: refusing to seed inside the repo")
            rc = 1
            continue
        now = datetime.datetime.now().astimezone().isoformat()
        L = ["# Demand snapshot, captured when this video was SELECTED.",
             "#",
             "# Written by tools/wtc_sidecar.py seed. It lives beside the media,",
             "# OUTSIDE every repo, on purpose: until the words exist there is",
             "# nothing to commit, and a stub inside the repo is a partial",
             "# transcript that an auto-committer will publish and a failure path",
             "# will then delete.",
             "#",
             "# video_demand.csv is REGENERATED every engine run. This is the only",
             "# record of what the row said when the work was started.",
             f"selected_at: {yq(now)}",
             f"roster_key: {yq(roster_key)}",
             f"video_key: {yq(video_key)}",
             f"video_uid: {yq(row.get('video_uid') or f'{roster_key}::{video_key}')}",
             f"demand_csv: {yq(os.path.abspath(args.demand_csv))}",
             "demand_row:"]
        for col, _, _ in DEMAND_COLUMNS:
            val = (row.get(col) or "").strip()
            if val:
                L.append(f"  {col}: {yq(val)}")
        for col, val in row.items():
            if col in DEMAND_KNOWN or col is None:
                continue
            val = (val or "").strip()
            if val:
                L.append(f"  {_norm_col(col)}: {yq(val)}")
        atomic_write(path, "\n".join(L) + "\n")
        print(f"  seeded {roster_key}/{video_key} -> {path}")
    return rc


def cmd_write(args) -> int:
    rc = 0
    for target in args.targets:
        roster_key, video_key = split_target(target)
        path = os.path.join(out_dir_for(roster_key, video_key), "transcription.yaml")
        try:
            facts = gather(roster_key, video_key, args.demand_csv)
        except (FileNotFoundError, OSError) as err:
            print(f"  FAIL  {roster_key}/{video_key}: {err}")
            rc = 1
            continue
        facts["asr_override"] = args.asr
        facts["diarization_override"] = args.diarization
        facts["evidence_grade_override"] = args.evidence_grade
        existing = load_existing(path)
        kept = merge_preserving(existing, facts)
        atomic_write(path, render(facts, kept))

        # Prove the merge actually preserved. This is the whole point of the
        # module, so it is asserted rather than assumed.
        after = merge_preserving(load_existing(path), facts)
        lost = [f for f in HAND_WRITTEN if kept.get(f) and not after.get(f)]
        if lost:
            print(f"  FAIL  {roster_key}/{video_key}: merge dropped {lost}")
            rc = 1
            continue
        note = []
        if kept["Description"]:
            note.append("kept Description")
        if kept["Topics"]:
            note.append(f"kept {len(kept['Topics'])} Topics")
        if kept["people"]:
            note.append(f"kept {len(kept['people'])} named speaker(s)")
        if facts["capture"]:
            note.append(f"Capture[{len(facts['capture'])}]")
        print(f"  wrote {roster_key}/{video_key}"
              + (f"  ({', '.join(note)})" if note else "  (new)"))
    return rc


def cmd_verify(args) -> int:
    targets = args.targets
    if args.all or not targets:
        targets = []
        for rk in sorted(os.listdir(TRANSCRIPTIONS_ROOT)):
            rkd = os.path.join(TRANSCRIPTIONS_ROOT, rk)
            if not os.path.isdir(rkd):
                continue
            for vk in sorted(os.listdir(rkd)):
                if os.path.isdir(os.path.join(rkd, vk)):
                    targets.append(f"{rk}/{vk}")

    problems, unrepairable = [], []
    for target in targets:
        roster_key, video_key = split_target(target)
        d = out_dir_for(roster_key, video_key)
        miss = []

        # The words themselves. A directory whose video_key does not match its
        # filenames is a LEGACY layout, not an error: find the real stem.
        stems = {f[: -len(".transcription")] for f in os.listdir(d)
                 if f.endswith(".transcription")}
        if not stems:
            problems.append((target, ["NO_TRANSCRIPT"]))
            continue
        stem = video_key if video_key in stems else sorted(stems)[0]

        sc = os.path.join(d, "transcription.yaml")
        if not os.path.exists(sc):
            miss.append("NO_SIDECAR")
            problems.append((target, miss))
            continue
        doc = load_existing(sc)
        if doc is None:
            miss.append("SIDECAR_DOES_NOT_PARSE")
            problems.append((target, miss))
            continue

        # WHICH ARTIFACTS ARE OWED DEPENDS ON WHAT MADE THE WORDS. This loop used
        # to demand all nine OUTPUT_SUFFIXES from every transcript, which silently
        # assumed the aligned_local pipeline was the only transcriber that would
        # ever write here. It is not: a words-only engine (transcription.mdx §5.1
        # `flat`) emits the .transcription and nothing else, and there is no .srt
        # for it to be missing. Demanding one reports a fabricated defect and, worse,
        # the only way to satisfy it would be to synthesise timings nothing measured.
        # So the grade the sidecar RECORDS is what sets the bar. `aligned` still owes
        # all nine, and that is the check that matters — an aligned claim with no
        # .ctm or .rttm beside it is the sidecar lying about its own provenance.
        grade = _str((reader_facts(doc) or {}).get("evidence_grade")) or "flat"
        owed = OUTPUT_SUFFIXES if grade == "aligned" else ("transcription",)
        for suf in owed:
            fp = os.path.join(d, f"{stem}.{suf}")
            if not os.path.exists(fp) or os.path.getsize(fp) == 0:
                miss.append(f"missing:{suf}")

        # The four the product actually reads.
        for k, v in reader_facts(doc).items():
            if not v:
                miss.append(f"reader:{k}")

        # The parts no contract checks, which is exactly why we check them.
        body = doc.get("Transcription") if isinstance(doc, dict) else None
        body = body if isinstance(body, dict) else {}
        video = body.get("Video") if isinstance(body.get("Video"), dict) else {}
        media = body.get("Media") if isinstance(body.get("Media"), dict) else {}
        if not _str(video.get("Description")):
            miss.append("NO_DESCRIPTION")
        if not body.get("Topics"):
            miss.append("NO_TOPICS")
        # A sidecar predating this schema, whose media has since been cleared,
        # cannot be repaired: the SHA-256 describes bytes that no longer exist
        # anywhere. Distinguish that from a gap this run could actually close,
        # so the gate fails on what is fixable and REPORTS what is not.
        legacy = (
            not media
            and not body.get("Demand")
            and media_file_for(roster_key, video_key) is None
        )
        if legacy:
            unrepairable.append(
                (target, "pre-schema sidecar; its media is gone, so Media.SHA256 "
                         "is unrecoverable. Left as written.")
            )
        else:
            if not media.get("SHA256"):
                miss.append("NO_MEDIA_SHA256")
            if not body.get("Demand"):
                miss.append("NO_DEMAND")

        # The hash must describe the bytes actually on disk.
        tp = os.path.join(d, f"{stem}.transcription")
        files = body.get("Files") if isinstance(body.get("Files"), dict) else {}
        claimed = _str(files.get("Transcript_SHA256"))
        if claimed and os.path.exists(tp):
            with open(tp, "rb") as fh:
                actual = hashlib.sha256(fh.read()).hexdigest()
            if actual != claimed:
                miss.append("TRANSCRIPT_SHA_MISMATCH")

        if miss:
            problems.append((target, miss))

    ok = len(targets) - len(problems) - len(unrepairable)
    print(f"sidecars complete: {ok} / {len(targets)}"
          + (f"   ({len(unrepairable)} legacy, reported not gated)" if unrepairable else ""))
    for t, m in problems:
        print(f"  INCOMPLETE  {t}: {', '.join(m)}")
    for t, why in unrepairable:
        print(f"  LEGACY      {t}: {why}")
    if problems:
        print("\nFix these and RE-RUN. Fixing one miss routinely reveals the next.")
    # Legacy files do not fail the gate: nothing can close those gaps, and a gate
    # that can never go green stops being read.
    return 1 if problems else 0


def split_target(target: str, must_exist: bool = True):
    if "/" in target:
        rk, vk = target.split("/", 1)
        return rk, vk
    # Bare video key: find its roster directory. `seed` runs before any repo
    # directory exists, so it passes must_exist=False and requires the pair.
    for rk in sorted(os.listdir(TRANSCRIPTIONS_ROOT)):
        if os.path.isdir(os.path.join(TRANSCRIPTIONS_ROOT, rk, target)):
            return rk, target
    if not must_exist:
        raise SystemExit(
            f"wtc_sidecar: give this one as roster_key/{target} — the roster key "
            "cannot be inferred before the directory exists, and it is the "
            "directory segment everywhere else in this product."
        )
    raise SystemExit(f"wtc_sidecar: cannot locate {target} under {TRANSCRIPTIONS_ROOT}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("USAGE")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write", help="build or refresh sidecars, preserving hand-written fields")
    w.add_argument("targets", nargs="+", metavar="roster_key/video_key")
    w.add_argument("--demand-csv", default=DEFAULT_DEMAND_CSV)
    w.add_argument("--asr", default=None,
                   help="the engine that actually produced the words, e.g. "
                        "'apple-speechanalyzer (Large File Bridge)'. Recorded as "
                        "Source.ASR. Without it the sidecar keeps what it already "
                        "says, and a new one states only what the artifacts prove.")
    w.add_argument("--diarization", default=None,
                   help="the diarizer, when one ran. Omitted when none did.")
    w.add_argument("--evidence-grade", default=None,
                   help="override the grade derived from the artifacts on disk "
                        "(transcription.mdx §5.1: aligned | attested | "
                        "machine_caption | flat | legacy_*).")
    w.set_defaults(func=cmd_write)

    sd = sub.add_parser("seed", help="record the demand row beside the media, OUTSIDE the repo")
    sd.add_argument("targets", nargs="+", metavar="roster_key/video_key")
    sd.add_argument("--demand-csv", default=DEFAULT_DEMAND_CSV)
    sd.set_defaults(func=cmd_seed)

    v = sub.add_parser("verify", help="assert every sidecar is complete; exits non-zero if not")
    v.add_argument("targets", nargs="*", metavar="roster_key/video_key")
    v.add_argument("--all", action="store_true")
    v.set_defaults(func=cmd_verify)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
