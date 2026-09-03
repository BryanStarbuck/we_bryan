# we_bryan — Bryan's We The Citizens User Data Repo

ROOT_DIR dir is ~/BGit/Bryan_git/we_bryan

TEMPLATE_REPO dir is ~/BGit/act3/template_user_repo_we_citizens
TEMPLATE_REPO_URL is https://github.com/ACT3ai/template_user_repo_we_citizens.git

THIS_REPO_URL is https://github.com/BryanStarbuck/we_bryan.git

CONFIG_FILE is file ~/.config/we_citizens/config.yaml


====================================================================
WHAT THIS REPO IS
====================================================================

* {ROOT_DIR} is Bryan's own clone of the We The Citizens User Data Repo.
* It is ONE user's User Data Repo. Every citizen gets their own.
* The thing it is cloned from is {TEMPLATE_REPO} — the template repo that
  citizens copy to create their own User Data Directory.
* The template holds the general structure: a number of directories that get
  created but are often empty. Content lands in them per-citizen, here.
* These two repos pair up. {TEMPLATE_REPO} is the shape; {ROOT_DIR} is Bryan's
  instance of that shape with his real data in it.


====================================================================
KEEPING UP WITH THE TEMPLATE
====================================================================

* {TEMPLATE_REPO} advances over time — new directories, new structure, new
  conventions. When it does, we pull those advances down into {ROOT_DIR}.
* The flow is one-directional for structure: template -> user repo.
  * Structure (directories, .gitkeep files, layout, conventions) comes DOWN
    from the template into this repo.
  * Bryan's actual citizen data stays HERE and is never pushed back up to the
    template. Never put personal data into {TEMPLATE_REPO}.
* When asked to update this repo from the template:
  * Read {TEMPLATE_REPO} structure and compare against {ROOT_DIR}.
  * Add any new directories and files that are missing here.
  * Do NOT delete anything here that the template no longer has, unless
    explicitly told to. This repo holds real data the template does not know
    about.
* Never modify {TEMPLATE_REPO} while working in this repo. It is read-only
  reference from here, unless the user explicitly says to edit the template.


====================================================================
HOW THE WEB APP FINDS THIS REPO — {CONFIG_FILE}
====================================================================

* A citizen may pull down the full open-source We The Citizens web app and run
  it on their own computer. That web app then needs to go find the local user's
  data repo on that machine.
* It finds it through {CONFIG_FILE}. That YAML file stores ONE value: the full
  path to the user's User Data Repo directory.
* On this machine that value is the path to this directory: {ROOT_DIR}.

Format:

    # ~/.config/we_citizens/config.yaml
    user_repo_path: /Users/bryan/BGit/Bryan_git/we_bryan

Rules:

* The path is stored ABSOLUTE and fully expanded — no "~", no relative paths.
  Another process reading this file may have a different working directory or
  a different HOME.
* {CONFIG_FILE} lives OUTSIDE any repo, in the user's XDG config directory. It
  is machine-local, never checked in, and never synced. Each of the user's
  computers has its own copy pointing at wherever the clone lives there.
* If the web app cannot find {CONFIG_FILE}, or the path in it does not exist,
  the app should ask the citizen where their User Data Repo is and then WRITE
  that answer back into {CONFIG_FILE}. Creating the file is the app's job on
  first run; it is not shipped with the app.
* Create ~/.config/we_citizens/ if it does not exist.


====================================================================
GIT BEHAVIOR — EMPTY DIRECTORIES MUST SURVIVE
====================================================================

Git does not track directories, only files. An empty directory will silently
vanish on push and will NOT come back on clone. That breaks the whole point of
a template that hands citizens a ready-made structure.

* Every directory that is meant to exist but is currently empty MUST contain a
  .gitkeep file so the directory reaches the git server and comes back down on
  `git clone`.
* When creating any new directory in this repo or in the template, create its
  .gitkeep in the same step. Do not leave it for later.
* Do not let .gitignore rules exclude .gitkeep. If a broad ignore pattern
  covers a directory, add a negation so .gitkeep still gets tracked:

      some_dir/*
      !some_dir/.gitkeep

* Before committing structural work, verify it: every directory under
  {ROOT_DIR} either has tracked content or has a tracked .gitkeep.


====================================================================
GIT BRANCH RULES
====================================================================

* NEVER create, switch, or push git branches. Work on the current branch.
* No `git checkout -b`, `git switch -c`, `git branch`, `git checkout <other>`,
  or `git push` unless the user explicitly asks for it.


====================================================================
CONTENT RULES
====================================================================

* Never download videos or create transcriptions in violation of any site's
  Terms of Service. Do not do that here, and do not do it in the template.
* This is a personal citizen data repo. Treat its contents as the user's own
  material — do not publish, post, or send anything from it anywhere without
  being explicitly asked.


====================================================================
RELATED
====================================================================

* We The Citizens web app: ~/BGit/Bryan_git/uplift/
  * Web UI http://localhost:4444/ · API http://localhost:9333/
  * Local-first, flat-file state under ~/T/_uplift, no database.
  * Login is OpenAuthFederated with Google, and is optional.
* Public Docusaurus site source: ~/BGit/act3/docus_we_citizens/site/docs/
* Messaging files: ~/BGit/all/politics/citizens_we/marketing/messaging/
* Orientation / fact base: ~/BGit/act3/we_citizens/KNOWLEDGE_we_citizens.md
