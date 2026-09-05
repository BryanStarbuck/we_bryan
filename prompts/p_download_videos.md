p_download_videos

Download political videos into this citizen's own We The Citizens User Data Repo,
transcribe them on THIS machine, and commit the transcriptions so the movement can
read them.

This prompt is run from inside ONE citizen's personal user data repo. It finds the
other We The Citizens repos on this machine by itself, reads the shared demand list
to learn which videos the movement still needs, downloads the ones this citizen does
not already hold, transcribes them against a localhost install, writes a
transcription.yaml sidecar beside every result, and pushes.

Read every stage before starting. Stages run in order. A stage that cannot complete
STOPS the run and reports; it never guesses past a missing input.


====================================================================
VARIABLES
====================================================================

ROOT_DIR dir is ~/BGit/Bryan_git/we_bryan
  * The citizen's own User Data Repo. This is the repo this prompt lives in and the
    only repo this prompt is allowed to WRITE to.
  * On another citizen's computer this is a different path. Change this one line.
  * If {CONFIG_FILE} already carries we_citizens.user_repo_path and that path is a
    valid user data repo, that value WINS over the line above — the citizen may have
    cloned this repo somewhere else. Stage 1 settles it.

CONFIG_FILE is file ~/.config/we_citizens/config.yaml
  * Machine-local. Outside every repo. Never checked in. Schema in APPENDIX A.

DATA_REPO dir is DISCOVERED IN STAGE 1
  * The shared We The Citizens data repo.
  * Remote: https://github.com/ACT3ai/data_we_citizens.git
  * Read-only from this prompt. Never write to it, never commit in it.

WTC_REPO dir is DISCOVERED IN STAGE 1
  * The We The Citizens product repo — the web app and the citizens CLI.
  * Remote: https://github.com/ACT3ai/we_the_citizens.git
  * Read-only from this prompt except for `just build` / `just run`, which are allowed.

VIDEO_DEMAND_CSV is file {DATA_REPO}/video_demand.csv
VIDEO_DEMAND_YAML is file {DATA_REPO}/video_demand.yaml

VIDEO_DOWNLOAD_ROOT dir is ~/T/_we_citizens/download/videos
  * Where downloaded media lands. OUTSIDE every git repo, on purpose: media is large,
    it is never committed, and it is disposable once the words exist.
  * Layout: {VIDEO_DOWNLOAD_ROOT}/{person_key}/{video_key}/{video_key}.{ext}

VIDEO_DOWNLOAD_ROOT_LEGACY dir is ~/T/_we_citizens/videos
  * An OLDER media root written by an earlier tool, same
    {person_key}/{video_key}/ shape. It may hold media, or only a
    {video_key}.info.json with no media beside it.
  * READ it in Stage 2 so a video already downloaded there is not downloaded twice.
    Never write into it.

TRANSCRIPTIONS_ROOT dir is {ROOT_DIR}/videos/transcriptions
  * Layout: {TRANSCRIPTIONS_ROOT}/{person_key}/{video_key}/
  * This is what gets committed and pushed.

MANIFEST_FILE is file {ROOT_DIR}/user_repo.yaml
  * The repo's own index of its transcripts. A transcript not listed here is
    INVISIBLE to the movement's scanner. See STAGE 8 and APPENDIX C.

CITIZENS_CLI is file {WTC_REPO}/cli/citizens
LOCALHOST_API is the string "http://127.0.0.1:9333"
LOCALHOST_WEB is the string "http://localhost:4444"

VIDEO_COUNT is the number of videos to process this run
  * DEFAULT = 20. The person running this prompt may name a different number in the
    text they typed with the command ("download 5", "do 50", "just 1").

MAX_PARALLEL_TRANSCRIBE is the value 12
  * Ceiling, not a target. See STAGE 6.

THE_DATE_TIME_STRING is the string "{Date}_{Time}_" using only alphanumerics and
underscores, e.g. 2026_Sep_05_08_14_31_

RUN_LOG is file {VIDEO_DOWNLOAD_ROOT}/_runs/{THE_DATE_TIME_STRING}_download_videos.log
  * Outside the repo. Every stage appends what it did, what it skipped and why.


====================================================================
HARD RULES — VIOLATING ANY OF THESE FAILS THE RUN
====================================================================

* NEVER ask production to transcribe. Not once, not as a fallback, not "just to
  test". Transcription is work a citizen's own machine does. Every CLI call in this
  prompt carries --local. The CLI's DEFAULT TARGET IS PRODUCTION, so an omitted
  --local is a production call by accident. There is no acceptable reason to reach
  https://api.wethecitizens.io from this prompt.

* NEVER write to {DATA_REPO}. It is read-only reference here. Do not commit in it,
  do not `git add` in it, do not repair it.

* NEVER write application code into {WTC_REPO}. `just build` and `just run` are the
  only things this prompt does there.

* NEVER commit a PARTIAL or FAILED transcription into {ROOT_DIR}. A failed
  transcription's artefacts move OUT of the repo and next to the video (STAGE 7.4).
  A half-written directory in the repo is worse than an absent one: the scanner
  cannot tell it from a complete one.

* NEVER download in violation of a site's Terms of Service. If a URL cannot be
  fetched lawfully, skip it, record the reason in {RUN_LOG}, and move on.

* NEVER invent a video_key or a person_key. Both are FROZEN keys and both come from
  {VIDEO_DEMAND_CSV}, verbatim. A key derived from a filename or a title is a bug.

* NEVER commit media. No .mp4, .webm, .m4a, .info.json inside {ROOT_DIR}. Media
  lives under {VIDEO_DOWNLOAD_ROOT}, which is outside every repo.

* NEVER create or switch a git branch. Work on whatever branch is checked out.


====================================================================
STAGE 1 — FIND THE OTHER REPOS AND SETTLE {CONFIG_FILE}
====================================================================

