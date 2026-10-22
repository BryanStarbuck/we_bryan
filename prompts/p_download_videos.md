p_download_videos

Download political videos into this citizen's own We The Citizens User Data Repo,
transcribe them on THIS machine, and commit the transcriptions so the movement can
read them.

Run from inside ONE citizen's user data repo. It finds the other We The Citizens
repos itself, reads the shared demand list for videos the movement still needs,
downloads those this citizen does not hold, transcribes them against a localhost
install, writes a transcription.yaml sidecar beside each result, and pushes.

IT FINISHES EARLIER RUNS' WORK FIRST. A download whose transcription died is the
most valuable work on the machine (bytes here, movement waiting), so STAGE 1C
reconciles the cross-run ledger {IN_PROGRESS_CSV} against disk and STAGE 1D adopts
that backlog ahead of the demand ladder. The ledger also keeps two runs in two
windows apart: a claim is written BEFORE the work and believed for
{STALE_CLAIM_HOURS}.

Read every stage first. Stages run in order. A stage that cannot complete STOPS
and reports; it never guesses past a missing input.

Every citizen-facing message is in APPENDIX Z by code ("print Z4"). A situation
with no Z code: write the message in the same shape (one sentence of WHY, then the
copyable lines) and note in the run report that a new message was needed.


====================================================================
OUTPUT DISCIPLINE — WHAT REACHES THE CITIZEN
====================================================================

The citizen sees SEVEN things only:

  1. The Stage 1 repo table (Z1).
  2. The Stage 1B top-up table (Z40), ONLY when it added rows.
  3. The Stage 1C backlog table (Z50), ONLY when a backlog exists (a citizen who
     typed "download 20" and is getting a catch-up run must know BEFORE it happens).
  4. The Stage 2 selection table.
  5. The Stage 6 "this will take N" warning (Z20).
  6. Any Z-coded problem, when it happens.
  7. The Stage 10 final report.

Everything else (per-file progress, ffmpeg/yt-dlp output, skips and reasons,
resolved paths) goes to {RUN_LOG}, not the screen. No stage narration, no heading
for a stage with nothing to say.

ONE EXCEPTION: Stage 6 can be silent for most of an hour, which looks hung. Print
one line as each video finishes, nothing more:

      [ DONE] kari_lake_us_pres/0jIindXGitE   374s   1748 s audio


====================================================================
VARIABLES
====================================================================

ROOT_DIR dir is ~/BGit/Bryan_git/we_bryan
  * The citizen's own User Data Repo: where this prompt lives and the ONLY repo it
    may WRITE to. On another citizen's computer, change this one line.
  * If {CONFIG_FILE} carries we_citizens.user_repo_path and it is a valid user data
    repo, that value WINS (the citizen may have cloned elsewhere). Stage 1 settles it.

CONFIG_FILE is file ~/.config/we_citizens/config.yaml
  * Machine-local, outside every repo, never checked in. Schema in APPENDIX A.

DATA_REPO dir is DISCOVERED IN STAGE 1
  * Shared data repo. Remote: https://github.com/ACT3ai/data_we_citizens.git
  * Read-only: never write or commit in it.

WTC_REPO dir is DISCOVERED IN STAGE 1
  * Product repo (web app + citizens CLI). Remote: https://github.com/ACT3ai/we_the_citizens.git
  * Read-only except `just build` / `just run`.

VIDEO_DEMAND_CSV is file {DATA_REPO}/video_demand.csv
VIDEO_DEMAND_YAML is file {DATA_REPO}/video_demand.yaml
  * THE MOVEMENT'S QUEUE, a SNAPSHOT from the video-demand calc engine (runs where
    the private video library is visible), correct only as of its generated_at.
    Read-only. STAGE 1B covers the window since generated_at.

PEOPLE_DIR dir is {DATA_REPO}/people
  * One YAML seed per public figure the movement listens to. Admins add these
    continuously; the engine learns of them only on its next run, and prices them
    only once it holds a video. STAGE 1B's input. Read-only.

ROSTER_DIR dir is {DATA_REPO}/politicians/new
  * Roster records a seed's links[] point at: office, jurisdiction,
    youtube_channel. Read-only.

YOUTUBE_QUEUE_CSV is file {DATA_REPO}/youtube.csv
  * Channel-fetch queue; STAGE 1B's third source for a channel URL. Read-only.

CONTENDERS_SLATE is file {DATA_REPO}/contenders/slate.yaml
  * Sealed contenders edition: live-challenger term and, for anyone on it, a
    seat_kind the rank map understands. ABSENT = challenger column BLANK, never false.

OFFICE_RANK_FILE is the NEWEST file matching
{DATA_REPO}/scores/new_politician_qualified/npq_*.yaml
  * Carries office_importance_rank, the admin-repriceable seat ladder. Read at run
    time so a reprice reprices STAGE 1B too. See APPENDIX F.

QUEUE_ROOT dir is {VIDEO_DOWNLOAD_ROOT}/_queue
  * Outside every repo. `mkdir -p` in STAGE 1B before writing.

QUEUE_SUPPLEMENT_CSV is file {QUEUE_ROOT}/video_demand_supplement.csv
QUEUE_SUPPLEMENT_YAML is file {QUEUE_ROOT}/video_demand_supplement.yaml
  * STAGE 1B's output: rows for people the engine has not priced, SAME COLUMNS as
    {VIDEO_DEMAND_CSV}; Stage 2 reads both as one list.
  * PROVISIONAL on every row: notes names this prompt, run_id is
    "{THE_DATE_TIME_STRING}local_supplement". A statement about who the queue is
    not asking about, never a claim to have run the engine.
  * NEVER appended to {VIDEO_DEMAND_CSV} (STAGE 1B gives three reasons).
  * PERSISTS and accumulates: never truncated, rows never deleted by this prompt.

NEW_PEOPLE_MAX_VIDEOS is the value 10
  * STAGE 1B per-person cap = VIDEO_DEMAND_ROUND_SIZE (round 1 = top 10 per
    person); more would bury the round-1 ladder under one new person.

