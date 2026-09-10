p_download_videos

Download political videos into this citizen's own We The Citizens User Data Repo,
transcribe them on THIS machine, and commit the transcriptions so the movement can
read them.

This prompt is run from inside ONE citizen's personal user data repo. It finds the
other We The Citizens repos on this machine by itself, reads the shared demand list
to learn which videos the movement still needs, downloads the ones this citizen does
not already hold, transcribes them against a localhost install, writes a
transcription.yaml sidecar beside every result, and pushes.

IT FINISHES WHAT EARLIER RUNS STARTED BEFORE IT STARTS ANYTHING NEW. A download
whose transcription died is the most valuable work on the machine — the bytes are
already here and the movement is already waiting — so STAGE 1C reconciles a
cross-run ledger ({IN_PROGRESS_CSV}) against what is actually on disk, and STAGE 1D
adopts that backlog ahead of the demand ladder. The ledger is also how two runs in
two windows stay out of each other's way: a claim is written BEFORE the work, not
after, and is believed for {STALE_CLAIM_HOURS}.

Read every stage before starting. Stages run in order. A stage that cannot complete
STOPS the run and reports; it never guesses past a missing input.

Every message this prompt prints to the citizen is in APPENDIX Z, by code. A stage
says "print Z4" rather than carrying its own wall of text. When a situation arises
that has no Z code, write the message in the same shape — one sentence of WHY, then
the copyable lines — and say in the run report that a new message was needed.


====================================================================
OUTPUT DISCIPLINE — WHAT REACHES THE CITIZEN
====================================================================

The citizen sees SEVEN things and nothing else:

  1. The Stage 1 repo table (Z1).
  2. The Stage 1B top-up table (Z40) — and ONLY when it actually added rows.
  3. The Stage 1C backlog table (Z50) — and ONLY when a backlog exists. It earns
     its place because it changes what the run is about to spend an hour on: a
     citizen who typed "download 20" and is about to get a catch-up run instead
     needs to know BEFORE it happens, not from the final report.
  4. The Stage 2 selection table.
  5. The Stage 6 "this will take N" warning (Z20).
  6. Any Z-coded problem, at the moment it happens.
  7. The Stage 10 final report.

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
  * THE MOVEMENT'S QUEUE, and it is a SNAPSHOT rather than a live list. It is the
    output of the video-demand calc engine, which runs on an install that can see
    the private video library, and it is correct only as of its own generated_at.
    Read-only here, like everything else in {DATA_REPO}. STAGE 1B is what covers
    the window between its generated_at and now.

PEOPLE_DIR dir is {DATA_REPO}/people
  * One committed YAML seed per public figure the movement has decided to listen to.
    An admin adds files here continuously; the demand engine only learns about them
    when it next runs, and can only price them when it holds a video for them.
    This is STAGE 1B's input. Read-only.

ROSTER_DIR dir is {DATA_REPO}/politicians/new
  * The roster records a seed's links[] point at. Holds the office, the jurisdiction
    and youtube_channel. Read-only.

YOUTUBE_QUEUE_CSV is file {DATA_REPO}/youtube.csv
  * The movement's channel-fetch queue. STAGE 1B reads it as a third source for a
    person's channel URL. Read-only, and never written by this prompt.

CONTENDERS_SLATE is file {DATA_REPO}/contenders/slate.yaml
  * The sealed contenders edition. Supplies the live-challenger term and, for anyone
    on it, a seat_kind in the vocabulary the rank map understands. ABSENT means the
    challenger column is BLANK, never false.

OFFICE_RANK_FILE is the NEWEST file matching
{DATA_REPO}/scores/new_politician_qualified/npq_*.yaml
  * Carries office_importance_rank, the movement's admin-repriceable seat ladder.
    Read at run time rather than copied into this prompt, so an admin who reprices
    the ladder reprices STAGE 1B in the same edit. See APPENDIX F.

QUEUE_ROOT dir is {VIDEO_DOWNLOAD_ROOT}/_queue
  * OUTSIDE every repo, beside the media roots and the run logs. `mkdir -p` it in
    STAGE 1B before anything writes into it.

QUEUE_SUPPLEMENT_CSV is file {QUEUE_ROOT}/video_demand_supplement.csv
QUEUE_SUPPLEMENT_YAML is file {QUEUE_ROOT}/video_demand_supplement.yaml
  * STAGE 1B's output: rows for people the engine has not priced, in the SAME
    COLUMNS as {VIDEO_DEMAND_CSV}. Stage 2 reads the two files as one list.
  * PROVISIONAL and it says so on every row — notes names this prompt and run_id is
    "{THE_DATE_TIME_STRING}local_supplement". It is a statement about who the
    movement's queue is not asking about, never a claim to have run the engine.
  * IT IS NEVER APPENDED TO {VIDEO_DEMAND_CSV}. See STAGE 1B's opening for the three
    separate reasons, any one of which is enough.
  * It PERSISTS between runs and accumulates. It is never truncated and rows are
    never deleted from it by this prompt.

NEW_PEOPLE_MAX_VIDEOS is the value 10
  * The per-person cap in STAGE 1B, and it is VIDEO_DEMAND_ROUND_SIZE — round 1 is
    the top 10 videos per person. A supplement that dealt 200 rows for one newly
    added human would bury the movement's whole round-1 ladder under one person.

VIDEO_DOWNLOAD_ROOT dir is ~/T/_we_citizens/download/videos
  * Where media THIS PROMPT downloads lands. OUTSIDE every git repo, on purpose:
    media is large and it is never committed.
  * THE MEDIA IS DISPOSABLE ONCE THE WORDS EXIST. THE METADATA BESIDE IT IS NOT.
    The {video_key}.info.json holds the only copy of the channel id, the view /
    like / comment counts at capture time, and the availability — facts that
    change hourly, are never recoverable for a past date, and vanish outright if
    the video is edited, made private or deleted. Nothing else on this machine
    has them, and *.info.json is in {ROOT_DIR}/.gitignore, so they can never
    reach the repo by accident.
    Stage 7's Capture block is what rescues them. Until a video's sidecar carries
    a Capture block, deleting its directory destroys evidence permanently.
    This is not theoretical: the one transcript in this repo that predates the
    Capture block, tucker/joe_kent, has lost its media, and its Media.SHA256 can
    now never be computed. `verify` reports it as LEGACY forever.
  * SAFE TO DELETE: the media file itself, and any superseded full-video file,
    once `verify` is green for that video. Deleting the .info.json is only safe
    after its facts are in the sidecar.
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