The goal of this stage: end with DATA_REPO, WTC_REPO and ROOT_DIR all set to real,
verified, absolute paths, and with {CONFIG_FILE} on disk saying the same three
things. Nothing after this stage guesses a path.

1.1 READ {CONFIG_FILE} IF IT EXISTS

* If the file does not exist, note "config absent — will create" and go to 1.3.
* If it exists, parse it. Accept BOTH shapes:
  * The CURRENT shape, nested under a `we_citizens:` key (APPENDIX A).
  * The RETIRED shape, a bare top-level `user_repo_path:` with no nesting. If you
    read the retired shape, carry its value forward and REWRITE the file into the
    current shape in 1.6. Say so in the output.
* Every value read here is a CLAIM, not a fact. 1.2 turns claims into facts.

1.2 VERIFY EVERY PATH THE CONFIG CLAIMS — A STALE PATH IS WORSE THAN A MISSING ONE

For each of the three values, in order, run this check:

  * Does the directory exist? If not, the value is STALE. Discard it and search.
  * Is it a git repo (does it have a .git)? If not, STALE. Discard and search.
  * Run: git -C <path> remote -v
    Compare the fetch remote against the expected remote for that slot:
      user_repo_path        expect a clone of template_user_repo_we_citizens, i.e. the
                            citizen's OWN fork/clone. The remote is per-citizen and is
                            NOT a fixed string — accept any remote here, but require
                            {path}/user_repo.yaml OR {path}/videos/ to exist as the
                            shape test.
      data_repo             expect github.com/ACT3ai/data_we_citizens
      we_the_citizens_repo  expect github.com/ACT3ai/we_the_citizens
    A remote that does not match is STALE. Discard and search. Do not "fix it up" —
    a directory that is a repo but the WRONG repo is exactly the failure that makes
    a run write a transcript into somebody else's tree.
  * Confirm the slot's own content marker as a second, independent test:
      data_repo             {path}/video_demand.csv exists
      we_the_citizens_repo  {path}/cli/citizens exists AND {path}/justfile exists
      user_repo_path        {path}/videos/ exists (create it if the rest checks out)

Anything that survives all four checks is CONFIRMED. Record it.

1.3 SEARCH THE DISK FOR ANYTHING NOT CONFIRMED

Search in this order and stop at the first confirmed hit per slot.

  * Search the common locations first — they cost nothing:
      data_repo:            ~/BGit/act3/data_we_citizens
                            ~/data_we_citizens
                            ~/BGit/data_we_citizens
      we_the_citizens_repo: ~/BGit/act3/we_citizens
                            ~/BGit/act3/we_the_citizens
                            ~/we_citizens
                            ~/BGit/we_citizens
      user_repo_path:       the directory this prompt file is in, walked UP to the
                            nearest enclosing git repo root. That is almost always
                            the answer and should be tried before any search.

  * If still not found, search by REMOTE, which is the only reliable identifier:
    walk the likely repo parents (~/BGit and its immediate children, ~/, ~/Documents,
    ~/Projects, ~/src, ~/code) to a depth of 4, and for every directory holding a
    .git, run `git -C <dir> remote -v` and match the expected remote.

  * DO NOT use the macOS `find` command's index-backed search, and do not use
    Spotlight/mdfind — filesystem indexing is off on this machine and both return
    nothing while appearing to succeed. Use `fd` if installed, otherwise GNU-style
    `find` with explicit -maxdepth, otherwise `git -C ... remote -v` over a plain
    directory listing walk. Prefer brew-installed tools that do their own walking.

  * Put every candidate through the FULL 1.2 verification before accepting it.

1.4 WHAT TO DO WHEN A SLOT CANNOT BE FOUND

  * user_repo_path NOT FOUND — this is fatal. This prompt runs from inside the user
    data repo; if it cannot identify one, stop and say so.

  * data_repo NOT FOUND — this is fatal for this run, because the demand list lives
    there and there is nothing to download without it. Output to stdout:

      ============================================================
      The shared We The Citizens data repo was not found on this
      computer. It holds video_demand.csv — the list of videos the
      movement still needs — so there is nothing to download without
      it. Copy these three lines into a terminal:
      ============================================================
      mkdir -p ~/BGit/act3
      cd ~/BGit/act3
      git clone https://github.com/ACT3ai/data_we_citizens.git

    Then STOP. Do not clone it yourself.

  * we_the_citizens_repo NOT FOUND — NOT fatal here. Stages 2, 3 and 4 (select and
    download) run without it. Stage 5 handles the install, and that is where the
    citizen is asked to clone it. Carry the absence forward; do not stop now.

1.5 REPORT WHAT STAGE 1 DECIDED

Output to stdout, one line per slot, and say how each was resolved:

      ============================================================
      Repos for this run
      ------------------------------------------------------------
      user repo   [ OK ] /Users/…/we_bryan            (from config, verified)
      data repo   [ OK ] /Users/…/data_we_citizens    (found by remote — config was stale)
      product     [MISS] not on this machine          (Stage 5 will ask)
      ============================================================

1.6 WRITE {CONFIG_FILE} BACK

* Create ~/.config/we_citizens/ if it does not exist.
* Write every CONFIRMED path into {CONFIG_FILE} in the APPENDIX A shape.
* Absolute and fully expanded. No "~". No relative paths. Another process reading
  this file has a different working directory and may have a different HOME.
* Preserve any key already in the file that this prompt does not own. Do not delete
  what you did not write.
* Leave a slot OUT rather than writing a path that failed verification. An absent
  key means "go look"; a wrong key means "go to the wrong place".
* If the file was in the retired flat shape, rewrite it into the current shape and
  keep the explanatory comment block at the bottom.


====================================================================
STAGE 2 — CHOOSE WHICH VIDEOS TO DOWNLOAD
====================================================================

2.1 READ THE DEMAND LIST

* Read {VIDEO_DEMAND_CSV}. Columns are in APPENDIX B. It is generated by the
  video-demand calc engine and is ALREADY SORTED by priority, highest first.
