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

Every message this prompt prints to the citizen is in APPENDIX Z, by code. A stage
says "print Z4" rather than carrying its own wall of text. When a situation arises
that has no Z code, write the message in the same shape — one sentence of WHY, then
the copyable lines — and say in the run report that a new message was needed.


====================================================================
OUTPUT DISCIPLINE — WHAT REACHES THE CITIZEN
====================================================================

The citizen sees FIVE things and nothing else:

  1. The Stage 1 repo table (Z1).
  2. The Stage 2 selection table.
  3. The Stage 6 "this will take N" warning (Z20).
  4. Any Z-coded problem, at the moment it happens.
  5. The Stage 10 final report.

Everything else — per-file progress, ffmpeg output, yt-dlp chatter, every skip and
its reason, every path resolved — goes to {RUN_LOG} and NOT to the screen. A run
that prints a line per file buries the three lines that needed reading.

Do not narrate stages. Do not print a heading for a stage that had nothing to say.
Silence between the selection table and the final report is the correct output for a
run where nothing went wrong.

ONE EXCEPTION, and it matters on a long run: Stage 6 can be silent for the better
part of an hour, and a silent terminal is indistinguishable from a hung one. Print a
single line each time a video finishes — nothing more than

      [ DONE] kari_lake_us_pres/0jIindXGitE   374s   1748 s audio

