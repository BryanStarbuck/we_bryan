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
    python3 tools/wtc_sidecar.py write  <roster_key> <video_key> [...]
    python3 tools/wtc_sidecar.py verify [--all | <roster_key>/<video_key> ...]

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
import subprocess
import sys
import tempfile

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


def demand_row_for(video_key: str, csv_path: str):
    if not os.path.exists(csv_path):
        return None
    with open(csv_path, newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("video_key") == video_key:
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
    facts["demand"] = demand_row_for(video_key, demand_csv)
    return facts


# ---------------------------------------------------------------------------
# RULE 1 — merge, never clobber
# ---------------------------------------------------------------------------

def merge_preserving(existing, facts) -> dict:
    """Pull every hand-written value out of the file already on disk.

    Returns {"Description":..., "Topics":[...], "people":{label:{...}}, "extra":{...}}
    Anything returned here is written back verbatim.
    """
    kept = {"Description": None, "Topics": None, "people": {}, "extra": {}}
    if not isinstance(existing, dict):
        return kept
    body = existing.get("Transcription")
    if not isinstance(body, dict):
        return kept

    video = body.get("Video") if isinstance(body.get("Video"), dict) else {}
    if _str(video.get("Description")):
        kept["Description"] = video["Description"]
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
# Rendering
# ---------------------------------------------------------------------------

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
        A("    Description: >-")
        for line in str(kept["Description"]).strip().splitlines():
            A("      " + line.strip())
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
    A('    ASR: "whisper_cpp / ggml-large-v3-turbo-q5_0"')
    A('    Diarization: "sherpa-onnx-node / pyannote-segmentation-3-0-onnx"')
    A('    Evidence_Grade: "aligned"')
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

    row = facts["demand"]
    if row:
        A("  Demand:   # the join back to the server: which request this answers")
        A(f"    roster_key: {yq(row['person_key'])}")
        A(f"    video_uid: {yq(row['video_uid'])}")
        A(f"    video_key: {yq(row['video_key'])}")
        A(f"    priority: {row['priority']}")
        if row.get("seat_rank"):
            A(f"    seat_rank: {row['seat_rank']}")
        if row.get("challenger"):
            A(f"    challenger: {row['challenger']}")
        if row.get("round"):
            A(f"    round: {row['round']}")
        A(f"    demand_run_id: {yq(row['run_id'])}")
        A(f"    demand_generated_at: {yq(row['computed_at'])}")
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

        for suf in OUTPUT_SUFFIXES:
            p = os.path.join(d, f"{stem}.{suf}")
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                miss.append(f"missing:{suf}")

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


def split_target(target: str):
    if "/" in target:
        rk, vk = target.split("/", 1)
        return rk, vk
    # Bare video key: find its roster directory.
    for rk in sorted(os.listdir(TRANSCRIPTIONS_ROOT)):
        if os.path.isdir(os.path.join(TRANSCRIPTIONS_ROOT, rk, target)):
            return rk, target
    raise SystemExit(f"wtc_sidecar: cannot locate {target} under {TRANSCRIPTIONS_ROOT}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("USAGE")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write", help="build or refresh sidecars, preserving hand-written fields")
    w.add_argument("targets", nargs="+", metavar="roster_key/video_key")
    w.add_argument("--demand-csv", default=DEFAULT_DEMAND_CSV)
    w.set_defaults(func=cmd_write)

    v = sub.add_parser("verify", help="assert every sidecar is complete; exits non-zero if not")
    v.add_argument("targets", nargs="*", metavar="roster_key/video_key")
    v.add_argument("--all", action="store_true")
    v.set_defaults(func=cmd_verify)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