* Read {VIDEO_DEMAND_YAML} for the run record that produced it — run_id,
  generated_at, rows_open, and its stated gaps. Log the run_id in {RUN_LOG} so a
  later reader can tell which demand snapshot this run worked from.
* If {VIDEO_DEMAND_YAML} carries csv_sha256, verify {VIDEO_DEMAND_CSV} against it
  with `shasum -a 256`. A mismatch means the CSV was edited or regenerated out of
  band. Warn, log it, and keep going — the CSV is still the list.
* Consider only rows whose status is `open` or `partial`. Skip `satisfied` and
  anything with a closed_reason.

2.2 PICK THE TRAVERSAL — ODD/EVEN STRIDE ON LONG LISTS

* Count the eligible rows.
* If the count is 1000 OR FEWER: walk the list straight down from the top, in order.
* If the count is MORE THAN 1000: read the CURRENT WALL-CLOCK MINUTE on this machine.
  * Minute is ODD  → take rows at odd positions  (1st, 3rd, 5th, …)
  * Minute is EVEN → take rows at even positions (2nd, 4th, 6th, …)
  * Positions are 1-based over the eligible rows after 2.1's filtering.
  * WHY: several citizens run this at once against the same list. A straight
    top-down walk has all of them download the same twenty videos. The stride
    spreads the work across machines at no coordination cost.
  * Log the minute and which stride was chosen.

2.3 SKIP WHAT THIS CITIZEN ALREADY HAS

Walk the chosen traversal and, for each row, skip it if ANY of these is true:

  * {TRANSCRIPTIONS_ROOT}/{person_key}/{video_key}/ exists and holds a
    {video_key}.transcription file. This citizen has already done it. This is the
    main test.
  * {MANIFEST_FILE} already lists that video_key.
  * The media is already downloaded — {VIDEO_DOWNLOAD_ROOT}/{person_key}/{video_key}/
    or {VIDEO_DOWNLOAD_ROOT_LEGACY}/{person_key}/{video_key}/ holds a media file
    (not merely a .info.json). Do NOT re-download it; carry it forward to Stage 5
    with the path it already has and mark it "already on disk".
  * The row is marked unobtainable / closed in the CSV.

Keep going down the traversal until VIDEO_COUNT videos have been selected, or the
list runs out. A skip does not consume a slot.

2.4 REPORT THE SELECTION BEFORE DOING ANY WORK

Output to stdout a compact table — person_key, video_key, priority, and the state
each one is in:

      ============================================================
      Selected 20 of 8400 open rows   (stride: EVEN, minute 42)
      ------------------------------------------------------------
      [     ] kari_lake_us_pres      -6tC15BHdh4   pri 850   to download
      [     ] kari_lake_us_pres      -EZZ6G-xuyk   pri 850   to download
      [ DL  ] darryl_cooper_us       3EG0ZJh6lWs   pri 810   media already on disk
      …
      ============================================================

Status brackets used through the rest of this run:
      [     ]  not started
      [ DL  ]  media downloaded, not transcribed
      [IN-PR]  transcription running
      [ DONE]  transcribed, sidecar written, staged for commit
      [FAIL ]  failed — artefacts moved out of the repo, reason logged


====================================================================
STAGE 3 — CREATE THE DESTINATION AND SEED transcription.yaml
====================================================================

For each selected video, before downloading anything:

3.1 CREATE THE DIRECTORIES

  * {TRANSCRIPTIONS_ROOT}/{person_key}/{video_key}/
  * {VIDEO_DOWNLOAD_ROOT}/{person_key}/{video_key}/
  * The directory name IS the video_key from the CSV, byte for byte. Not a title,
    not a slug, not a guest's name. The video_key is the join key everywhere else in
    this product and a directory named anything else is invisible to every reader.

3.2 SEED transcription.yaml

Write {TRANSCRIPTIONS_ROOT}/{person_key}/{video_key}/transcription.yaml with
everything KNOWN AT THIS POINT — the schema is APPENDIX D.

At seed time that is: Video.URL, Video.Video_ID, Video.Title (if the CSV or the
yt-dlp metadata gives one — otherwise leave it out entirely), and the Demand block
carrying the row this video came from.

Rules for this file, and they hold at every stage that touches it:

  * ABSENT IS ABSENT. A field whose value is not yet known is OMITTED. Never write
    "unknown", "", "TBD" or 0 as a placeholder — a zero read later is a measurement,
    and it will be believed.
  * The schema is EXPANDABLE. If this run learns a fact that APPENDIX D has no field
    for, add a field for it rather than dropping the fact, and say in the run report
    which field was added so the schema can be folded back into the appendix.
  * Every property the server side needs to reconnect this transcript to its demand
    row must survive into this file. That is what the Demand block is for.


====================================================================
STAGE 4 — DOWNLOAD THE VIDEO
====================================================================

4.1 CHECK FOR yt-dlp FIRST

Run `which yt-dlp`. If it is not installed, output to stdout:

      ============================================================
      yt-dlp is not installed. It is the downloader this prompt
      uses. Copy this line into a terminal:
      ============================================================
      brew install yt-dlp

Then ask whether to install it here. Install it only with explicit permission.
Do not silently install it, and do not substitute another downloader.

Also check `which ffmpeg` — Stage 4.4 needs it. Same treatment: `brew install ffmpeg`.

4.2 RUN THE DOWNLOAD

  * The URL for a YouTube row is https://www.youtube.com/watch?v={youtube_id}
  * cd into {VIDEO_DOWNLOAD_ROOT}/{person_key}/{video_key}/ first. Download into the
    working directory; do not pass an output path.
  * PUT THE URL IN DOUBLE QUOTES. Both sides. This is not optional and it is not
    style: an unquoted URL loses its query string to the shell and yt-dlp then
    fetches the wrong thing or nothing.

        cd "{VIDEO_DOWNLOAD_ROOT}/{person_key}/{video_key}"
        yt-dlp "https://www.youtube.com/watch?v={youtube_id}"

  * Downloads run ONE AT A TIME. Do not parallelise this stage — parallel fetches
    from one host is what gets an IP throttled, and a throttled machine transcribes
    nothing for the rest of the day.
  * A download that fails: log the reason in {RUN_LOG}, mark the row [FAIL ], leave
    the seeded transcription.yaml OUT of the commit (delete the empty repo directory
    for that video), and move to the next video. One bad URL never stops a run.