STAGE_DIR is {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/out/, PER VIDEO
  * Where the CLI writes its nine output files (STAGE 6.2). OUTSIDE every repo.
  * A transcription takes minutes to hours. Writing it straight into
    {TRANSCRIPTIONS_ROOT} leaves a half-finished directory inside the repo for that
    whole window, where the auto-committer of STAGE 9.4 can and does commit it.
    Staging outside and moving in on success (STAGE 7.1) costs one rename.
  * On failure it stays exactly where it is, beside the media, as the evidence.

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
  * The CHECKED-IN builder and verifier for transcription.yaml. Three verbs:
      seed    {roster_key}/{video_key}   Stage 3.2. Snapshots the demand row BESIDE
                                         THE MEDIA, outside every repo. It refuses
                                         to write under {TRANSCRIPTIONS_ROOT}.
      write   {roster_key}/{video_key}   Stage 7.1. Creates the repo directory and
                                         writes the complete sidecar, merging every
                                         hand-written field already there.
      verify  --all                      Stage 7.5. The gate. It is committed code with a test beside it
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
  * IT IS A BUDGET FOR VIDEOS PROCESSED, NOT FOR VIDEOS DOWNLOADED. STAGE 1D spends
    it on the backlog first, so a run with 20 un-transcribed downloads already on
    disk downloads NOTHING and still does 20 videos' worth of work. A citizen who
    typed "download 20" is told that before it happens (Z50), because the word
    "download" in what they typed is about the size of the run, not a demand that
    bytes be fetched.

MAX_PARALLEL_TRANSCRIBE is the value 12
DEFAULT_PARALLEL_TRANSCRIBE is the value 4
  * Ceiling and starting point. See STAGE 6.3.

THE_DATE_TIME_STRING is the string "{Date}_{Time}_" using only alphanumerics and
underscores, e.g. 2026_Sep_05_08_14_31_

RUN_LOG is file {VIDEO_DOWNLOAD_ROOT}/_runs/{THE_DATE_TIME_STRING}download_videos.log
  * Outside the repo. Every stage appends what it did, what it skipped and why.
  * `mkdir -p` its directory in Stage 1 before any stage tries to append to it.

IN_PROGRESS_CSV is file ~/T/_we_citizens/videos/download/in_progress.csv
  * THE CROSS-RUN TRANSCRIPTION LEDGER, and the answer to the failure this prompt
    kept having: a video gets downloaded, the transcription dies, and the next run
    walks straight past it because Stage 2.3 only skips on "the words exist" and
    only selects from the demand ladder — so the media sits on disk forever and
    nobody ever finishes it. MEASURED 2026-09-10: 20 videos downloaded, 0
    transcribed, and nothing in the pipeline would have picked them up again.
  * It is a LEDGER, not a queue: one row per {video_uid}, carrying who is working
    it, since when, how many times it has been tried, and how it ended. STAGE 1C
    reconciles it against the disk; STAGE 1D works the backlog it exposes.
  * OUTSIDE EVERY REPO and never committed. It is machine-local operational state
    about attempts, not a record of the corpus — the corpus is the repo.
  * SEVERAL RUNS SHARE IT. The citizen may have this prompt open in two windows,
    and a run may have been killed, cancelled or crashed at any point. Every rule
    in APPENDIX G exists because the writer cannot assume it is alone.
  * `mkdir -p` its directory in Stage 1. If the file does not exist, STAGE 1C
    creates it with the header from APPENDIX G and no rows. An absent ledger is a
    first run, never an error.
  * NOTE ON THE PATH: this is `videos/download`, which is the reverse of
    {VIDEO_DOWNLOAD_ROOT}'s `download/videos`, and it is deliberate — the owner
    named this location. It therefore lands beside
    {VIDEO_DOWNLOAD_ROOT_LEGACY}. Both are outside every repo, so nothing is at
    risk either way; if it should move under {QUEUE_ROOT} instead, this is the one
    line to change.

IN_PROGRESS_LOCK is file {IN_PROGRESS_CSV}.lock
  * A directory created with `mkdir` — atomic on every filesystem this runs on, and
    the reason a lock is a directory here rather than a file with a flag in it.
  * Held ONLY around a read-modify-write of {IN_PROGRESS_CSV}, which is
    milliseconds. It is NEVER held across a download or a transcription: a lock
    held for the hour a transcription takes would block every other run on the
    machine, which is the opposite of what the ledger is for. The CLAIM in the
    ledger is what marks long work in flight; the lock only protects the file.
  * STALE LOCK: if the directory exists and its mtime is older than 60 seconds, the
    run that held it is gone. Remove it, log that it was broken, and proceed.

STALE_CLAIM_HOURS is the value 8
  * How long a `started` row is believed. Inside this window the row is ANOTHER
    RUN'S WORK and is left alone — a transcription legitimately runs for hours, and
    stealing one wastes an hour of CPU on both machines and can have two processes
    writing the same STAGE_DIR. Outside it, the claim is dead and this run may take
    it over. 8 hours is longer than any single transcription measured on this
    hardware and short enough that an overnight crash is recovered the next morning.

MAX_TRANSCRIBE_TRIES is the value 3
  * After three genuine attempts a video is SKIPPED rather than tried a fourth time.
    A video that fails three times is not failing on luck: it is a truncated file, a
    codec the transcriber refuses, or a bug in the pipeline, and the fourth attempt
    burns the same CPU to reach the same place. The row stays in the ledger with its
    reasons so a human can see what it hit.
  * THE CITIZEN CAN OVERRIDE IT. If the run text says "retry the failures", "retry
    exhausted", "try the max-tries ones" or names such a video, the cap is lifted
    for that run and the ledger says the attempt was a forced retry. That is the
    intended way to work a video after fixing the bug that blocked it.


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
               for most roster entries IT DOES NOT EXIST — there are ~100 person
               seeds against thousands of roster entries.
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
  * THE ONE CASE WHERE THE TWO ARE THE SAME STRING, and it is not a collapse of the
    namespaces: a row whose subject_kind is `people_only` is published under the
    PERSON key, because there is no roster record to scope it to an office. Column 1
    carries that person key, it is the directory segment like any other column-1
    value, AND {DATA_REPO}/people/{that key}.yaml exists by definition — so Stage 8
    can state a person_key for it without looking anything up. Verify the file
    exists rather than assuming the equality; that check is one `test -f`.
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
  do not `git add` in it, do not repair it, do not pull it, and do not append a row
  to {VIDEO_DEMAND_CSV}. STAGE 1B adds rows for people the engine has not seen — it
  writes them to {QUEUE_SUPPLEMENT_CSV}, outside every repo, for the three reasons
  that stage states.

* NEVER write application code into {WTC_REPO}. `just build` and `just run` are the
  only things this prompt does there.

* NEVER PUT A PARTIAL OR FAILED TRANSCRIPTION INTO {ROOT_DIR} — and the way to
  honour that is to never write it there in the first place, not to write it and
  clean up afterwards. Nothing enters {TRANSCRIPTIONS_ROOT} until the words exist
  (STAGE 3, STAGE 7.1); a failed transcription's artefacts are written beside the
  video, outside every repo (STAGE 7.4). A half-written directory in the repo is
  worse than an absent one: the scanner cannot tell it from a complete one.

* NEVER DELETE A TRANSCRIPT OR A TRACKED FILE UNDER {ROOT_DIR}. "Clean up the
  partial" is how fifteen committed transcription.yaml files were destroyed on
  2026-09-07. If a path under {TRANSCRIPTIONS_ROOT} is tracked by git, or holds a
  {video_key}.transcription, it is not this run's to remove — whatever state it is
  in. STAGE 7.4a is the guard and it is two commands.

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

* NEVER START A TRANSCRIPTION WITHOUT FIRST WRITING THE CLAIM TO
  {IN_PROGRESS_CSV}, and never delete or truncate that file. Stage 6.1b is the
  claim and it happens BEFORE the transcriber is called, because a hung or killed
  attempt runs no code afterwards — so a ledger written after the work records only
  the successes and loses exactly the failures the next run has to find. This is
  how 20 downloaded videos came to be transcribed zero times with nothing in the
  pipeline that would ever pick them up again.

* NEVER STEAL A LIVE CLAIM. A ledger row marked `started` within
  {STALE_CLAIM_HOURS} belongs to another run — possibly another window the citizen
  has open right now. Leave it, count it, report it. Two runs transcribing one
  video waste an hour of CPU each and race on the same STAGE_DIR.


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
STAGE 1B — TOP UP THE QUEUE WITH PEOPLE THE ENGINE HAS NOT PRICED
====================================================================

THE WINDOW THIS STAGE CLOSES.

{VIDEO_DEMAND_CSV} is not a live queue. It is the OUTPUT of the video-demand calc
engine, which runs on an install that can see the private video library, and it is
correct only as of its own generated_at. Meanwhile an admin commits a new person
seed into {PEOPLE_DIR} whenever the movement decides to start listening to somebody
new. Between those two facts is a window — sometimes days long — in which a human is
on the movement's books and on nobody's work queue, and a citizen running this
prompt walks straight past them because the CSV has no row to walk.

It is not a hypothetical and it is not small. {VIDEO_DEMAND_YAML}'s own gap
sentences say it out loud, in the engine's voice: people entered the eligible
universe from data_we_citizens/people/, fewer of them were priced, and for the
remainder "we hold no video and no channel record for them, so there is nothing on
the ladder to ask a miner for. This is a SOURCING gap, not a calc gap — re-running
this engine cannot move it." A citizen's own machine, with yt-dlp on it, can close
exactly that sourcing gap for exactly those people.

WHAT THIS STAGE PRODUCES: {QUEUE_SUPPLEMENT_CSV}, a file with the SAME COLUMNS as
{VIDEO_DEMAND_CSV} holding only rows the engine has not published, plus
{QUEUE_SUPPLEMENT_YAML} beside it saying how it was built and what it could not
establish. Stage 2 reads the two files as one list.

WHERE IT DOES NOT GO, AND WHY THE HARD RULE IS NOT BENT HERE. The supplement is
written under {QUEUE_ROOT}, outside every repo. It is NOT appended to
{VIDEO_DEMAND_CSV}. Three reasons, and any one of them is enough:

  * {DATA_REPO} is read-only from this prompt. That rule exists so a citizen's run
    can never corrupt the movement's shared record, and a stage that needed an
    exception to it would be the wrong stage.
  * The next engine run OVERWRITES that file wholesale. An appended row survives
    until the next sweep and then vanishes, which is worse than never adding it:
    the citizen would have no way to tell a row that was priced from a row that was
    guessed and then deleted.
  * {VIDEO_DEMAND_YAML} publishes csv_sha256 over the CSV. Appending a row breaks
    that hash, and every reader that verifies it — including Stage 2.1 of this very
    prompt — starts reporting the movement's own file as tampered with.

The supplement is PROVISIONAL, and every consumer is told so: its rows carry
run_id "{THE_DATE_TIME_STRING}local_supplement" and a notes cell naming this prompt.
A row here is this machine's best answer to "who is the movement not asking about",
never a claim to have run the engine.

If nothing needs topping up, this stage writes nothing, prints nothing, and logs one
line. Silence here is the normal case on a machine whose data repo was pulled today.


1B.0 PRECONDITION

Stage 1 has confirmed {DATA_REPO} and {RUN_LOG} is open. If {PEOPLE_DIR} does not
exist, log it and skip this whole stage — an older data repo has no seed directory
and that is not an error.

Do a read-only freshness check on the data repo before trusting its age:

        git -C {DATA_REPO} fetch --dry-run 2>&1 | head -5

If it reports the remote is ahead, print Z42 and CARRY ON. A citizen whose data repo
is a week behind will be shown people as "new" who were priced days ago, and the fix
is one pull they can run themselves. Do not pull {DATA_REPO} yourself — this prompt
does not write to it and a merge is a write.


1B.1 THE QUEUE'S OWN AS-OF DATE

* Read generated_at and run_id from {VIDEO_DEMAND_YAML}. That timestamp is
  QUEUE_ASOF and everything in this stage is measured against it.
* If the yaml is missing or has no generated_at, fall back to the newest
  computed_at in {VIDEO_DEMAND_CSV}, and say in the log that the fallback was used.
* Log QUEUE_ASOF and the run_id. The Stage 10 report names them.


1B.2 THE TIMESTAMP IS THE HINT. ABSENCE FROM THE LADDER IS THE TEST.

The obvious implementation — "list {PEOPLE_DIR} for files newer than the CSV" —
gets this wrong in both directions, and both failures are silent:

  * FILESYSTEM MTIME IS NOT A COMMIT DATE. `git clone` and `git checkout` stamp
    every file with the moment of the checkout, so on a fresh clone mtime says all
    of them are new, and on a long-lived clone it says none of them are. Never let
    mtime NARROW the candidate set. It may only widen it.
  * A SEED CAN BE OLD AND STILL UNPRICED. The 33 people the engine's own gap
    sentence names were committed long before the last run and have no row on the
    ladder anyway, because the engine holds no video for them. A pure timestamp
    test walks past every one of them — the exact people this stage exists for.

So build the candidate set as the UNION of these three, and log which test caught
each candidate:

  (a) SEED NEWER THAN THE QUEUE. For each {PEOPLE_DIR}/*.yaml take the LATEST of:
        - the file's own updated_at (and created_at, if updated_at is absent)
        - git -C {DATA_REPO} log -1 --format=%cI -- people/<file>
        - the filesystem mtime
      If that is after QUEUE_ASOF, it is a candidate.

  (b) ZERO ROWS ON THE LADDER. Read the seed's person_key and EVERY links[].key it
      names. Ask whether ANY of those keys appears in column 1 of
      {VIDEO_DEMAND_CSV}. If none does, it is a candidate, whatever its date.

      DO NOT test the person key alone. A roster-linked human's rows are published
      under the ROSTER key, and a person-key-only test reports every roster-linked
      seed as new and then mints a second, duplicate ladder for them under a key
      nothing else in the product uses.

      AND THIS TEST IS STILL NOT SUFFICIENT, WHICH IS WHY 1B.5 DE-DUPLICATES AGAIN.
      A seed's links[] can be INCOMPLETE, so "none of the seed's keys has rows" is
      not the same fact as "the movement has no rows for this human". MEASURED,
      2026-09-10: marjorie_taylor_greene's seed links marjorie_taylor_greene_us_pres
      and her rows are on the ladder under marjorie_taylor_greene_ga_14;
      matt_gaetz's seed links matt_gaetz_us and his rows are under matt_gaetz_fl_01.
      Both looked new here and neither was. Nothing in the seed can catch that — the
      only thing that can is comparing the actual video ids, which 1B.5 does.

  (c) NAMED BY THE CITIZEN. If the run text names a person ("do the new people",
      "add jack_farley"), take them as a candidate even when (a) and (b) would both
      have passed over them.

Read column 1 of the CSV ONCE into a set. It is ~150k rows and a per-person grep
over it re-reads 35MB a hundred times.

        cut -d, -f1 {VIDEO_DEMAND_CSV} | tail -n +2 | sort -u

Then SUBTRACT, and log each subtraction with its reason:

  * a candidate that already has rows under any of its keys — not new, drop it
  * a candidate already present in {QUEUE_SUPPLEMENT_CSV} from an earlier run whose
    rows are still unworked — already topped up, drop it and do not re-list the
    channel
  * bryan_starbuck, or any seed whose person_key matches the citizen running this.
    THE CITIZEN IS NOT A WORK ITEM. Log it and move on.


1B.3 WHICH STORE IS THIS HUMAN KNOWN FROM — subject_kind, IN THE SPEC'S OWN ORDER

This decides the arithmetic, so resolve it by the ORDERED list and not by "is there
a seed?", which answers the question backwards for every roster-linked human.
Take the FIRST that matches (calc_engine_video_demand.mdx §12.2):

  1. a links[] entry of kind new_politician       -> new_politician
  2. a links[] entry of kind worrisome_challenger -> worrisome_challenger
  3. a links[] entry of kind legacy_politician    -> legacy_politician
  4. a links[] entry of kind fix_bill_author      -> fix_bill_author
  5. none of the four, and the seed exists        -> people_only
  6. none of the above                            -> BLANK, never people_only

`people_only` means A SEED WITH NO ROSTER LINK AT ALL. It is the absence of a roster
record, not the presence of a seed. A human on politicians/new/ is a new_politician
even when a seed also exists.

THE KEY THIS ROW IS PUBLISHED UNDER follows from the same answer, and it is the
directory segment every later stage uses:

  * subject_kind people_only          -> column 1 is the PERSON key
  * any roster kind                   -> column 1 is that link's ROSTER key

Both are read verbatim from the seed. Neither is derived by adding or removing an
office suffix. See TWO KEY NAMESPACES: a key built by chopping "_us_pres" off
another key is a fabricated identity claim.


1B.4 FIND THE CHANNEL — ATTRIBUTED, OR NOT AT ALL

A video attributed to the wrong human publishes one person's recorded words under
another's name. That is the single worst thing this prompt can do, so the channel
must come from a record the movement already committed. Look in this order and take
the first hit:

  1. the seed's own source_urls[] — any youtube.com entry
  2. {ROSTER_DIR}/{roster_key}/{roster_key}.yaml -> youtube_channel
  3. {YOUTUBE_QUEUE_CSV} — the row whose person_key (col 18) or politician_key
     (col 3) is one of this human's keys, and its target (col 4)

NEVER search YouTube for the person's name and take the first channel back. Never
accept a channel because the handle resembles the name. If none of the three hits,
the candidate is UNSOURCED: it gets no rows, it is counted, and it is named in Z40
with the one thing a human can do about it — add a youtube.com URL to the seed's
source_urls, or file a youtube.csv row. That is a stated gap with a remedy, which is
worth more than a guessed channel that renders perfectly.

Log, per candidate, WHICH of the three sources supplied the channel. When two of
them disagree, take the seed's and log both — the seed is the record an admin
committed about the human; youtube.csv is a work queue.


1B.5 LIST THE UPLOADS — REAL PLATFORM IDS, NEVER MINTED KEYS

        yt-dlp --flat-playlist --playlist-end {NEW_PEOPLE_MAX_VIDEOS} \
               --print "%(id)s\t%(duration)s\t%(title)s" \
               "{channel_url}/videos"

  * This is a metadata listing of a public channel page. It downloads no media. It
    is the same tool Stage 4 already uses and the same Terms of Service rule
    applies: if a channel cannot be listed lawfully, skip it and log the reason.
  * THE `/videos` SUFFIX IS A GUESS ABOUT A URL SHAPE AND IT FAILS OFTEN. MEASURED,
    2026-09-10: seven of twelve channels answered "This channel does not have a
    videos tab" or "Unable to download API page", including handle URLs that open
    perfectly in a browser. On failure, retry ONCE against the BARE channel URL with
    no suffix, and once against `{channel_url}/streams` if the person is known for
    live shows. Those are three cheap attempts at the same public page, not three
    attempts to get around a refusal — a 403, a login wall, an age gate or a
    members-only listing is a NO and is not retried at all.
  * THE video_key IS THE 11-CHARACTER YOUTUBE ID, byte for byte as yt-dlp printed
    it. That is what the engine publishes on every YouTube row today — video_key,
    youtube_id and source_ref are the same string — so this stage is READING a
    frozen platform key, not inventing one. Nothing here derives a key from a title,
    a slug, a date or a counter. If yt-dlp returns something that is not
    [A-Za-z0-9_-]{11}, drop that entry and log it.
  * {NEW_PEOPLE_MAX_VIDEOS} is 10 because that is VIDEO_DEMAND_ROUND_SIZE — round 1
    is the top 10 videos per person, and a supplement that dealt 200 rows for one
    newly-added human would bury the movement's whole round-1 ladder under one
    person. Every supplement row is round 1 and there is no round 2 here.
  * `--playlist-end` yields the channel's MOST RECENT uploads, which is a different
    selection from the engine's "highest priority within this person". With no
    duration and no transcript counts, every one of this person's rows prices
    identically anyway (§3.2 gives one raw score per person when nothing is held),
    so recency is the only ordering available. Say that in {QUEUE_SUPPLEMENT_YAML};
    do not present it as the engine's ordering.
  * If yt-dlp lists ZERO videos — channel deleted, renamed, or nothing public — the
    candidate is counted as listed-empty. No rows, no error, one log line.
  * A candidate whose listing fails twice is dropped for this run. Do not retry a
    third time and do not try a different channel.

DE-DUPLICATE BEFORE PRICING. Drop any id that already appears anywhere in column 3
of {VIDEO_DEMAND_CSV}, or that this repo already holds words for:

        find {TRANSCRIPTIONS_ROOT} -name "{video_key}.transcription"

A channel re-listed on a later run must produce no duplicate row.

THE BARE-KEY TEST IS THE RIGHT ONE HERE, AND ONLY HERE. Everywhere else in this
prompt a bare video_key comparison is a bug, because a video_key is unique within
one person only. On a YouTube row it is also the YouTube id, and a YouTube id names
ONE video on the whole platform — so an id already in column 3 is the same video,
whoever the ladder filed it under. That is exactly the case worth catching.

AND WHEN IT CATCHES EVERY ID FOR A CANDIDATE, THAT CANDIDATE WAS NEVER NEW. It means
the movement already has this human's videos on the ladder under a roster key the
seed's links[] does not name — 1B.2's test (b) asked whether any of the seed's OWN
keys had rows, and the answer was no for a key nobody publishes under. MEASURED on
2026-09-10: matt_gaetz's seed links matt_gaetz_us, and all ten of his recent uploads
were already on the ladder under matt_gaetz_fl_01. Record that candidate as
`already_on_ladder_under=<the key that holds them>`, add no rows, and name it in the
patch CSV of 1B.8 — the remedy is a links[] entry on the seed, which is an admin's
one-line edit, and it is a more valuable thing to report than a row.


1B.6 PRICE EACH ROW — APPENDIX F, NOT A NUMBER INVENTED HERE

The arithmetic is normative and it is written out in APPENDIX F. Run it; do not
approximate it, and do not copy a neighbouring row's priority because the person
"seems similar". Two inputs need sourcing before the sum:

  * office_importance_rank — read from the NEWEST
    {DATA_REPO}/scores/new_politician_qualified/npq_*.yaml. It is the movement's
    admin-repriceable policy and this run reads it rather than carrying a copy, so a
    reprice reaches this stage the same day it reaches the engine. If it cannot be
    read, the seat term is a stated cause and NOT a zero — see APPENDIX F.
  * the sealed contenders slate — {DATA_REPO}/contenders/slate.yaml. A key present
    in assignments[] is challenger true; a key absent from a slate THAT EXISTS is
    false; NO slate on disk means the column is BLANK. Blank is not false.

THE TWO TRANSCRIPT COUNTS ARE LOCAL AND SAY SO. This machine cannot see the
movement's corpus, so transcripts_held and person_transcripts_held are counted over
{TRANSCRIPTIONS_ROOT} on THIS computer only. For a genuinely new person both are 0
and the answer is the same one the engine would give. Where they are not, the
supplement's priority is HIGHER than the movement's would be, and
{QUEUE_SUPPLEMENT_YAML} states that as a gap in exactly those words. Do not fold in
a guess about what other citizens hold.

The expected shape of the answer, so an implausible number is caught rather than
published:

  * a never-heard people_only human       ->  priority 100
  * a never-heard state assembly seat     ->  priority 490
  * a never-heard senator                 ->  priority 595
  * a never-heard president               ->  priority 700
  * any of the above, +150, when the key is on the sealed slate
  * any of the above, +100, when yt-dlp printed a duration over 2400 seconds

THAT LAST ONE IS THE LONG-FORM TERM WAKING UP, AND IT IS NOT A DEVIATION. Every row
the engine publishes today has a blank duration, so on the engine's ladder the term
is structurally dead. A channel listing gives this stage a real duration for free,
so a supplement row for a 45-minute video legitimately prices 100 points above the
band — a people_only human at 200 rather than 100. Say so in
{QUEUE_SUPPLEMENT_YAML}: it is the one place a supplement row is knowingly priced
higher than the engine would price the same video today, and a reader comparing the
two files deserves the reason rather than a discrepancy.

A supplement row above 950, or below 0, is a bug in the sum. Log it, drop the row,
and say so in Stage 10 rather than publishing a number nobody can reproduce.


1B.7 WRITE {QUEUE_SUPPLEMENT_CSV}

* The header is the header of {VIDEO_DEMAND_CSV}, READ FROM THAT FILE at run time
  and copied byte for byte. Never a header typed out here: the columns are
  append-only and a newer engine may have added a 26th, which this stage must carry
  as an empty cell rather than refuse.
* Every cell is filled by column NAME, never by position.
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
* BLANK IS AN ABSENCE AND NEVER A ZERO. seat_rank is blank whenever the seat term
  carried a cause — including for every people_only row, whose cause is "no
  candidacy on file — known from people/ only". A seat_rank of 0 published against a
  named living person reads as "the least important office there is", which is a
  measurement this run never made. duration_seconds is blank unless yt-dlp printed a
  real number.
* Rows are written in the same published order the engine uses: round ascending,
  then priority descending, then column-1 key ascending, then video_uid ascending.
* If the file already exists, MERGE by video_uid: rows already there are kept as
  they are, new ones are added, and nothing is rewritten. This stage never deletes a
  supplement row — Stage 2 skips what has been transcribed, and a row that has been
  worked costs one skip, while a row deleted in error costs a video nobody fetches.

Write {QUEUE_SUPPLEMENT_YAML} beside it, in the shape of {VIDEO_DEMAND_YAML} so the
same readers work:

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

Then verify what was written before anything trusts it: re-read the supplement,
confirm every row parses under the real header, that no video_uid is duplicated
within it or shared with {VIDEO_DEMAND_CSV}, and that every priority is an integer
in [0, 1000]. A row that fails is dropped and named in the log.


1B.8 THE PATCH THE ENGINE'S OWNER CAN ACTUALLY USE

This stage answers one run on one machine. The durable fix is the movement's engine
learning these people exist. So also write, to
{QUEUE_ROOT}/{THE_DATE_TIME_STRING}new_people_patch.csv, one row per PERSON — not
per video — with these columns:

    person_key,column_1_key,subject_kind,channel_url,channel_source,videos_listed,rows_added,status

`status` is one of added, unsourced, listed_empty, dropped, and carries the reason.
Name the file in Stage 10. It is the artifact a citizen can send to whoever runs the
demand engine, and it is the thing that makes this stage stop being necessary.


1B.9 SAY WHAT ADDING THEM DOES AND DOES NOT DO

A supplement row is on the queue. It is not near the top of it, and a citizen who
watches this stage add thirty rows and then watches Stage 2 select none of them is
owed the reason BEFORE the selection table, not after.

The bands are the reason and they are the ratified design, not a defect: a
never-heard senator prices 595 and a never-heard people_only human prices 100. With
150,000 priced rows on the ladder, everything STAGE 1B adds sorts below all of them
and a default depth-first run of 20 never reaches it. The owner ratified exactly
this — "a human with no candidacy on file waits behind one who has" — and the
mechanism that keeps a low row reachable at all is the ROUND, which this stage
cannot raise anybody in.

MEASURED, 2026-09-10: 30 supplement rows were added at 400 / 200 / 100 and the run's
20 slots all went to senators at 595.

So STAGE 1B's output is a STANDING addition to the queue rather than this run's
work, and two things make it reachable now rather than eventually:

  * THE CITIZEN NAMES THEM. If the run text names a person or says "do the new
    people", Stage 2.3 restricts the traversal to those keys and the bands stop
    mattering. That is the intended way to work a newly-added human, and Z40 says
    so in its last line.
  * THE ENGINE PRICES THEM PROPERLY. The patch CSV of 1B.8 is what makes that
    happen, and it is the durable fix.

Say this in Stage 10 whenever rows were added and none were selected. A citizen who
concludes the stage did nothing will turn it off.

1B.10 REPORT

* Rows added: print Z40, once, before Stage 2's selection table.
* Nothing added: print nothing at all. One line to {RUN_LOG}.
* Never print a per-candidate line to the terminal. The table is the output; the
  reasoning goes to {RUN_LOG}.


====================================================================
STAGE 1C — RECONCILE THE LEDGER WITH WHAT IS ACTUALLY ON DISK
====================================================================

THE HOLE THIS STAGE CLOSES, AND IT IS NOT HYPOTHETICAL.

A video gets downloaded and the transcription then dies — the app falls over, the
run is cancelled, the machine sleeps, a watcher restarts the server mid-job. The
media is on disk and the words do not exist. Nothing in this prompt used to pick
that up again: Stage 2 selects from the demand ladder, and Stage 2.3 skips a row
only when the WORDS exist, so an un-transcribed download is neither skipped nor
selected — it is simply never looked at again. MEASURED 2026-09-10: a run
downloaded 20 videos, transcribed 0, and every one of those 20 would have sat
under the media root untouched by every future run.

So this stage asks the question no earlier stage asked: WHAT HAS THIS MACHINE
ALREADY PAID TO DOWNLOAD AND NOT YET TURNED INTO WORDS?

THE DISK IS THE TRUTH AND THE LEDGER IS THE CLAIM. Everything below reconciles in
that direction. A ledger row saying `finished` for a video with no transcript is
wrong and gets corrected; a transcript with no ledger row is a completed video from
before the ledger existed and gets a row stating so. Never the other way round: a
ledger that overrides the disk would let one bad row hide a real backlog forever.

1C.0 PRECONDITION

Stage 1 has confirmed {ROOT_DIR} and the media roots, and {RUN_LOG} is open.
`mkdir -p` the directory holding {IN_PROGRESS_CSV}.

If {IN_PROGRESS_CSV} does not exist, create it with the APPENDIX G header and no
rows, log "ledger created — first run on this machine", and carry on into 1C.2.
There is no backlog to find in an absent ledger, but 1C.2 still scans the disk,
and on a machine with existing downloads that first scan is exactly what populates
it.

1C.1 READ THE LEDGER UNDER THE LOCK

Take {IN_PROGRESS_LOCK} (breaking it if stale, per its variable note), read the
whole file, release the lock. Parse by COLUMN NAME, never by position — APPENDIX G
is append-only and a newer version of this prompt may have added a column.

A row that does not parse is LEFT EXACTLY AS IT IS and reported. Do not drop it and
do not repair it: it is another run's writing, and a row this run cannot read is
not a row this run may delete.

1C.2 WALK BOTH MEDIA ROOTS AND CLASSIFY EVERY VIDEO

For every {roster_key}/{video_key}/ directory under {MEDIA_ROOTS}, establish two
facts and nothing else:

  HAS_MEDIA   a file on the transcriber's allowlist (Stage 4.4) exists in it,
              preferring audio over video exactly as Stage 2.3 does. A directory
              holding only a .info.json is NOT media. A .fNNN pre-merge part is
              never media.
  HAS_WORDS   `find {TRANSCRIPTIONS_ROOT} -name "{video_key}.transcription"`
              returns a hit. BY VIDEO KEY, NOT BY PATH — legacy transcript
              directories use hand-made names and a path-shaped test walks past
              them and re-transcribes an hour of audio this citizen already has.

That gives four classes, and each has exactly one correct ledger state:

  media + words        -> `finished`. If the ledger says anything else, CORRECT it
                          and log the correction. This is the common case on a
                          machine that has been working for a while, and it is how
                          a `started` row left behind by a run that actually
                          succeeded before dying gets closed.
  media, NO words      -> THE BACKLOG. This is what the stage exists to find.
                          1C.3 decides what state it should carry.
  NO media, words      -> `finished`, media cleared. Normal and safe: the media is
                          disposable once the words and the Capture block exist.
                          Never re-download it.
  NO media, no words   -> not a row at all. There is nothing here. If the ledger
                          has a row for it, mark it `media_gone` and say so — the
                          download either never completed or the file was removed,
                          and Stage 2 may legitimately select it again.

Log the four counts. Print nothing yet.

1C.3 WHAT STATE A BACKLOG ROW SHOULD CARRY — THE ONE PLACE JUDGEMENT IS NEEDED

For a video with media and no words:

  * NO LEDGER ROW -> add one, `status: pending`, `tries: 0`, every timestamp empty.
    It has never been attempted as far as this machine can prove. Do NOT invent a
    `tries` count from the presence of a STAGE_DIR or a .FAILED.txt — those are
    evidence that something happened, not a count of how many times.
    DO read a {video_key}.FAILED.txt if one is there and carry its reason into
    `note`, because that is the most useful thing a human will read.
  * `status: started` AND `started_at` IS WITHIN {STALE_CLAIM_HOURS}
    -> LEAVE IT COMPLETELY ALONE. Another run is working it right now. It is not
    this run's backlog, it is not this run's row to touch, and its media is not
    this run's to re-download. Count it and move on.
  * `status: started` AND `started_at` IS OLDER THAN {STALE_CLAIM_HOURS}
    -> the claim is DEAD. Whoever held it is gone. Set `status: failed`, put the
    reason `claim expired after {STALE_CLAIM_HOURS}h — the run that held it did not
    finish`, and leave `tries` where it is: the attempt genuinely happened and
    already counted. It is now adoptable by 1D.
  * `status: failed` -> adoptable, subject to the tries cap.
  * `status: finished` but no words -> the ledger is wrong (see 1C.2). Set
    `status: failed`, reason `ledger said finished but no transcript exists`, and
    log the correction loudly: it means some earlier run reported success it did
    not achieve, which is worth a human knowing.
  * `status: pending` -> adoptable.

A ROW THIS RUN DID NOT CLAIM IS NEVER GIVEN A NEW `started_at`. The timestamps
belong to the attempt that made them; rewriting one destroys the only evidence of
how long something has been stuck.

1C.4 WRITE THE RECONCILED LEDGER BACK, ONCE, UNDER THE LOCK

Take the lock. RE-READ the file — another run may have written between 1C.1 and
now, and the copy in memory is already stale. Merge by {video_uid}:

  * a row THIS STAGE corrected -> write the correction, unless the re-read shows
    the row now `started` inside {STALE_CLAIM_HOURS}, in which case ANOTHER RUN
    JUST CLAIMED IT and its claim wins. Drop the correction and log it.
  * a row this stage did not touch -> keep the re-read version byte for byte.
  * a row this stage is adding -> add it.

Write atomically (temp file plus rename, both on the same filesystem, so no reader
ever sees a half-written ledger), release the lock.

NEVER TRUNCATE THE LEDGER AND NEVER DELETE A ROW. A `finished` row costs one line
and is the record that the work was done; a deleted row costs a re-download and a
re-transcription of something this machine already has. If the file ever needs
pruning that is a human's decision, not a run's.

1C.5 REPORT

* A backlog exists: print Z50 — the table of what is adoptable, what is claimed by
  another run, and what is capped out. This is one of the few things the citizen
  sees, because it changes what the run is about to spend an hour doing.
* No backlog and no corrections: print nothing. One line to {RUN_LOG}.
* Corrections made but no backlog: print nothing to the terminal, but NAME every
  correction in the Stage 10 report. A ledger that said `finished` for a video with
  no words is a fact about an earlier run that somebody should see.


====================================================================
STAGE 1D — WORK THE BACKLOG BEFORE DOWNLOADING ANYTHING NEW
====================================================================

THE PRIORITY RULE, AND THE REASON FOR IT:

        AN ALREADY-DOWNLOADED VIDEO OUTRANKS EVERY ROW ON THE DEMAND LADDER.

The bytes are already on this disk. Somebody's bandwidth and somebody's disk have
already been spent, the movement is already waiting for those words, and no new
download can be worth more than finishing work that is one stage from done.
Downloading twenty more videos while twenty un-transcribed ones sit on the same
disk is how a machine accumulates a permanent backlog it never works off.

1D.1 BUILD THE ADOPTION LIST

From 1C's reconciled ledger, take every row where ALL of these hold:

  * HAS_MEDIA is true and HAS_WORDS is false
  * status is `pending` or `failed`
  * NOT (`started` within {STALE_CLAIM_HOURS}) — 1C already excluded these
  * `tries` < {MAX_TRANSCRIBE_TRIES}, UNLESS the citizen lifted the cap

Order it: fewest `tries` first, then oldest `earliest_attempt_at` first, then
{video_uid}. Fewest tries first because a never-attempted video is more likely to
succeed than one that has already failed twice, and a run that dies partway
through should have spent its time on the likely wins. Oldest-first inside that,
because a video that has been stuck for three weeks has been keeping the movement
waiting for three weeks.

RESTRICTIONS THE CITIZEN NAMED STILL APPLY. If the run text named people (Stage
2.3b), the adoption list is filtered to those keys too — a citizen who asked for
"peter" did not ask for somebody else's backlog. Say so in the table.

1D.2 THE CAP, AND WHAT IT DOES TO {VIDEO_COUNT}

Adopted videos CONSUME {VIDEO_COUNT} SLOTS, and they consume them FIRST.

  * Backlog ≥ {VIDEO_COUNT}: this run is entirely a catch-up run. Take the first
    {VIDEO_COUNT}, download NOTHING, and say so plainly — a citizen who typed
    "download 20" and sees no downloads is owed the reason before it happens, not
    in the final report.
  * Backlog < {VIDEO_COUNT}: adopt all of it, and let Stage 2 fill the remaining
    slots with new rows from the ladder.
  * Backlog empty: Stage 2 behaves exactly as it always has.

THE CITIZEN CAN CHANGE THIS. "just the backlog" / "catch up" -> adopt only, never
download. "skip the backlog" / "only new" -> log the backlog size, adopt nothing,
and STILL report it in Stage 10 so it is not silently abandoned.

1D.3 CARRY THEM FORWARD

An adopted row arrives at Stage 4 with its MEDIA_FILE already resolved (1C.2 found
it) and marked "already on disk", so it SKIPS 4.2–4.4 and runs 4.5 and 4.6 like
any other carried-in video. It still needs its Stage 3.2 demand seed if one is
missing, and Stage 6 claims it in the ledger exactly like a fresh download. From
Stage 4 onward an adopted video and a newly downloaded one are indistinguishable,
which is the point: there is one transcription path, not two.

ONE THING TO CHECK BEFORE TRUSTING OLD MEDIA. Run the ffprobe of 4.5 and believe
it: a file left by an interrupted download is frequently TRUNCATED, and a truncated
file is why some of these failed the first time. If ffprobe cannot open it, mark
the row `failed` with reason `media will not open in ffprobe — probably a truncated
download`, do NOT delete the file (it is the citizen's, and outside every repo),
and let Stage 2 decide whether to re-download it. Say it in Stage 10.


====================================================================
STAGE 2 — CHOOSE WHICH VIDEOS TO DOWNLOAD
====================================================================

2.1 READ THE DEMAND LIST — BOTH HALVES OF IT

* Read {VIDEO_DEMAND_CSV}. Columns are in APPENDIX B. It is generated by the
  video-demand calc engine and is ALREADY SORTED by priority, highest first.
* Read {QUEUE_SUPPLEMENT_CSV} if STAGE 1B wrote or found one, and treat its rows as
  part of the same list. It has the same columns and it is read the same way, by
  column NAME. There is no separate traversal for it and no separate quota.
  * A supplement row is MARKED, everywhere the citizen can see it: in the Stage 2.4
    table (Z41), and in the Stage 10 report. A citizen must be able to tell which
    videos the movement asked for and which this machine added on its own.
  * If a video_uid appears in BOTH files, THE ENGINE'S ROW WINS and the supplement
    row is dropped for this run. The engine can see the movement's corpus and this
    prompt cannot, so its priority, its transcript counts and its status are the
    better answer wherever both exist.
  * Everything downstream is unchanged. Stage 3.2 and Stage 7.1 read a supplement
    row's demand facts by passing --demand-csv {QUEUE_SUPPLEMENT_CSV} to
    {SIDECAR_TOOL}; the sidecar records the row it actually used, so a later reader
    can tell a provisional row from a priced one.
* Read {VIDEO_DEMAND_YAML} for the run record that produced it — run_id,
  generated_at, rows_open, and its stated gaps. Log the run_id in {RUN_LOG} so a
  later reader can tell which demand snapshot this run worked from.
* If {VIDEO_DEMAND_YAML} carries csv_sha256, verify {VIDEO_DEMAND_CSV} against it
  with `shasum -a 256`. On mismatch print Z10, log it, and keep going — the CSV is
  still the list.
* Consider only rows whose status is `open` or `partial`. Skip `satisfied` and
  anything with a closed_reason.

2.2 PICK THE TRAVERSAL — ODD/EVEN STRIDE ON LONG LISTS

* Count the eligible rows across BOTH files together.
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

A DIRECTORY IS NOT A TRANSCRIPT. The test above is for {video_key}.transcription
and it is deliberately not "does the directory exist": runs before Stage 3 was
fixed left seed-only directories holding a stub transcription.yaml and no words,
and treating those as done would skip a video the movement is still waiting for.
Such a directory is neither a skip nor an error. Note it on the row, work the video
normally, and let Stage 7.1 overwrite the stub with the real record — the tool
merges, so anything a human wrote into that stub survives. List them in Stage 10;
Stage 7.4b says when one may be cleared and when it must be left alone.

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

STAGE 1D HAS ALREADY TAKEN SOME OF THOSE SLOTS. The number this stage may select is
{VIDEO_COUNT} MINUS the count adopted from the backlog, and it may be zero — on a
machine with a real backlog a run legitimately downloads nothing at all. Do not
treat a remaining count of zero as an error or as a reason to raise
{VIDEO_COUNT}: the run is full, of work that was already paid for.

ALSO SKIP A ROW THE LEDGER SAYS IS IN FLIGHT. A row whose {video_uid} is `started`
in {IN_PROGRESS_CSV} within {STALE_CLAIM_HOURS} is another run's work even if its
words do not exist yet, and selecting it would have two runs download the same
video and race on the same STAGE_DIR. Skip it, count it, and log it — this is the
one skip reason that is about coordination rather than about the corpus.

2.3b DEPTH OR BREADTH — SAY WHICH, BECAUSE THE DEFAULT IS DEPTH

The demand CSV is sorted by priority and priority is largely a property of the
PERSON, so consecutive rows are usually the same person. Walking it straight down
means a run of 20 covers about four people, 5 videos each. That is DEPTH, and it is
the default because the engine's ordering is the movement's stated ranking.

It is not always what is wanted. The product's own `citizens batch` defaults the
other way — `--breadth 2`, "breadth-first, so every person gets words early" — on
the view that one video each for twenty people is worth more than five each for
four. Both are defensible and this prompt does not get to decide it silently.

  * THE CITIZEN NAMED PEOPLE. If the run text names one or more people — a
    person_key, a roster key, or "the new people" / "the ones Stage 1B added" —
    restrict the traversal to rows whose column-1 key matches, in priority order
    within that restriction, and ignore the stride. This overrides both defaults
    below and it is the only way a low-priced row gets worked on purpose. Say in
    the selection table that the traversal was restricted, and to what.
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
STAGE 3 — SEED THE DEMAND ROW, OUTSIDE THE REPO
====================================================================

THE ONE RULE THIS STAGE EXISTS TO ENFORCE:

        NOTHING IS WRITTEN INTO {TRANSCRIPTIONS_ROOT} UNTIL THE WORDS EXIST.

Not a directory, not a .gitkeep, not a stub transcription.yaml. Stage 7.1 creates
the directory and writes the sidecar in one step, when there is a complete record
to put there. Until then this run leaves no trace inside {ROOT_DIR}.

WHY, AND IT IS NOT HYPOTHETICAL. This stage used to seed a stub transcription.yaml
into the repo before the download. On 2026-09-07 that produced this sequence:

  1. Twenty stubs were seeded into {TRANSCRIPTIONS_ROOT}. Each held Video.URL,
     Video_ID and a partial Demand block — sixteen lines, no words.
  2. The external auto-committer (Stage 9.4, commits titled "Bryan 26 Tower")
     swept mid-run and COMMITTED FIFTEEN OF THEM. It knows nothing about this
     prompt and nothing here can stop it.
  3. The app on :9333 would not stay up and those fifteen transcriptions failed.
  4. Stage 7.4 did what it is told — "a failed transcription leaves NOTHING behind
     in {ROOT_DIR}" — and removed the directories.
  5. Fifteen committed transcription.yaml files were therefore DELETED from the
     repo (901615a created them, d4452fa removed them), which reads in the history
     as this pipeline destroying its own sidecars.

Every step of that was individually correct. The mistake was upstream of all of
them: a file that had not earned its place in the repo was put in the repo, and
from that moment every later rule had to choose between committing a partial
transcript and deleting a tracked file. Do not recreate that choice.

3.1 CREATE ONLY THE MEDIA DIRECTORY

  * {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/ — ONLY when this run is going to
    download. A video already on disk keeps the directory it is already in.
  * DO NOT create {TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/. Stage 7.1 does,
    on success, and nothing else does.
  * The directory name IS the video_key from the CSV, byte for byte. Not a title,
    not a slug, not a guest's name. The video_key is the join key everywhere else in
    this product and a directory named anything else is invisible to every reader.

3.2 SNAPSHOT THE DEMAND ROW BESIDE THE MEDIA

        python3 {SIDECAR_TOOL} seed {roster_key}/{video_key}

For a row that came from {QUEUE_SUPPLEMENT_CSV}, point the tool at the file the row
is actually in — otherwise it reports "no row" for a video this run legitimately
selected:

        python3 {SIDECAR_TOOL} seed {roster_key}/{video_key} \
                --demand-csv {QUEUE_SUPPLEMENT_CSV}

That writes {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/{video_key}.demand.yaml
— outside every repo, beside the media it belongs to.

This is not a placeholder standing in for the sidecar. It does a job nothing else
does: {VIDEO_DEMAND_CSV} IS REGENERATED EVERY ENGINE RUN, so by the time a
twenty-video batch reaches Stage 7 the row it was selected from may carry a
different priority, a different status, or be gone. The seed is what that row
actually said when the work started, and Stage 7.1 falls back to it when the live
CSV no longer has the row.

  * If the seed cannot be written, LOG IT AND CARRY ON. It is a debugging aid and a
    fallback, not a gate. A run must never fail because a scratch directory was
    not writable.
  * If {SIDECAR_TOOL} reports no row for {roster_key}::{video_key} AND the video
    came from STAGE 2's ladder traversal, that is a SELECTION bug, not a seed bug —
    Stage 2 chose a row that is not in the CSV. Drop the video, log it, and say so
    in Stage 10.
  * BUT IF THE VIDEO WAS ADOPTED BY STAGE 1D, "no row" IS EXPECTED AND IS NOT A
    REASON TO DROP IT. {VIDEO_DEMAND_CSV} is regenerated on every engine run and
    rows leave it — a video downloaded three weeks ago may have no row today. The
    media is on this disk and the movement has no words for it; that is the whole
    case for transcribing it, and it does not depend on a row still existing.
    Carry on with whatever seed is already beside the media from the original
    download, note "no live demand row — adopted from the ledger" on the row, and
    let Stage 7.1 fall back to the old seed exactly as it was designed to. Dropping
    these would make STAGE 1D silently useless on precisely the oldest and most
    neglected part of the backlog.


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
  * A download that fails: log the reason in {RUN_LOG}, mark the row [FAIL ], and
    move to the next video. One bad URL never stops a run.
    THERE IS NOTHING TO DELETE. Stage 3 wrote nothing into {ROOT_DIR}, so a failed
    download leaves the repo exactly as it found it. If you find yourself about to
    remove a path under {TRANSCRIPTIONS_ROOT} here, STOP — that path was not made
    by this run, and Stage 7.4's guard applies.

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

  * ⚠️ THE APP MUST OUTLIVE THE THING THAT STARTED IT, AND AN AUTOMATED RUN IS THE
    ONE CONTEXT WHERE IT WILL NOT. `just run` returns as soon as the services are
    up, but the processes it leaves behind belong to the STARTING SHELL's process
    group. When this prompt is driven by an agent or a script, that group is torn
    down at the end of the step that ran the command, and every service in it gets
    SIGTERM — minutes later, silently, with nothing in the app's own log but a
    successful boot followed by no more lines.
    MEASURED, 2026-09-10: fifteen short videos finished, then the app went away and
    the five LONGEST videos in the batch all failed with the identical
    `ECONNREFUSED 127.0.0.1:9333`. Two restarts from inside the run were killed the
    same way, each within a minute or two. Nothing about the videos was wrong; two
    hours of downloaded audio simply had nowhere to go.
    THE TELL is a batch whose failures are sorted by duration — the short ones pass,
    the long ones do not — with one identical connection error and no CLI stderr
    beyond it. That is not a hard video and it is not a model problem.
    THE FIX IS TO START IT SOMEWHERE THAT STAYS UP: the citizen's own terminal, or
    the agent's persistent background facility if it genuinely survives across
    steps. In Claude Code the citizen types

        ! cd {WTC_REPO} && just run

    which runs in the session's own shell rather than a step's. Confirm :9333 is
    still answering IMMEDIATELY BEFORE Stage 6 and again if any job returns
    ECONNREFUSED — and if it has gone, say so and stop rather than retrying, because
    every retry against a dead app burns the media's turn in the batch for nothing.

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

6.1b CLAIM THE VIDEO IN THE LEDGER — BEFORE THE WORK, NOT AFTER

        THE LEDGER IS WRITTEN AND FLUSHED TO DISK BEFORE THE TRANSCRIBER IS
        CALLED. NOT AFTER, NOT ALONGSIDE, NOT AT THE END OF THE BATCH.

This ordering is the entire mechanism, and getting it backwards makes the ledger
worse than useless. A transcription can hang forever, be cancelled by the citizen,
or die with the machine, and in every one of those cases NOTHING RUNS AFTER IT.
A ledger updated after the work therefore records only the successes, which is
precisely the population that needs no record — the failures, the ones the next run
must find, leave no trace at all. Write first and a crash leaves a `started` row
with a timestamp, which is exactly the evidence 1C.3 turns back into work.

For each video, immediately before its transcriber call:

  * Take {IN_PROGRESS_LOCK}. Re-read the ledger — between selection and now,
    another run may have claimed this video, and the answer decides whether this
    run may touch it at all.
  * IF the row is now `started` within {STALE_CLAIM_HOURS} and it is not this
    run's own claim: ANOTHER RUN GOT THERE FIRST. Release the lock, print nothing,
    log it, drop the video from this run's batch, and move to the next. Do not
    transcribe it. This is the race the lock cannot prevent and the re-read can.
  * OTHERWISE claim it, in one write:
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
  * Write atomically, release the lock, and only then call the transcriber.

`tries` IS INCREMENTED HERE AND NOT ON FAILURE. A video that hangs forever never
reaches a failure handler, so a counter that increments on failure never counts the
worst case and the video is retried indefinitely. Counting attempts STARTED is the
only count that cannot be lost. It does mean a run killed between the claim and the
first decode burns a try — that is the correct trade, and it is why the cap is 3
rather than 1.

`last_tried_at` CARRIES THE PREVIOUS ATTEMPT so a human reading the ledger can see
how old the trouble is: `started_at` is always this attempt, `last_tried_at` is the
one before it, and `earliest_attempt_at` never moves once set. Three columns because
they answer three different questions, and collapsing any two of them loses the
ability to tell "tried once, long ago" from "tried three times, just now".

6.2 THE COMMAND — --out IS A STAGING DIRECTORY, NOT THE REPO

For each video, one call. Every path is ABSOLUTE — `just citizens` changes directory
before it runs, so a relative --out lands somewhere nobody asked for. The input is
MEDIA_FILE as resolved in Stage 2.3 or Stage 4, which may be under EITHER media root;
it is never assumed to be under {VIDEO_DOWNLOAD_ROOT}.

STAGE_DIR is {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/out/
  * Outside every repo, beside the media and the Stage 3.2 seed.
  * `mkdir -p` it before the call.

        {CITIZENS_CLI} transcribe "{MEDIA_FILE}" \
          --create \
          --local \
          --out "{STAGE_DIR}" \
          --name "{video_key}" \
          --also rttm,ctm \
          --media-url "https://www.youtube.com/watch?v={youtube_id}"

DO NOT POINT --out AT {TRANSCRIPTIONS_ROOT}. It used to, and that is a second way
into the same failure Stage 3 describes: a job takes minutes to hours, and for that
whole window a half-written directory sits inside the repo where the auto-committer
can reach it. Nine files appearing one at a time is exactly the partial state the
scanner cannot distinguish from a finished one.

Staging outside costs one `mv` in Stage 7.1 — both paths are on the same volume, so
it is a rename, not a copy — and buys the invariant that a directory under
{TRANSCRIPTIONS_ROOT} always holds a finished transcript.

Add --title "<title>" and --recorded <ISO date> when Stage 4.6 resolved them. Omit
either flag entirely when it did not — an absent value is printed as absent, and
that is the correct record.

What each flag is doing, because omitting one silently changes the result:

  * --create      LOCATE is the default. Without --create nothing is transcribed and
                  the command just prints where a transcript WOULD be.
  * --local       THE HARD RULE. Without it this is a production call.
  * --out         writes the COMPLETE FILE SET into STAGE_DIR, derived from the
                  sidecar this run produced. Nothing is re-decoded. Stage 7.1 moves
                  it into the repo once it is complete; a failed run leaves it here,
                  outside every repo, for debugging.
  * --name        the base name for those files. Without it the media file's stem is
                  used — which is right only when Stage 4.3 renamed the media to the
                  video key, and is WRONG for legacy media whose stem may differ.
                  Pass it always; it is the frozen key and it should be stated.
  * --also rttm,ctm   adds the two evaluation formats. They are what let an outsider
                  compute DER against our diarization and WER against our words.
  * --media-url   index data only. It is NEVER fetched. The CLI does not download.

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

DO NOT pass --person / --video unless the citizen explicitly asks. Those flags file
the result under a person AND MIRROR IT INTO THE SHARED DATA REPO — a write this
prompt's hard rules forbid. Without them the run produces a hash-keyed adhoc
transcript in the app's state root PLUS the full file set in STAGE_DIR. The copy
Stage 7.1 moves into the repo is the deliverable; the manifest in Stage 8 is what
makes it visible.

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

  * {video_key}.transcription exists in STAGE_DIR and is non-empty.
  * {video_key}.segments.json exists and parses.
  * The CLI exited 0.

These are checked in STAGE_DIR, before anything moves. That ordering is the point:
the verdict is reached entirely outside the repo, so a FAILURE never has to be
undone inside it.

Anything else is a FAILURE. In particular, the CLI writes the words and NAMES the
absent derivations when the sidecar is missing — a directory with a .transcription
and nothing else is a real, reported state, and it is a FAILURE for this prompt's
purposes because a transcript with no timings cannot be cited.

6.5 RELEASE THE CLAIM — EVERY PATH OUT OF 6.4 WRITES THE LEDGER

A claim taken in 6.1b is released here, and BOTH verdicts write. Under
{IN_PROGRESS_LOCK}, re-read, update this row only, write atomically, release:

  PASSED   status `finished`, `finished_at` now, `words` the word count, `note`
           emptied. Write this AFTER Stage 7.1 has moved the files into the repo,
           not before — `finished` in this ledger means "the words are in the
           repo", and a row that claims it before the move is a lie for however
           long the move takes.
  FAILED   status `failed`, `finished_at` now (the attempt ended, even badly),
           `note` the reason from 6.4 — which check failed, the CLI's exit code,
           the head of its stderr. `tries` is NOT touched; 6.1b already counted it.

WHAT A CANCELLED RUN LOOKS LIKE, AND WHY THAT IS FINE: neither branch runs, so the
row stays `started` with this run's `started_at`. For {STALE_CLAIM_HOURS} every
other run treats it as live work and leaves it alone; after that 1C.3 converts it
to `failed` with `claim expired` and it becomes adoptable. That is the design
working, not a leak — and it is why no cleanup handler is specified here. A prompt
cannot rely on running code after being killed, so the recovery lives in the NEXT
run's reconciliation rather than in this run's good intentions.

IF THE ROW REACHED {MAX_TRANSCRIBE_TRIES} ON THIS FAILURE, say so in the note
(`reached the try cap`) and name it in Stage 10 with Z51. It will not be attempted
again until a human either fixes the cause or lifts the cap, and a video quietly
falling out of the queue is exactly what this ledger exists to prevent.


====================================================================
STAGE 7 — PUT THE RESULT IN THE REPO, OR LEAVE IT OUTSIDE
====================================================================

7.1 ON SUCCESS — CREATE THE DIRECTORY AND WRITE transcription.yaml

THIS IS THE FIRST AND ONLY MOMENT ANYTHING ENTERS {TRANSCRIPTIONS_ROOT}. The words
now exist, so the record has earned its place in the repo. Create
{TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/, move all nine files from STAGE_DIR
into it, and write the sidecar — in that order, in one go, only after Stage 6.4's
checks passed. A directory that exists under {TRANSCRIPTIONS_ROOT} always holds a
real transcript; there is no window in which a partial one is visible to the
auto-committer.

Move, do not copy. Both paths are under $HOME on one volume, so it is a rename: the
nine files appear together rather than growing one at a time inside the repo.

RUN THE TOOL. Do not hand-roll a writer and do not improvise one in a scratch
directory:

        python3 {SIDECAR_TOOL} write {roster_key}/{video_key} [...]

The tool creates the directory itself, reads the demand row by video_uid, falls
back to Stage 3.2's seed when the CSV has moved on, and carries forward every
hand-written field already in the file.

A row selected from {QUEUE_SUPPLEMENT_CSV} needs --demand-csv {QUEUE_SUPPLEMENT_CSV}
here too, for the same reason as Stage 3.2. The sidecar's Demand block then carries
run_id "{THE_DATE_TIME_STRING}local_supplement" and the notes cell naming this
prompt, which is how a later reader tells a provisional row from an engine-priced
one without having to reconstruct anything.

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

7.4 ON FAILURE — THE REPO WAS NEVER TOUCHED, SO LEAVE IT THAT WAY

A failed transcription leaves NOTHING behind in {ROOT_DIR}, and since Stage 3 the
way it achieves that is BY NOT HAVING WRITTEN ANYTHING, not by deleting.

  * LEAVE STAGE_DIR WHERE IT IS. Whatever the CLI managed to write is already
    outside every repo, beside the seed from Stage 3.2 and the media it came from,
    so the evidence survives for debugging and nothing partial is ever committed.
    There is nothing to move and nothing to remove.
    If MEDIA_FILE is under {VIDEO_DOWNLOAD_ROOT_LEGACY}, which this prompt never
    writes to, STAGE_DIR is under {VIDEO_DOWNLOAD_ROOT}/{roster_key}/{video_key}/
    anyway — say where the media actually is in the FAILED file.
  * Write a {video_key}.FAILED.txt beside them: the command that was run verbatim,
    the CLI's exit code, its stderr, which of Stage 6.4's checks failed, and the
    timestamp.
  * Mark the row [FAIL ] and append the reason to {RUN_LOG}.
  * Do NOT retry automatically. A silent retry loop burns an hour of CPU against a
    cause that has not changed.

7.4a THE DELETION GUARD — READ THIS BEFORE REMOVING ANY PATH UNDER {ROOT_DIR}

This prompt has exactly one legitimate reason to remove a path under
{TRANSCRIPTIONS_ROOT}, and it is Stage 7.4b. Everywhere else, deleting there is a
bug. It has already cost this repo fifteen committed sidecars once (Stage 3's
preamble has the sequence), and the failure mode is nasty because every individual
step looked right.

BEFORE removing anything under {ROOT_DIR}, run BOTH checks and pass BOTH:

  1. GIT DOES NOT KNOW ABOUT IT.

        git -C {ROOT_DIR} ls-files --error-unmatch -- "<path>"

     Exit 0 means git TRACKS it. A tracked file is committed work — someone else's,
     or an earlier run's, or a mid-run auto-commit's. STOP. Do not remove it, do not
     `git rm` it, do not "tidy" it. Print Z22, leave it exactly where it is, and say
     so in Stage 10. Removing it does not undo the commit; it adds a deletion on top
     of it, which is what the history shows for 2026-09-07.

  2. THERE ARE NO WORDS IN IT.

        find "<path>" -name "*.transcription"

     Any hit means a transcript lives there. Those are the words this whole pipeline
     exists to produce and they are never collateral. STOP, and print Z22.

Neither check needs judgement and both are one command. Run them.

7.4b THE ONE PERMITTED CLEANUP — A STRANDED SEED-ONLY DIRECTORY

An older run of this prompt, before Stage 3 was fixed, could leave
{TRANSCRIPTIONS_ROOT}/{roster_key}/{video_key}/ holding a stub transcription.yaml
and NOTHING ELSE. It is invisible to Stage 2.3's skip test, which looks for
{video_key}.transcription, so it is re-selected and re-stranded on every run.

Such a directory may be cleared ONLY when ALL of these hold:

  * it contains no {video_key}.transcription and no other output file — the only
    thing in it is transcription.yaml
  * that transcription.yaml has no Media.SHA256 and no Source block, i.e. it is a
    seed and not a real record
  * `git ls-files` shows it as UNTRACKED

If git tracks it, it is committed history: leave it, name it in the Stage 10
report, and let the citizen decide. This prompt does not delete a citizen's
committed files to make its own bookkeeping tidy.


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
"Bryan 26 Tower"). It knows nothing about this prompt's rules and it will commit
whatever it finds, mid-run, at any moment. Nothing in this prompt can prevent it.

SO THE DEFENCE IS NOT TO TRY. It is to make sure there is never anything partial
for it to find: Stage 3 writes nothing into {ROOT_DIR}, and Stage 7.1 creates the
directory and the sidecar together only once the words exist. An auto-commit that
lands between two videos therefore captures completed transcripts and nothing else,
which is a harmless early commit rather than a published partial.

That defence is the whole reason Stage 3 works the way it does. Two earlier runs
show what happens without it: one committed 189 files at 09:04:44 while
transcriptions were still running, capturing directories whose sidecars had not
been written; the next (901615a) committed fifteen stub sidecars that Stage 7.4
then deleted. If a future edit ever moves the seed back into {TRANSCRIPTIONS_ROOT},
both failures return together.

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
  * THE BACKLOG, ALWAYS, even when it was empty and even when nothing was adopted:
    how many downloaded-but-untranscribed videos this machine holds, how many this
    run adopted and finished, how many were left because another run has them
    claimed, how many are capped out at {MAX_TRANSCRIBE_TRIES} (Z51), and how many
    are new backlog created by THIS run's own failures. A citizen who is told
    "20 transcribed" while 40 un-transcribed downloads sit on the disk has been
    told the least useful true thing available.
  * EVERY LEDGER CORRECTION Stage 1C made, by video_uid and reason. A row that said
    `finished` with no transcript behind it means an earlier run reported success it
    did not achieve, and that is worth a human's attention.
  * any row whose media would not open in ffprobe (Stage 1D.3), by path — those are
    probably truncated downloads and only the citizen should decide to delete them
  * any ledger row this run could not parse and therefore left alone
  * WHAT STAGE 1B ADDED, and what it could not: how many people it examined, how
    many it added rows for, how many had no channel on record and therefore got no
    rows, how many listed empty, and the path to the patch CSV a human can hand to
    whoever runs the demand engine. Say the queue's as-of date and run_id beside it,
    so a reader knows how stale the movement's list was on this machine.
  * how many of this run's transcripts came from SUPPLEMENT rows rather than from
    the engine's ladder, by roster_key/video_key. These are the ones nobody asked
    for yet, and a reader of the repo deserves to know which they are.
  * Z42 if the data repo was behind, since that changes what "new person" meant
  * whether {WTC_REPO} is behind and needs a pull
  * ANY DELETION THIS RUN REFUSED (Z22), by path and reason. Never leave this
    silent: a refusal means something under {ROOT_DIR} is in a state this prompt
    would not touch, and only the citizen can settle it.
  * ANY STRANDED SEED-ONLY DIRECTORY found in Stage 2.3, by roster_key/video_key,
    and whether git tracks it. Those are the residue of runs that predate Stage 3's
    fix. Say which ones Stage 7.4b cleared and which were left because they are
    committed.
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

THE COLUMNS ARE APPEND-ONLY AND ARE LOOKED UP BY HEADER NAME, NEVER BY POSITION.
That rule is what makes appending safe, and it binds this prompt in both directions:
a newer engine may have added a 26th column that this appendix does not list, and a
reader that indexes by position reads it as the wrong field. STAGE 1B copies the
header out of the live file for exactly this reason.

    person_key                MISLABELLED. For a roster human it is the ROSTER key —
                              office-scoped, e.g. kari_lake_us_pres. For a
                              people_only human it is the PERSON key. Either way it
                              is the directory segment under {TRANSCRIPTIONS_ROOT}
                              and every media root. See TWO KEY NAMESPACES.
    video_uid                 "{column-1 key}::{video_key}" — THE KEY. Unique across
                              the corpus, and the only thing anything joins on.
                              NEVER join on the bare video_key: it is unique within
                              ONE PERSON ONLY, two different videos are both named
                              v0001 on disk today, and a video_key join matches
                              silently across two people and publishes one person's
                              recorded words under another's name.
    video_key                 THE FROZEN PRIMARY KEY of this video for this person.
                              Directory name. [A-Za-z0-9_-], 1..64. Never invented.
                              On a YouTube row it IS the 11-char YouTube id.
    youtube_id                the 11-char YouTube id. URL is
                              https://www.youtube.com/watch?v={youtube_id}
    duration_seconds          BLANK MEANS UNKNOWN, never 0
    priority                  the computed demand score, integer 0..1000. Higher is
                              wanted more. APPENDIX F is the arithmetic.
    ceiling                   the maximum this row's priority could reach
    raw                       the pre-clamp score. MAY BE NEGATIVE.
    bound_by                  ceiling | raw — which of the two produced priority
    transcripts_held          copies of THIS VIDEO's transcript the movement holds
    trusted_transcripts_held  of those, how many came from a trusted supplier
    person_transcripts_held   transcripts for THIS PERSON across every video — the
                              damper's input, and a different fact from the above
    seat_rank                 office_importance_rank for the seat this person holds
                              or seeks. BLANK IS AN ABSENCE, NOT A ZERO.
    challenger                true | false | blank. BLANK means there was no sealed
                              contenders edition to ask. Blank is not false.
    round                     which breadth-first round admitted this row. Round 1
                              for everybody comes before round 2 for anybody.
    status                    open | partial | satisfied | unobtainable | withdrawn
                              — only open/partial are worked
    closed_reason             why it is closed, when it is
    notes                     free text, human
    computed_at               ISO 8601
    run_id                    the demand engine run that produced this row. CARRY IT
                              INTO transcription.yaml — it is the join back.
    source_type               where this video lives — youtube, rumble, ipfs, x,
                              bluesky, nostr, mastodon, peertube, web and others.
                              BLANK means the record carries no address at all;
                              `web` means an address we can read and cannot place.
    source_url                an address a reader can open. NEVER an IPFS gateway —
                              ipfs://<cid> is the address and a gateway is one
                              mirror's opinion of where to find it.
    ipfs_cid                  the canonical CID, and only for an IPFS address. Blank
                              on almost every row, by design.
    source_ref                the platform-native unique id, normalized. On YouTube
                              it is the same string as video_key.
    subject_kind              WHICH STORE THIS HUMAN IS KNOWN FROM — new_politician |
                              legacy_politician | worrisome_challenger |
                              fix_bill_author | people_only. A fact about the
                              movement's FILING, never a judgement of the person and
                              never an input to any award. Blank on a row written
                              before 2026-09-09, and blank is what an unrecognised
                              value reads back as. BLANK IS NEVER people_only —
                              they are opposite facts.

{VIDEO_DEMAND_YAML} is the run record for the same generation: schema_version,
run_id, generated_at, engine_version, universe counts, rows_open / rows_partial /
rows_satisfied, a `gaps:` list stating what the engine could NOT determine, and
csv_sha256 for verifying the CSV.

READ THE GAPS LIST. It is not decoration — it is the engine saying, in its own
voice, which people it could not price and why. The sentence that begins "N
person(s) entered the eligible universe from data_we_citizens/people/" is the exact
population STAGE 1B exists to serve, and its remedy is stated there as a SOURCING
gap that re-running the engine cannot move.

{QUEUE_SUPPLEMENT_CSV} carries THE SAME COLUMNS, written by STAGE 1B, for people the
engine has not priced. Its rows are provisional and every one of them says so.


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

CARRY THE WHOLE DEMAND ROW, NOT A SELECTION FROM IT. Every column in APPENDIX B
gets a home here. {VIDEO_DEMAND_CSV} is REGENERATED on every engine run: today's
priority, transcripts_held and status are overwritten by tomorrow's, and the values
that were true WHEN THIS TRANSCRIPT WAS MADE then exist nowhere on earth. This block
is the only record of why this video was worked on, and a column dropped from it is
a fact destroyed, not a fact stored elsewhere.

ABSENT IS ABSENT APPLIES HARDEST HERE. A blank cell is OMITTED. seat_rank is the one
that bites — APPENDIX B says "BLANK IS AN ABSENCE, NOT A ZERO", and a 0 written into
this block reads to every later reader as "the least important seat there is".

A COLUMN THE ENGINE ADDS LATER is carried through under its own name rather than
dropped. {SIDECAR_TOOL} does this automatically; it is written down here so a reader
of the appendix knows the block is not a fixed list.

THE JOIN KEY IS video_uid, NEVER video_key. The demand engine issues placeholder
keys — v0001, v0002 — one per person, so `v0001` appears against dozens of different
roster_keys, each with a DIFFERENT youtube_id. Matching a demand row on a bare
video_key returns whichever person sorted first and attaches their video's URL to
this person's transcript, in Video.URL, which is one of the four fields the product
actually reads. {SIDECAR_TOOL} joins on video_uid; anything else that reads this CSV
must too. The data repo states the same rule in
{DATA_REPO}/prompts/p_transcriptions_speakers_to_people.md.


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
APPENDIX F — THE DEMAND ARITHMETIC, FOR STAGE 1B ONLY
====================================================================

NORMATIVE SOURCE, and this appendix is a transcription of it rather than a second
opinion: we_the_citizens/pm/calc_engine_video_demand.mdx §3, implemented in
code/packages/shared/src/video_demand.ts as videoDemandTerms() /
computeVideoDemand(). If the two ever disagree, THE SPEC WINS and this appendix is
wrong. Re-read it before trusting these numbers on a machine that has {WTC_REPO}.

Every term is an INTEGER. There is no floating-point arithmetic anywhere in this
engine and therefore nothing to round.

THE CEILING — per VIDEO

    steps   = transcripts_held + trusted_transcripts_held
    ceiling = max(0, 1000 - 200 * steps)

For a video nobody holds words for, steps is 0 and the ceiling is 1000. It exists to
pull a video DOWN once we have heard it, so on a new person's rows it is inert.

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

The floor is not a third binder. bound_by has two values and raw prints the true sum
even when it is negative — that is how the floor stays legible to a reader adding
the terms up by hand.

FOUR RULES THAT ARE EASIER TO GET WRONG THAN THE SUM ITSELF

  * THE -300 KEYS ON subject_kind, NEVER ON AN UNRESOLVED SEAT. A roster human whose
    office this run could not price gets the term "seat rank / points 0 / cause seat
    unknown" and NO PENALTY. Nine thousand rows on the live ladder carry a blank
    seat_rank because the movement failed to resolve THEIR OFFICE; that is a gap in
    our records, and pricing our own sourcing failure as their unimportance would
    demote thousands of named living people, silently, and every row would render
    perfectly.

  * BLANK IS AN ABSENCE IN BOTH DIRECTIONS. seat_rank is written blank whenever the
    seat term carried a cause, and never as 0. challenger is blank when no sealed
    slate exists to ask — blank is not false. duration_seconds is blank when unknown
    — blank is not 0.

  * THE TWO TRANSCRIPT COUNTS ARE TWO DIFFERENT FACTS. transcripts_held is per
    VIDEO and feeds the ceiling; person_transcripts_held is per PERSON and feeds the
    damper. Collapsing them gives everybody with a large corpus a ceiling of 0 and
    buries every one of their videos at priority 0 — which renders perfectly,
    because 0 is a legal priority.

  * THE LONG-FORM TERM IS DEAD AND SAYS SO. duration_seconds is blank on essentially
    every row because the videos.list queue kind is declared and not implemented, so
    the >2400 test can never be true. The term is emitted with points 0 and the
    cause "duration unknown — videos.list not implemented" rather than omitted: a
    sum that adds up perfectly while quietly asserting "we considered length and it
    did not matter" is a small lie a reader cannot catch. If yt-dlp DID print a real
    duration in 1B.5, the term fires normally — that is the term waking up, not a
    deviation.

THE OFFICE LADDER — office_importance_rank, read at run time from the newest
{DATA_REPO}/scores/new_politician_qualified/npq_*.yaml. Today it reads:

    president 100, governor 80, speaker_house 74, speaker_senate 72,
    senator 65, us_house 50, mayor 40, state_assembly 30

RESOLVING A SEAT IS TOTAL AND HAS NO ?? 0 FALLBACK. Two spellings are accepted
because they name the same office: the seat-kind vocabulary (president, governor,
us_senate, us_house, state_assembly) translated through

    us_senate -> senator

and then the rank map's own vocabulary (senator, mayor, speaker_house,
speaker_senate). Anything else produces a NAMED term — points 0, cause
"unknown office <x> — not in office_importance_rank" — and a BLANK seat_rank.
us_senate and senator being two spellings of one office is the trap: a ?? 0 fallback
there publishes "a United States Senate seat does not matter", silently, and nothing
fails.

For a Stage 1B candidate the office comes from, in order:
  1. {DATA_REPO}/contenders/slate.yaml — the assignment's seat_kind, if the key is
     on the sealed slate. This is the most reliable, because it is already in the
     seat-kind vocabulary.
  2. {ROSTER_DIR}/{roster_key}/{roster_key}.yaml — its office and level fields.
     These are FREE TEXT written for humans ("Candidate for Governor", level:
     state). Map them only where the reading is unambiguous; where it is not, do not
     guess — an unresolved seat costs no penalty (rule 1 above), while a wrong one
     reprices a human against the whole ladder.
  3. Nothing else. A people_only candidate has no seat by definition and takes the
     -300 term with the cause "no candidacy on file — known from people/ only".

THE FOUR BANDS, TO THE DIGIT — never-heard rows, ceiling inert:

    president        200 + 300 + 200  =  700
    governor         200 + 240 + 200  =  640
    senator          200 + 195 + 200  =  595
    US House         200 + 150 + 200  =  550
    state assembly   200 +  90 + 200  =  490
    people_only      200 + 200 - 300  =  100

Add +150 to any of them for a live challenger on the sealed slate. A people_only
human this repo already holds words for prices below zero and publishes 0 — which is
LOW, not excluded: round 1 for everybody comes before round 2 for anybody, so their
first videos still sort above every round-2 row on the ladder including the
president's. A supplement row must never be dropped for having priority 0.


====================================================================
APPENDIX G — {IN_PROGRESS_CSV} SCHEMA
====================================================================

One row per {video_uid}. Machine-local, outside every repo, never committed. Read
and written by STAGE 1C, 1D, 6.1b and 6.5, and shared by every run on this machine.

COLUMNS ARE APPEND-ONLY AND ARE LOOKED UP BY HEADER NAME, NEVER BY POSITION. A
newer version of this prompt may add a column, and a reader that indexes by
position reads it as the wrong field. A writer that meets a column it does not know
CARRIES IT THROUGH UNCHANGED rather than dropping it.

    video_uid                 "{roster_key}::{video_key}" — THE KEY, and the only
                              thing anything joins on. NEVER the bare video_key:
                              the demand engine issues placeholder keys like v0001
                              once per person, so a bare key matches across two
                              people and would let one person's failure claim
                              another person's video.
    roster_key                the demand CSV's first column, verbatim
    video_key                 the frozen per-person key, verbatim
    media_file                ABSOLUTE path to the file that will be handed to the
                              transcriber. May be under either media root. Empty
                              when the media is gone.
    status                    pending | started | finished | failed | media_gone
                              * pending     media on disk, never attempted
                              * started     an attempt is IN FLIGHT. Believed for
                                            {STALE_CLAIM_HOURS} from started_at,
                                            then treated as dead by 1C.3.
                              * finished    THE WORDS ARE IN THE REPO. Not "the
                                            transcriber exited 0" — Stage 6.5
                                            writes this only after Stage 7.1 moved
                                            the files in.
                              * failed      an attempt ended without words
                              * media_gone  the row's media is no longer on disk
                                            and there are no words either
    tries                     integer, incremented in 6.1b BEFORE the transcriber
                              is called. It counts attempts STARTED, not attempts
                              that reached a verdict — a hung or killed attempt
                              never reaches one, and a counter that misses those is
                              a counter that lets a bad video be retried forever.
    earliest_attempt_at       ISO 8601. The FIRST time this video was ever
                              attempted on this machine. WRITE ONCE AND NEVER
                              AGAIN. It is how a reader sees that something has
                              been stuck for three weeks rather than three minutes.
    started_at                ISO 8601. THIS attempt's start, stamped in 6.1b.
                              Overwritten on every attempt. The
                              {STALE_CLAIM_HOURS} test reads this and nothing else.
    last_tried_at             ISO 8601. The value started_at held BEFORE this
                              attempt — the previous try, kept so the age of the
                              trouble is visible without a history table. Empty on
                              a first attempt.
    finished_at              ISO 8601. When the attempt ENDED, on success or
                              failure. Emptied by 6.1b when a new attempt starts,
                              so a `started` row never carries a stale end time.
    words                     word count on success. Empty otherwise. Never 0 as a
                              placeholder — 0 is a measurement.
    host                      "{hostname}:{pid}" of the run holding or last holding
                              the row. It is what tells a citizen with two windows
                              open WHICH window is working a video.
    run_id                    {THE_DATE_TIME_STRING} of the run that last wrote
                              this row, so a row can be traced to a {RUN_LOG}.
    note                      free text, human. The last failure's reason, the
                              ledger correction that was applied, "reached the try
                              cap", the contents of a {video_key}.FAILED.txt. This
                              is the column a human actually reads.

WRITING RULES, AND EVERY ONE OF THEM EXISTS BECAUSE SEVERAL RUNS SHARE THE FILE:

  * Every write is TAKE LOCK -> RE-READ -> MERGE BY video_uid -> ATOMIC WRITE ->
    RELEASE. The re-read is not optional: the copy in memory is stale the moment
    the lock is released, and merging a stale copy silently reverts another run's
    claim.
  * The lock is held for the read-modify-write ONLY — milliseconds. NEVER across a
    download or a transcription.
  * A row this run does not own is written back BYTE FOR BYTE. Not reformatted, not
    re-quoted, not re-timestamped.
  * NEVER TRUNCATE THE FILE. NEVER DELETE A ROW. A `finished` row costs one line
    and records that the work was done; a deleted row costs a re-download and a
    re-transcription of something this machine already holds. Pruning is a human's
    decision.
  * ABSENT IS ABSENT: an unknown timestamp is an EMPTY CELL, never a zero and never
    today's date. A zero-epoch `started_at` reads as a claim from 1970 and makes
    every stale-claim test true.

WHAT THIS FILE IS NOT. It is not evidence, it is not part of the corpus, and
nothing in the product reads it. It is one machine's operational memory of which
attempts happened, and its only job is to make sure a downloaded video is never
forgotten.


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

  a ledger row is `started` by THIS host and pid, from an earlier run
    * The previous run with this pid is gone (pids are reused, but not by a live
      run of this prompt). Treat it exactly like any other claim: believed for
      {STALE_CLAIM_HOURS}, then adoptable. Do not special-case "it looks like me".

  {IN_PROGRESS_LOCK} exists and is younger than 60 seconds
    * Another run is mid-write. Wait briefly and retry — a few hundred milliseconds
      is enough, because the lock is only ever held around one file write. If it is
      still there after ~10 seconds, treat it as stale, break it, and log that.

  the ledger has a row whose roster_key/video_key is not in {VIDEO_DEMAND_CSV}
    * Normal, not an error: the engine regenerates that file and rows leave it. The
      media and the words are what matter. Work it if it has media and no words,
      and do not attempt to re-derive a demand row that no longer exists — Stage
      3.2's seed beside the media is the fallback and it says what the row said.

  yt-dlp says "video unavailable", is geo-blocked, or is members-only
    * Skip it. Log it. It is a fact about the video, not a fault in the run. Do not
      try to route around it, and never attempt a paywall or a login.

  `citizens` exits 69
    * The CLI is not built. Build it (Stage 5.3) and continue. No banner needed.

  STAGE_DIR has a .transcription and nothing else
    * The sidecar was missing, so nothing could be derived. This is a real state the
      CLI reports, and for this prompt it is a FAILURE — Stage 7.4 applies. Do not
      commit words that cannot be cited.

  A selected row's media is on disk but will not open in ffprobe
    * Treat it as a failed download: mark [FAIL ], log it, do not delete the file.
      A truncated file from an earlier interrupted run is the usual cause, and the
      citizen may want it removed by hand rather than by this prompt.