— so the citizen can see the batch moving. That is one line per video for the whole
run, which is the floor, not the per-file chatter this section rules out.


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
  * Where media THIS PROMPT downloads lands. OUTSIDE every git repo, on purpose:
    media is large, it is never committed, and it is disposable once the words exist.
  * Layout: {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/{video_key}.{ext}
  * It may not exist yet. Create it, and create {VIDEO_DOWNLOAD_ROOT}/_runs, before
    anything writes into either.

VIDEO_DOWNLOAD_ROOT_LEGACY dir is ~/T/_we_citizens/videos
  * An OLDER media root written by code/scripts/download_politician_videos.mjs, same
    {roster_key}/{video_key}/ shape. It holds media for several hundred videos, and
    for some rows only a {video_key}.info.json with no media beside it.
  * READ it in Stage 2 so a video already downloaded there is not downloaded twice,
    and transcribe FROM it in place. Never write into it, never move media out of it.
  * Its {video_key}.video.yaml carries title, published_at, bytes, downloaded_at and
    the yt-dlp version. Stage 4.6 reads it.

MEDIA_FILE is RESOLVED PER VIDEO, in STAGE 2.3 or STAGE 4
  * The absolute path to the one file that will actually be handed to the
    transcriber for this video. It may sit under EITHER media root and it is NOT
    assumed to be under {VIDEO_DOWNLOAD_ROOT}: a video found in the legacy root is
    transcribed in place. Every later stage refers to this, never to a rebuilt path.

MEDIA_ROOTS is the ordered list [{VIDEO_DOWNLOAD_ROOT}, {VIDEO_DOWNLOAD_ROOT_LEGACY}]
  * Searched in this order whenever the question is "does this machine already hold
    the media for {roster_key}/{video_key}?".

TRANSCRIPTIONS_ROOT dir is {ROOT_DIR}/videos/transcriptions
  * Layout for anything THIS prompt writes:
    {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/
  * Older hand-made directories under here use other shapes. They are LEGACY, they
    are left exactly as they are, and Stage 2.3 finds them by video_key, not by path.
  * This is what gets committed and pushed.

MANIFEST_FILE is file {ROOT_DIR}/user_repo.yaml
  * The repo's own index of its transcripts. A transcript not listed here is
    INVISIBLE to the movement's scanner. See STAGE 8 and APPENDIX C.

SIDECAR_TOOL is file {ROOT_DIR}/tools/wtc_sidecar.py
  * The CHECKED-IN builder and verifier for transcription.yaml. Stage 7 calls it;
    Stage 7.5 gates on it. It is committed code with a test beside it
    ({ROOT_DIR}/tools/test_wtc_sidecar.py) precisely so this prompt never has to
    describe a schema that nothing implements.
  * WHY IT EXISTS: before it, the writer was improvised in /tmp on every run. The
    outputs were committed and auditable forever; the program that produced them
    was deleted by the next /tmp sweep. Unversioned code wrote files into a repo
    meant to be published. If it ever moves back to a scratch directory, that
    regression has returned.

CITIZENS_CLI is file {WTC_REPO}/cli/citizens
LOCALHOST_API is the string "http://127.0.0.1:9333"
LOCALHOST_WEB is the string "http://localhost:4444"

VIDEO_COUNT is the number of videos to process this run
  * DEFAULT = 20. The person running this prompt may name a different number in the
    text they typed with the command ("download 5", "do 50", "just 1").

MAX_PARALLEL_TRANSCRIBE is the value 12
DEFAULT_PARALLEL_TRANSCRIBE is the value 4
  * Ceiling and starting point. See STAGE 6.3.

THE_DATE_TIME_STRING is the string "{Date}_{Time}_" using only alphanumerics and
underscores, e.g. 2026_Sep_05_08_14_31_

RUN_LOG is file {VIDEO_DOWNLOAD_ROOT}/_runs/{THE_DATE_TIME_STRING}download_videos.log
  * Outside the repo. Every stage appends what it did, what it skipped and why.
  * `mkdir -p` its directory in Stage 1 before any stage tries to append to it.


====================================================================
TWO KEY NAMESPACES — DO NOT COLLAPSE THEM
====================================================================

This product names the same human two ways and the difference decides where files go.

  roster_key   The key in {VIDEO_DEMAND_CSV}'s FIRST COLUMN. Office-scoped:
               kari_lake_us_pres, tucker_carlson_us_pres, darryl_cooper_us.
               It matches a directory in {DATA_REPO}/politicians/new/.
               THIS IS THE DIRECTORY SEGMENT under {TRANSCRIPTIONS_ROOT} and every
               media root. Use it verbatim, byte for byte, always.

  person_key   The frozen PERSON key, office-free: tucker_carlson, casey_putsch.
               It exists only when {DATA_REPO}/people/{person_key}.yaml exists, and
               for most roster entries IT DOES NOT EXIST — there are ~30 person
               records against thousands of roster entries.
               It is what {MANIFEST_FILE}'s speaker map is keyed by.

Rules:

  * The CSV column is LABELLED person_key and is NOT one. Read it as roster_key.
  * To get a person_key: strip nothing, guess nothing. Look for
    {DATA_REPO}/politicians/new/{roster_key}/{roster_key}.yaml and read a
    person_key out of it if it states one; otherwise test whether
    {DATA_REPO}/people/{candidate}.yaml exists for a candidate the roster record
    itself names.
  * If no person_key resolves, OMIT it. Absent is absent. A person_key invented by
    chopping "_us_pres" off a roster key is a fabricated identity claim, and the
    scanner treats manifest person keys as claims it will surface to an admin.
  * Report in Stage 10 how many entries could not resolve a person_key.


====================================================================
HARD RULES — VIOLATING ANY OF THESE FAILS THE RUN
====================================================================

* NEVER ask production to transcribe. Not once, not as a fallback, not "just to
  test". Transcription is work a citizen's own machine does. Every CLI call in this
  prompt carries --local. The CLI's DEFAULT TARGET IS PRODUCTION, so an omitted
  --local is a production call by accident. There is no acceptable reason to reach
  https://app.WeTheCitizens.io from this prompt.

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

* NEVER invent a video_key or a roster_key. Both are FROZEN and both come from
  {VIDEO_DEMAND_CSV}, verbatim. A key derived from a filename or a title is a bug.

* NEVER commit media. No .mp4, .webm, .m4a, .info.json inside {ROOT_DIR}. Media
  lives under a media root, which is outside every repo.

* NEVER create or switch a git branch. Work on whatever branch is checked out.

* NEVER modify a transcript directory this run did not create. Legacy directories
  under {TRANSCRIPTIONS_ROOT} are read to answer "do we already have this?" and are
  otherwise untouched.


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
      user_repo_path        a clone of template_user_repo_we_citizens, i.e. the
                            citizen's OWN fork/clone. The remote is per-citizen and
                            is NOT a fixed string — accept any remote here, and rely
                            on the content marker below as the shape test.
      data_repo             github.com/ACT3ai/data_we_citizens
      we_the_citizens_repo  github.com/ACT3ai/we_the_citizens
    A remote that does not match is STALE. Discard and search. Do not "fix it up" —
    a directory that is a repo but the WRONG repo is exactly the failure that makes
    a run write a transcript into somebody else's tree.
  * Confirm the slot's own content marker as a second, independent test:
      data_repo             {path}/video_demand.csv exists
      we_the_citizens_repo  {path}/cli/citizens exists AND {path}/justfile exists
      user_repo_path        {path}/user_repo.yaml OR {path}/videos/ exists

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

  * DO NOT use Spotlight or `mdfind`, and do not rely on any index-backed search —
    filesystem indexing is off on this machine and they return nothing while
    appearing to succeed. Use `fd` if installed, otherwise `find` with an explicit
    -maxdepth, otherwise `git -C ... remote -v` over a plain directory listing walk.

  * Put every candidate through the FULL 1.2 verification before accepting it.

1.4 WHAT TO DO WHEN A SLOT CANNOT BE FOUND

  * user_repo_path NOT FOUND — fatal. Print Z2 and STOP.
  * data_repo NOT FOUND — fatal for this run: the demand list lives there and there
    is nothing to download without it. Print Z3 and STOP. Do not clone it yourself.
  * we_the_citizens_repo NOT FOUND — NOT fatal here. Stages 2, 3 and 4 run without
    it. Carry the absence forward; Stage 5.1 is where the citizen is asked for it.

1.5 REPORT WHAT STAGE 1 DECIDED

Print Z1 — one line per slot, saying how each was resolved.

1.6 WRITE {CONFIG_FILE} BACK, AND MAKE THE RUN DIRECTORIES

* Create ~/.config/we_citizens/ if it does not exist.
* Write every CONFIRMED path into {CONFIG_FILE} in the APPENDIX A shape.
* Absolute and fully expanded. No "~". No relative paths. Another process reading
  this file has a different working directory and may have a different HOME.
* Preserve any key already in the file that this prompt does not own. Do not delete
  what you did not write.
* Leave a slot OUT rather than writing a path that failed verification. An absent
  key means "go look"; a wrong key means "go to the wrong place".
* If the file was already correct, do not rewrite it, and say "unchanged" in Z1.
* mkdir -p {VIDEO_DOWNLOAD_ROOT} and {VIDEO_DOWNLOAD_ROOT}/_runs. Open {RUN_LOG}.

1.7 THE MEDIA GITIGNORE — A SAFETY NET FOR THE HARD RULE

The "never commit media" rule needs an enforcement that survives a mistake. If
{ROOT_DIR}/.gitignore does not already ignore media, append this block to it (create
the file if absent) and include it in Stage 9's commit:

    # Media never belongs in this repo — it lives under ~/T/_we_citizens/.
    *.mp4
    *.webm
    *.mkv
    *.m4a
    *.info.json
    *.webp
    # ...but the empty-directory markers must always survive.
    !.gitkeep

Say in Stage 10 whether this was added. Never REMOVE a rule already in the file.


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
  with `shasum -a 256`. On mismatch print Z10, log it, and keep going — the CSV is
  still the list.
* Consider only rows whose status is `open` or `partial`. Skip `satisfied` and
  anything with a closed_reason.

2.2 PICK THE TRAVERSAL — ODD/EVEN STRIDE ON LONG LISTS

* Count the eligible rows.
* If the count is 1000 OR FEWER: walk the list straight down from the top, in order.
* If the count is MORE THAN 1000: read the CURRENT WALL-CLOCK MINUTE on this machine.
  * Minute is ODD  -> take rows at odd positions  (1st, 3rd, 5th, ...)
  * Minute is EVEN -> take rows at even positions (2nd, 4th, 6th, ...)
  * Positions are 1-based over the eligible rows after 2.1's filtering.
  * WHY: several citizens run this at once against the same list. A straight
    top-down walk has all of them download the same twenty videos. The stride
    spreads the work across machines at no coordination cost.
  * It is TWO buckets, so it halves collisions, it does not eliminate them. That is
    the intended trade — the alternative is a coordination service this movement
    does not have, and Stage 2.3 makes a collision cost a skip, not a duplicate.
  * Log the minute and which stride was chosen.

2.3 SKIP WHAT THIS CITIZEN ALREADY HAS

Walk the chosen traversal and, for each row, skip it if ANY of these is true:

  * THE WORDS ALREADY EXIST IN THIS REPO. Test it by VIDEO KEY, not by path:
    does any file named {video_key}.transcription exist ANYWHERE under
    {TRANSCRIPTIONS_ROOT}? Older transcripts in this repo sit under hand-made
    directory names that predate the {roster_key}/{video_key} rule, and a
    path-shaped test walks straight past them and re-transcribes an hour of audio
    this citizen already has.

        find {TRANSCRIPTIONS_ROOT} -name "{video_key}.transcription"

  * {MANIFEST_FILE} already lists that video_key.
  * The row is marked unobtainable, satisfied, or carries a closed_reason.

Do NOT skip a row merely because the media is on disk. Media without words is work
still to do. Instead, resolve it now and carry it forward:

  * MEDIA_FILE — search {MEDIA_ROOTS} in order for
    <root>/{roster_key}/{video_key}/{video_key}.<ext> where <ext> is on the
    transcriber's allowlist (4.4). A directory holding only a .info.json is NOT a
    hit, and a .fNNN pre-merge part is never a hit.
    A directory may hold BOTH an audio file and a full-video file left by an older
    run. PREFER THE AUDIO ONE — .m4a, .opus, .mp3, .wav, .flac, .ogg — over .mp4,
    .mkv, .webm, .mov, .avi. Same words, a fraction of the bytes to read, and the
    transcriber discards the video stream anyway. Within a group, largest wins.
    The first hit wins; record its ABSOLUTE path on the row and mark the row
    "already on disk". It is transcribed in place from wherever it is — the legacy
    root is never written to and media is never moved.
    Note .webm can be either: audio-only from bestaudio, or a full merge from an
    older run. Ask ffprobe whether it carries a video stream rather than guessing
    from the extension.
  * If nothing is found, MEDIA_FILE is absent and Stage 4 downloads it.

Keep going down the traversal until VIDEO_COUNT videos have been selected, or the
list runs out. A skip does not consume a slot.

2.3b DEPTH OR BREADTH — SAY WHICH, BECAUSE THE DEFAULT IS DEPTH

The demand CSV is sorted by priority and priority is largely a property of the
PERSON, so consecutive rows are usually the same person. Walking it straight down
means a run of 20 covers about four people, 5 videos each. That is DEPTH, and it is
the default because the engine's ordering is the movement's stated ranking.

It is not always what is wanted. The product's own `citizens batch` defaults the
other way — `--breadth 2`, "breadth-first, so every person gets words early" — on
the view that one video each for twenty people is worth more than five each for
four. Both are defensible and this prompt does not get to decide it silently.

  * DEFAULT: depth. Walk the traversal as ordered.
  * If the citizen says "spread it out", "breadth", "one each", or names a number of
    people, cap the selection at N rows per roster_key and move on to the next
    person, still in priority order.
  * Either way, SAY IN THE SELECTION TABLE how many distinct people the run covers.
    A citizen who expected twenty voices and got four should learn it before the
    download starts, not from the commit.

2.4 REPORT THE SELECTION BEFORE DOING ANY WORK

Print the selection table (Z11): roster_key, video_key, priority, and state.

Status brackets used through the rest of this run:
      [     ]  not started
      [ DL  ]  media on disk, not transcribed
      [IN-PR]  transcription running
      [ DONE]  transcribed, sidecar written, staged for commit
      [FAIL ]  failed — artefacts moved out of the repo, reason logged


====================================================================
STAGE 3 — CREATE THE DESTINATION AND SEED transcription.yaml
====================================================================

For each selected video, before downloading anything:

3.1 CREATE THE DIRECTORIES

  * {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/
  * {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/ — ONLY when this run is going to
    download. A video already on disk keeps the directory it is already in.
  * The directory name IS the video_key from the CSV, byte for byte. Not a title,
    not a slug, not a guest's name. The video_key is the join key everywhere else in
    this product and a directory named anything else is invisible to every reader.

3.2 SEED transcription.yaml

Write {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/transcription.yaml with
everything KNOWN AT THIS POINT — the schema is APPENDIX D.

At seed time that is: Video.URL, Video.Video_ID, Video.Title (only if the CSV, a
legacy {video_key}.video.yaml or an existing .info.json gives one — otherwise leave
it out entirely), and the Demand block carrying the row this video came from.

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
STAGE 4 — GET THE MEDIA AND ITS FACTS
====================================================================

Every selected video ends this stage with a MEDIA_FILE that exists and with its
media facts measured. That is true whether this run downloaded it or found it. A
video carried in from Stage 2.3 SKIPS 4.2–4.4 and still runs 4.5 and 4.6 — the
SHA-256 is required in Stage 7 and nothing else computes it.

4.1 CHECK THE TOOLS FIRST — ONCE PER RUN, NOT PER VIDEO

Run `which yt-dlp` and `which ffmpeg` and `which ffprobe`.

  * Missing yt-dlp: print Z4, then ask whether to install it here. Install only with
    explicit permission. Do not silently install, do not substitute a downloader.
  * Missing ffprobe: print Z5. It measures every file's duration and 4.5 needs it.
  * Missing ffmpeg: print Z5 only if 4.4 is actually going to run — with the
    allowlist as wide as it is, most runs never call ffmpeg at all.
  * If every selected video already has MEDIA_FILE, yt-dlp is not needed this run —
    say so instead of blocking on it. ffprobe is still needed, by 4.5.

4.2 RUN THE DOWNLOAD

  * The URL for a YouTube row is https://www.youtube.com/watch?v={youtube_id}
  * cd into {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/ first. Download into the
    working directory; do not pass an output path.
  * PUT THE URL IN DOUBLE QUOTES. Both sides. This is not optional and it is not
    style: an unquoted URL loses its query string to the shell and yt-dlp then
    fetches the wrong thing or nothing.
  * WRITE THE INFO JSON. It is the only source for Title, Description, upload date,
    channel and duration, and Stage 7 forbids inferring the recorded date from the
    decode date — so without it those fields can never be filled at all.

  * NAME THE OUTPUT WITH THE VIDEO KEY, so no rename step is needed and no
    title-derived filename ever exists to be mistaken for a key.
  * FETCH THE AUDIO ONLY. -f bestaudio is not a size optimisation, it is what the
    rung is specified as: pm/transcription.mdx names rung 3 `aligned_local` as
    "yt-dlp bestaudio -> ffmpeg -> Silero VAD -> whisper.cpp -> sherpa diarize ->
    merge", and its Fetch-audio step says outright "the video stream is never
    downloaded; we want the words, not the pixels". Measured against this list, a
    full-video fetch of six clips came to 1.1 GB and the pipeline discarded every
    pixel; bestaudio is about 1 MB per audio-minute.

        cd "{VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}"
        yt-dlp -f "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio" \
               --write-info-json --no-progress --no-playlist \
               --retries 10 --fragment-retries 10 --concurrent-fragments 4 \
               -o "{video_key}.%(ext)s" \
               "https://www.youtube.com/watch?v={youtube_id}"

  * DO NOT add --extract-audio. It re-encodes a lossy source a second time for no
    gain: bestaudio already lands as .m4a or .webm/opus and both are accepted as-is
    (4.4). Archive the bytes the site served.
  * If the citizen wants the video kept for some other purpose, that is a different
    job from this one. Say so rather than quietly fetching 200 MB a clip on the
    chance somebody wants it.

  * Downloads run ONE AT A TIME. Do not parallelise this stage — parallel fetches
    from one host is what gets an IP throttled, and a throttled machine transcribes
    nothing for the rest of the day.
  * yt-dlp's output goes to {RUN_LOG}, not to the screen.
  * yt-dlp picks the container from the format it got — .m4a or .webm here. Whatever
    it picks is the answer, and both are accepted as-is (4.4).
  * MEDIA under this prompt is an AUDIO file. A directory left from an older
    full-video run may hold a .mkv or .mp4 plus its pre-merge parts (.f136.mp4,
    .f251.webm). Those still transcribe fine and Stage 2.3 still finds them. Only
    the merged file is MEDIA_FILE — never a .fNNN part.
  * A download that fails: log the reason in {RUN_LOG}, mark the row [FAIL ], delete
    the seeded {TRANSCRIPTIONS_ROOT} directory for that video so nothing partial is
    left in the repo, and move to the next video. One bad URL never stops a run.

4.3 SET MEDIA_FILE — NO RENAME, NO RE-ENCODE

MEDIA_FILE is {video_key}.{ext} as yt-dlp wrote it. That is the whole step.

  * The stem is already the frozen key because 4.2 asked for it. Never rename a file
    to a title, and never mint a key from a filename.
  * The sidecars (.info.json, .description, thumbnails) share that stem and stay
    here. They never enter the repo.

4.4 CONVERT ONLY WHEN THE CONTAINER IS NOT ACCEPTED — WHICH IS ALMOST NEVER

DO NOT re-encode video. The transcriber reads the AUDIO TRACK and nothing else, and
it accepts the container list below directly. Transcoding an .mkv into an H.264 .mp4
so it "looks like" what the pipeline wants costs more CPU than the transcription
itself, doubles the disk footprint, and buys nothing.

The pipeline's own allowlist — verified in
{WTC_REPO}/code/packages/backend/src/modules/machine/machine-transcription.controller.ts,
ALLOWED_EXTENSIONS, and anything outside it is refused with 415:

        .mp4  .m4a  .mov  .mkv  .webm  .avi  .mp3  .wav  .flac  .ogg  .opus

  * MEDIA_FILE's extension is on that list: do nothing. This is the normal path.
  * It is NOT on the list: extract the AUDIO ONLY into .m4a. Never touch the video
    stream.

        ffmpeg -nostdin -loglevel error -i "{video_key}.{ext}" \
               -vn -c:a aac -b:a 128k "{video_key}.m4a"

  * Keep BOTH files. The original is the evidence; the .m4a is the working copy.
  * Set MEDIA_FILE to whichever file will actually be handed to the CLI.

4.5 MEASURE THE MEDIA — RUNS FOR EVERY VIDEO, DOWNLOADED OR FOUND

Against MEDIA_FILE, and hold the results for Stage 7:

  * SHA-256:          shasum -a 256 "{MEDIA_FILE}"
  * Bytes:            the file size
  * Duration seconds: ffprobe -v error -show_entries format=duration \
                              -of default=nw=1:nk=1 "{MEDIA_FILE}"
  * Container and codecs, from the same ffprobe.
  * The ABSOLUTE path, and which root it came from.

4.5b NOTE ANY SUPERSEDED FULL-VIDEO FILES

If a directory holds both an audio file and a full-video file for the same key, the
video one is dead weight left by an older run. Total the bytes and print Z18 ONCE at
the end of the stage. Do not delete anything: they are outside every repo, they cost
only disk, and removing a citizen's files is not this prompt's call.

4.6 READ WHATEVER METADATA IS ALREADY BESIDE THE MEDIA

Look in MEDIA_FILE's own directory, in this order, and take the first value found
for each field. Absent stays absent — never fill one of these from the other.

  * {video_key}.info.json (yt-dlp) — title, description, upload_date, duration,
    uploader / channel, webpage_url. upload_date is the RECORDED date; it is the
    only trustworthy source for Video.Recorded.
  * {video_key}.video.yaml (the legacy downloader) — title, published_at,
    duration_seconds, bytes, downloaded_at, yt_dlp_version, media_url.
  * The CSV row — duration_seconds, when the columns above gave none.

Record which file each fact came from in {RUN_LOG}. Mark the row [ DL  ].


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

If it did not, print Z6, then STOP the run after reporting what was already
downloaded. The media stays under {VIDEO_DOWNLOAD_ROOT} and a later run picks it up
at Stage 2.3 as "already on disk", so nothing is wasted. Do not clone it yourself.

5.2 IS IT UP TO DATE?

  * git -C {WTC_REPO} fetch, then compare HEAD against the tracking branch.
  * If it is behind, print Z7 — do not pull. An older install still transcribes, and
    a surprise pull in the middle of somebody's work is not this prompt's call to
    make. Then continue.

5.3 IS THE CLI BUILT?

  * {CITIZENS_CLI} execs {WTC_REPO}/code/packages/citizens/dist/main.js. If that file
    is absent the CLI exits 69 and says so.
  * If absent, build it — this is a build, not a code change, and it is allowed:

        cd {WTC_REPO} && pnpm --filter @wethecitizens/citizens build

5.4 IS THE APP RUNNING?

  * The test is the API, not the process list. Any HTTP answer on {LOCALHOST_API} —
    including a 404 — means the app is up:

        curl -s -o /dev/null -w "%{http_code}" --max-time 3 {LOCALHOST_API}/

  * If nothing answers, this prompt IS allowed to start it. `just` resolves its
    justfile from the working directory, so change into the repo rather than
    pointing at the file:

        cd {WTC_REPO} && just build
        cd {WTC_REPO} && just run

  * `just run` prints the URLs and brings up {LOCALHOST_WEB} with the API on :9333.
  * Poll {LOCALHOST_API} until it answers before continuing. Do not race it. If it
    has not answered within about 90 seconds, print Z8 and stop.

5.5 CONFIRM THE MACHINE CAN ACTUALLY TRANSCRIBE

        {CITIZENS_CLI} capability --local

  * The command prints a human table AND a JSON object on the last line. Read the
    JSON: `asr` names the engine, `models_missing` lists what is absent, `cause`
    says why when something is off.
  * asr == "none" (or exit 1): this install has no speech engine. Print Z12, run
    `{CITIZENS_CLI} install --local` if the citizen agrees, and re-check.
  * cause == "asr_disabled_on_host": you are talking to a HOSTED install. Print Z13
    and STOP. That is the production call this prompt forbids.

5.6 CLEAR ANY OPEN CIRCUIT BREAKERS

        {CITIZENS_CLI} circuit --local

  * Ten consecutive failures open a tier's breaker for an hour. If one is open from
    an earlier run whose cause has since been fixed, close it:

        {CITIZENS_CLI} circuit reset --local

  * If the fault is still real the next run re-opens it. That is the breaker working.
  * Only mention this to the citizen if a breaker was actually open (Z14).


====================================================================
STAGE 6 — TRANSCRIBE
====================================================================

6.1 TELL THE CITIZEN HOW LONG THIS WILL TAKE, BEFORE STARTING

Sum the Duration_Seconds measured in Stage 4.5 across every video about to be
transcribed. Then:

        estimated_wall_clock_seconds = total_audio_seconds * 0.19

DO NOT DIVIDE BY P. That is the trap, and it is worth stating plainly because the
arithmetic looks wrong until you have measured it. Per-stream the rung runs at
0.21x–0.56x of realtime, so it is tempting to take a per-stream figure and divide by
the four streams running at once. The streams are competing for the same cores, and
the two effects very nearly cancel. The 0.19 constant is the AGGREGATE already —
audio seconds in, wall-clock seconds out, with P at the default 4.

MEASURED, 24-core Apple Silicon, 2026-09-05, P=4:
        5804 s of audio (1.61 h)  ->  ~1080 s wall clock  =  0.186
Per stream over the same batch: 0.23x, 0.29x, 0.27x, 0.27x, 0.21x, 0.38x, 0.56x.
An earlier version of this file said "* 0.25 / min(P,4)" and underestimated the same
batch by a factor of three.

Say the result as a RANGE — the estimate to twice it — rounded to the nearest
quarter hour, with the total audio hours it came from. The spread is real: the
per-stream figures above vary by 2.7x on the same machine in the same batch.

WHAT MAKES A VIDEO SLOW IS TURN COUNT, NOT LENGTH. The two 1750-1900 s videos in
that batch took 374 s and 722 s. Diarization clusters speaker turns, and a
fast-cutting interview with ~287 estimated turns costs far more than a monologue of
the same duration. A long single-speaker video is cheap; a short crosstalk-heavy one
is not.

Re-measure on an unfamiliar machine rather than trusting 0.19: time the shortest
video first. A machine with fewer cores will be several times slower.

The range is wide on purpose. The pipeline has two long stages and only one of them
reports progress:

  * asr reports a chunk percentage. That percentage is NOT the job's progress.
  * diarize reports ONCE, on completion, and the CLI says so itself: "this stage
    typically runs minutes, not seconds". On long audio it can take as long as the
    ASR did. A job sitting silent on "diarize clustering 1748 s of audio" is
    working, not hung — do not kill it and do not re-queue it.

Print Z20 with that estimate, BEFORE the first job is queued. The point is that the
citizen is not surprised by their own machine, and "several minutes" is the wrong
answer for twenty long-form interviews — say hours when it is hours.

If the estimate exceeds 3 hours, print Z21 and ask whether to continue, reduce
VIDEO_COUNT, or stop. Do not start a multi-hour run nobody agreed to.

6.2 THE COMMAND

For each video, one call. Every path is ABSOLUTE — `just citizens` changes directory
before it runs, so a relative --out lands somewhere nobody asked for. The input is
MEDIA_FILE as resolved in Stage 2.3 or Stage 4, which may be under EITHER media root;
it is never assumed to be under {VIDEO_DOWNLOAD_ROOT}.

        {CITIZENS_CLI} transcribe "{MEDIA_FILE}" \
          --create \
          --local \
          --out "{TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}" \
          --name "{video_key}" \
          --also rttm,ctm \
          --media-url "https://www.youtube.com/watch?v={youtube_id}"

Add --title "<title>" and --recorded <ISO date> when Stage 4.6 resolved them. Omit
either flag entirely when it did not — an absent value is printed as absent, and
that is the correct record.

What each flag is doing, because omitting one silently changes the result:

  * --create      LOCATE is the default. Without --create nothing is transcribed and
                  the command just prints where a transcript WOULD be.
  * --local       THE HARD RULE. Without it this is a production call.
  * --out         writes the COMPLETE FILE SET into the citizen's repo, derived from
                  the sidecar this run produced. Nothing is re-decoded.
  * --name        the base name for those files. Without it the media file's stem is
                  used — which is right only when Stage 4.3 renamed the media to the
                  video key, and is WRONG for legacy media whose stem may differ.
                  Pass it always; it is the frozen key and it should be stated.
  * --also rttm,ctm   adds the two evaluation formats. They are what let an outsider
                  compute DER against our diarization and WER against our words.
  * --media-url   index data only. It is NEVER fetched. The CLI does not download.

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
prompt's hard rules forbid. Without them the run produces a hash-keyed adhoc
transcript in the app's state root PLUS the full file set in the citizen's own repo.
The repo copy is the deliverable; the manifest in Stage 8 is what makes it visible.

6.3 PARALLELISM — IT IS REQUEST CONCURRENCY, NOT LOCAL CPU

The CLI decodes nothing. Every one of these calls is an HTTP request to the ONE app
on :9333, and that app does all the CPU work. So the number to choose is how many
jobs the server is asked to carry at once, and adding more does not add workers.

  * The app QUEUES what it cannot run now — a job beyond its capacity sits printing
    "queued…" until a slot frees. Asking for more concurrency than the server will
    run does not fail and does not speed anything up; it just moves the wait from
    your shell into its queue. Observed: several short jobs decode side by side,
    but a long diarization narrows that sharply.
  * SORT SHORTEST-FIRST. Order the batch by Duration_Seconds ascending. A 30-minute
    video queued first holds the slot while ten 3-minute ones wait behind it, and
    the run has nothing to show for twenty minutes. Shortest-first gets most of the
    batch finished and committable early, which also means an interrupted run
    leaves more done.
  * Start at {DEFAULT_PARALLEL_TRANSCRIBE}. Never exceed {MAX_PARALLEL_TRANSCRIBE}.
  * The server decodes 4 ASR chunks at a time WITHIN one job. Four concurrent jobs
    therefore already ask for 16 decode threads. That is why the default is 4 and
    not the core count — raising it oversubscribes the same cores and makes the
    batch slower while making the machine unusable.
  * Go above the default only when the citizen asked for speed AND the machine has
    cores genuinely idle.
  * A run of 3 or fewer videos runs sequentially. The coordination is not worth it.
  * DO NOT use a subagent per video. This is a shell fan-out over one command —
    `xargs -P {DEFAULT_PARALLEL_TRANSCRIBE} -L 1` over a list of
    "{roster_key} {video_key} {youtube_id}" lines does the whole job. Spawning an
    agent per video costs more than it saves and buys no isolation the filesystem
    is not already giving.
  * Each unit of work owns exactly one video end to end — resolve MEDIA_FILE,
    transcribe, verify the file set, decide pass/fail. They never share a directory.
  * One failure never stops the others.
  * Print nothing per video. Progress belongs in {RUN_LOG}.

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

RUN THE TOOL. Do not hand-roll a writer and do not improvise one in a scratch
directory:

        python3 {SIDECAR_TOOL} write {roster_key}/{video_key} [...]

It gathers every mechanical field itself — SHA-256, bytes, duration, codecs,
word count, speaker shares from the .rttm, the Capture block, the demand row —
and it MERGES: any Description, Topics or named speaker already in the file is
carried forward untouched, and it asserts that afterwards rather than assuming it.
It writes atomically, so a crash cannot leave a truncated file that still parses.

What the tool CANNOT do, and what is therefore still your job: read the transcript
and write Description and Topics. Nothing on disk contains them.

Full schema in APPENDIX D. The blocks, and who fills them:

  * Video      — Title, Description, URL, Video_ID, Show, Runtime, Language.
                 Title, Show, Runtime and the recorded date come from Stage 4.6 and
                 need no judgement. DESCRIPTION AND TOPICS DO: they cannot be built
                 from metadata, and they are the slowest part of this stage because
                 they require READING each transcript. Budget for it — on a 20-video
                 run that is 20 reads, and it is the step most likely to be skipped
                 under time pressure. A sidecar with a real SHA-256 and an empty
                 Description is a half-finished record.
                 Write several sentences saying what the video actually is and what
                 is discussed in it, FROM THE TRANSCRIPT. A restatement of the title
                 is not a description.
                 ATTRIBUTE CONTESTED CLAIMS. This corpus is political speech and the
                 sidecar is read as a neutral record of it. Where the speaker asserts
                 figures, motives or wrongdoing, the description says WHO is
                 asserting it — "she argues", "he puts the figure at", "the
                 characterisation is his own and is contested" — and never restates
                 an advocate's claim in the product's own voice. Describing what was
                 said is the job; endorsing it is not. Note too when the person named
                 in a claim is absent and unable to answer it.
  * Media      — THE SHA-256 OF THE FILE THAT WAS TRANSCRIBED. Required, not
                 optional: it is what lets the server side prove the words came from
                 that exact file. Also Bytes, Duration_Seconds, Container,
                 Source_URL, Downloaded_At, Downloader, and Stored_At — the absolute
                 directory, which for legacy media is under
                 {VIDEO_DOWNLOAD_ROOT_LEGACY} and must say so.
  * People_in_Video — one entry per diarized speaker, with Speaker_Label,
                 Share_Of_Speech and Turns read from the .rttm. Name a person only
                 when the transcript actually identifies them; an unidentified
                 cluster is written as "Unidentified" with its label, never guessed.
                 SUBJECT IS NOT A DEFAULT. Mark Subject: true on the cluster whose
                 words are being assessed ONLY when the transcript actually
                 identifies which cluster that is. When it does not, OMIT Subject
                 from every entry and say why in a comment. Putting Subject: true on
                 whichever label sorted first is not a fallback, it is a fabricated
                 attribution — and it is the one field a scorer will trust.
                 Expect noise on montages and ad-style clips: diarization routinely
                 returns 7+ clusters for two minutes of music and voice-over. Report
                 the count; do not merge clusters yourself.
  * Topics     — what the video is actually about, FROM THE TRANSCRIPT, not from what
                 the person is on the roster for. The demand list is built from a
                 person's whole channel, so a candidate's corpus routinely contains
                 videos with no political content at all — a gubernatorial figure's
                 channel that is mostly car reviews, a commentator's cooking videos,
                 adverts and sponsor reads. Describe what was actually said. Do NOT
                 stretch a description toward politics to make the row look like it
                 earned its priority: a transcript honestly labelled "car culture" is
                 useful, and one mislabelled "policy discussion" poisons every search
                 that later trusts it.
  * Source     — Canonical_ID, Transcribed (ISO 8601 with timezone), ASR model,
                 Diarization model, Evidence_Grade, Word_Count.
  * Timestamps — Downloaded_At, Transcription_Started, Transcription_Finished,
                 Duration_Seconds of the transcription itself. All ISO 8601 with an
                 explicit timezone offset. These are asked for explicitly: a run
                 with no timestamps cannot be reconstructed later.
                 Recorded comes from Stage 4.6's upload_date / published_at ONLY. If
                 neither existed, omit it. Never from today's date.
  * Files      — every file actually written, by its real name. A file that was not
                 written is not listed. Do not list the file set from APPENDIX D and
                 assume it landed.
                 Files is a MAPPING (Plain_Text:, Fountain:, ...), not a sequence.
                 It holds Transcript_SHA256 alongside the filenames, and a YAML
                 block cannot be both a list and a mapping — writing "- file.srt"
                 items next to a "Transcript_SHA256:" key produces a file that will
                 not parse. Parse every sidecar you write back before committing it.
  * Demand     — the row from {VIDEO_DEMAND_CSV} this video came from: roster_key,
                 video_uid, video_key, priority, run_id, and the demand snapshot's
                 generated_at. THIS IS THE JOIN BACK TO THE SERVER. Without it the
                 server cannot tell which request this transcript answers.

Absent is absent, at every field. And if a fact has no field, ADD the field.

7.1a SWEEP FOR THE PART A MACHINE COULD NOT HAVE WRITTEN

transcription.yaml has two kinds of field and only one of them defends itself.

  MECHANICAL — SHA256, Bytes, Duration, Word_Count, Files, Demand, Title, Show,
  Recorded. All derived from the media, ffprobe, the .info.json and the CSV row.
  A script produces them and reproduces them.

  HAND-WRITTEN — Description and Topics. Nothing on disk contains them. They
  require reading the transcript. No script can produce them, and no mechanical
  check tends to look for them.

That asymmetry is the danger: the cheap fields become the APPEARANCE of
completeness. A sidecar with no Description still parses, still carries a correct
and verified SHA-256, still joins back to its demand row, and would be committed,
indexed, pushed and trusted. The absence surfaces only when a human opens it.

So before Stage 8, sweep EVERY selected video and assert:

  * the nine output files exist and are non-empty
  * transcription.yaml parses
  * Video.Description is present and NON-EMPTY
  * Topics is present and NON-EMPTY
  * Media.SHA256 and Demand are present

THAT SWEEP IS NOW A COMMITTED COMMAND, not a thing to reinvent:

        python3 {SIDECAR_TOOL} verify --all

It exits non-zero while anything is missing, checks the four fields the product
actually reads as well as the human ones, and re-verifies each transcript's
SHA-256 against the bytes on disk.

RE-RUN IT UNTIL IT COMES BACK CLEAN. Fixing one miss routinely reveals the next:
in the run that produced this file it reported 19/20, then 19/20 again for a
DIFFERENT video, then 20/20. A sweep that runs once and reports "one problem" has
not finished.

Both misses that run were OMISSIONS — a video whose sidecar was never generated,
and a video handled early and out of band whose description was never written
because it was already "done". Sidecars written in batches lose the exception you
handled first. Do not trust that a directory with ten files in it is complete.

SEPARATELY, THE GENERATOR IS A HAZARD. A generator that writes the file from
scratch destroys Description and Topics on any re-run — after a bug fix, or when a
field is added — and leaves a file that still parses and still hashes correctly.
Regenerate the mechanical fields only, or re-apply the written ones afterwards.
This is a different failure from the omission above and the sweep is what catches
both.

7.1b PARSE WHAT YOU WROTE

Read transcription.yaml back with a real YAML parser before calling the video DONE.
A sidecar that does not parse is a failed transcription for Stage 6.4's purposes: it
carries the SHA-256 that proves the words, and an unparseable one proves nothing.

The two ways these files break, both of which cost a whole run if found late:

  * A block that is half sequence and half mapping (see Files, above).
  * A QUOTE INSIDE A QUOTED SCALAR. Political transcripts are full of phrases the
    writer wants in quotation marks — "border czar", "state of confusion" — and
    "The "border czar" designation" is not a YAML string, it is a parse error.
    Use single quotes for any value containing a double quote, or drop the inner
    quotes. Same for apostrophes inside a single-quoted scalar.

7.2 HASH THE TRANSCRIPT TOO

        shasum -a 256 {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/{video_key}.transcription

Hold it for Stage 8 — the manifest stores it and treats a mismatch as a REFUSAL, not
a warning.

7.3 MARK IT [ DONE]

If Word_Count is under about 30 words per minute of audio, note it with Z19 in the
Stage 10 tail. It is not a failure and not a retry — political feeds carry a lot of
adverts, montages and music beds, and the honest record of one is a short transcript
and a pile of spurious speaker clusters. Say so rather than letting a reader assume
the transcription underperformed.

7.4 ON FAILURE — MOVE EVERYTHING OUT OF THE REPO

This is the rule that keeps the repo trustworthy. A failed transcription leaves
NOTHING behind in {ROOT_DIR}.

  * Move every file the failed run wrote in
    {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/ — including the seeded
    transcription.yaml — into MEDIA_FILE's own directory, beside the video it came
    from. That directory is outside every repo, so the evidence survives for
    debugging and nothing partial is ever committed.
    If MEDIA_FILE is under {VIDEO_DOWNLOAD_ROOT_LEGACY}, which this prompt never
    writes to, put them under
    {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/ instead and say where the media
    actually is in the FAILED file.
  * Write a {video_key}.FAILED.txt beside them: the command that was run verbatim,
    the CLI's exit code, its stderr, which of Stage 6.4's checks failed, and the
    timestamp.
  * Remove the now-empty {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/ directory.
    Remove the {roster_key} directory too if this run created it and it is now empty.
  * Mark the row [FAIL ] and append the reason to {RUN_LOG}.
  * Do NOT retry automatically. A silent retry loop burns an hour of CPU against a
    cause that has not changed.


7.5 THE GATE — NOTHING REACHES STAGE 8 UNTIL THIS IS GREEN

        python3 {SIDECAR_TOOL} verify --all

  * Exit 0: proceed to Stage 8.
  * Exit non-zero: fix what it names and run it AGAIN. Do not index, commit or
    push past a red gate. An incomplete sidecar that reaches the manifest is
    indistinguishable from a complete one to every automatic check downstream.
  * Lines marked LEGACY do not fail the gate and must not be "fixed". They are
    sidecars written before this schema whose media has since been cleared, so
    their Media.SHA256 describes bytes that no longer exist anywhere and cannot
    be recomputed. Report them; leave them exactly as written. A gate that can
    never go green stops being read.


====================================================================
STAGE 8 — INDEX THE NEW TRANSCRIPTS IN {MANIFEST_FILE}
====================================================================

{MANIFEST_FILE} is read FIRST by the movement's scanner, and when it carries a
`transcriptions:` index that index is AUTHORITATIVE — the fallback directory walk
does not run. A transcript added to this repo and NOT added here is invisible, and
"not found" is byte-indistinguishable from "this person has never spoken".

8.1 DECIDE WHETHER THIS REPO IS INDEXED

  * If {MANIFEST_FILE} ALREADY HAS a `transcriptions:` block, it is an indexed repo.
    APPEND every [ DONE] video to it. Leaving one out makes it invisible, and a HALF
    index is worse than none because the listed entries suppress the walk that would
    have found the rest.
  * If it has NO `transcriptions:` block, the repo relies on the walk. Leave it that
    way and do not create one — unless the citizen asked for an index, in which case
    build a complete one covering EVERY transcript in the repo, not just this run's.
  * Either way, update `user_repo.updated_at`.

8.1b APPEND AS TEXT. NEVER ROUND-TRIP THE MANIFEST THROUGH A YAML DUMPER

{MANIFEST_FILE} is heavily commented, and those comments are the spec citations that
explain why the file says what it says — which §, which reader function, why THIS
person key and not that one, which hash was verified and when.

A YAML dumper drops every one of them. Read-modify-dump produces a file that parses,
validates and looks correct, and has silently destroyed the documentation. In the run
that produced this prompt that cost 68 comment lines on the first attempt, and it was
only caught by reading the diff.

  * Split the file TEXTUALLY at the final `updated_at:` line.
  * Append the new entries as formatted text after the existing ones.
  * Rewrite `updated_at:`.
  * Then parse the result to prove it is valid, and `git diff` it to prove the only
    removed line is the old `updated_at`. If anything else shows as removed, restore
    from git and do it again.

8.2 THE ENTRY

For every [ DONE] video append to `user_repo.transcriptions:`:

  * video_key, title, source_url, recorded_language
  * roster_key — the CSV's first column, verbatim
  * person_key — ONLY when it resolved per the key-namespaces section. Omit it
                 otherwise; never derive one from the roster key.
  * path       — repo-root-relative, forward slashes, no leading "./"
                 videos/transcriptions/{roster_key}/{video_key}/{video_key}.transcription
  * sidecar    — .../transcription.yaml
  * segments   — .../{video_key}.segments.json
  * text_sha256 — the hash from 7.2. A hash that does not match the bytes is stored
                 as gap_reason: manifest_hash_mismatch and the source is NOT SCORED.
                 Re-hash after any edit.
  * transcribed_at, word_count
  * demand_run_id — the demand snapshot this entry answers
  * speakers   — the label -> {person_key, role, display_name} map. Give a
                 person_key only where one resolved; otherwise give role and
                 display_name and omit person_key. Exactly one role: subject.
  * unread_sidecars — the files the scanner's allow-list does not admit (.ctm, .rttm,
                 .fountain, .segments.jsonl, .script.txt, .srt, .vtt), listed so their
                 absence from the read is STATED rather than silent.

8.3 THE TOP-LEVEL person_key IS A KNOWN CONFLICT — REPORT IT, DO NOT RESOLVE IT

{MANIFEST_FILE} carries ONE `user_repo.person_key` for the whole repo, and the
schema comment says the repo's speaking corpus is scoped by it. This prompt fills a
repo with videos of MANY different people, which that single key cannot describe.

  * NEVER change the existing top-level person_key. It is the citizen's own claim
    and the app's registration is what actually wins.
  * When this run adds transcripts whose roster_key does not belong to that person,
    print Z15 once at the end and name the count. It is a schema question for the
    product, not something a download run gets to decide.


====================================================================
STAGE 9 — COMMIT AND PUSH
====================================================================

Only [ DONE] videos are committed. Nothing from Stage 7.4 is anywhere near the repo.

9.1 CHECK WHAT IS ABOUT TO BE COMMITTED

        git -C {ROOT_DIR} status --short

  * Confirm every path is under {ROOT_DIR}/videos/transcriptions/, or is
    {MANIFEST_FILE}, or is {ROOT_DIR}/.gitignore.
  * Confirm NO media file is staged — no .mp4, .webm, .mkv, .m4a, .info.json, no
    thumbnails. If one appears, something wrote to the wrong root: print Z16, stop,
    and commit nothing.
  * Every directory that is meant to exist but is empty needs a .gitkeep, or git
    drops it on push and clone never brings it back.

9.2 COMMIT

        git -C {ROOT_DIR} add videos/transcriptions user_repo.yaml .gitignore
        git -C {ROOT_DIR} commit -m "$(cat <<'MSG'
<one line: what was added>

<person/video lines, one per transcript, with the demand run_id they answer>

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: <the session URL for this run>
MSG
)"

9.3 PUSH — ONLY IF THE CITIZEN ASKS. DO NOT PUSH BY DEFAULT.

{ROOT_DIR}/CLAUDE.md says, under GIT BRANCH RULES:

        No `git checkout -b`, `git switch -c`, `git branch`, `git checkout <other>`,
        or `git push` unless the user explicitly asks for it.

That is a standing instruction from the repo owner and it OUTRANKS this prompt.
Running this prompt is not itself a request to push: pushing publishes a citizen's
transcripts to a public repo, and that is the citizen's call to make each time.

  * DEFAULT: commit, then STOP. Print Z31 with the exact push command and the
    number of commits waiting.
  * ONLY if the citizen asked for a push in the text they typed with the command:

        git -C {ROOT_DIR} push

  * Current branch only. Never create or switch a branch.
  * If a requested push is rejected, `git pull --rebase` and retry ONCE. If it fails
    again, print Z17 and stop — never force.

9.4 THIS MACHINE HAS AN AUTOMATIC COMMITTER — EXPECT IT

{ROOT_DIR} is swept by an external auto-committer (its commits are titled
"Bryan 26 Tower"). It knows nothing about this prompt's rules, and during the run
that produced this file it committed 189 files at 09:04:44 while transcriptions were
still running — capturing directories whose sidecars had not been written yet.

That directly defeats the hard rule about never committing a partial transcription,
and nothing in this prompt can prevent it.

  * Re-read `git log` before Stage 9.1. Work already committed is normal, not an
    error, and it is not a reason to stop.
  * Commit the REMAINDER so the tree ends complete, and say in the run report that
    an auto-commit landed mid-run and what this commit closed.
  * Never `git reset` or amend the auto-committer's commits to "tidy up". They may
    already have been pushed, and they are not this prompt's to rewrite.


====================================================================
STAGE 10 — REPORT
====================================================================

Print Z30 — the counts, then the failures by roster_key/video_key with the reason.
Then Z31, unless the citizen asked for a push and it succeeded.

Then say, in plain sentences and only where there is something to say:

  * whether {CONFIG_FILE} was changed, and whether .gitignore was created
  * whether {WTC_REPO} is behind and needs a pull
  * any transcription.yaml FIELD THAT WAS ADDED beyond APPENDIX D
  * how many entries could not resolve a person_key, and Z15 if it applies
  * Z18 if superseded video files are sitting on disk, Z19 for any low-word video
  * the measured throughput this run achieved — total audio seconds, wall clock,
    and the ratio — so the next run's Stage 6.1 estimate is calibrated to THIS
    machine rather than to the constant in this file
  * anything left in a state a human needs to act on

If none of those apply, say nothing beyond Z30. Append the whole thing to {RUN_LOG}.


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

    person_key                MISLABELLED. It is the ROSTER key — office-scoped,
                              e.g. kari_lake_us_pres. Read it as roster_key. It is
                              the directory segment under {TRANSCRIPTIONS_ROOT} and
                              every media root. See TWO KEY NAMESPACES.
    video_uid                 "{roster_key}::{video_key}" — unique across the corpus
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
      person_key: "tucker_carlson"          # the repo's own claim. See STAGE 8.3.
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
        - video_key: "-6tC15BHdh4"
          roster_key: "kari_lake_us_pres"
          # person_key omitted: data_we_citizens/people/ has no record for her.
          title: "..."
          source_url: "https://www.youtube.com/watch?v=-6tC15BHdh4"
          recorded_language: "en"
          path: "videos/transcriptions/kari_lake_us_pres/-6tC15BHdh4/-6tC15BHdh4.transcription"
          sidecar: "videos/transcriptions/kari_lake_us_pres/-6tC15BHdh4/transcription.yaml"
          segments: "videos/transcriptions/kari_lake_us_pres/-6tC15BHdh4/-6tC15BHdh4.segments.json"
          text_sha256: "..."
          transcribed_at: 2026-09-05T09:11:02.000Z
          word_count: 8412
          demand_run_id: "job_1788525549225_32"
          speakers:
            SPEAKER_00: { role: "subject", display_name: "Kari Lake" }
            SPEAKER_01: { role: "guest",   display_name: "Unidentified" }
          unread_sidecars:
            - "videos/transcriptions/kari_lake_us_pres/-6tC15BHdh4/-6tC15BHdh4.ctm"
            - "videos/transcriptions/kari_lake_us_pres/-6tC15BHdh4/-6tC15BHdh4.rttm"
      updated_at: 2026-09-05T09:30:00.000Z

  * repo_url must be PUBLIC and https. No ssh, no git://, no token. The test the
    scan performs is "can the WORLD read this?".
  * `path` values are repo-root-relative; the scanner applies `subpath` itself.
  * `person_key` anywhere in this file is a CLAIM. The registration in the app wins.
  * LEGACY ENTRIES in a real repo may carry paths that predate the
    {roster_key}/{video_key} rule, e.g. videos/transcriptions/tucker/joe_kent/.
    Those are correct AS WRITTEN and are never rewritten by this prompt. Only new
    entries follow the shape above.


====================================================================
APPENDIX D — transcription.yaml SCHEMA
====================================================================

One per video, at
{TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/transcription.yaml

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
        File: "1cbw1utqzHg.m4a"
        SHA256: "..."                   REQUIRED. Of the file that was transcribed.
        Bytes: 62483104
        Duration_Seconds: 7538
        Container: "m4a"
        Audio_Codec: "aac"
        Video_Codec: omitted — bestaudio fetches no video stream. Present only on a
                     file left by an older full-video run.
        Original_Download: "1cbw1utqzHg.webm"   only when 4.4 actually converted
        Source_URL: "https://www.youtube.com/watch?v=1cbw1utqzHg"
        Downloader: "yt-dlp 2026.08.19"
        Metadata_From: "1cbw1utqzHg.info.json"  which file Stage 4.6 read
        Stored_At: "/Users/.../T/_we_citizens/download/videos/tucker_carlson_us_pres/1cbw1utqzHg/"
        Media_Kind: "audio"             audio | video — what was actually fetched

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
        Recorded: "2026-09-02"          the date the MEDIA was recorded. Comes from
                                        info.json upload_date or video.yaml
                                        published_at ONLY. Omitted when neither
                                        exists. NEVER the decode date.

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
        Transcript_SHA256: "43201be4..."

      Demand:
        roster_key: "tucker_carlson_us_pres"
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
    MediaNotLocalError. That is why Stage 4 exists and uses yt-dlp. `capability`
    reports yt_dlp: false and that is correct and expected.
  * THE DEFAULT TARGET IS PRODUCTION. --local on every call, every time.
    `videos`, `install`, `circuit` and `capability` REFUSE a non-local target.
  * LOCATE IS THE DEFAULT. Without --create, `transcribe` only prints where the
    transcript would be and exits 3 if there is none.

Verbs used here:

    citizens capability --local          capability table + a JSON line; asr == "none" is the fault
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
APPENDIX Z — EVERY MESSAGE THIS PROMPT PRINTS
====================================================================

Print these verbatim in shape: a rule line, one or two sentences of WHY, a rule
line, then the copyable commands with nothing else on those lines. Substitute the
real values for anything in {braces}. Print nothing that is not called for.


Z1 — the Stage 1 repo table. Always printed.

      ============================================================
      Repos for this run
      ------------------------------------------------------------
      user repo   [ OK ] {path}                  (from config, verified)
      data repo   [ OK ] {path}                  (found by remote — config was stale)
      product     [MISS] not on this machine     (Stage 5 will ask)
      config      unchanged
      ============================================================

  The parenthetical says HOW each was resolved: "from config, verified",
  "found by remote — config was stale", "found at a common location", "not found".
  The config line says "unchanged", "updated", or "created".


Z2 — the user data repo could not be identified. FATAL.

      ============================================================
      This prompt has to run from inside a We The Citizens User
      Data Repo and could not find one. Run it from inside your
      own clone, or create one:
      ============================================================
      git clone https://github.com/ACT3ai/template_user_repo_we_citizens.git my_citizen_repo


Z3 — the shared data repo is missing. FATAL.

      ============================================================
      The shared We The Citizens data repo was not found on this
      computer. It holds video_demand.csv — the list of videos the
      movement still needs — so there is nothing to download
      without it. Copy these three lines into a terminal:
      ============================================================
      mkdir -p ~/BGit/act3
      cd ~/BGit/act3
      git clone https://github.com/ACT3ai/data_we_citizens.git

  Then STOP. Do not clone it yourself.


Z4 — yt-dlp is missing.

      ============================================================
      yt-dlp is not installed. It is the downloader this prompt
      uses, and no substitute is acceptable. Copy this line:
      ============================================================
      brew install yt-dlp

  Then ask whether to install it here. Install only with explicit permission.


Z5 — ffmpeg or ffprobe is missing.

      ============================================================
      {ffmpeg|ffprobe} is not installed. ffprobe measures every
      file's duration; ffmpeg extracts audio from the rare
      container the transcriber will not accept. Copy this line:
      ============================================================
      brew install ffmpeg

  Then ask. Both come from the same formula.


Z6 — the product repo is not installed. STOPS the run after Stage 4.

      ============================================================
      The We The Citizens app is not on this computer. It is
      needed to do the transcriptions — the transcribing runs on
      YOUR machine, against your own local install, and nothing is
      sent anywhere. Copy these three lines into a terminal:
      ============================================================
      mkdir -p ~/BGit/act3
      cd ~/BGit/act3
      git clone https://github.com/ACT3ai/we_the_citizens.git

  Then say what was downloaded and where it is waiting. Do not clone it yourself.


Z7 — the product repo is behind. WARNING ONLY, the run continues.

      ============================================================
      Your We The Citizens install is {N} commits behind. It will
      still transcribe. Pull it when you are not mid-run:
      ============================================================
      cd {WTC_REPO} && git pull


Z8 — the app would not come up on :9333.

      ============================================================
      The local app did not answer on {LOCALHOST_API} after 90
      seconds. Usually this is a stale watcher from an earlier run
      holding the port. Copy these two lines, then run this prompt
      again:
      ============================================================
      cd {WTC_REPO} && just stop
      cd {WTC_REPO} && just run

  Nothing downloaded is lost — the next run finds it as "already on disk".


Z10 — the demand CSV does not match its stated hash. WARNING ONLY.

      ============================================================
      video_demand.csv does not match the csv_sha256 in
      video_demand.yaml, so it was edited or regenerated out of
      band. Using it anyway — it is still the list — but the row
      counts in the yaml may not describe this file.
      ============================================================


Z11 — the selection table. Always printed.

      ============================================================
      Selected {n} of {eligible} open rows   (stride: {EVEN}, minute {42})
      {p} people, depth-first — 5 videos each
      ------------------------------------------------------------
      [     ] kari_lake_us_pres      -6tC15BHdh4   pri 850   to download
      [ DL  ] darryl_cooper_us       3EG0ZJh6lWs   pri 810   already on disk (legacy root)
      ------------------------------------------------------------
      Skipped {k} rows already held. {j} to download, {m} already on disk.
      ============================================================


Z12 — no speech engine installed.

      ============================================================
      This install has no speech engine yet, so it cannot
      transcribe. The models are a one-time download to your own
      machine. Install them now?
      ============================================================
      {CITIZENS_CLI} install --local

  Ask first. Re-run `capability --local` afterwards and continue only if asr is set.


Z13 — you reached a hosted install. FATAL.

      ============================================================
      That capability check answered from a HOSTED install, not
      from this computer. This prompt never asks production to
      transcribe — the work belongs on your machine. Start your
      local app and run this again:
      ============================================================
      cd {WTC_REPO} && just run

  STOP. Do not fall back to production for any reason.


Z14 — a circuit breaker was open. Only printed when one actually was.

      ============================================================
      A transcription tier had an open circuit breaker from an
      earlier run ({tier}). It was reset. If the underlying fault
      is still there it will re-open, and that is the breaker
      doing its job.
      ============================================================


Z15 — the manifest's single person_key cannot describe this repo.

      ============================================================
      This repo's manifest claims one person ({person_key}), but
      this run added transcripts for {N} other people. The claim
      was left alone — the app's registration is what counts — but
      the schema has no way to say "this repo holds many people".
      Worth raising against pm/user_repos.mdx.
      ============================================================


Z16 — media was about to be committed. FATAL, commit nothing.

      ============================================================
      A media file is staged for commit in the user repo:
        {path}
      Media never enters this repo. Something wrote to the wrong
      root. Nothing was committed. Move it out and re-run.
      ============================================================


Z17 — the push failed twice.

      ============================================================
      The push was rejected, a rebase was tried, and it was
      rejected again. The work is committed locally and safe.
      Sort the remote out by hand — do not force:
      ============================================================
      cd {ROOT_DIR} && git pull --rebase && git push


Z20 — the time estimate, printed before the first job. Always printed.

      ============================================================
      Transcribing {N} videos — {H} hours of audio.
      Expect roughly {LO} to {HI} on this machine, running {P} at
      a time. It all happens HERE: a lot of CPU, loud fans, and a
      machine that feels busy. Nothing is uploaded anywhere.
      ============================================================


Z21 — the estimate is over three hours. Ask before starting.

      ============================================================
      That is a long run — {LO} to {HI}. Continue, do fewer
      videos, or stop?
      ============================================================


Z18 — an older run left full-video files that bestaudio has superseded.
      Only printed when such files exist. NEVER delete them without being asked:
      they are the citizen's files and they are outside every repo.

      ============================================================
      {N} full-video downloads from an earlier run are superseded
      by the audio files beside them — {SIZE} that nothing reads.
      Delete them when you want the space back:
      ============================================================
      find ~/T/_we_citizens/download/videos -name "*.mkv" -delete


Z19 — a video produced far fewer words than its length suggests.
      A note, not a failure. Log it and print it only in the Stage 10 tail.

      ============================================================
      {roster_key}/{video_key}: {N} words from {M} minutes of
      audio. Usually a montage, an advert or a music bed rather
      than speech — the transcript is real, there is just little
      being said. Diarization on this kind of clip also returns
      many more speaker clusters than there are humans.
      ============================================================


Z31 — committed but not pushed. This is the DEFAULT ending of a successful run.

      ============================================================
      Committed to {branch}. NOT pushed — pushing publishes these
      transcripts to a public repo, so it is your call. {N} commits
      are waiting:
      ============================================================
      cd {ROOT_DIR} && git push


Z30 — the final report. Always printed.

      ============================================================
      Run complete — {THE_DATE_TIME_STRING}
      ------------------------------------------------------------
      Selected     20
      Downloaded   18      (2 already on disk)
      Transcribed  17
      Failed        3      artefacts under {VIDEO_DOWNLOAD_ROOT}
      Committed    17      on {branch}, not pushed (see below)
      ------------------------------------------------------------
      Failures:
        kari_lake_us_pres / -EZZ6G-xuyk   yt-dlp: video unavailable
      ============================================================


OTHER SITUATIONS, AND WHAT TO DO — no banner, just log it and carry on

  yt-dlp says "video unavailable", is geo-blocked, or is members-only
    * Skip it. Log it. It is a fact about the video, not a fault in the run. Do not
      try to route around it, and never attempt a paywall or a login.

  `citizens` exits 69
    * The CLI is not built. Build it (Stage 5.3) and continue. No banner needed.

  The out directory has a .transcription and nothing else
    * The sidecar was missing, so nothing could be derived. This is a real state the
      CLI reports, and for this prompt it is a FAILURE — Stage 7.4 applies. Do not
      commit words that cannot be cited.

  A selected row's media is on disk but will not open in ffprobe
    * Treat it as a failed download: mark [FAIL ], log it, do not delete the file.
      A truncated file from an earlier interrupted run is the usual cause, and the
      citizen may want it removed by hand rather than by this prompt.