4.3 RENAME TO THE VIDEO KEY

yt-dlp names the file after the video's title. Rename it:

        {video_key}.{original extension}

Keep the extension yt-dlp produced — .mp4, .webm, .mkv, .m4a, whatever came down.
The stem is the frozen key and nothing else. If yt-dlp also wrote sidecars
(.info.json, .description, thumbnails), rename their stems the same way and leave
them here; they never enter the repo.

4.4 CONVERT TO MP4 IF IT IS NOT ALREADY

The transcription pipeline wants an MP4. If the downloaded file is not .mp4:

        ffmpeg -i "{video_key}.webm" -c:v libx264 -c:a aac -pix_fmt yuv420p "{video_key}.mp4"

  * H.264 video, AAC audio, yuv420p. Not AV1 — it is refused by too many downstream
    consumers to be worth the smaller file here.
  * Keep BOTH files. The original is the evidence; the .mp4 is the working copy.
  * If the source is audio-only, that is fine — transcription needs the audio track.
    Convert to .m4a/.mp4 audio rather than synthesising a video stream.

4.5 RECORD THE MEDIA FACTS

Compute and hold for Stage 7:

  * SHA-256 of the .mp4 that will be transcribed: `shasum -a 256 {video_key}.mp4`
  * The file's byte size and its duration (`ffprobe`).
  * The absolute path to the .mp4.

Mark the row [ DL  ].


====================================================================
STAGE 5 — MAKE THE LOCAL WEB APP READY
====================================================================

Transcription is done by the We The Citizens app running on THIS machine. The CLI is
a thin HTTP client — it decodes nothing in its own process. So the app has to be up
before Stage 6, and it has to be the LOCAL app.

READ THIS FIRST, IT IS THE HARD RULE: production is never asked to transcribe. The
CLI's default target IS production. Every call in Stage 6 carries --local.

5.1 IS THE PRODUCT REPO INSTALLED?

If Stage 1 confirmed {WTC_REPO}, go to 5.2.

If it did not, output to stdout — one sentence of why, then three copyable lines:

      ============================================================
      The We The Citizens app is not on this computer. It is needed
      to do the transcriptions — the transcribing runs on YOUR
      machine, against your own local install, and nothing is sent
      anywhere. Copy these three lines into a terminal:
      ============================================================
      mkdir -p ~/BGit/act3
      cd ~/BGit/act3
      git clone https://github.com/ACT3ai/we_the_citizens.git

Then STOP the run after reporting what was already downloaded. The media stays under
{VIDEO_DOWNLOAD_ROOT} and a later run picks it up at Stage 2.3 as "already on disk",
so nothing is wasted. Do not clone the repo yourself.

5.2 IS IT UP TO DATE?

  * git -C {WTC_REPO} fetch, then compare HEAD against the tracking branch.
  * If it is behind, WARN — do not pull. Output the exact line the citizen can run:

        cd {WTC_REPO} && git pull

    Say how many commits behind it is. Then continue: an older install still
    transcribes, and a surprise pull in the middle of somebody's work is not this
    prompt's call to make.

5.3 IS THE CLI BUILT?

  * {CITIZENS_CLI} execs {WTC_REPO}/code/packages/citizens/dist/main.js. If that file
    is absent the CLI exits 69 and says so.
  * If absent, build it:

        cd {WTC_REPO} && pnpm --filter @wethecitizens/citizens build

5.4 IS THE APP RUNNING?

  * Check: `just --justfile {WTC_REPO}/justfile status` — or probe {LOCALHOST_API}.
  * If the API on :9333 is down, this prompt IS allowed to start it:

        cd {WTC_REPO} && just build
        cd {WTC_REPO} && just run

    `just run` prints the URLs and brings up {LOCALHOST_WEB} with the API on :9333.
  * Wait for :9333 to answer before continuing. Do not race it.

5.5 CONFIRM THE MACHINE CAN ACTUALLY TRANSCRIBE

        {CITIZENS_CLI} capability --local

  * Exit 1 / `asr: "none"` means this install has no speech engine. Report it, run
    `{CITIZENS_CLI} install --local` if the citizen agrees, and re-check.
  * `cause: "asr_disabled_on_host"` means you are talking to a HOSTED install. Stop.
    That is the production call this prompt forbids — find the local one.

5.6 CLEAR ANY OPEN CIRCUIT BREAKERS

        {CITIZENS_CLI} circuit --local

  * Ten consecutive failures open a tier's breaker for an hour. If one is open from
    an earlier run whose cause has since been fixed, close it:

        {CITIZENS_CLI} circuit reset --local

  * If the fault is still real the next run re-opens it. That is the breaker working.


====================================================================
STAGE 6 — TRANSCRIBE
====================================================================

6.1 WARN THE HUMAN BEFORE STARTING

Output to stdout, before the first job is queued:

      ============================================================
      Starting high-quality transcription of N videos.
      This runs entirely on THIS computer and will use a LOT of CPU
      for several minutes — expect fans, expect the machine to feel
      busy. Nothing is uploaded anywhere.
      ============================================================

Say it BEFORE launching, not after. The point is that the citizen is not surprised
by their own machine.

6.2 THE COMMAND