VIDEO_DOWNLOAD_ROOT dir is ~/T/_we_citizens/download/videos
  * Where this prompt's media lands; OUTSIDE every repo (large, never committed).
  * MEDIA IS DISPOSABLE ONCE THE WORDS EXIST; THE METADATA IS NOT. The
    {video_key}.info.json holds the only copy of channel id, view/like/comment
    counts at capture time, and availability: facts unrecoverable for a past date
    and lost if the video is edited, made private or deleted. *.info.json is in
    {ROOT_DIR}/.gitignore. Stage 7's Capture block rescues them; until a sidecar has
    a Capture block, deleting its directory destroys evidence permanently (e.g.
    tucker/joe_kent predates Capture, lost its media, and `verify` reports it LEGACY
    forever).
  * SAFE TO DELETE: the media file and any superseded full-video file once `verify`
    is green; the .info.json only after its facts are in the sidecar.
  * Layout: {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/{video_key}.{ext}
  * Create it and {VIDEO_DOWNLOAD_ROOT}/_runs before writing.

VIDEO_DOWNLOAD_ROOT_LEGACY dir is ~/T/_we_citizens/videos
  * OLDER media root from code/scripts/download_politician_videos.mjs, same
    {roster_key}/{video_key}/ shape; several hundred videos, some rows only a
    {video_key}.info.json with no media.
  * READ in Stage 2 to avoid double downloads; transcribe FROM it in place. Never
    write into it or move media out.
  * Its {video_key}.video.yaml has title, published_at, bytes, downloaded_at, yt-dlp
    version (Stage 4.6 reads it).

MEDIA_FILE is RESOLVED PER VIDEO, in STAGE 2.3 or STAGE 4
  * Absolute path of the one file handed to the transcriber; may be under EITHER
    media root. Later stages use it, never a rebuilt path.

STAGE_DIR is {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/out/, PER VIDEO
  * Where the CLI writes its nine output files (STAGE 6.2), OUTSIDE every repo.
    Transcription takes minutes to hours; writing into {TRANSCRIPTIONS_ROOT} leaves
    a half-finished dir the STAGE 9.4 auto-committer can commit. Stage outside,
    move in on success (STAGE 7.1). On failure it stays beside the media as evidence.

MEDIA_ROOTS is the ordered list [{VIDEO_DOWNLOAD_ROOT}, {VIDEO_DOWNLOAD_ROOT_LEGACY}]
  * Search order for "does this machine already hold {roster_key}/{video_key}?".

TRANSCRIPTIONS_ROOT dir is {ROOT_DIR}/videos/transcriptions
  * Layout for what THIS prompt writes: {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/
  * Older hand-made dirs with other shapes are LEGACY, left as they are, found by
    video_key not path (Stage 2.3). This tree is committed and pushed.

MANIFEST_FILE is file {ROOT_DIR}/user_repo.yaml
  * The repo's transcript index; unlisted = INVISIBLE to the movement's scanner.
    See STAGE 8 and APPENDIX C.

SIDECAR_TOOL is file {ROOT_DIR}/tools/wtc_sidecar.py
  * The CHECKED-IN builder/verifier for transcription.yaml (test beside it:
    {ROOT_DIR}/tools/test_wtc_sidecar.py), so this prompt never describes a schema
    nothing implements. Three verbs:
      seed    {roster_key}/{video_key}   Stage 3.2. Snapshots the demand row BESIDE
                                         THE MEDIA, outside every repo; refuses to
                                         write under {TRANSCRIPTIONS_ROOT}.
      write   {roster_key}/{video_key}   Stage 7.1. Creates the repo directory and
                                         writes the complete sidecar, merging every
                                         hand-written field already there.
      verify  --all                      Stage 7.5. The gate.
  * It replaced a writer improvised in /tmp each run (outputs committed forever,
    program deleted by the next /tmp sweep). Never move it back to scratch.

CITIZENS_CLI is file {WTC_REPO}/cli/citizens
LOCALHOST_API is the string "http://127.0.0.1:9333"
LOCALHOST_WEB is the string "http://localhost:4444"

VIDEO_COUNT is the number of videos to process this run
  * DEFAULT = 20; the run text may name another ("download 5", "do 50", "just 1").
  * A BUDGET FOR VIDEOS PROCESSED, NOT DOWNLOADED. STAGE 1D spends it on the backlog
    first, so 20 un-transcribed downloads on disk = download NOTHING, still 20
    videos of work. Z50 tells the citizen first ("download" sizes the run).

MAX_VIDEO_SECONDS is the value 10800
  * THREE HOURS. Longer videos are NOT WORKED (not downloaded, adopted, or
    transcribed): skipped, counted, named.
  * Owner's ruling: one 3+ hour podcast eats a run (measured 2026-09-17: three
    baron_coleman_al shows of 13151, 13621, 13903 s were 11.3 of one run's 16.8
    audio hours; the other seventeen videos totalled 5.5). Not a content judgement.
  * THE CITIZEN CAN LIFT IT: run text "do the long ones", "no length limit",
    "include the long podcasts", or naming such a video; Stage 10 says it was lifted.
  * A length skip is NEVER deleted or marked failed: media stays, ledger status
    unchanged, `tries` not incremented. Deferred, not abandoned.

MAX_PARALLEL_TRANSCRIBE is the value 12
DEFAULT_PARALLEL_TRANSCRIBE is the value 4
  * Ceiling and starting point. See STAGE 6.3.

THE_DATE_TIME_STRING is the string "{Date}_{Time}_" using only alphanumerics and
underscores, e.g. 2026_Sep_05_08_14_31_

RUN_LOG is file {VIDEO_DOWNLOAD_ROOT}/_runs/{THE_DATE_TIME_STRING}download_videos.log
  * Outside the repo. Every stage appends what it did, skipped, and why.
    `mkdir -p` its directory in Stage 1.

IN_PROGRESS_CSV is file ~/T/_we_citizens/videos/download/in_progress.csv
  * THE CROSS-RUN TRANSCRIPTION LEDGER. Fixes the recurring failure: a video
    downloaded, transcription died, and the next run walked past it (Stage 2.3
    skips only on "words exist" and selects only from the ladder). Measured
    2026-09-10: 20 downloaded, 0 transcribed, nothing would pick them up.
  * A LEDGER, not a queue: one row per {video_uid} (who works it, since when, tries,
    outcome). STAGE 1C reconciles it with disk; STAGE 1D works the backlog.
  * OUTSIDE EVERY REPO, never committed (operational state, not corpus).
  * SHARED BY SEVERAL RUNS (two windows, killed or crashed runs); APPENDIX G's rules
    exist because the writer is never assumed alone.
  * `mkdir -p` its directory in Stage 1. Missing file: STAGE 1C creates it with the
    APPENDIX G header (a first run, never an error).
  * Path is `videos/download` (reverse of {VIDEO_DOWNLOAD_ROOT}) on purpose: the
    owner named it. To move it under {QUEUE_ROOT}, change this one line.

IN_PROGRESS_LOCK is file {IN_PROGRESS_CSV}.lock
  * A DIRECTORY created with `mkdir` (atomic everywhere).
  * Held ONLY around a read-modify-write of {IN_PROGRESS_CSV} (milliseconds), NEVER
    across a download or transcription. The ledger CLAIM marks long work in flight;
    the lock only protects the file.
  * STALE LOCK: exists with mtime older than 60 seconds = holder gone. Remove it,
    log the break, proceed.

STALE_CLAIM_HOURS is the value 8
  * How long a `started` row is believed. Inside the window it is ANOTHER RUN'S
    WORK, left alone (stealing wastes an hour of CPU on both and races on one
    STAGE_DIR). Outside it the claim is dead and may be taken over. Longer than any
    measured transcription, short enough to recover an overnight crash next morning.

MAX_TRANSCRIBE_TRIES is the value 3
  * After three genuine attempts a video is SKIPPED (truncated file, refused codec,
    or pipeline bug; a fourth try reaches the same place). Its row and reasons stay
    for a human.
  * OVERRIDE: run text "retry the failures", "retry exhausted", "try the max-tries
    ones", or naming such a video lifts the cap for that run; the ledger records a
    forced retry. The intended way to rework a video after fixing its bug.


====================================================================
TWO KEY NAMESPACES — DO NOT COLLAPSE THEM
====================================================================

The same human has two names, and the difference decides where files go.

  roster_key   {VIDEO_DEMAND_CSV}'s FIRST COLUMN. Office-scoped:
               kari_lake_us_pres, tucker_carlson_us_pres, darryl_cooper_us.
               Matches a directory in {DATA_REPO}/politicians/new/.
               THE DIRECTORY SEGMENT under {TRANSCRIPTIONS_ROOT} and every media
               root. Verbatim, byte for byte, always.

  person_key   The frozen office-free PERSON key: tucker_carlson, casey_putsch.
               Exists only when {DATA_REPO}/people/{person_key}.yaml exists (~100
               seeds vs thousands of roster entries, so usually NOT).
               {MANIFEST_FILE}'s speaker map is keyed by it.

Rules:
  * The CSV column LABELLED person_key is NOT one; read it as roster_key.
  * To get a person_key, strip and guess nothing: read one from
    {DATA_REPO}/politicians/new/{roster_key}/{roster_key}.yaml if stated, else test
    {DATA_REPO}/people/{candidate}.yaml for a candidate the roster record names.
  * None resolves: OMIT it. Chopping "_us_pres" off a roster key fabricates an
    identity claim the scanner surfaces to an admin.
  * Exception (not a collapse): a `people_only` row is published under the PERSON
    key (no roster record to scope it). Column 1 holds that person key, it is the
    directory segment, and {DATA_REPO}/people/{that key}.yaml exists by definition,
    so Stage 8 may state it; still verify with one `test -f`.
  * Stage 10 reports how many entries could not resolve a person_key.


====================================================================
HARD RULES — VIOLATING ANY OF THESE FAILS THE RUN
====================================================================

* NEVER ask production to transcribe (not as fallback, not "to test"). Every CLI
  call carries --local; the CLI's DEFAULT TARGET IS PRODUCTION, so an omitted
  --local is an accidental production call. Never reach https://app.WeTheCitizens.io.

* NEVER write to {DATA_REPO}: no commit, `git add`, repair, pull, or appended row to
  {VIDEO_DEMAND_CSV}. STAGE 1B writes to {QUEUE_SUPPLEMENT_CSV} outside every repo.

* NEVER write application code into {WTC_REPO}; only `just build` and `just run`.

* NEVER PUT A PARTIAL OR FAILED TRANSCRIPTION INTO {ROOT_DIR}, by never writing it
  there, not by cleaning up. Nothing enters {TRANSCRIPTIONS_ROOT} until the words
  exist (STAGE 3, 7.1); failure artefacts stay beside the video (STAGE 7.4). The
  scanner cannot tell a half-written repo dir from a complete one.

* NEVER DELETE A TRANSCRIPT OR A TRACKED FILE UNDER {ROOT_DIR}. "Clean up the
  partial" destroyed fifteen committed transcription.yaml files on 2026-09-07. A
  path under {TRANSCRIPTIONS_ROOT} tracked by git, or holding a
  {video_key}.transcription, is never this run's to remove. STAGE 7.4a is the guard.

* NEVER download in violation of a site's Terms of Service. Unlawful URL: skip,
  record in {RUN_LOG}, move on.

* NEVER WORK A VIDEO LONGER THAN {MAX_VIDEO_SECONDS} unless the citizen lifted the
  cap. Tested where length becomes known: STAGE 2.3 (row or legacy sidecar), STAGE
  1D.1 (backlog media on disk), STAGE 4.5 (everything else; always available and
  true). Media and ledger row untouched; a deferral, not a failure.

* NEVER invent a video_key or roster_key. Both FROZEN, verbatim from
  {VIDEO_DEMAND_CSV}; one derived from a filename or title is a bug.

* NEVER commit media (.mp4, .webm, .m4a, .info.json) inside {ROOT_DIR}.

* NEVER create or switch a git branch.

* NEVER modify a transcript directory this run did not create. Legacy dirs are read
  to answer "do we already have this?" and otherwise untouched.

* NEVER START A TRANSCRIPTION WITHOUT FIRST WRITING THE CLAIM TO {IN_PROGRESS_CSV}
  (Stage 6.1b), and never delete or truncate it. A hung or killed attempt runs no
  code afterwards, so a post-hoc ledger records only successes and loses exactly
  the failures the next run must find.

* NEVER STEAL A LIVE CLAIM. A `started` row within {STALE_CLAIM_HOURS} belongs to
  another run, maybe another open window. Leave it, count it, report it.


====================================================================
STAGE 1 — FIND THE OTHER REPOS AND SETTLE {CONFIG_FILE}
====================================================================

Goal: DATA_REPO, WTC_REPO and ROOT_DIR set to verified absolute paths, and
{CONFIG_FILE} saying the same. Nothing later guesses a path.

1.1 READ {CONFIG_FILE} IF IT EXISTS

* Absent: note "config absent — will create", go to 1.3.
* Present: parse BOTH shapes: CURRENT (nested under `we_citizens:`, APPENDIX A) and
  RETIRED (bare top-level `user_repo_path:`). Retired: carry the value forward,
  REWRITE into the current shape in 1.6, say so.
* Every value is a CLAIM until 1.2 verifies it.

1.2 VERIFY EVERY PATH THE CONFIG CLAIMS — A STALE PATH IS WORSE THAN A MISSING ONE

For each of the three values: directory exists, has .git, and
`git -C <path> remote -v` fetch remote matches the slot:
      user_repo_path        the citizen's own fork/clone of
                            template_user_repo_we_citizens; any remote accepted,
                            the content marker is the shape test
      data_repo             github.com/ACT3ai/data_we_citizens
      we_the_citizens_repo  github.com/ACT3ai/we_the_citizens
and the content marker holds:
      data_repo             {path}/video_demand.csv exists
      we_the_citizens_repo  {path}/cli/citizens exists AND {path}/justfile exists
      user_repo_path        {path}/user_repo.yaml OR {path}/videos/ exists
Any failure = STALE: discard and search; never "fix it up" (the wrong repo is how
a transcript lands in somebody else's tree). All four pass = CONFIRMED.

1.3 SEARCH THE DISK FOR ANYTHING NOT CONFIRMED (first confirmed hit per slot)

  * Common locations first:
      data_repo:            ~/BGit/act3/data_we_citizens
                            ~/data_we_citizens
                            ~/BGit/data_we_citizens
      we_the_citizens_repo: ~/BGit/act3/we_citizens
                            ~/BGit/act3/we_citizens
                            ~/we_citizens
                            ~/BGit/we_citizens
      user_repo_path:       this prompt's directory walked UP to the enclosing git
                            root (almost always the answer; try it first).
  * Else search by REMOTE: walk ~/BGit and its children, ~/, ~/Documents,
    ~/Projects, ~/src, ~/code to depth 4; `git -C <dir> remote -v` on each .git dir.
  * NEVER Spotlight/`mdfind` or any index-backed search (indexing is off; they
    return nothing while appearing to succeed). Use `fd`, else `find -maxdepth`,
    else a plain listing walk.
  * Every candidate goes through the full 1.2 check.

1.4 WHAT TO DO WHEN A SLOT CANNOT BE FOUND

  * user_repo_path: fatal. Print Z2, STOP.
  * data_repo: fatal (no demand list). Print Z3, STOP. Do not clone it yourself.
  * we_the_citizens_repo: NOT fatal here (Stages 2-4 run without it); Stage 5.1 asks.

1.5 Print Z1 (one line per slot: how it was resolved).

1.6 WRITE {CONFIG_FILE} BACK, AND MAKE THE RUN DIRECTORIES

* Create ~/.config/we_citizens/ if needed. Write every CONFIRMED path in the
  APPENDIX A shape, absolute and fully expanded (no "~", no relative; readers have
  other cwd and maybe other HOME).
* Preserve keys this prompt does not own. Leave a slot OUT rather than write an
  unverified path (absent = go look; wrong = go to the wrong place).
* Already correct: do not rewrite; Z1 says "unchanged".
* mkdir -p {VIDEO_DOWNLOAD_ROOT} and {VIDEO_DOWNLOAD_ROOT}/_runs. Open {RUN_LOG}.

1.7 THE MEDIA GITIGNORE — A SAFETY NET FOR THE HARD RULE

If {ROOT_DIR}/.gitignore does not already ignore media, append this (create the
file if absent) and include it in Stage 9's commit:

    # Media never belongs in this repo — it lives under ~/T/_we_citizens/.
    *.mp4
    *.webm
    *.mkv
    *.m4a
    *.info.json
    *.webp
    # ...but the empty-directory markers must always survive.
    !.gitkeep

Stage 10 says whether it was added. Never REMOVE an existing rule.


====================================================================
STAGE 1B — TOP UP THE QUEUE WITH PEOPLE THE ENGINE HAS NOT PRICED
====================================================================

THE WINDOW THIS STAGE CLOSES. {VIDEO_DEMAND_CSV} is the engine's output as of its
generated_at; admins commit new seeds into {PEOPLE_DIR} anytime. In between
(sometimes days) a human is on the movement's books and on nobody's queue. The
engine's own {VIDEO_DEMAND_YAML} gap sentences admit it: for some eligible people
"we hold no video and no channel record for them ... This is a SOURCING gap, not a
calc gap — re-running this engine cannot move it." A citizen's machine with yt-dlp
can close exactly that gap.

PRODUCES {QUEUE_SUPPLEMENT_CSV} (same columns as {VIDEO_DEMAND_CSV}, only rows the
engine has not published) and {QUEUE_SUPPLEMENT_YAML} (how it was built, what it
could not establish). Stage 2 reads both as one list.

NEVER APPENDED TO {VIDEO_DEMAND_CSV}; written under {QUEUE_ROOT}. Any one reason suffices:
  * {DATA_REPO} is read-only so a citizen's run can never corrupt the shared record.
  * The next engine run OVERWRITES that file; an appended row would later vanish,
    leaving no way to tell priced from guessed-then-deleted.
  * {VIDEO_DEMAND_YAML} publishes csv_sha256; appending breaks it and every verifier
    (including Stage 2.1) reports the movement's file as tampered.

PROVISIONAL: rows carry run_id "{THE_DATE_TIME_STRING}local_supplement" and a notes
cell naming this prompt; this machine's best answer to "who is the movement not
asking about", never an engine run.

Nothing to top up (normal on a freshly pulled data repo): write and print nothing,
log one line.


1B.0 PRECONDITION

Stage 1 confirmed {DATA_REPO}; {RUN_LOG} is open. No {PEOPLE_DIR} (older data repo):
log it and skip the stage (not an error). Read-only freshness check:

        git -C {DATA_REPO} fetch --dry-run 2>&1 | head -5

Remote ahead: print Z42 and CARRY ON (stale data repos show priced people as "new";
the fix is the citizen's own pull). Never pull {DATA_REPO} yourself (a merge is a write).


1B.1 THE QUEUE'S OWN AS-OF DATE

* QUEUE_ASOF = generated_at from {VIDEO_DEMAND_YAML}; also read run_id. Missing:
  fall back to the newest computed_at in {VIDEO_DEMAND_CSV} and log the fallback.
* Log QUEUE_ASOF and run_id; Stage 10 names them.


1B.2 THE TIMESTAMP IS THE HINT. ABSENCE FROM THE LADDER IS THE TEST.

"Seeds newer than the CSV" fails silently both ways: filesystem mtime is the
checkout time, not commit date (fresh clone = all new, old clone = none), so mtime
may only WIDEN the set, never narrow it; and an OLD seed can still be unpriced (the
33 people in the engine's gap sentence). Candidates = UNION of, logging which test
caught each:

  (a) SEED NEWER THAN THE QUEUE: latest of the seed's updated_at (else created_at),
      `git -C {DATA_REPO} log -1 --format=%cI -- people/<file>`, and mtime is after
      QUEUE_ASOF.

  (b) ZERO ROWS ON THE LADDER: none of the seed's person_key and EVERY links[].key
      appears in column 1 of {VIDEO_DEMAND_CSV}. Never test the person key alone
      (roster-linked humans publish under the ROSTER key; a person-key test mints a
      duplicate ladder). Still insufficient: links[] can be incomplete (measured
      2026-09-10: marjorie_taylor_greene links ..._us_pres but her rows are under
      marjorie_taylor_greene_ga_14; matt_gaetz links matt_gaetz_us, rows under
      matt_gaetz_fl_01), so 1B.5 de-duplicates by video id again.

  (c) NAMED BY THE CITIZEN ("do the new people", "add jack_farley"), even if (a)
      and (b) passed them over.

Read column 1 ONCE into a set (~150k rows, 35MB; never grep per person):

        cut -d, -f1 {VIDEO_DEMAND_CSV} | tail -n +2 | sort -u

Then SUBTRACT, logging each reason:
  * already has rows under any of its keys
  * already in {QUEUE_SUPPLEMENT_CSV} with unworked rows (do not re-list the channel)
  * bryan_starbuck, or any seed matching the citizen running this (THE CITIZEN IS
    NOT A WORK ITEM)


1B.3 WHICH STORE IS THIS HUMAN KNOWN FROM — subject_kind, IN THE SPEC'S OWN ORDER

Resolve by this ordered list (calc_engine_video_demand.mdx §12.2), FIRST match, not
by "is there a seed?":

  1. a links[] entry of kind new_politician       -> new_politician
  2. a links[] entry of kind worrisome_challenger -> worrisome_challenger
  3. a links[] entry of kind legacy_politician    -> legacy_politician
  4. a links[] entry of kind fix_bill_author      -> fix_bill_author
  5. none of the four, and the seed exists        -> people_only
  6. none of the above                            -> BLANK, never people_only

people_only = a seed with NO roster link (a human on politicians/new/ is
new_politician even with a seed).

Column 1 (the directory segment later stages use): people_only -> the PERSON key;
any roster kind -> that link's ROSTER key. Both verbatim from the seed, never built
by adding/removing an office suffix (TWO KEY NAMESPACES).


1B.4 FIND THE CHANNEL — ATTRIBUTED, OR NOT AT ALL

Attributing videos to the wrong human publishes one person's words under another's
name, the worst thing this prompt can do. The channel must come from a committed
record, first hit of:

  1. the seed's own source_urls[] — any youtube.com entry
  2. {ROSTER_DIR}/{roster_key}/{roster_key}.yaml -> youtube_channel
  3. {YOUTUBE_QUEUE_CSV} — the row whose person_key (col 18) or politician_key
     (col 3) is one of this human's keys, and its target (col 4)

NEVER search YouTube by name or accept a lookalike handle. No hit = UNSOURCED: no
rows, counted, named in Z40 with the remedy (add a youtube.com URL to the seed's
source_urls, or file a youtube.csv row). Log which source supplied each channel; on
disagreement take the seed's (an admin's record; youtube.csv is a work queue) and
log both.


1B.5 LIST THE UPLOADS — REAL PLATFORM IDS, NEVER MINTED KEYS

        yt-dlp --flat-playlist --playlist-end {NEW_PEOPLE_MAX_VIDEOS} \
               --print "%(id)s\t%(duration)s\t%(title)s" \
               "{channel_url}/videos"

  * Metadata listing of a public page, no media; same ToS rule as Stage 4 (cannot
    list lawfully: skip, log).
  * `/videos` often fails (measured 2026-09-10: 7 of 12 channels, "This channel does
    not have a videos tab" / "Unable to download API page"). On failure retry ONCE
    with the BARE channel URL, and once with `{channel_url}/streams` for live-show
    people. A 403, login wall, age gate or members-only listing is a NO, never retried.
  * video_key = the 11-character YouTube id exactly as printed (the engine publishes
    video_key = youtube_id = source_ref on YouTube rows), so this READS a frozen key.
    Anything not [A-Za-z0-9_-]{11}: drop and log.
  * Every supplement row is round 1 (cap {NEW_PEOPLE_MAX_VIDEOS}); there is no round 2.
  * `--playlist-end` gives MOST RECENT uploads, not the engine's priority order; with
    no held transcripts every row for a person prices identically (§3.2), so recency
    is the only ordering. State that in {QUEUE_SUPPLEMENT_YAML}.
  * Zero videos listed: counted listed-empty, no rows, one log line.
  * Listing fails twice: drop for this run; no third try, no other channel.

DE-DUPLICATE BEFORE PRICING: drop any id already in column 3 of {VIDEO_DEMAND_CSV} or
with words in this repo:

        find {TRANSCRIPTIONS_ROOT} -name "{video_key}.transcription"

A re-listed channel must produce no duplicate. A bare-key comparison is a bug
everywhere else (video_key is unique per person only) but right here: a YouTube id
names one video platform-wide.

If this drops EVERY id for a candidate, it was never new: the ladder has them under a
roster key the seed's links[] omits (measured: all ten matt_gaetz uploads were under
matt_gaetz_fl_01). Record `already_on_ladder_under=<that key>`, add no rows, and name
it in the 1B.8 patch CSV (remedy: an admin's one-line links[] edit).


1B.6 PRICE EACH ROW — APPENDIX F, NOT A NUMBER INVENTED HERE

Run APPENDIX F exactly; never approximate or copy a "similar" row's priority.
Inputs to source:
  * office_importance_rank from the NEWEST
    {DATA_REPO}/scores/new_politician_qualified/npq_*.yaml (admin policy, read live).
    Unreadable: the seat term is a stated cause, NOT zero (APPENDIX F).
  * sealed slate {DATA_REPO}/contenders/slate.yaml: key in assignments[] = challenger
    true; absent from an EXISTING slate = false; NO slate = BLANK (not false).

The two transcript counts are LOCAL (over this machine's {TRANSCRIPTIONS_ROOT}).
For a new person both are 0, same as the engine. Otherwise the supplement's priority
is HIGHER than the movement's would be; state that gap in {QUEUE_SUPPLEMENT_YAML}.
Never guess what other citizens hold.

Expected answers (catch implausible numbers):
  * a never-heard people_only human       ->  priority 100
  * a never-heard state assembly seat     ->  priority 490
  * a never-heard senator                 ->  priority 595
  * a never-heard president               ->  priority 700
  * any of the above, +150, when the key is on the sealed slate
  * any of the above, +100, when yt-dlp printed a duration over 2400 seconds

The +100 is the long-form term working (engine rows have blank durations so it is
dead there; a listing gives real durations). The one place a supplement row is
knowingly priced above the engine; say so in {QUEUE_SUPPLEMENT_YAML}.

A row above 950 or below 0 is a sum bug: log, drop, say so in Stage 10.


1B.7 WRITE {QUEUE_SUPPLEMENT_CSV}

* Header READ from {VIDEO_DEMAND_CSV} at run time, byte for byte (columns are
  append-only; carry an unknown newer column as an empty cell). Fill cells by
  column NAME, never position.
* Fixed values on every supplement row:
      round                     1
      status                    open
      closed_reason             (empty)
      notes                     added by p_download_videos STAGE 1B — not engine-priced
      computed_at               this run's ISO 8601 timestamp
      run_id                    {THE_DATE_TIME_STRING}local_supplement
      trusted_transcripts_held  0
      source_type               youtube
      source_url                https://www.youtube.com/watch?v={video_key}
      ipfs_cid                  (empty)
      source_ref                {video_key}
      video_uid                 {column-1 key}::{video_key}
      youtube_id                {video_key}
* BLANK IS AN ABSENCE, NEVER A ZERO. seat_rank blank whenever the seat term carried a
  cause, including every people_only row ("no candidacy on file — known from people/
  only"); a 0 against a named living person reads as "least important office", a
  measurement never made. duration_seconds blank unless yt-dlp printed a number.
* Order: round asc, priority desc, column-1 key asc, video_uid asc (engine order).
* Existing file: MERGE by video_uid (keep existing rows untouched, add new). Never
  delete a supplement row (a worked row costs one Stage 2 skip; a wrongly deleted
  one costs a video nobody fetches).

{QUEUE_SUPPLEMENT_YAML} beside it, in {VIDEO_DEMAND_YAML}'s shape:

    video_demand_supplement:
      schema_version: 1
      run_id: "{THE_DATE_TIME_STRING}local_supplement"
      generated_at: <ISO 8601>
      generated_by: "p_download_videos STAGE 1B"
      queue_asof: <QUEUE_ASOF>
      queue_run_id: "<the engine run_id this supplements>"
      people_examined: <n>
      people_added: <n>
      people_unsourced: <n>
      people_listed_empty: <n>
      rows_added: <n>
      csv_sha256: <sha256 of the supplement csv>
      gaps:
        - "PROVISIONAL, NOT ENGINE-PRICED. These rows were priced on one citizen's
          machine by a prompt, against calc_engine_video_demand.mdx §3. They are a
          statement about who the movement's queue is not asking about, never a
          claim to have run the engine, and the next engine sweep supersedes them."
        - "transcripts_held and person_transcripts_held are LOCAL counts over this
          citizen's own repo. This machine cannot see the movement's corpus, so a
          priority here is an UPPER bound on the movement's."
        - "<one sentence per unsourced person: no committed YouTube channel, remedy
          is a source_urls entry on the seed or a youtube.csv row>"
        - "<the recency note from 1B.5>"

Verify before trusting: re-read; every row parses under the real header; no
video_uid duplicated within it or shared with {VIDEO_DEMAND_CSV}; every priority an
integer in [0, 1000]. Failing rows dropped and logged.


1B.8 THE PATCH THE ENGINE'S OWNER CAN ACTUALLY USE

The durable fix is the engine learning these people exist. Write
{QUEUE_ROOT}/{THE_DATE_TIME_STRING}new_people_patch.csv, one row per PERSON:

    person_key,column_1_key,subject_kind,channel_url,channel_source,videos_listed,rows_added,status

status: added, unsourced, listed_empty, dropped, with the reason. Name the file in
Stage 10 (the artifact a citizen sends to whoever runs the demand engine).


1B.9 SAY WHAT ADDING THEM DOES AND DOES NOT DO

Supplement rows are on the queue but not near the top, by ratified design: a
never-heard senator is 595, a people_only human 100, and with 150,000 priced rows a
default run of 20 never reaches them ("a human with no candidacy on file waits behind
one who has"; only the ROUND keeps low rows reachable, and this stage cannot raise
rounds). Measured 2026-09-10: 30 rows added at 400/200/100; all 20 slots went to
senators at 595. So 1B output is a STANDING queue addition. Reachable now via:
  * THE CITIZEN NAMES THEM (or says "do the new people"): Stage 2.3 restricts to
    those keys and bands stop mattering (Z40's last line says so).
  * THE ENGINE PRICES THEM: the 1B.8 patch CSV, the durable fix.
Whenever rows were added and none selected, say this in Stage 10 (otherwise the
citizen concludes the stage did nothing and turns it off).

1B.10 REPORT

* Rows added: print Z40 once, before the selection table. Nothing added: print
  nothing, one {RUN_LOG} line. Never per-candidate terminal lines.


====================================================================
STAGE 1C — RECONCILE THE LEDGER WITH WHAT IS ACTUALLY ON DISK
====================================================================

THE HOLE: a video downloads, then transcription dies (app crash, cancel, sleep,
server restart). Stage 2 selects only from the ladder and 2.3 skips only when WORDS
exist, so the download is never looked at again (measured 2026-09-10: 20 downloaded,
0 transcribed). This stage asks: WHAT HAS THIS MACHINE DOWNLOADED AND NOT YET TURNED
INTO WORDS?

THE DISK IS THE TRUTH; THE LEDGER IS THE CLAIM. Reconcile in that direction only: a
`finished` row with no transcript is corrected; a transcript with no row (pre-ledger)
gets a row. A ledger overriding the disk would let one bad row hide a backlog forever.

1C.0 PRECONDITION

Stage 1 confirmed {ROOT_DIR} and media roots; {RUN_LOG} open. `mkdir -p` the
{IN_PROGRESS_CSV} directory. Missing ledger: create it with the APPENDIX G header,
log "ledger created — first run on this machine", continue to 1C.2 (the first scan
populates it from existing downloads).

1C.1 READ THE LEDGER UNDER THE LOCK

Take {IN_PROGRESS_LOCK} (break if stale), read the whole file, release. Parse by
COLUMN NAME (APPENDIX G is append-only). An unparseable row is LEFT EXACTLY AS IT IS
and reported: another run's writing, never this run's to drop or repair.

1C.2 WALK BOTH MEDIA ROOTS AND CLASSIFY EVERY VIDEO

For every {roster_key}/{video_key}/ under {MEDIA_ROOTS}, two facts only:

  HAS_MEDIA   a transcriber-allowlisted file (Stage 4.4) exists, audio preferred over
              video as in Stage 2.3. A lone .info.json is NOT media; a .fNNN
              pre-merge part is never media.
  HAS_WORDS   `find {TRANSCRIPTIONS_ROOT} -name "{video_key}.transcription"` hits. BY
              VIDEO KEY, NOT PATH (legacy dirs have hand-made names; a path test
              re-transcribes audio the citizen already has).

Four classes, one correct ledger state each:

  media + words        -> `finished`; correct and log any other state (closes
                          `started` rows from runs that succeeded then died).
  media, NO words      -> THE BACKLOG; 1C.3 decides its state.
  NO media, words      -> `finished`, media cleared. Normal (media disposable after
                          words + Capture). Never re-download.
  NO media, no words   -> no row. If the ledger has one, mark `media_gone` and say so
                          (download never completed or file removed); Stage 2 may
                          select it again.

Log the four counts; print nothing yet.

1C.3 WHAT STATE A BACKLOG ROW SHOULD CARRY

For media with no words:

  * NO LEDGER ROW -> add `status: pending`, `tries: 0`, timestamps empty. Never infer
    `tries` from a STAGE_DIR or .FAILED.txt (evidence, not a count). Do carry a
    {video_key}.FAILED.txt reason into `note`.
  * `started` within {STALE_CLAIM_HOURS} -> LEAVE COMPLETELY ALONE (another run is on
    it; not this run's row or media). Count it.
  * `started` older than {STALE_CLAIM_HOURS} -> DEAD claim: `status: failed`, reason
    `claim expired after {STALE_CLAIM_HOURS}h — the run that held it did not
    finish`, `tries` unchanged (the attempt counted). Adoptable by 1D.
  * `failed` -> adoptable, subject to the tries cap.
  * `finished` but no words -> ledger wrong: `status: failed`, reason `ledger said
    finished but no transcript exists`; log loudly (an earlier run claimed false success).
  * `pending` -> adoptable.

Never give a row this run did not claim a new `started_at` (timestamps are the only
evidence of how long something has been stuck).

1C.4 WRITE THE RECONCILED LEDGER BACK, ONCE, UNDER THE LOCK

Take the lock and RE-READ (another run may have written since 1C.1). Merge by
{video_uid}:
  * row this stage corrected -> write it, UNLESS the re-read shows it now `started`
    within {STALE_CLAIM_HOURS} (another run just claimed it; its claim wins; log).
  * row untouched -> keep the re-read version byte for byte.
  * row being added -> add it.
Write atomically (temp file + rename on the same filesystem), release.

NEVER TRUNCATE THE LEDGER OR DELETE A ROW (a `finished` row is the record of done
work; deleting it costs a re-download and re-transcription). Pruning is a human's call.

1C.5 REPORT

* Backlog exists: print Z50 (adoptable / claimed by another run / capped out).
* No backlog, no corrections: print nothing; one {RUN_LOG} line.
* Corrections but no backlog: nothing on the terminal, but NAME every correction in
  Stage 10.


====================================================================
STAGE 1D — WORK THE BACKLOG BEFORE DOWNLOADING ANYTHING NEW
====================================================================

        AN ALREADY-DOWNLOADED VIDEO OUTRANKS EVERY ROW ON THE DEMAND LADDER.

The bytes and bandwidth are spent and the movement is waiting; no new download is
worth more than finishing work one stage from done. Downloading more while
un-transcribed media sits on disk builds a permanent backlog.

1D.1 BUILD THE ADOPTION LIST

From 1C's ledger, rows where ALL hold:
  * HAS_MEDIA true, HAS_WORDS false
  * status `pending` or `failed` (live `started` already excluded by 1C)
  * `tries` < {MAX_TRANSCRIBE_TRIES}, unless the citizen lifted the cap
  * media shorter than {MAX_VIDEO_SECONDS} (ffprobe it; 1D.3 does anyway), unless
    lifted. Over-cap rows stay untouched (not adopted, not failed, tries unchanged),
    counted SEPARATELY from try-capped rows in Z50 and named in Stage 10 ("too long"
    and "failed three times" are opposite facts).

Order: fewest `tries`, then oldest `earliest_attempt_at`, then {video_uid} (likely
wins first; longest-stuck first within that).

Citizen-named restrictions (Stage 2.3b) filter this list too ("peter" did not ask for
someone else's backlog); say so in the table.

1D.2 THE CAP, AND WHAT IT DOES TO {VIDEO_COUNT}

Adopted videos consume {VIDEO_COUNT} slots FIRST.
  * Backlog >= {VIDEO_COUNT}: catch-up run only; take the first {VIDEO_COUNT},
    download NOTHING, say so before it happens.
  * Backlog < {VIDEO_COUNT}: adopt all; Stage 2 fills the rest from the ladder.
  * Empty: Stage 2 as always.
Overrides: "just the backlog" / "catch up" -> adopt only, never download. "skip the
backlog" / "only new" -> adopt nothing, log the size, STILL report it in Stage 10.

1D.3 CARRY THEM FORWARD

An adopted row reaches Stage 4 with MEDIA_FILE resolved (1C.2) and marked "already
on disk": it SKIPS 4.2-4.4, runs 4.5 and 4.6, gets its Stage 3.2 seed if missing,
and is claimed in Stage 6 like a fresh download. One transcription path, not two.

Believe 4.5's ffprobe: interrupted downloads are often TRUNCATED (why some failed).
Won't open: mark `failed`, reason `media will not open in ffprobe — probably a
truncated download`, do NOT delete the file, let Stage 2 decide on re-download, say
it in Stage 10.


====================================================================
STAGE 2 — CHOOSE WHICH VIDEOS TO DOWNLOAD
====================================================================

2.1 READ THE DEMAND LIST — BOTH HALVES OF IT

* Read {VIDEO_DEMAND_CSV} (columns in APPENDIX B), ALREADY SORTED by priority, highest first.
* Read {QUEUE_SUPPLEMENT_CSV} if 1B wrote or found one, as part of the same list (same
  columns, read by NAME; no separate traversal or quota).
  * Supplement rows are MARKED wherever the citizen sees them (Z41 in the 2.4 table,
    Stage 10) so movement-requested and machine-added videos are distinguishable.
  * A video_uid in BOTH files: THE ENGINE'S ROW WINS (it sees the corpus); drop the
    supplement row this run.
  * Downstream unchanged: Stages 3.2 and 7.1 pass --demand-csv {QUEUE_SUPPLEMENT_CSV}
    to {SIDECAR_TOOL} for supplement rows; the sidecar records which row it used.
* Read {VIDEO_DEMAND_YAML} (run_id, generated_at, rows_open, gaps); log run_id.
* If it carries csv_sha256, verify with `shasum -a 256`; mismatch: print Z10, log, keep
  going (the CSV is still the list).
* Only status `open` or `partial`; skip `satisfied` and any closed_reason.

2.2 PICK THE TRAVERSAL — ODD/EVEN STRIDE ON LONG LISTS

* Count eligible rows across BOTH files.
* <= 1000: walk straight down from the top.
* > 1000: CURRENT WALL-CLOCK MINUTE odd -> odd positions (1st, 3rd, ...); even -> even
  positions (2nd, 4th, ...); 1-based over eligible rows after 2.1. Several citizens run
  this at once; the stride spreads work at no coordination cost. Two buckets halve
  collisions, not eliminate them (2.3 makes a collision cost a skip). Log the minute
  and stride.

2.3 SKIP WHAT THIS CITIZEN ALREADY HAS

Skip a row if ANY holds:

  * THE WORDS ALREADY EXIST IN THIS REPO, tested by VIDEO KEY anywhere under
    {TRANSCRIPTIONS_ROOT} (legacy dirs have hand-made names):

        find {TRANSCRIPTIONS_ROOT} -name "{video_key}.transcription"

  * {MANIFEST_FILE} already lists the video_key.
  * The row is unobtainable, satisfied, or has a closed_reason.
  * STATED LENGTH OVER {MAX_VIDEO_SECONDS} (cap not lifted), from duration_seconds or a
    {video_key}.video.yaml beside on-disk media. Catches little (duration_seconds is
    blank on nearly every engine row; APPENDIX F says why), so 4.5 is the real
    enforcement; this saves downloads only where length is known. BLANK IS UNKNOWN,
    NEVER SHORT: neither a pass nor a fail, deferred to 4.5.
  * The {video_uid} is `started` in {IN_PROGRESS_CSV} within {STALE_CLAIM_HOURS}
    (another run's work; selecting it races on STAGE_DIR). Skip, count, log.

A DIRECTORY IS NOT A TRANSCRIPT. Older runs left seed-only dirs with a stub
transcription.yaml and no words. Not a skip, not an error: note it, work the video
normally, let Stage 7.1 overwrite the stub (the tool merges, so human edits survive).
List them in Stage 10; 7.4b says when one may be cleared.

Never skip merely because media is on disk; resolve and carry it forward:

  * MEDIA_FILE: search {MEDIA_ROOTS} in order for
    <root>/{roster_key}/{video_key}/{video_key}.<ext>, <ext> on the 4.4 allowlist (a
    lone .info.json or a .fNNN part is never a hit). PREFER AUDIO (.m4a, .opus, .mp3,
    .wav, .flac, .ogg) over video (.mp4, .mkv, .webm, .mov, .avi): same words, fewer
    bytes. Largest within a group. First hit wins; record its ABSOLUTE path, mark
    "already on disk", transcribe in place (never write the legacy root or move media).
    .webm may be audio-only or a full merge: ask ffprobe for a video stream.
  * Nothing found: Stage 4 downloads it.

Continue until VIDEO_COUNT are selected or the list ends; skips do not consume slots.
Stage 1D already took slots: this stage selects {VIDEO_COUNT} minus adopted, which may
be zero (a full run of already-paid work, not an error).

2.3b DEPTH OR BREADTH — SAY WHICH, BECAUSE THE DEFAULT IS DEPTH

Priority is largely per PERSON, so consecutive rows are usually one person: a run of
20 covers about four people (DEPTH, the default, following the engine's ranking).
The product's `citizens batch` defaults the other way (`--breadth 2`, "breadth-first,
so every person gets words early"). Never decide silently:

  * CITIZEN NAMED PEOPLE (person_key, roster key, "the new people" / "the ones Stage
    1B added"): restrict to matching column-1 keys in priority order, ignore the
    stride. Overrides both defaults; the only way to work low-priced rows on purpose.
    Say so in the table.
  * DEFAULT: depth.
  * "spread it out", "breadth", "one each", or a number of people: cap at N rows per
    roster_key, still in priority order.
  * Always state in the selection table how many distinct people the run covers.

2.4 REPORT THE SELECTION BEFORE DOING ANY WORK

Print the selection table (Z11): roster_key, video_key, priority, state.

Status brackets used through the rest of this run:
      [     ]  not started
      [ DL  ]  media on disk, not transcribed
      [IN-PR]  transcription running
      [ DONE]  transcribed, sidecar written, staged for commit
      [FAIL ]  failed — artefacts moved out of the repo, reason logged


====================================================================
STAGE 3 — SEED THE DEMAND ROW, OUTSIDE THE REPO
====================================================================

        NOTHING IS WRITTEN INTO {TRANSCRIPTIONS_ROOT} UNTIL THE WORDS EXIST.

Not a directory, .gitkeep, or stub transcription.yaml; Stage 7.1 creates the dir and
sidecar in one step on success.

WHY (2026-09-07): stubs were seeded into the repo before download; the external
auto-committer (Stage 9.4, "Bryan 26 Tower") committed fifteen mid-run; the app on
:9333 would not stay up and they failed; Stage 7.4 removed the dirs; so fifteen
committed transcription.yaml files were DELETED (901615a created, d4452fa removed).
Each step was correct; the mistake was putting an unearned file in the repo, forcing
a choice between committing a partial and deleting a tracked file. Never recreate it.

3.1 CREATE ONLY THE MEDIA DIRECTORY

  * {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/, ONLY if this run will download
    (on-disk media keeps its directory).
  * NOT {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/ (only Stage 7.1, on success).
  * The name IS the CSV video_key byte for byte (the product-wide join key), never a
    title, slug, or guest name.

3.2 SNAPSHOT THE DEMAND ROW BESIDE THE MEDIA

        python3 {SIDECAR_TOOL} seed {roster_key}/{video_key}

For a {QUEUE_SUPPLEMENT_CSV} row, point at its file (else "no row"):

        python3 {SIDECAR_TOOL} seed {roster_key}/{video_key} \
                --demand-csv {QUEUE_SUPPLEMENT_CSV}

Writes {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/{video_key}.demand.yaml outside
every repo. Not a placeholder: {VIDEO_DEMAND_CSV} IS REGENERATED EVERY ENGINE RUN, so
by Stage 7 the row may differ or be gone; the seed is what it said when work started,
and Stage 7.1 falls back to it.

  * Seed cannot be written: LOG AND CARRY ON (a debugging aid and fallback, not a gate).
  * "No row" for a Stage 2 ladder pick = a SELECTION bug: drop, log, report in Stage 10.
  * "No row" for a STAGE 1D adoption is EXPECTED (rows leave the CSV): keep the
    existing seed from the original download, note "no live demand row — adopted from
    the ledger", let 7.1 fall back. Dropping these would make 1D useless on the
    oldest backlog.


====================================================================
STAGE 4 — GET THE MEDIA AND ITS FACTS
====================================================================

Every selected video ends with an existing MEDIA_FILE and measured facts. Carried-in
videos SKIP 4.2-4.4 but still run 4.5 and 4.6 (Stage 7 needs the SHA-256 and only 4.5
computes it).

4.1 CHECK THE TOOLS FIRST — ONCE PER RUN

`which yt-dlp`, `which ffmpeg`, `which ffprobe`.
  * No yt-dlp: print Z4, ask to install; install only with explicit permission; never
    substitute a downloader.
  * No ffprobe: print Z5 (4.5 needs it).
  * No ffmpeg: Z5 only if 4.4 will actually run (rare).
  * Every video already has MEDIA_FILE: yt-dlp not needed; say so instead of blocking.

4.2 RUN THE DOWNLOAD

  * YouTube URL: https://www.youtube.com/watch?v={youtube_id}
  * cd into {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/ and download there.
  * URL IN DOUBLE QUOTES, always (unquoted, the shell eats the query string).
  * WRITE THE INFO JSON: only source of Title, Description, upload date, channel,
    duration (Stage 7 forbids inferring recorded date from decode date).
  * NAME OUTPUT BY VIDEO KEY (no rename, no title-derived filename).
  * AUDIO ONLY: rung 3 `aligned_local` in pm/transcription.mdx is "yt-dlp bestaudio ->
    ffmpeg -> Silero VAD -> whisper.cpp -> sherpa diarize -> merge", and "the video
    stream is never downloaded; we want the words, not the pixels". (Six full-video
    clips = 1.1 GB of discarded pixels; bestaudio is ~1 MB per audio-minute.)

        cd "{VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}"
        yt-dlp -f "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio" \
               --write-info-json --no-progress --no-playlist \
               --retries 10 --fragment-retries 10 --concurrent-fragments 4 \
               -o "{video_key}.%(ext)s" \
               "https://www.youtube.com/watch?v={youtube_id}"

  * NO --extract-audio (re-encodes a lossy source; .m4a and .webm/opus are accepted
    as-is). Keeping video for another purpose is a different job; say so.
  * ONE DOWNLOAD AT A TIME (parallel fetches get the IP throttled for the day).
  * yt-dlp output to {RUN_LOG}. Its container choice (.m4a or .webm) is the answer.
  * Older full-video dirs may hold .mkv/.mp4 plus .f136.mp4/.f251.webm parts; they
    transcribe fine. Only the merged file is MEDIA_FILE, never a .fNNN part.
  * Failed download: log, mark [FAIL ], next video. NOTHING TO DELETE (Stage 3 wrote
    nothing to {ROOT_DIR}). About to remove a path under {TRANSCRIPTIONS_ROOT} here?
    STOP: this run did not make it; 7.4's guard applies.

4.3 SET MEDIA_FILE — NO RENAME, NO RE-ENCODE

MEDIA_FILE is {video_key}.{ext} as yt-dlp wrote it. Never rename to a title or mint a
key from a filename. Sidecars (.info.json, .description, thumbnails) share the stem,
stay here, never enter the repo.

4.4 CONVERT ONLY WHEN THE CONTAINER IS NOT ACCEPTED — WHICH IS ALMOST NEVER

Never re-encode video (the transcriber reads only the audio; transcoding costs more
CPU than transcription). Allowlist from
{WTC_REPO}/code/packages/backend/src/modules/machine/machine-transcription.controller.ts
ALLOWED_EXTENSIONS (anything else gets 415):

        .mp4  .m4a  .mov  .mkv  .webm  .avi  .mp3  .wav  .flac  .ogg  .opus

  * On the list: do nothing (normal).
  * Not on it: extract AUDIO ONLY to .m4a, keep BOTH (original = evidence), set
    MEDIA_FILE to the file handed to the CLI.

        ffmpeg -nostdin -loglevel error -i "{video_key}.{ext}" \
               -vn -c:a aac -b:a 128k "{video_key}.m4a"

4.5 MEASURE THE MEDIA — RUNS FOR EVERY VIDEO, DOWNLOADED OR FOUND

Against MEDIA_FILE, held for Stage 7:
  * SHA-256:          shasum -a 256 "{MEDIA_FILE}"
  * Bytes:            the file size
  * Duration seconds: ffprobe -v error -show_entries format=duration \
                              -of default=nw=1:nk=1 "{MEDIA_FILE}"
  * Container and codecs, from the same ffprobe.
  * The ABSOLUTE path, and which root it came from.

4.5a DROP ANYTHING OVER {MAX_VIDEO_SECONDS} — WHERE THE CAP ACTUALLY BITES

For most videos this is the first known length. Measured Duration_Seconds over the cap
(not lifted):
  * Drop from the batch: never reaches Stage 6, never claimed, `tries` untouched.
  * LEAVE THE MEDIA (next cap-lifting run finds it "already on disk").
  * Leave the ledger row alone, or write `status: pending` if none (media on disk,
    never attempted).
  * Do NOT backfill: 20 selected, 3 dropped = 17 done, stated (refilling turns a cap
    into an unbounded search).
  * Count, print Z53 once at stage end, name each with its length in Stage 10.
Such a video will be re-selected each default run; cost is one ffprobe since the media
stays. Never "fix" by marking it satisfied in {VIDEO_DEMAND_CSV} (read-only; deferred,
not satisfied).

4.5b NOTE ANY SUPERSEDED FULL-VIDEO FILES

Audio and full-video for the same key: the video file is dead weight. Total bytes,
print Z18 ONCE at stage end. Delete nothing (outside repos, citizen's files).

4.6 READ WHATEVER METADATA IS ALREADY BESIDE THE MEDIA

First value found per field, in this order; absent stays absent, never cross-filled:
  * {video_key}.info.json (yt-dlp): title, description, upload_date, duration,
    uploader / channel, webpage_url. upload_date is the RECORDED date, the only
    trustworthy source for Video.Recorded.
  * {video_key}.video.yaml (legacy downloader): title, published_at,
    duration_seconds, bytes, downloaded_at, yt_dlp_version, media_url.
  * The CSV row: duration_seconds, when the above gave none.
Log each fact's source. Mark the row [ DL  ].


====================================================================
STAGE 5 — MAKE THE LOCAL WEB APP READY
====================================================================

The local We The Citizens app transcribes; the CLI is a thin HTTP client. The app must
be up, and LOCAL, before Stage 6. HARD RULE: production never transcribes; the CLI
defaults to production; every Stage 6 call carries --local.

5.1 IS THE PRODUCT REPO INSTALLED?

Stage 1 confirmed {WTC_REPO}: go to 5.2. Otherwise print Z6 and STOP after reporting
what was downloaded (media stays; a later run picks it up at 2.3). Never clone it.

5.2 IS IT UP TO DATE?

`git -C {WTC_REPO} fetch`, compare HEAD to the tracking branch. Behind: print Z7, do not
pull (old installs still transcribe), continue.

5.3 IS THE CLI BUILT?

{CITIZENS_CLI} execs {WTC_REPO}/code/packages/citizens/dist/main.js (absent: exit 69).
Build it if absent (a build, allowed):

        cd {WTC_REPO} && pnpm --filter @wethecitizens/citizens build

5.4 IS THE APP RUNNING?

  * Test the API; any HTTP answer, even 404, means up:

        curl -s -o /dev/null -w "%{http_code}" --max-time 3 {LOCALHOST_API}/

  * No answer: start it (cd into the repo; `just` resolves its justfile from cwd):

        cd {WTC_REPO} && just build
        cd {WTC_REPO} && just run

  * `just run` prints URLs and brings up {LOCALHOST_WEB} with the API on :9333. Poll
    until it answers; ~90 seconds without: print Z8, stop.

  * ⚠️ THE APP MUST OUTLIVE WHAT STARTED IT. `just run`'s processes belong to the
    starting shell's process group; under an agent or script that group is torn down
    after the step and services get SIGTERM minutes later, silently (log shows a boot
    and then nothing). Measured 2026-09-10: fifteen short videos finished, then the
    five LONGEST all failed with identical `ECONNREFUSED 127.0.0.1:9333`; two in-run
    restarts died the same way. THE TELL: failures sorted by duration, one identical
    connection error, no other CLI stderr. FIX: start it somewhere persistent (the
    citizen's terminal, or a background facility that truly survives steps). In
    Claude Code the citizen types

        ! cd {WTC_REPO} && just run

    Confirm :9333 answers IMMEDIATELY BEFORE Stage 6 and on any ECONNREFUSED; if gone,
    say so and stop (retries against a dead app waste the batch).

5.5 CONFIRM THE MACHINE CAN ACTUALLY TRANSCRIBE

        {CITIZENS_CLI} capability --local

  * Prints a table and a JSON object on the last line: `asr` (engine),
    `models_missing`, `cause`.
  * asr == "none" (or exit 1): no speech engine. Print Z12, run
    `{CITIZENS_CLI} install --local` if the citizen agrees, re-check.
  * cause == "asr_disabled_on_host": a HOSTED install. Print Z13, STOP (the forbidden
    production call).

5.6 CLEAR ANY OPEN CIRCUIT BREAKERS

        {CITIZENS_CLI} circuit --local

  * Ten consecutive failures open a tier's breaker for an hour. If open from an earlier,
    since-fixed cause, close it (a real fault re-opens it):

        {CITIZENS_CLI} circuit reset --local

  * Mention only if one was open (Z14).


====================================================================
STAGE 6 — TRANSCRIBE
====================================================================

6.1 TELL THE CITIZEN HOW LONG THIS WILL TAKE, BEFORE STARTING

Sum Stage 4.5 Duration_Seconds over the batch:

        estimated_wall_clock_seconds = total_audio_seconds * 0.19

DO NOT DIVIDE BY P. 0.19 is the AGGREGATE at the default P=4 (concurrent streams compete
for the same cores, cancelling the gain). Measured 24-core Apple Silicon, 2026-09-05,
P=4: 5804 s audio (1.61 h) -> ~1080 s wall = 0.186; per stream 0.21x-0.56x. (An old
"* 0.25 / min(P,4)" underestimated by 3x.)

State a RANGE (estimate to 2x), rounded to the quarter hour, with total audio hours
(per-stream speed varies 2.7x). SLOWNESS IS TURN COUNT, NOT LENGTH: diarization clusters
speaker turns (two ~1800 s videos took 374 s and 722 s); crosstalk is costly, monologue
cheap. On an unfamiliar machine, time the shortest video first.

Only asr reports progress (a chunk percentage, not job progress). diarize reports once,
on completion ("this stage typically runs minutes, not seconds"), and can take as long
as ASR; a job silent on "diarize clustering 1748 s of audio" is working: never kill or
re-queue it.

Print Z20 with the estimate BEFORE queueing (say hours when it is hours). Over 3 hours:
print Z21 and ask whether to continue, reduce VIDEO_COUNT, or stop.

6.1b CLAIM THE VIDEO IN THE LEDGER — BEFORE THE WORK, NOT AFTER

        THE LEDGER IS WRITTEN AND FLUSHED TO DISK BEFORE THE TRANSCRIBER IS
        CALLED. NOT AFTER, NOT ALONGSIDE, NOT AT THE END OF THE BATCH.

A hung, cancelled, or crashed transcription runs nothing afterwards; a post-hoc ledger
records only successes. Written first, a crash leaves a timestamped `started` row that
1C.3 turns back into work.

Per video, immediately before its transcriber call:
  * Take {IN_PROGRESS_LOCK}; RE-READ the ledger.
  * Row now `started` within {STALE_CLAIM_HOURS} and not this run's claim: ANOTHER RUN
    GOT THERE FIRST. Release, log, drop from the batch, next video (the race the lock
    cannot prevent and the re-read can).
  * Otherwise claim in one write:
        status                    started
        tries                     tries + 1
        earliest_attempt_at       UNCHANGED if already set, else now
        last_tried_at             the PREVIOUS value of started_at (may be empty)
        started_at                now
        finished_at               emptied — this attempt has not finished
        host                      {hostname}:{pid}
        run_id                    {THE_DATE_TIME_STRING}
        media_file                the resolved absolute MEDIA_FILE
        note                      emptied, or the previous failure kept as history
  * Write atomically, release, THEN call the transcriber.

`tries` increments HERE, not on failure (a hang never reaches a failure handler;
counting starts is the only count that cannot be lost; a kill before decode burns a
try, hence a cap of 3). started_at = this attempt, last_tried_at = the one before,
earliest_attempt_at never moves: three questions ("tried once long ago" vs "three
times just now").

6.2 THE COMMAND — --out IS A STAGING DIRECTORY, NOT THE REPO

One call per video, ABSOLUTE paths (`just citizens` changes directory). Input is
MEDIA_FILE from 2.3 or 4 (either media root). `mkdir -p` STAGE_DIR
({VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/out/) first.

        {CITIZENS_CLI} transcribe "{MEDIA_FILE}" \
          --create \
          --local \
          --out "{STAGE_DIR}" \
          --name "{video_key}" \
          --also rttm,ctm \
          --media-url "https://www.youtube.com/watch?v={youtube_id}"

NEVER --out {TRANSCRIPTIONS_ROOT}: for minutes-to-hours a half-written dir (nine files
appearing one by one) sits where the auto-committer reaches it. Staging costs one
same-volume `mv` in 7.1 and guarantees repo dirs always hold finished transcripts.

Add --title "<title>" and --recorded <ISO date> when 4.6 resolved them; omit otherwise
(absent is the correct record).

Flags, since omitting one silently changes the result:
  * --create      default is LOCATE; without it nothing is transcribed.
  * --local       THE HARD RULE; without it, a production call.
  * --out         writes the COMPLETE FILE SET into STAGE_DIR from this run's sidecar
                  (no re-decode); 7.1 moves it in; failures stay here for debugging.
  * --name        base name; else the media stem, WRONG for legacy media whose stem
                  differs. Always pass the frozen key.
  * --also rttm,ctm   evaluation formats (outsiders compute DER and WER).
  * --media-url   index data only; NEVER fetched.

Nine files land in STAGE_DIR:

        {video_key}.transcription     the words — the authority, byte-identical forever
        {video_key}.segments.json     the sidecar: timings, speakers, provenance
        {video_key}.segments.jsonl    the committed line-oriented form
        {video_key}.srt               SubRip
        {video_key}.vtt               WebVTT
        {video_key}.script.txt        as-broadcast script
        {video_key}.fountain          screenplay, fountain.io
        {video_key}.ctm               word timings  (from --also)
        {video_key}.rttm              diarization   (from --also)

NEVER pass --person / --video unless the citizen explicitly asks: they MIRROR INTO THE
SHARED DATA REPO (forbidden). Without them: a hash-keyed adhoc transcript in the app's
state root plus the file set in STAGE_DIR. The 7.1 copy is the deliverable; Stage 8's
manifest makes it visible.

6.3 PARALLELISM — IT IS REQUEST CONCURRENCY, NOT LOCAL CPU

Every call is an HTTP request to the ONE app on :9333, which does all CPU work.
  * The app QUEUES beyond capacity ("queued…"); more concurrency just moves the wait.
    A long diarization sharply narrows side-by-side decoding.
  * SORT SHORTEST-FIRST by Duration_Seconds (long first blocks the slot; short first
    gets most of the batch committable early, and an interrupted run leaves more done).
  * Start at {DEFAULT_PARALLEL_TRANSCRIBE}; never exceed {MAX_PARALLEL_TRANSCRIBE}. The
    server decodes 4 ASR chunks per job, so 4 jobs = 16 threads already; more
    oversubscribes and slows the batch. Go higher only if the citizen asked for speed
    AND cores are idle.
  * 3 or fewer videos: sequential.
  * NO subagent per video: `xargs -P {DEFAULT_PARALLEL_TRANSCRIBE} -L 1` over
    "{roster_key} {video_key} {youtube_id}" lines does it.
  * Each unit owns one video end to end (resolve, transcribe, verify, verdict); never a
    shared directory. One failure never stops others. No per-video printing beyond the
    one [ DONE] line.

6.4 VERIFY EACH RESULT

PASSED only if, in STAGE_DIR (before anything moves, so a failure never needs undoing
in the repo): {video_key}.transcription exists and is non-empty;
{video_key}.segments.json exists and parses; the CLI exited 0. Anything else FAILS,
including words with no sidecar (the CLI names absent derivations; untimed words
cannot be cited).

6.5 RELEASE THE CLAIM — EVERY PATH OUT OF 6.4 WRITES THE LEDGER

Under {IN_PROGRESS_LOCK}: re-read, update this row only, write atomically, release.

  PASSED   status `finished`, `finished_at` now, `words` the word count, `note`
           emptied. Written AFTER Stage 7.1 moved the files (`finished` means "the
           words are in the repo").
  FAILED   status `failed`, `finished_at` now, `note` the reason (failed check, CLI
           exit code, head of stderr). `tries` NOT touched (6.1b counted it).

A cancelled run runs neither branch: the row stays `started`, is treated as live for
{STALE_CLAIM_HOURS}, then 1C.3 makes it `failed` / `claim expired`, adoptable. By
design: a killed prompt runs no cleanup, so recovery lives in the NEXT run.

Row reached {MAX_TRANSCRIBE_TRIES} on this failure: note `reached the try cap`, name it
in Stage 10 with Z51. A later run may fix the cause or lift the cap on its own once it
can name the cause in the note; the cap stops runaway retries, it does not park work
for a human.


====================================================================
STAGE 7 — PUT THE RESULT IN THE REPO, OR LEAVE IT OUTSIDE
====================================================================

7.1 ON SUCCESS — CREATE THE DIRECTORY AND WRITE transcription.yaml

THE FIRST AND ONLY MOMENT ANYTHING ENTERS {TRANSCRIPTIONS_ROOT}. Only after 6.4 passed,
in one go: create {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/, MOVE (same-volume
rename, not copy) all nine files from STAGE_DIR into it, write the sidecar. A repo
directory always holds a real transcript; the auto-committer never sees a partial.

RUN THE TOOL; never hand-roll or improvise a writer:

        python3 {SIDECAR_TOOL} write {roster_key}/{video_key} [...]

Supplement rows also need --demand-csv {QUEUE_SUPPLEMENT_CSV}; the Demand block then
carries run_id "{THE_DATE_TIME_STRING}local_supplement" and the notes cell, marking it
provisional.

The tool creates the dir, reads the demand row by video_uid (falling back to the 3.2
seed), gathers every mechanical field (SHA-256, bytes, duration, codecs, word count,
.rttm speaker shares, Capture block, demand row), MERGES (existing Description, Topics,
named speakers carried forward and asserted), and writes atomically.

YOUR JOB, which the tool cannot do: read each transcript and write Description and
Topics.

Full schema in APPENDIX D. The blocks and who fills them:

  * Video      — Title, Description, URL, Video_ID, Show, Runtime, Language. Title,
                 Show, Runtime and recorded date come from 4.6. DESCRIPTION AND TOPICS
                 require READING each transcript (20 reads on a 20-video run; the step
                 most likely skipped under pressure; a real SHA-256 with an empty
                 Description is a half-finished record). Several sentences on what the
                 video is and discusses, FROM THE TRANSCRIPT, not a restated title.
                 ATTRIBUTE CONTESTED CLAIMS: this is political speech read as a neutral
                 record. Say WHO asserts figures, motives or wrongdoing ("she argues",
                 "he puts the figure at", "the characterisation is his own and is
                 contested"); never restate an advocate's claim in the product's voice.
                 Note when the person named in a claim is absent and cannot answer.
  * Media      — THE SHA-256 OF THE FILE TRANSCRIBED (required: proves the words came
                 from that exact file). Also Bytes, Duration_Seconds, Container,
                 Source_URL, Downloaded_At, Downloader, Stored_At (absolute dir; legacy
                 media is under {VIDEO_DOWNLOAD_ROOT_LEGACY} and must say so).
  * People_in_Video — one entry per diarized speaker: Speaker_Label, Share_Of_Speech,
                 Turns from the .rttm. Name a person only when the transcript
                 identifies them; else "Unidentified" with its label, never guessed.
                 SUBJECT IS NOT A DEFAULT: Subject: true only on the cluster the
                 transcript identifies as the assessed speaker; otherwise OMIT Subject
                 everywhere and say why in a comment (first-sorted label = fabricated
                 attribution, and scorers trust this field). Montages/ads often yield
                 7+ clusters; report the count, never merge clusters.
  * Topics     — what the video is actually about, FROM THE TRANSCRIPT, not the
                 person's roster role. Channels include car reviews, cooking, adverts,
                 sponsor reads. Never stretch toward politics to justify priority: an
                 honest "car culture" is useful; a false "policy discussion" poisons
                 every later search.
  * Source     — Canonical_ID, Transcribed (ISO 8601 with timezone), ASR model,
                 Diarization model, Evidence_Grade, Word_Count.
  * Timestamps — Downloaded_At, Transcription_Started, Transcription_Finished,
                 Duration_Seconds of the transcription, all ISO 8601 with explicit
                 offset (without them a run cannot be reconstructed). Recorded ONLY
                 from 4.6's upload_date / published_at; else omit; never today.
  * Files      — every file actually written, by real name (never assume APPENDIX D's
                 set landed). A MAPPING (Plain_Text:, Fountain:, ...) holding
                 Transcript_SHA256 beside filenames; mixing "- file.srt" items with a
                 key will not parse. Parse every sidecar back before committing.
  * Demand     — the source row: roster_key, video_uid, video_key, priority, run_id,
                 the snapshot's generated_at. THE JOIN BACK TO THE SERVER.

Absent is absent at every field. A fact with no field: ADD the field.

7.1a SWEEP FOR THE PART A MACHINE COULD NOT HAVE WRITTEN

MECHANICAL fields (SHA256, Bytes, Duration, Word_Count, Files, Demand, Title, Show,
Recorded) are scripted and reproducible. HAND-WRITTEN fields (Description, Topics)
need a reading and no mechanical check looks for them, so a sidecar missing them still
parses, hashes, joins, and gets committed and trusted. Before Stage 8, for EVERY
selected video assert: the nine files exist and are non-empty; transcription.yaml
parses; Video.Description and Topics present and NON-EMPTY; Media.SHA256 and Demand
present. The committed command:

        python3 {SIDECAR_TOOL} verify --all

(non-zero while anything is missing; also checks fields the product reads and
re-verifies each transcript's SHA-256 against disk.) RE-RUN UNTIL CLEAN: fixing one
miss often reveals another (one run went 19/20, 19/20 for a different video, 20/20).
Typical misses are OMISSIONS: a sidecar never generated, or an early out-of-band video
never described because it was "done". Also: a from-scratch generator destroys
Description and Topics on any re-run while the file still parses; regenerate
mechanical fields only, or re-apply the written ones.

7.1b PARSE WHAT YOU WROTE

Read transcription.yaml back with a real YAML parser before DONE; unparseable = failed
for 6.4 purposes (the SHA-256 proves nothing). Two common breaks:
  * A block half sequence, half mapping (see Files).
  * A QUOTE INSIDE A QUOTED SCALAR: "The "border czar" designation" is a parse error.
    Single-quote values containing double quotes, or drop the inner quotes; same for
    apostrophes inside single-quoted scalars.

7.2 HASH THE TRANSCRIPT TOO

        shasum -a 256 {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/{video_key}.transcription

Hold for Stage 8 (a manifest mismatch is a REFUSAL, not a warning).

7.3 MARK IT [ DONE]

Under ~30 words per audio-minute: note with Z19 in the Stage 10 tail. Not a failure or
retry (adverts, montages, music beds give short transcripts and spurious clusters).

7.4 ON FAILURE — THE REPO WAS NEVER TOUCHED, SO LEAVE IT THAT WAY

Nothing is left in {ROOT_DIR} because nothing was written there (not by deleting).
  * LEAVE STAGE_DIR where it is, beside the 3.2 seed and media; nothing to move or
    remove. For legacy-root media, STAGE_DIR is still under
    {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/; state where the media is in the
    FAILED file.
  * Write {video_key}.FAILED.txt beside it: the exact command, CLI exit code, stderr,
    which 6.4 check failed, timestamp.
  * Mark [FAIL ], append the reason to {RUN_LOG}.
  * NO automatic retry (burns an hour against an unchanged cause).

7.4a THE DELETION GUARD — READ THIS BEFORE REMOVING ANY PATH UNDER {ROOT_DIR}

The only legitimate removal under {TRANSCRIPTIONS_ROOT} is 7.4b; anywhere else it is a
bug (it cost fifteen committed sidecars once; Stage 3). Before removing anything under
{ROOT_DIR}, pass BOTH:

  1. GIT DOES NOT KNOW ABOUT IT.

        git -C {ROOT_DIR} ls-files --error-unmatch -- "<path>"

     Exit 0 = TRACKED = committed work. STOP: no remove, no `git rm`, no tidy. Print
     Z22, leave it, report in Stage 10. (Removal adds a deletion on top of the commit,
     as on 2026-09-07.)

  2. THERE ARE NO WORDS IN IT.

        find "<path>" -name "*.transcription"

     Any hit: words are never collateral. STOP, print Z22.

7.4b THE ONE PERMITTED CLEANUP — A STRANDED SEED-ONLY DIRECTORY

Pre-fix runs could leave {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/ holding only a
stub transcription.yaml (invisible to 2.3's test, so re-stranded every run). Clear it
ONLY when ALL hold:
  * no {video_key}.transcription or other output file; only transcription.yaml
  * that file has no Media.SHA256 and no Source block (a seed, not a record)
  * `git ls-files` shows it UNTRACKED
Tracked = committed history: leave it, name it in Stage 10, citizen decides.

7.5 THE GATE — NOTHING REACHES STAGE 8 UNTIL THIS IS GREEN

        python3 {SIDECAR_TOOL} verify --all

  * Exit 0: proceed.
  * Non-zero: fix what it names, run AGAIN. Never index, commit or push past red (an
    incomplete sidecar in the manifest looks complete to every downstream check).
  * LEGACY lines do not fail the gate and must NOT be "fixed": pre-schema sidecars
    whose media is gone, so Media.SHA256 cannot be recomputed. Report, leave as written.


====================================================================
STAGE 8 — INDEX THE NEW TRANSCRIPTS IN {MANIFEST_FILE}
====================================================================

The scanner reads {MANIFEST_FILE} FIRST; a `transcriptions:` index there is
AUTHORITATIVE and the directory walk does not run. Unlisted = invisible ("not found" is
indistinguishable from "never spoke").

8.1 DECIDE WHETHER THIS REPO IS INDEXED

  * Has a `transcriptions:` block: APPEND every [ DONE] video (a HALF index is worse
    than none: listed entries suppress the walk).
  * None: the repo relies on the walk; do not create one unless the citizen asks, and
    then index EVERY transcript in the repo.
  * Either way, update `user_repo.updated_at`.

8.1b APPEND AS TEXT. NEVER ROUND-TRIP THE MANIFEST THROUGH A YAML DUMPER

Its comments are the spec citations (which §, which reader, why this person key, which
hash verified when). A dumper drops them all while the file still parses (once cost 68
comment lines, caught only in the diff).
  * Split TEXTUALLY at the final `updated_at:` line; append new entries as formatted
    text; rewrite `updated_at:`.
  * Parse the result, then `git diff`: the only removed line must be the old
    `updated_at`. Otherwise restore from git and redo.

8.2 THE ENTRY

For every [ DONE] video append to `user_repo.transcriptions:`:
  * video_key, title, source_url, recorded_language
  * roster_key — the CSV's first column, verbatim
  * person_key — ONLY when resolved per TWO KEY NAMESPACES; else omit, never derive
  * path       — repo-root-relative, forward slashes, no leading "./"
                 videos/transcriptions/{roster_key}/{video_key}/{video_key}.transcription
  * sidecar    — .../transcription.yaml
  * segments   — .../{video_key}.segments.json
  * text_sha256 — the 7.2 hash. A mismatch with the bytes is stored as gap_reason:
                 manifest_hash_mismatch and the source is NOT SCORED. Re-hash after edits.
  * transcribed_at, word_count
  * demand_run_id — the demand snapshot this entry answers
  * speakers   — label -> {person_key, role, display_name}; person_key only where
                 resolved, else role + display_name. Exactly one role: subject.
  * unread_sidecars — files the scanner's allow-list does not admit (.ctm, .rttm,
                 .fountain, .segments.jsonl, .script.txt, .srt, .vtt), so their absence
                 from the read is STATED.

8.3 THE TOP-LEVEL person_key IS A KNOWN CONFLICT — REPORT IT, DO NOT RESOLVE IT

One `user_repo.person_key` scopes the repo, but this prompt adds many people's videos.
NEVER change it (the citizen's claim; the app's registration wins). If this run adds
transcripts whose roster_key is not that person's, print Z15 once at the end with the
count (a product schema question).


====================================================================
STAGE 9 — COMMIT AND PUSH
====================================================================

Only [ DONE] videos are committed.

9.1 CHECK WHAT IS ABOUT TO BE COMMITTED

        git -C {ROOT_DIR} status --short

  * Every path under {ROOT_DIR}/videos/transcriptions/, or {MANIFEST_FILE}, or
    {ROOT_DIR}/.gitignore.
  * NO media staged (.mp4, .webm, .mkv, .m4a, .info.json, thumbnails). If any: print
    Z16, stop, commit nothing.
  * Empty-but-intended directories need a .gitkeep.

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

The repo owner's standing rule (GIT BRANCH RULES in {ROOT_DIR}'s charter) outranks
this prompt: no `git checkout -b`, `git switch -c`, `git branch`, `git checkout
<other>`, or `git push` unless the user explicitly asks. Running this prompt is not a
push request (pushing publishes transcripts publicly; the citizen's call each time).
  * DEFAULT: commit, STOP, print Z31 with the push command and commits waiting.
  * Only if the run text asked:

        git -C {ROOT_DIR} push

  * Current branch only. Rejected: `git pull --rebase`, retry ONCE; fails again: Z17,
    stop, never force.

9.4 THIS MACHINE HAS AN AUTOMATIC COMMITTER — EXPECT IT

An external auto-committer ("Bryan 26 Tower" commits) sweeps {ROOT_DIR} at any moment
and nothing here can stop it. The defence is that nothing partial ever exists for it
to find (Stage 3 writes nothing to the repo; 7.1 adds dir + sidecar together once words
exist), so a mid-run auto-commit captures only complete transcripts. Without that
defence: one run had 189 files committed at 09:04:44 mid-transcription (sidecars
unwritten); the next (901615a) committed fifteen stubs that 7.4 deleted. Moving the
seed back into {TRANSCRIPTIONS_ROOT} brings both back.
  * Re-read `git log` before 9.1; already-committed work is normal, not a stop.
  * Commit the REMAINDER; report that an auto-commit landed mid-run and what this
    commit closed.
  * Never `git reset` or amend its commits (may be pushed; not this prompt's).


====================================================================
STAGE 10 — REPORT
====================================================================

Print Z30 (counts, then failures by roster_key/video_key with reason), then Z31 unless
a requested push succeeded.

Then, in plain sentences, only where there is something to say:
  * {CONFIG_FILE} changed? .gitignore created?
  * THE BACKLOG, ALWAYS (even empty): downloaded-but-untranscribed held, adopted and
    finished, left (claimed by another run), capped at {MAX_TRANSCRIBE_TRIES} (Z51),
    new backlog from this run's failures. ("20 transcribed" with 40 untranscribed on
    disk is the least useful true statement.)
  * EVERY 1C LEDGER CORRECTION by video_uid and reason (a `finished` row with no
    transcript = an earlier false success).
  * EVERY LENGTH SKIP (Z53) by roster_key/video_key with measured duration, backlog or
    this run; media on disk, lifting the cap costs no re-download. Never report 17 of
    20 without saying where 3 went.
  * Media that would not open in ffprobe (1D.3), by path (probably truncated; the
    citizen decides on deletion).
  * Ledger rows this run could not parse and left alone.
  * STAGE 1B: people examined, rows added for, unsourced, listed empty, patch CSV path,
    with the queue's as-of date and run_id.
  * Transcripts from SUPPLEMENT rows, by roster_key/video_key (nobody asked yet).
  * Z42 if the data repo was behind.
  * Whether {WTC_REPO} is behind and needs a pull.
  * ANY REFUSED DELETION (Z22) by path and reason; never silent.
  * Stranded seed-only dirs from 2.3, by roster_key/video_key, tracked or not; which
    7.4b cleared and which were left as committed.
  * Any transcription.yaml FIELD added beyond APPENDIX D.
  * Entries without a resolvable person_key; Z15 if it applies.
  * Z18 for superseded video files on disk; Z19 for any low-word video.
  * Measured throughput (total audio seconds, wall clock, ratio) to calibrate the next
    6.1 estimate to THIS machine.
  * Anything left needing a human.

None apply: nothing beyond Z30. Append everything to {RUN_LOG}.


====================================================================
APPENDIX A — {CONFIG_FILE} SCHEMA
====================================================================

Machine-local at ~/.config/we_citizens/config.yaml, OUTSIDE every repo, never checked in
or synced; each computer has its own.

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
  * Keys may be ABSENT ("not found on this machine, go look"; better than wrong).
  * Present keys may be STALE; verify with `git remote -v` plus a content marker (1.2).
  * RETIRED SHAPE on older machines (bare top-level key): read, carry the value,
    rewrite into the shape above:

        user_repo_path: /Users/bryan/BGit/Bryan_git/we_bryan


====================================================================
APPENDIX B — {VIDEO_DEMAND_CSV} COLUMNS
====================================================================

Engine-generated (never hand-edit; next run overwrites), sorted highest priority first.
COLUMNS ARE APPEND-ONLY, LOOKED UP BY HEADER NAME, NEVER POSITION (a newer engine may
add a 26th; 1B copies the live header for this reason).

    person_key                MISLABELLED. For a roster human it is the ROSTER key —
                              office-scoped, e.g. kari_lake_us_pres. For a
                              people_only human it is the PERSON key. Either way it
                              is the directory segment under {TRANSCRIPTIONS_ROOT}
                              and every media root. See TWO KEY NAMESPACES.
    video_uid                 "{column-1 key}::{video_key}" — THE KEY, unique across
                              the corpus; the only join key. NEVER join on bare
                              video_key: unique within ONE PERSON only (two videos are
                              both v0001 on disk today), so it silently matches across
                              people and publishes one person's words under another's.
    video_key                 THE FROZEN PRIMARY KEY of this video for this person.
                              Directory name. [A-Za-z0-9_-], 1..64. Never invented.
                              On a YouTube row it IS the 11-char YouTube id.
    youtube_id                the 11-char YouTube id. URL is
                              https://www.youtube.com/watch?v={youtube_id}
    duration_seconds          BLANK MEANS UNKNOWN, never 0
    priority                  computed demand score, integer 0..1000, higher = wanted
                              more. APPENDIX F is the arithmetic.
    ceiling                   the maximum this row's priority could reach
    raw                       the pre-clamp score. MAY BE NEGATIVE.
    bound_by                  ceiling | raw — which of the two produced priority
    transcripts_held          copies of THIS VIDEO's transcript the movement holds
    trusted_transcripts_held  of those, how many came from a trusted supplier
    person_transcripts_held   transcripts for THIS PERSON across every video — the
                              damper's input, a different fact from the above
    seat_rank                 office_importance_rank for the seat held or sought.
                              BLANK IS AN ABSENCE, NOT A ZERO.
    challenger                true | false | blank. BLANK = no sealed contenders
                              edition to ask. Blank is not false.
    round                     breadth-first round that admitted this row. Round 1 for
                              everybody comes before round 2 for anybody.
    status                    open | partial | satisfied | unobtainable | withdrawn
                              — only open/partial are worked
    closed_reason             why it is closed, when it is
    notes                     free text, human
    computed_at               ISO 8601
    run_id                    the engine run that produced this row. CARRY IT INTO
                              transcription.yaml — it is the join back.
    source_type               where the video lives — youtube, rumble, ipfs, x,
                              bluesky, nostr, mastodon, peertube, web and others.
                              BLANK = no address at all; `web` = readable address we
                              cannot place.
    source_url                an address a reader can open. NEVER an IPFS gateway —
                              ipfs://<cid> is the address and a gateway is one
                              mirror's opinion of where to find it.
    ipfs_cid                  canonical CID, only for an IPFS address. Blank on almost
                              every row, by design.
    source_ref                platform-native unique id, normalized. On YouTube the
                              same string as video_key.
    subject_kind              WHICH STORE THIS HUMAN IS KNOWN FROM — new_politician |
                              legacy_politician | worrisome_challenger |
                              fix_bill_author | people_only. A fact about the
                              movement's FILING, never a judgement of the person or an
                              award input. Blank on rows before 2026-09-09 and for
                              unrecognised values. BLANK IS NEVER people_only.

{VIDEO_DEMAND_YAML} is the run record: schema_version, run_id, generated_at,
engine_version, universe counts, rows_open / rows_partial / rows_satisfied, a `gaps:`
list of what the engine could NOT determine, and csv_sha256. READ THE GAPS: the
sentence beginning "N person(s) entered the eligible universe from
data_we_citizens/people/" is exactly STAGE 1B's population (a SOURCING gap re-running
the engine cannot move).

{QUEUE_SUPPLEMENT_CSV} has THE SAME COLUMNS (STAGE 1B, provisional rows).


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

  * repo_url must be PUBLIC https (no ssh, git://, or token); the scan tests "can the
    WORLD read this?".
  * `path` is repo-root-relative; the scanner applies `subpath`.
  * Any `person_key` here is a CLAIM; the app registration wins.
  * LEGACY entries with pre-rule paths (e.g. videos/transcriptions/tucker/joe_kent/) are
    correct AS WRITTEN and never rewritten; only new entries follow this shape.

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

      Capture:                        # facts about the POSTING at fetch time.
        Channel_ID: "UCakn6ZCwlFA6Ct6XSU-HmtQ"   the DURABLE uploader identity.
                                        A handle can be renamed or reassigned to
                                        a different human; a UC id cannot.
        Uploader_ID: "@karilake"
        View_Count: 1790                reach AT CAPTURE TIME. Changes hourly and
        Like_Count: 276                 is never recoverable for a past date.
        Comment_Count: 45
        Availability: "public"          public / unlisted / members-only, then
        Published_At: "2024-10-14T20:08:25+00:00"
        Captured_At: "2026-09-05T08:39:08-07:00"

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

      Demand:                       # THE WHOLE CSV ROW. See below.
        roster_key: "tucker_carlson_us_pres"        # the CSV's person_key column
        video_uid: "tucker_carlson_us_pres::1cbw1utqzHg"
        video_key: "1cbw1utqzHg"
        youtube_id: "1cbw1utqzHg"
        duration_seconds: 7538
        priority: 850
        ceiling: 1000
        raw_score: 850             # the CSV's `raw` column, renamed: `raw` alone
                                   # reads as a YAML scalar style, not a score
        bound_by: "raw"
        transcripts_held: 0
        trusted_transcripts_held: 0
        person_transcripts_held: 3
        seat_rank: 300
        challenger: true
        round: 1
        status: "open"
        closed_reason: omitted unless the CSV carries one
        notes: omitted unless the CSV carries one
        demand_generated_at: "2026-09-04T12:39:10.038Z"   # the CSV's computed_at
        demand_run_id: "job_1788525549225_32"             # the CSV's run_id
        source_type: "youtube"
        source_url: "https://www.youtube.com/watch?v=1cbw1utqzHg"
        ipfs_cid: omitted unless the CSV carries one
        source_ref: "1cbw1utqzHg"


CARRY THE WHOLE DEMAND ROW, NOT A SELECTION. Every APPENDIX B column gets a home here.
{VIDEO_DEMAND_CSV} is REGENERATED every engine run, so the values true WHEN THIS
TRANSCRIPT WAS MADE exist nowhere else; a dropped column is a fact destroyed.

ABSENT IS ABSENT APPLIES HARDEST HERE: blank cells are OMITTED. seat_rank bites: a 0
reads to every later reader as "the least important seat there is".

A COLUMN THE ENGINE ADDS LATER is carried through under its own name ({SIDECAR_TOOL}
does this automatically; the block is not a fixed list).

THE JOIN KEY IS video_uid, NEVER video_key. The engine issues placeholder keys (v0001,
v0002) per person, so `v0001` appears against dozens of roster_keys with DIFFERENT
youtube_ids; a bare-key match attaches another person's URL to this transcript's
Video.URL (one of the four fields the product reads). Everything reading this CSV joins
on video_uid (also stated in {DATA_REPO}/prompts/p_transcriptions_speakers_to_people.md).


====================================================================
APPENDIX E — THE citizens CLI, ONLY WHAT THIS PROMPT USES
====================================================================

Run as {WTC_REPO}/cli/citizens, `just citizens <verb>` from {WTC_REPO}, or
`node {WTC_REPO}/code/packages/citizens/dist/main.js` (same binary and arguments).

  * A THIN HTTP CLIENT; the app must be running.
  * NEVER FETCHES MEDIA: a URL to `transcribe` is refused with MediaNotLocalError
    (hence Stage 4's yt-dlp). `capability` reporting yt_dlp: false is expected.
  * DEFAULT TARGET IS PRODUCTION: --local on every call. `videos`, `install`, `circuit`
    and `capability` REFUSE a non-local target.
  * LOCATE IS THE DEFAULT: without --create, `transcribe` only prints where the
    transcript would be (exit 3 if none).

Verbs used here:

    citizens capability --local          capability table + a JSON line; asr == "none" is the fault
    citizens install --local             install the speech engine
    citizens circuit --local             which tiers are carrying failures
    citizens circuit reset --local       close them after fixing the cause
    citizens videos --local              what media is on disk, per person
    citizens transcribe <abs-file> --create --local --out <abs-dir> --name <video_key> --also rttm,ctm

Exit codes: 2 usage, 3 not found, 4 verify failed, 69 CLI not built.

Not used here:
    citizens batch      walks a MEDIA ROOT this prompt does not own and defaults --out
                        into the shared data repo; this prompt drives one video at a
                        time into the citizen's own repo.
    --person / --video  MIRRORS THE RESULT INTO THE SHARED DATA REPO; forbidden unless
                        the citizen asks.


====================================================================
APPENDIX F — THE DEMAND ARITHMETIC, FOR STAGE 1B ONLY
====================================================================

A transcription, not a second opinion, of we_citizens/pm/calc_engine_video_demand.mdx
§3 (code/packages/shared/src/video_demand.ts: videoDemandTerms() / computeVideoDemand()).
On disagreement THE SPEC WINS; re-read it when {WTC_REPO} is on the machine. All terms
are INTEGERS (nothing to round).

THE CEILING — per VIDEO

    steps   = transcripts_held + trusted_transcripts_held
    ceiling = max(0, 1000 - 200 * steps)

(1000 for an unheard video; inert on a new person's rows.)

THE RAW SUM — before the ceiling

    base                                          +200   every eligible video
    seat rank        office_importance_rank * 3          president +300 ... state assembly +90
    live challenger                               +150   from the sealed slate only
    no transcripts for this PERSON at all         +200   the breadth-first push
    long-form (duration_seconds > 2400)           +100   STRUCTURALLY DEAD — see below
    person corpus damper   -min(150, 10 * person_transcripts_held)
    no candidacy on file                          -300   subject_kind == people_only, and nothing else

THE PUBLISHED NUMBER

    priority = max(0, min(ceiling, raw))
    bound_by = priority == ceiling && ceiling < raw ? "ceiling" : "raw"

The floor is not a third binder; raw prints the true (possibly negative) sum so a
hand-check stays legible.

FOUR RULES THAT ARE EASIER TO GET WRONG THAN THE SUM ITSELF

  * THE -300 KEYS ON subject_kind, NEVER ON AN UNRESOLVED SEAT. An unpriceable roster
    office gets "seat rank / points 0 / cause seat unknown" and NO PENALTY (~9,000 live
    rows have blank seat_rank from OUR failure to resolve their office; penalising it
    would silently demote thousands of named living people).
  * BLANK IS AN ABSENCE IN BOTH DIRECTIONS: seat_rank blank (never 0) when the seat term
    carried a cause; challenger blank (not false) with no sealed slate; duration_seconds
    blank (not 0) when unknown.
  * THE TWO TRANSCRIPT COUNTS ARE DIFFERENT FACTS: transcripts_held (per VIDEO, feeds the
    ceiling) vs person_transcripts_held (per PERSON, feeds the damper). Collapsing them
    gives large-corpus people a ceiling of 0 on every video, silently (0 is legal).
  * THE LONG-FORM TERM IS DEAD AND SAYS SO: duration_seconds is blank nearly everywhere
    (the videos.list queue kind is declared, not implemented), so it is emitted with
    points 0 and cause "duration unknown — videos.list not implemented", not omitted.
    A real yt-dlp duration in 1B.5 makes it fire normally.

THE OFFICE LADDER — office_importance_rank, read at run time from the newest
{DATA_REPO}/scores/new_politician_qualified/npq_*.yaml. Today it reads:

    president 100, governor 80, speaker_house 74, speaker_senate 72,
    senator 65, us_house 50, mayor 40, state_assembly 30

RESOLVING A SEAT IS TOTAL, WITH NO ?? 0 FALLBACK. Accept the seat-kind vocabulary
(president, governor, us_senate, us_house, state_assembly) translated through

    us_senate -> senator

and the rank map's own vocabulary (senator, mayor, speaker_house, speaker_senate).
Anything else: a NAMED term (points 0, cause "unknown office <x> — not in
office_importance_rank") and BLANK seat_rank. (A ?? 0 fallback on us_senate would
publish "a United States Senate seat does not matter", silently.)

A Stage 1B candidate's office, in order:
  1. {DATA_REPO}/contenders/slate.yaml assignment seat_kind, if on the sealed slate
     (most reliable; already seat-kind vocabulary).
  2. {ROSTER_DIR}/{roster_key}/{roster_key}.yaml office and level fields: FREE TEXT
     ("Candidate for Governor", level: state); map only when unambiguous (unresolved
     costs no penalty; wrong reprices a human against the whole ladder).
  3. Nothing else. people_only has no seat and takes -300 with cause "no candidacy on
     file — known from people/ only".

THE FOUR BANDS, TO THE DIGIT — never-heard rows, ceiling inert:

    president        200 + 300 + 200  =  700
    governor         200 + 240 + 200  =  640
    senator          200 + 195 + 200  =  595
    US House         200 + 150 + 200  =  550
    state assembly   200 +  90 + 200  =  490
    people_only      200 + 200 - 300  =  100

+150 for a live challenger on the sealed slate. A people_only human this repo already
has words for prices below zero and publishes 0: LOW, not excluded (round 1 for
everybody precedes round 2 for anybody). Never drop a supplement row for priority 0.


====================================================================
APPENDIX G — {IN_PROGRESS_CSV} SCHEMA
====================================================================

One row per {video_uid}; machine-local, outside every repo, never committed; read and
written by STAGE 1C, 1D, 6.1b and 6.5 and shared by every run on this machine.

COLUMNS ARE APPEND-ONLY, LOOKED UP BY HEADER NAME, NEVER POSITION. An unknown column is
CARRIED THROUGH UNCHANGED, never dropped.

    video_uid                 "{roster_key}::{video_key}" — THE KEY, the only join.
                              NEVER bare video_key (placeholder keys like v0001 repeat
                              per person; one person's failure would claim another's
                              video).
    roster_key                the demand CSV's first column, verbatim
    video_key                 the frozen per-person key, verbatim
    media_file                ABSOLUTE path handed to the transcriber (either media
                              root). Empty when the media is gone.
    status                    pending | started | finished | failed | media_gone
                              * pending     media on disk, never attempted
                              * started     an attempt is IN FLIGHT. Believed for
                                            {STALE_CLAIM_HOURS} from started_at,
                                            then treated as dead by 1C.3.
                              * finished    THE WORDS ARE IN THE REPO (written by
                                            6.5 only after 7.1 moved them), not
                                            "the transcriber exited 0"
                              * failed      an attempt ended without words
                              * media_gone  media no longer on disk, no words either
    tries                     integer, incremented in 6.1b BEFORE the transcriber is
                              called: counts attempts STARTED (hung/killed attempts
                              never reach a verdict; missing them allows infinite
                              retries).
    earliest_attempt_at       ISO 8601. FIRST attempt on this machine. WRITE ONCE,
                              never again (shows three weeks stuck vs three minutes).
    started_at                ISO 8601. THIS attempt's start (6.1b), overwritten each
                              attempt. The {STALE_CLAIM_HOURS} test reads only this.
    last_tried_at             ISO 8601. started_at's value BEFORE this attempt. Empty
                              on a first attempt.
    finished_at               ISO 8601. When the attempt ENDED (success or failure).
                              Emptied by 6.1b at a new attempt.
    words                     word count on success, else empty. Never 0 as a
                              placeholder (0 is a measurement).
    host                      "{hostname}:{pid}" of the run holding or last holding the
                              row (which window is working it).
    run_id                    {THE_DATE_TIME_STRING} of the last writer (traces to a
                              {RUN_LOG}).
    note                      free text, human: last failure reason, applied
                              correction, "reached the try cap", FAILED.txt contents.
                              The column a human reads.

WRITING RULES (several runs share the file):
  * Every write: TAKE LOCK -> RE-READ -> MERGE BY video_uid -> ATOMIC WRITE -> RELEASE.
    The re-read is mandatory (a stale copy silently reverts another run's claim).
  * Lock held for the read-modify-write ONLY (milliseconds), NEVER across a download or
    transcription.
  * Rows this run does not own are written back BYTE FOR BYTE.
  * NEVER TRUNCATE THE FILE OR DELETE A ROW. Pruning is a human's decision.
  * ABSENT IS ABSENT: unknown timestamps are EMPTY, never zero or today (a zero-epoch
    started_at is a 1970 claim that makes every stale test true).

Not evidence, not corpus, read by nothing in the product: one machine's memory of
attempts, so a downloaded video is never forgotten.

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
      [     ] jack_farley            dQw4w9WgXcQ   pri 100 (supplement)   to download
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


Z22 — a deletion under {ROOT_DIR} was refused. The run continues.

      ============================================================
      REFUSED to remove a path inside the user repo:
        {path}
      Reason: {tracked by git | it holds {n} transcript file(s)}
      Left exactly as it was. This prompt does not delete a
      citizen's committed transcripts to tidy its own bookkeeping.
      Fifteen sidecars were destroyed this way on 2026-09-07.
      Look at it by hand:
        git -C {ROOT_DIR} log --oneline -- "{path}"
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
      Safe to delete once `verify` is green: the words and the
      Capture block are already in the repo. This removes only the
      video files, never the .info.json beside them, which holds
      facts that exist nowhere else.
      ============================================================
      find ~/T/_we_citizens/download/videos \
           \( -name "*.mkv" -o -name "*.f[0-9]*" \) -delete


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
      Queue        +30 rows for 3 new people (Stage 1B)
      Selected     20      (4 from the supplement)
      Downloaded   18      (2 already on disk)
      Transcribed  17
      Failed        3      artefacts under {VIDEO_DOWNLOAD_ROOT}
      Committed    17      on {branch}, not pushed (see below)
      ------------------------------------------------------------
      Failures:
        kari_lake_us_pres / -EZZ6G-xuyk   yt-dlp: video unavailable
      ============================================================


Z40 — the Stage 1B top-up table. Printed only when rows were added.

      ============================================================
      Queue topped up — {r} rows for {n} people the engine has
      not priced yet   (queue as of {QUEUE_ASOF}, run {run_id})
      ------------------------------------------------------------
      jack_farley           people_only    10 videos   pri 100
      mike_maloney          people_only    10 videos   pri 100
      matt_gaetz_us         new_politician 10 videos   pri 550
      ------------------------------------------------------------
      No channel on record, so no rows: alex_krainer, art_berman
        -> add a youtube.com URL to that seed's source_urls, or
           file a youtube.csv row for them.
      Written OUTSIDE the data repo, provisional, superseded by the
      next engine run:
      ------------------------------------------------------------
      {QUEUE_SUPPLEMENT_CSV}
      {QUEUE_ROOT}/{THE_DATE_TIME_STRING}new_people_patch.csv
      ------------------------------------------------------------
      These price below every senator on the ladder, so a default
      run will not reach them. To work them now, name them:
      ============================================================
      ... p_download_videos.md   do the new people

  The unsourced block is omitted when there are none. Never print a line per
  candidate examined — those go to {RUN_LOG}.


Z41 — a supplement row was selected, so Stage 2's table has to say so.

      Printed as part of Z11 rather than on its own: a selected supplement row
      carries the marker (supplement) after its priority, e.g.

      [     ] jack_farley           dQw4w9WgXcQ   pri 100 (supplement)   to download

  A citizen must be able to see, before the download starts, which of these videos
  the movement asked for and which this machine added on its own.


Z42 — the data repo is behind, so "new" may mean "already priced elsewhere".

      ============================================================
      Your copy of the shared data repo is behind its remote, so
      video_demand.csv may be older than the movement's. People
      this run treats as new may already be on the current queue.
      Pull it and re-run to be sure — this prompt does not write
      to that repo, so it will not pull it for you:
      ============================================================
      git -C {DATA_REPO} pull

  WARNING ONLY. The run continues: a duplicate supplement row costs one skip, and
  Stage 1B.5 de-duplicates against the CSV it does have.


Z50 — the backlog table. Printed whenever a backlog exists, BEFORE Stage 2's
      selection table, because it changes what the run is about to do.

      ============================================================
      {n} videos on this machine are downloaded but NOT transcribed
      — work already paid for that no earlier run picked up.
      ------------------------------------------------------------
      adoptable now      {a}   ({s} never tried, {f} failed before)
      claimed by another run {c}   started under {STALE_CLAIM_HOURS}h ago
      at the try cap     {x}   {MAX_TRANSCRIBE_TRIES} attempts, skipped
      over 3 hours       {t}   deferred, never attempted (Z53)
      media gone         {g}   nothing on disk to transcribe
      ------------------------------------------------------------
      This run adopts {k} of them FIRST, so it will download {d}
      new videos instead of {VIDEO_COUNT}. Already-downloaded work
      outranks every row on the demand ladder.
      ============================================================
      {IN_PROGRESS_CSV}

  The "claimed by another run" line is omitted when there are none, and likewise
  the cap and media-gone lines. When {k} equals {VIDEO_COUNT} the last sentence
  reads "so it will download nothing new this run" — say it plainly rather than
  letting a citizen who typed "download 20" wonder why nothing downloaded.


Z51 — a video has exhausted {MAX_TRANSCRIBE_TRIES}. Stage 10 tail only.

      ============================================================
      {n} video(s) have now failed {MAX_TRANSCRIBE_TRIES} times and
      will NOT be attempted again. Three failures is not bad luck —
      it is usually a truncated download, a container the
      transcriber refuses, or a bug in the pipeline. The reasons are
      in the ledger's note column:
      ------------------------------------------------------------
      {roster_key}/{video_key}   {note}
      ------------------------------------------------------------
      When the cause is fixed, run this prompt again and say so:
      ============================================================
      ... p_download_videos.md   retry the failures


Z53 — videos were skipped for being longer than {MAX_VIDEO_SECONDS}.
      Printed once at the end of Stage 4, and again in the Stage 10 tail.
      Never silent: a citizen who asked for 20 and got 17 is owed the reason.

      ============================================================
      {n} video(s) are longer than 3 hours and were NOT worked.
      One 4-hour podcast costs more than a dozen ordinary clips,
      and the movement gets more voices for the same machine time.
      Nothing was deleted and nothing was marked failed — the
      media is on disk and a run that lifts the cap picks these
      up with no re-download:
      ------------------------------------------------------------
      {roster_key}/{video_key}   {H}h {MM}m
      ------------------------------------------------------------
      To do them anyway, say so:
      ============================================================
      ... p_download_videos.md   do the long ones


Z52 — the ledger disagreed with the disk. Stage 10 tail only, and never silent.

      ============================================================
      {n} ledger row(s) were corrected against what is actually on
      disk. A row saying `finished` with no transcript behind it
      means an earlier run reported success it did not achieve,
      which is worth knowing about:
      ------------------------------------------------------------
      {video_uid}   was {old_status} -> now {new_status}   {reason}
      ============================================================


OTHER SITUATIONS, AND WHAT TO DO — no banner, just log it and carry on

  * Ledger row `started` by THIS host and pid from an earlier run: the old run is gone
    (pids get reused). Treat it like any claim (believed {STALE_CLAIM_HOURS}, then
    adoptable); no "it looks like me" special case.
  * {IN_PROGRESS_LOCK} exists, younger than 60 seconds: another run is mid-write; retry
    after a few hundred ms. Still there after ~10 seconds: treat as stale, break, log.
  * Ledger row not in {VIDEO_DEMAND_CSV}: normal (rows leave the regenerated file). Work
    it if it has media and no words; never re-derive the row; the 3.2 seed is the fallback.
  * yt-dlp "video unavailable", geo-blocked, or members-only: skip and log (a fact about
    the video). Never route around it; never attempt a paywall or login.
  * `citizens` exits 69: CLI not built; build it (5.3) and continue.
  * STAGE_DIR has a .transcription and nothing else: the sidecar was missing; a FAILURE
    for this prompt (7.4). Never commit words that cannot be cited.
  * Selected media on disk will not open in ffprobe: treat as a failed download, mark
    [FAIL ], log, never delete the file (usually truncated from an interrupted run; the
    citizen may remove it by hand).