For each video, one call. Every path is ABSOLUTE — `just citizens` changes directory
before it runs, so a relative --out lands somewhere nobody asked for.

        {CITIZENS_CLI} transcribe "{VIDEO_DOWNLOAD_ROOT}/{person_key}/{video_key}/{video_key}.mp4" \
          --create \
          --local \
          --out "{TRANSCRIPTIONS_ROOT}/{person_key}/{video_key}" \
          --name "{video_key}" \
          --also rttm,ctm \
          --media-url "https://www.youtube.com/watch?v={youtube_id}"

What each flag is doing, because omitting one silently changes the result:

  * --create      LOCATE is the default. Without --create nothing is transcribed and
                  the command just prints where a transcript WOULD be.
  * --local       THE HARD RULE. Without it this is a production call.
  * --out         writes the COMPLETE FILE SET into the citizen's repo, derived from
                  the sidecar this run produced. Nothing is re-decoded.
  * --name        the base name for those files. Without it the media file's stem is
                  used — which is right only because Stage 4.3 already renamed the
                  media to the video key. Pass it anyway; it is the frozen key and
                  it should be stated, not inferred.
  * --also rttm,ctm   adds the two evaluation formats. They are what let an outsider
                  compute DER against our diarization and WER against our words.
  * --media-url   index data only. It is NEVER fetched. The CLI does not download.
  * --title / --recorded are worth passing when known. --recorded is the date the
                  MEDIA was recorded and is never inferred from today's date.

Nine files land in the out directory:

        {video_key}.transcription     the words — the authority, byte-identical forever
        {video_key}.segments.json     the sidecar: timings, speakers, provenance
        {video_key}.segments.jsonl    the committed line-oriented form
        {video_key}.srt               SubRip
        {video_key}.vtt               WebVTT
        {video_key}.script.txt        as-broadcast script
        {video_key}.fountain          screenplay, fountain.io
        {video_key}.ctm               word timings  (from --also)
        {video_key}.rttm              diarization   (from --also)

DO NOT pass --person / --video unless the citizen explicitly asks. Those flags file
the result under a person AND MIRROR IT INTO THE SHARED DATA REPO — a write this
prompt's hard rules forbid. Without them the run produces an adhoc transcript in the
state root plus the full file set in the citizen's own repo, which is exactly what
is wanted here.

6.3 PARALLELISM

  * Up to {MAX_PARALLEL_TRANSCRIBE} videos may be transcribed at once, each in its
    own agent.
  * That is a CEILING, not a target. Transcription is CPU-bound and saturating every
    core makes the whole batch slower and the machine unusable. Size the fan-out to
    the machine: a sensible default is half the physical cores, capped at 12.
  * A run of 3 or fewer videos runs sequentially. The coordination is not worth it.
  * Each agent owns exactly one video end to end — transcribe, verify the file set,
    write the sidecar, decide pass/fail. Agents never share a directory.
  * One agent failing never stops the others.

6.4 VERIFY EACH RESULT

A transcription PASSED only if all of these hold:

  * {video_key}.transcription exists in the out directory and is non-empty.
  * {video_key}.segments.json exists and parses.
  * The CLI exited 0.

Anything else is a FAILURE. In particular, the CLI writes the words and NAMES the
absent derivations when the sidecar is missing — a directory with a .transcription
and nothing else is a real, reported state, and it is a FAILURE for this prompt's
purposes because a transcript with no timings cannot be cited.


====================================================================
STAGE 7 — COMPLETE transcription.yaml, OR CLEAN UP THE FAILURE
====================================================================

7.1 ON SUCCESS — FILL IN transcription.yaml

Update {TRANSCRIPTIONS_ROOT}/{person_key}/{video_key}/transcription.yaml with
everything the run now knows. Full schema in APPENDIX D. The blocks to complete:

  * Video      — Title, Description, URL, Video_ID, Show, Runtime, Language.
                 Write a real Description: what the video actually is and what is
                 discussed in it, several sentences, written from the transcript.
                 A one-line restatement of the title is not a description.
  * Media      — THE SHA-256 OF THE MP4. This is required, it is not optional, and
                 it is the thing that lets the server side prove the words came from
                 that exact file. Also Bytes, Duration_Seconds, Container, Source_URL,
                 Downloaded_At, and Downloader (yt-dlp + its version).
  * People_in_Video — one entry per diarized speaker, with Speaker_Label,
                 Share_Of_Speech and Turns read from the .rttm / sidecar. Name a
                 person only when the transcript actually identifies them; an
                 unidentified cluster is written as "Unidentified" with its label,
                 never guessed at. Mark which one is the SUBJECT — the person whose
                 words are being assessed — and which are guests.
  * Topics     — what the video is actually about, from the transcript.
  * Source     — Canonical_ID, Transcribed (ISO 8601 with timezone), ASR model,
                 Diarization model, Evidence_Grade, Word_Count.
  * Timestamps — Downloaded_At, Transcription_Started, Transcription_Finished,
                 Duration_Seconds of the transcription itself. All ISO 8601 with an
                 explicit timezone offset. These are asked for explicitly: a run
                 with no timestamps cannot be reconstructed later.
  * Files      — every file actually written, by its real name. A file that was not
                 written is not listed. Do not list the file set from APPENDIX D and
                 assume it landed.
  * Demand     — the row from {VIDEO_DEMAND_CSV} this video came from: person_key,
                 video_uid, video_key, priority, run_id, and the demand snapshot's
                 generated_at. THIS IS THE JOIN BACK TO THE SERVER. Without it the
                 server cannot tell which request this transcript answers.

Absent is absent, at every field. And if a fact has no field, ADD the field.

7.2 HASH THE TRANSCRIPT TOO

        shasum -a 256 {TRANSCRIPTIONS_ROOT}/{person_key}/{video_key}/{video_key}.transcription

Hold it for Stage 8 — the manifest stores it and treats a mismatch as a REFUSAL, not
a warning.

7.3 MARK IT [ DONE]

7.4 ON FAILURE — MOVE EVERYTHING OUT OF THE REPO

This is the rule that keeps the repo trustworthy. A failed transcription leaves
NOTHING behind in {ROOT_DIR}.

  * Move every file the failed run wrote in
    {TRANSCRIPTIONS_ROOT}/{person_key}/{video_key}/ — including the seeded
    transcription.yaml — into
    {VIDEO_DOWNLOAD_ROOT}/{person_key}/{video_key}/ , beside the video it came from.
    That directory is outside every repo, so the evidence survives for debugging and
    nothing partial is ever committed.
  * Write a {video_key}.FAILED.txt beside them: the command that was run verbatim,
    the CLI's exit code, its stderr, which of Stage 6.4's checks failed, and the
    timestamp.
  * Remove the now-empty {TRANSCRIPTIONS_ROOT}/{person_key}/{video_key}/ directory.
    Remove the {person_key} directory too if this run created it and it is now empty.
  * Mark the row [FAIL ] and append the reason to {RUN_LOG}.
  * Do NOT retry automatically. A silent retry loop burns an hour of CPU against a
    cause that has not changed.


====================================================================
STAGE 8 — INDEX THE NEW TRANSCRIPTS IN {MANIFEST_FILE}
====================================================================

{MANIFEST_FILE} is read FIRST by the movement's scanner, and when it carries a
`transcriptions:` index that index is AUTHORITATIVE — the fallback directory walk
does not run. A transcript added to this repo and NOT added here is invisible, and
"not found" is byte-indistinguishable from "this person has never spoken".

So for every [ DONE] video, append an entry to `user_repo.transcriptions:`:

  * video_key, title, source_url, recorded_language
  * path       — repo-root-relative, forward slashes, no leading "./"
                 videos/transcriptions/{person_key}/{video_key}/{video_key}.transcription
  * sidecar    — …/transcription.yaml
  * segments   — …/{video_key}.segments.json
  * text_sha256 — the hash from 7.2. A hash that does not match the bytes is stored
                 as gap_reason: manifest_hash_mismatch and the source is NOT SCORED.
                 Re-hash after any edit.
  * transcribed_at, word_count
  * speakers   — the label → {person_key, role, display_name} map, with exactly one
                 role: subject.
  * unread_sidecars — the files the scanner's allow-list does not admit (.ctm, .rttm,
                 .fountain, .segments.jsonl, .script.txt, .srt, .vtt), listed so their
                 absence from the read is STATED rather than silent.

Update `user_repo.updated_at`.

If this repo has no `transcriptions:` block at all, leave it that way — the walk
handles it — unless the citizen asks for an index. Never leave a HALF index: an
index that lists some transcripts and not others is worse than none, because the
listed ones suppress the walk that would have found the rest.


====================================================================
STAGE 9 — COMMIT AND PUSH
====================================================================

Only [ DONE] videos are committed. Nothing from Stage 7.4 is anywhere near the repo.

9.1 CHECK WHAT IS ABOUT TO BE COMMITTED

        git -C {ROOT_DIR} status --short

  * Confirm every path is under {ROOT_DIR}/videos/transcriptions/ or is
    {MANIFEST_FILE}.
  * Confirm NO media file is staged — no .mp4, .webm, .mkv, .m4a, .info.json, no
    thumbnails. If one appears, something wrote to the wrong root. Stop and report.
  * Every directory that is meant to exist but is empty needs a .gitkeep, or git
    drops it on push and clone never brings it back.

9.2 COMMIT

        git -C {ROOT_DIR} add videos/transcriptions user_repo.yaml
        git -C {ROOT_DIR} commit

Message: what was added, in one line, plus a body listing person_key/video_key for
each transcript and the demand run_id they answer. End the message with:

        Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

9.3 PUSH

        git -C {ROOT_DIR} push

  * Current branch only. Never create or switch a branch.
  * If the push is rejected, pull with rebase and retry once. If it fails again,
    report and stop — do not force.


====================================================================
STAGE 10 — REPORT
====================================================================

Output to stdout:

      ============================================================
      Run complete — {THE_DATE_TIME_STRING}
      ------------------------------------------------------------
      Selected     20
      Downloaded   18      (2 already on disk)
      Transcribed  17
      Failed        3      artefacts under {VIDEO_DOWNLOAD_ROOT}
      Committed    17      pushed to <branch>
      ------------------------------------------------------------
      Failures:
        kari_lake_us_pres / -EZZ6G-xuyk   yt-dlp: video unavailable
        …
      ============================================================

Then say, in plain sentences: which repos Stage 1 resolved and how, whether
{CONFIG_FILE} was changed, whether {WTC_REPO} is behind and needs a pull, any
transcription.yaml FIELD THAT WAS ADDED beyond APPENDIX D, and anything left in a
state a human needs to act on.

Append the whole thing to {RUN_LOG}.


====================================================================
APPENDIX A — {CONFIG_FILE} SCHEMA
====================================================================

Machine-local. Lives at ~/.config/we_citizens/config.yaml, OUTSIDE every repo. Never
checked in, never synced. Each of a citizen's computers has its own copy pointing at
wherever the clones live there.

    # We The Citizens — machine-local config.
    # Written by the web app on first run, or by hand. Each computer has its own copy.
    # NOT checked into any repo. See the notes at the bottom for what each path is.

    we_citizens:
      user_repo_path: /Users/bryan/BGit/Bryan_git/we_bryan
      data_repo: /Users/bryan/BGit/act3/data_we_citizens
      we_the_citizens_repo: /Users/bryan/BGit/act3/we_citizens

    # -----------------------------------------------------------------------
    # Notes
    #
    # All paths are absolute and fully expanded (no ~).
    #
    # user_repo_path
    #   This user's personal We The Citizens User Data Repo.
    #   Cloned from https://github.com/ACT3ai/template_user_repo_we_citizens.git
    #
    # data_repo
    #   Shared We The Citizens data repo.
    #   Remote: https://github.com/ACT3ai/data_we_citizens.git
    #   Common locations: ~/BGit/act3/data_we_citizens/  or  ~/data_we_citizens/
    #
    # we_the_citizens_repo
    #   The We The Citizens product repo.
    #   Remote: https://github.com/ACT3ai/we_the_citizens.git
    #   Common locations: ~/BGit/act3/we_citizens/  or  ~/we_citizens/
    # -----------------------------------------------------------------------

Rules:
  * Keys may be ABSENT. An absent key means "not found on this machine, go look".
    That is a legitimate state and it is better than a wrong path.
  * A key that is present may still be STALE. Always verify by `git remote -v` plus
    a content marker before trusting it (STAGE 1.2).
  * RETIRED SHAPE, still found on older machines — a bare top-level key with no
    nesting. Read it, carry the value, rewrite the file into the shape above:

        user_repo_path: /Users/bryan/BGit/Bryan_git/we_bryan


====================================================================
APPENDIX B — {VIDEO_DEMAND_CSV} COLUMNS
====================================================================

Generated by the video-demand calc engine. Do not hand-edit — the next run
overwrites it. Already sorted, highest priority first.

    person_key                the frozen person key. Also the directory segment under
                              {TRANSCRIPTIONS_ROOT} and {VIDEO_DOWNLOAD_ROOT}.
    video_uid                 "{person_key}::{video_key}" — unique across the corpus
    video_key                 THE FROZEN PRIMARY KEY of this video for this person.
                              Directory name. [A-Za-z0-9_-], 1..64. Never invented.
    youtube_id                the 11-char YouTube id. URL is
                              https://www.youtube.com/watch?v={youtube_id}
    duration_seconds          may be blank
    priority                  the computed demand score. Higher is wanted more.
    ceiling                   the maximum this row's priority could reach
    raw                       the pre-clamp score
    bound_by                  which term bound the score
    transcripts_held          how many copies of this transcript the movement holds
    trusted_transcripts_held  copies from a trusted supplier
    person_transcripts_held   copies for this person, all videos
    seat_rank                 office importance. BLANK IS AN ABSENCE, NOT A ZERO.
    challenger                true/false
    round                     which demand round issued this row
    status                    open | partial | satisfied — only open/partial are worked
    closed_reason             why it is closed, when it is
    notes
    computed_at               ISO 8601
    run_id                    the demand engine run that produced this row. CARRY IT
                              INTO transcription.yaml — it is the join back.

{VIDEO_DEMAND_YAML} is the run record for the same generation: schema_version,
run_id, generated_at, engine_version, universe counts, rows_open / rows_partial /
rows_satisfied, a `gaps:` list stating what the engine could NOT determine, and
csv_sha256 for verifying the CSV.


====================================================================
APPENDIX C — {MANIFEST_FILE} ENTRY SHAPE
====================================================================

    user_repo:
      schema_version: 1
      person_key: "tucker_carlson"
      display_name: "Tucker Carlson"
      repo_url: "https://github.com/BryanStarbuck/we_bryan.git"
      subpath: ""
      tooling:
        ladder_tier: 3
        tier_id: "aligned_local"
        transcriber: "whisper.cpp / ggml-large-v3-turbo-q5_0"
        diarizer: "sherpa-onnx-node / pyannote-segmentation-3.0 (onnx)"
        evidence_grade: "aligned"
        language: "en"
      transcriptions:
        - video_key: "1cbw1utqzHg"
          title: "Tucker Carlson interviews Joe Kent"
          source_url: "https://www.youtube.com/watch?v=1cbw1utqzHg"
          recorded_language: "en"
          path: "videos/transcriptions/tucker/joe_kent/1cbw1utqzHg.transcription"
          sidecar: "videos/transcriptions/tucker/joe_kent/transcription.yaml"
          segments: "videos/transcriptions/tucker/joe_kent/1cbw1utqzHg.segments.json"
          text_sha256: "43201be4…"
          transcribed_at: 2026-09-03T20:19:28.997Z
          word_count: 24110
          speakers:
            SPEAKER_00: { person_key: "tucker_carlson", role: "subject",  display_name: "Tucker Carlson" }
            SPEAKER_01: { person_key: "joe_kent",       role: "guest",    display_name: "Joe Kent" }
          unread_sidecars:
            - "videos/transcriptions/tucker/joe_kent/1cbw1utqzHg.ctm"
            - "videos/transcriptions/tucker/joe_kent/1cbw1utqzHg.rttm"
      updated_at: 2026-09-04T19:42:30.000Z

  * repo_url must be PUBLIC and https. No ssh, no git://, no token. The test the
    scan performs is "can the WORLD read this?".
  * `path` values are repo-root-relative; the scanner applies `subpath` itself.
  * `person_key` here is a CLAIM. The registration in the app wins, always.


====================================================================
APPENDIX D — transcription.yaml SCHEMA
====================================================================

One per video, at
{TRANSCRIPTIONS_ROOT}/{person_key}/{video_key}/transcription.yaml

EXPANDABLE: add fields for facts this schema has no home for, and report which were
added. ABSENT IS ABSENT: omit what is not known; never write a placeholder.

    Transcription:

      Video:
        Title: "Tucker Carlson interviews Joe Kent"
        Description: >-
          Several sentences saying what this video actually is and what is
          discussed in it, written from the transcript. Not a restatement of
          the title.
        URL: "https://www.youtube.com/watch?v=1cbw1utqzHg"
        Video_ID: "1cbw1utqzHg"
        Show: "The Tucker Carlson Show — Wednesday edition"
        Runtime: "02:05:38"
        Language: "en"

      Media:
        File: "1cbw1utqzHg.mp4"
        SHA256: "…"                    REQUIRED. Of the .mp4 that was transcribed.
        Bytes: 1483920104
        Duration_Seconds: 7538
        Container: "mp4"
        Video_Codec: "h264"
        Audio_Codec: "aac"
        Original_Download: "1cbw1utqzHg.webm"   when a conversion happened
        Source_URL: "https://www.youtube.com/watch?v=1cbw1utqzHg"
        Downloader: "yt-dlp 2026.08.19"
        Stored_At: "/Users/…/T/_we_citizens/download/videos/tucker_carlson/1cbw1utqzHg/"

      People_in_Video:
        Person_1:
          Name: "Tucker Carlson"
          Role: "Host / interviewer"
          Subject: true                 exactly one Subject: true per video
          Speaker_Label: "SPEAKER_00"
          Share_Of_Speech: "42.8%"
          Turns: 291
        Person_2:
          Name: "Joe Kent"
          Role: "Guest — former Director, National Counterterrorism Center"
          Subject: false
          Speaker_Label: "SPEAKER_01"
          Share_Of_Speech: "54.8%"
          Turns: 185
        Person_3:
          Name: "Unidentified"
          Role: "Two brief turns; diarization did not map an identity"
          Speaker_Label: "SPEAKER_02"
          Share_Of_Speech: "0.0%"
          Turns: 2

      Topics:
        - "Resignation from the National Counterterrorism Center"
        - "U.S. strikes on Iran and Operation Midnight Hammer"

      Source:
        Canonical_ID: "7fab41ab44b653f9"
        Transcribed: "2026-09-03T20:19:28.997Z"
        ASR: "whisper_cpp / ggml-large-v3-turbo-q5_0"
        Diarization: "sherpa-onnx-node / pyannote-segmentation-3-0-onnx — 3 clusters, 746 turns"
        Evidence_Grade: "aligned"
        Word_Count: 24110

      Timestamps:
        Downloaded_At: "2026-09-05T08:14:31-07:00"
        Transcription_Started: "2026-09-05T08:19:02-07:00"
        Transcription_Finished: "2026-09-05T08:47:55-07:00"
        Transcription_Duration_Seconds: 1733
        Recorded: "2026-09-02"          the date the MEDIA was recorded, when known.
                                        NEVER inferred from the decode date.

      Files:
        Plain_Text: "1cbw1utqzHg.transcription"
        As_Broadcast_Script: "1cbw1utqzHg.script.txt"
        Fountain: "1cbw1utqzHg.fountain"
        Segments_JSON: "1cbw1utqzHg.segments.json"
        Segments_JSONL: "1cbw1utqzHg.segments.jsonl"
        Word_Timings_CTM: "1cbw1utqzHg.ctm"
        Diarization_RTTM: "1cbw1utqzHg.rttm"
        Subtitles_SRT: "1cbw1utqzHg.srt"
        Subtitles_VTT: "1cbw1utqzHg.vtt"
        Transcript_SHA256: "43201be4…"

      Demand:
        person_key: "tucker_carlson_us_pres"
        video_uid: "tucker_carlson_us_pres::1cbw1utqzHg"
        video_key: "1cbw1utqzHg"
        priority: 850
        seat_rank: 300
        challenger: true
        round: 1
        demand_run_id: "job_1788525549225_32"
        demand_generated_at: "2026-09-04T12:39:10.038Z"


====================================================================
APPENDIX E — THE citizens CLI, ONLY WHAT THIS PROMPT USES
====================================================================

Run from {WTC_REPO}/cli/citizens, or `just citizens <verb>` from {WTC_REPO}, or
`node {WTC_REPO}/code/packages/citizens/dist/main.js`. Same binary, same arguments.

  * IT IS A THIN HTTP CLIENT. It decodes nothing in its own process — it asks the
    app to. So the app must be running.
  * IT NEVER FETCHES MEDIA. A URL handed to `transcribe` is refused at the edge with
    MediaNotLocalError. That is why Stage 4 exists and uses yt-dlp.
  * THE DEFAULT TARGET IS PRODUCTION. --local on every call, every time.
  * LOCATE IS THE DEFAULT. Without --create, `transcribe` only prints where the
    transcript would be and exits 3 if there is none.

Verbs used here:

    citizens capability --local          the capability object; exit 1 when asr == "none"
    citizens install --local             install the speech engine
    citizens circuit --local             which tiers are carrying failures
    citizens circuit reset --local       close them after fixing the cause
    citizens videos --local              what media is on disk, per person
    citizens transcribe <abs-file> --create --local --out <abs-dir> --name <video_key> --also rttm,ctm

Exit codes: 2 usage, 3 not found, 4 verify failed, 69 CLI not built.

Not used here, and why:
    citizens batch      walks a MEDIA ROOT this prompt does not own and defaults its
                        --out into the shared data repo. This prompt drives one video
                        at a time into the citizen's own repo instead.
    --person / --video  MIRRORS THE RESULT INTO THE SHARED DATA REPO. Forbidden by
                        this prompt's hard rules unless the citizen asks.


====================================================================
APPENDIX F — WHEN THINGS GO WRONG
====================================================================

yt-dlp says "video unavailable" or geo-blocks
  * Skip it. Log it. It is a fact about the video, not a fault in the run. Do not
    try to route around it.

yt-dlp downloads a .webm and ffmpeg is missing
  * Ask to `brew install ffmpeg`. Do not transcribe the .webm and hope.

`citizens` exits 69
  * The CLI is not built. `cd {WTC_REPO} && pnpm --filter @wethecitizens/citizens build`

`citizens capability` exits 1 with asr: "none"
  * No speech engine installed. `citizens install --local`.

`citizens capability` reports cause: "asr_disabled_on_host"
  * You are talking to a HOSTED install, not localhost. STOP — this is the hard rule.
    Find the local app, or start it with `just run` in {WTC_REPO}.

EADDRINUSE on :9333 after `just run` said it started
  * Stale watchers from an earlier run. `just stop` in {WTC_REPO}, then `just run`.

The out directory has a .transcription and nothing else
  * The sidecar was missing, so nothing could be derived. This is a real state the
    CLI reports, and for this prompt it is a FAILURE — Stage 7.4 applies. Do not
    commit words that cannot be cited.

The push is rejected
  * `git pull --rebase` then push once more. Never force. Never branch.
