# GDTT — DATA TRANSFORM TOOL BY GADASH (AKILA DJ)
## Master Product, Architecture, Codex, Git/GitHub and Vibe-Coding Specification

---

# 0. MASTER INSTRUCTION

Act as a senior:

- Software Architect
- Python Developer
- Data Engineer
- Desktop UX/UI Designer
- QA Engineer
- Git/GitHub Maintainer
- Windows Packaging Engineer
- Technical Documentation Writer

Build a modular, local/offline-first application named:

# GDTT — Data Transform Tool by Gadash (Akila DJ)

The application is mainly intended for transformation, standardization, verification and averaging of environmental monitoring and other time-series datasets, including:

- Air-quality data
- Meteorological data
- Noise/acoustic data
- Other monitoring data
- Generic tabular/time-series data

The project will be developed primarily using **OpenAI Codex**, with Gadash (Akila DJ) as the
vibe coder and prompter. Attribute **Codex** and **Gadash (Akila DJ)** in suitable metadata
sections without placing creator text in persistent application chrome.

This is an iterative AI-assisted / vibe-coded project.


The first implementation is not expected to be final.

I will repeatedly ask Codex to:

- modify existing features;
- change screens;
- add calculations;
- change workflows;
- correct bugs;
- replace modules;
- add new processing modes;
- refactor specific sections;
- package new releases.

Therefore, optimize the project for **safe repeated modification**, not merely for producing a working first prototype.

---

# 1. PRODUCT PRIORITIES

Use the following priority order:

1. Ease of use / UX
2. Correctness of data transformation
3. Data integrity
4. Transparent verification
5. Reliability
6. Performance with large datasets
7. Modular maintainability
8. UI appearance
9. Extensibility

The application should make it difficult for a user to transform a dataset incorrectly without noticing.

---

# 2. LOCAL / OFFLINE REQUIREMENT

Dataset processing must occur locally.

Default requirements:

- No dataset upload to cloud services
- No cloud database requirement
- No user account requirement
- No online processing requirement
- No telemetry containing dataset contents
- Templates stored locally
- Settings stored locally
- Logs stored locally
- Temporary processing files stored locally

The application should work completely offline after installation.

Internet functionality may be introduced only later as an explicitly separate optional feature.

---

# 3. TARGET DEPLOYMENT OPTIONS

Before coding the full application, evaluate deployment approaches.

My preferred direction is Python and Windows desktop, but first compare the options.

At minimum evaluate:

## Option A - Python Source

Run using something similar to:

`python main.py`

or preferably a proper package entry point.

Advantages:

- easiest to modify;
- easiest to debug;
- ideal for Codex development.

May require Python and dependencies.

## Option B - Windows Application With Installed Runtime/Dependencies

An executable or installer where supporting dependencies may be installed.

## Option C - Fully Standalone Windows Application

A click-and-run `.exe` or installer.

The end user should not need Python or project dependencies installed separately.

## Option D - Alternative

If technically justified, compare another architecture such as:

- .NET
- local web UI
- hybrid desktop application
- another Python GUI technology

Processing must still remain local.

---

# 4. PHASE 0 TECHNOLOGY DECISION

Do not lock the project to a framework before analysis.

Compare appropriate technologies such as:

## GUI

- PySide6 / Qt
- CustomTkinter
- another mature Python desktop framework

## Data Processing

- Polars
- PyArrow
- Pandas
- DuckDB
- combinations of these where appropriate

## Spreadsheet Processing

- openpyxl
- XlsxWriter
- other suitable libraries

## Packaging

- PyInstaller
- Nuitka
- another suitable Windows packaging approach

## Date/Time

Use reliable timezone-aware libraries and the standard IANA timezone database where applicable.

Recommend the most suitable architecture for:

- Windows
- large files
- modern GUI
- virtualized tables
- offline operation
- maintainability
- standalone packaging
- Codex-based repeated modification.

Document the final decision in:

`About-Info/AI-Handoff/DECISIONS.md`

---

# 5. CODEX-FIRST PROJECT DESIGN

This repository must be easy for a new Codex session to understand.

Create a short root:

`AGENTS.md`

AGENTS.md must function primarily as a **navigation map and development rulebook**, not as a giant duplicate of this entire specification.

It should tell Codex:

- what the project does;
- where important code lives;
- where detailed requirements live;
- what files must be read before modifications;
- exact build/run/test/lint commands;
- architectural boundaries;
- files that must not be modified casually;
- how to update documentation;
- definition of done;
- Git safety requirements.

Keep AGENTS.md concise enough to remain useful as working context.

Detailed knowledge belongs under:

`About-Info/`

Optional nested `AGENTS.md` files may later be added inside major folders such as:

- `core/`
- `ui/`
- `tests/`

only if those areas genuinely require specialized instructions.

Do not create unnecessary instruction files.

---

# 6. REQUIRED CODEX START-OF-TASK PROCEDURE

For any non-trivial future Codex task:

1. Read root `AGENTS.md`.
2. Read:
   - `About-Info/AI-Handoff/CURRENT_STATE.md`
   - `NEXT_STEPS.md`
   - `DECISIONS.md`
   - `KNOWN_ISSUES.md`
3. Read the relevant feature/design documentation.
4. Inspect the existing implementation.
5. Inspect relevant tests.
6. Identify the smallest affected module set.
7. Make a plan for the requested change.
8. Modify only what is reasonably necessary.
9. Run relevant tests.
10. Run regression tests appropriate to the change.
11. Update documentation.
12. Update AI handoff/state information.

Never assume that chat history contains the source of truth.

The repository is the source of truth.

---

# 7. VIBE-CODING SUPPORT SYSTEM

Create a dedicated guide:

`About-Info/Vibe-Coding/CODEX_VIBE_CODING_GUIDE.md`

It must explain how I should work with Codex on this project.

Include:

## A. Small Change Prompt Pattern

Example:

`Read AGENTS.md and the current handoff documentation. Modify only the date-format selector so that ISO formats appear before regional formats. Preserve existing parsing behavior. Add/update tests and update CURRENT_STATE.md and CHANGELOG.md.`

## B. Bug-Fix Prompt Pattern

Example:

`Investigate this bug before changing code. Identify the responsible module, reproduce it with a test, fix the smallest responsible component, run regression tests, and document the fix.`

## C. New Feature Prompt Pattern

Example:

`Add a new aggregation strategy. Do not place the calculation directly in the UI. Implement it through the aggregation strategy/registry architecture, expose it through the UI, add tests and documentation.`

## D. UI-Only Modification Pattern

## E. Transformation Engine Modification Pattern

## F. Averaging Modification Pattern

## G. File Import Modification Pattern

## H. Export Modification Pattern

## I. Refactoring Pattern

## J. Performance Optimization Pattern

## K. Packaging/Release Pattern

## L. Resume Interrupted Work Pattern

---

# 8. AI CREDIT / CONTEXT LIMIT SUPPORT

The project must remain recoverable if Codex stops because of:

- usage limits;
- context limits;
- interrupted session;
- application/browser closing;
- manual stopping;
- failed tool execution.

For this reason, use small logical checkpoints.

Before starting a long/risky modification:

- identify the intended scope;
- avoid leaving a broad half-completed refactor;
- preserve a runnable state whenever practical.

At the end of each meaningful session update:

`About-Info/AI-Handoff/CURRENT_STATE.md`

with:

- what currently works;
- what was modified;
- what remains unfinished;
- latest test status;
- known failures;
- exact next step.

Also maintain:

`NEXT_STEPS.md`

`DECISIONS.md`

`KNOWN_ISSUES.md`

`CHANGELOG.md`

`TASK_BOARD.md`

---

# 9. CODEX CONTINUATION PROMPT

Store the following or an improved version in:

`About-Info/Vibe-Coding/RESUME_PROMPT.md`

Text:

`This is a continuation of the GDTT project. Do not depend on previous chat context. First read AGENTS.md and the About-Info/AI-Handoff files, especially CURRENT_STATE.md, NEXT_STEPS.md, DECISIONS.md, KNOWN_ISSUES.md and CHANGELOG.md. Inspect the relevant implementation and tests. Determine the exact current state before modifying anything. Preserve working components, continue from the documented checkpoint, test your work, and update the handoff documentation before ending.`

---

# 10. SAFE MODIFICATION RULES

When I request a change:

1. Determine which requirement IDs are affected.
2. Identify affected modules.
3. Inspect existing behavior.
4. Avoid unrelated rewrites.
5. Preserve backward-compatible behavior where appropriate.
6. Add/update tests.
7. Update documentation.
8. Update requirement status.
9. Update CHANGELOG.
10. Update CURRENT_STATE.

Do not rebuild an entire module merely because modifying one function is inconvenient.

If a refactor is genuinely needed:

- explain why;
- keep its scope controlled;
- preserve behavior with tests.

---

# 11. CODING STANDARDS

Use:

- descriptive module names;
- descriptive function names;
- descriptive class names;
- type hints;
- useful docstrings;
- focused comments for non-obvious logic;
- small cohesive functions;
- clear public interfaces.

Avoid:

- giant files;
- giant classes;
- business logic inside button handlers;
- duplicated constants;
- circular imports;
- hidden global state;
- unrestricted `eval`;
- silent exception swallowing.

Keep domain calculations testable without launching the GUI.

---

# 12. PROJECT / REPOSITORY STRUCTURE

Do not blindly create this exact tree before Phase 0.

After selecting the architecture, create a structure based on the following concept:

```text
DataForge-Studio/
│
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── pyproject.toml
├── .gitignore
├── .gitattributes
├── .editorconfig
├── LICENSE or LICENSE-NOT-SELECTED.md
│
├── src/
│   └── dataforge_studio/
│       ├── __init__.py
│       ├── __main__.py
│       │
│       ├── app/
│       ├── domain/
│       ├── io/
│       ├── transformation/
│       ├── datetime/
│       ├── timezone/
│       ├── gaps/
│       ├── aggregation/
│       ├── validation/
│       ├── export/
│       ├── templates/
│       ├── reporting/
│       ├── settings/
│       └── ui/
│
├── config/
│   ├── format_profiles/
│   ├── defaults/
│   └── templates/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   ├── fixtures/
│   └── performance/
│
├── scripts/
│   ├── setup_dev.*
│   ├── run_dev.*
│   ├── test.*
│   ├── build_windows.*
│   └── verify_release.*
│
├── packaging/
│
├── About-Info/
│   ├── README.md
│   │
│   ├── Human-Docs/
│   ├── Architecture/
│   ├── Data-Processing/
│   ├── Git-GitHub/
│   ├── Vibe-Coding/
│   ├── Modification-Guides/
│   ├── Diagrams/
│   ├── Machine-Readable/
│   └── AI-Handoff/
│
└── .github/
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── PULL_REQUEST_TEMPLATE.md
```

Modify the exact tree if the selected architecture justifies it.

---

# 13. ROOT README

Create:

`README.md`

This is the primary introduction for humans and GitHub.

Include:

- GDTT overview
- Screenshots section/placeholders
- Main features
- Supported files
- Transformation mode
- Averaging mode
- Offline/privacy statement
- Installation
- Running from source
- Windows packaged application
- Quick-start example
- Repository structure
- Documentation map
- Development setup
- Testing
- Git/GitHub contribution workflow
- Release information
- License status
- Current development maturity/version

Keep it useful to both:

- a normal user;
- a developer opening the GitHub repository.

---

# 14. ABOUT-INFO MASTER INDEX

Create:

`About-Info/README.md`

It must explain:

- what each documentation folder contains;
- which document to read for which task;
- where application code is;
- where tests are;
- where configuration lives;
- where templates live;
- where UI code lives;
- where calculations live;
- where Git documentation lives;
- where packaging scripts live;
- where Codex continuation information lives.

This should function as the project's documentation navigation page.

---

# 15. CODE MODIFICATION GUIDE

Create:

`About-Info/Modification-Guides/CODE_MODIFICATION_GUIDE.md`

Include a **Module Locator Map**.

Example:

| Feature | Main Module | Main Symbols | Relevant Tests | Related Documentation |
|---|---|---|---|---|
| CSV import | `io/...` | `CsvReader` | `tests/...` | `...` |
| Date parsing | `datetime/...` | `DateTimeParser` | `...` | `...` |
| Timezone conversion | `timezone/...` | `TimezoneConverter` | `...` | `...` |
| Gap filling | `gaps/...` | `GapRegularizer` | `...` | `...` |
| Leq averaging | `aggregation/...` | `LeqEnergyStrategy` | `...` | `...` |
| Excel formatting | `export/...` | `FormattedExcelWriter` | `...` | `...` |

Do not manually rely on line numbers because they become stale.

If a generated source-code map with line numbers is useful, generate it automatically.

The guide must explain:

### Manual Modification

- create/activate development environment;
- install dependencies;
- locate feature;
- modify code;
- run focused tests;
- run regression tests;
- update documentation.

### Codex Modification

- how to phrase modification prompts;
- how to restrict scope;
- how to ask for tests first;
- how to request UI-only changes;
- how to request safe refactoring;
- how to continue after interruption.

---

# 16. GIT AS A FIRST-CLASS PROJECT SYSTEM

Initialize and maintain the project as a Git repository.

Git must not be an afterthought.

Provide:

- clean history;
- meaningful commits;
- branches for larger changes;
- tags/releases;
- recovery documentation;
- safe rollback guidance.

---

# 17. GIT SAFETY RULES FOR CODEX

Codex must follow these rules:

### Never without explicit instruction:

- `git push --force`
- destructive history rewriting;
- deleting remote branches;
- deleting tags;
- deleting releases;
- `git reset --hard` when work could be lost;
- discarding uncommitted user changes;
- overwriting GitHub remote configuration.

Before a potentially destructive Git action:

- inspect repository status;
- preserve user work;
- explain the action.

Codex must not push to GitHub automatically merely because a task is finished.

Local changes and local commits are separate from remote publication.

---

# 18. GIT WORKFLOW

Use a practical lightweight GitHub-flow style workflow.

Primary branch:

`main`

Main should represent:

- working;
- tested;
- documented states.

For significant development use short-lived branches.

Examples:

`feature/timezone-conversion`

`feature/averaging-season`

`fix/csv-null-export`

`refactor/export-engine`

`docs/git-guide`

`release/v0.5.0`

Small safe edits may be committed directly during early solo development if I deliberately choose that workflow.

Document both approaches.

---

# 19. COMMIT CONVENTION

Use clear commit messages.

Prefer Conventional Commit-style prefixes:

- `feat:`
- `fix:`
- `docs:`
- `refactor:`
- `test:`
- `perf:`
- `build:`
- `ci:`
- `chore:`

Examples:

`feat: add configurable local day start`

`fix: preserve true nulls in CSV output`

`test: add gap reconstruction regression fixture`

`docs: expand Codex continuation guide`

Avoid meaningless messages such as:

`update`

`changes`

`fix stuff`

---

# 20. COMMIT SCOPE / CHECKPOINTS

Prefer commits that represent one coherent change.

For large Codex tasks, logical checkpoint commits may be useful.

However:

`AUTO_COMMIT = FALSE` by default.

Codex should prepare a proposed commit message after completing a logical task.

Only create commits automatically when:

- I explicitly request it; or
- project-level Codex instructions later enable automatic checkpoint commits.

This prevents unexpected repository history changes.

---

# 21. .GITIGNORE

Generate a project-appropriate `.gitignore`.

At minimum exclude:

## Python

- `__pycache__/`
- `*.py[cod]`
- `.venv/`
- virtual environments
- build caches
- test caches
- coverage outputs

## Packaging

- `build/`
- `dist/`
- temporary packaging outputs
- installer intermediates

Do not automatically ignore a required packaging configuration such as a deliberately maintained `.spec` file.

## IDE / OS

- `.idea/`
- local editor state where appropriate
- `Thumbs.db`
- `Desktop.ini`
- `.DS_Store`

Do not ignore useful shared VS Code settings if the project intentionally uses them.

## Runtime

- logs
- crash dumps
- temporary previews
- temp processing files
- generated output files

## DATA - IMPORTANT

Do not commit operational monitoring datasets.

Ignore appropriate local data directories such as:

`data/private/`

`data/input/`

`data/output/`

`temp/`

Only small synthetic or intentionally sanitized test fixtures belong in Git.

Never commit confidential or large monitoring datasets merely because they are needed for testing.

---

# 22. .GITATTRIBUTES

Create `.gitattributes`.

Use it for:

- text normalization;
- predictable line endings;
- file-type handling;
- binary declarations where needed.

The project is primarily Windows-facing but must avoid unnecessary CRLF/LF churn in Git.

---

# 23. EDITORCONFIG

Create `.editorconfig`.

Standardize:

- encoding UTF-8;
- newline policy;
- indentation;
- trailing whitespace;
- final newline.

---

# 24. GIT AND GITHUB GUIDE

Create:

`About-Info/Git-GitHub/GIT_AND_GITHUB_GUIDE.md`

Write it for someone who is not a Git expert.

Include both:

## Simple Explanation

Explain:

- repository;
- working tree;
- staging;
- commit;
- branch;
- merge;
- pull request;
- remote;
- tag;
- release.

## Command-Line Instructions

Include installation/setup checks.

Example concepts:

`git --version`

`git config --global user.name "..."`

`git config --global user.email "..."`

### Initialize Existing Local Project

`git init`

`git add .`

`git status`

`git commit -m "feat: initialize GDTT project"`

`git branch -M main`

### Connect to New GitHub Repository

Explain that the GitHub repository should preferably be created empty if the local project already contains README/.gitignore/license files.

Then:

`git remote add origin <repository-url>`

`git remote -v`

`git push -u origin main`

Use placeholders rather than hardcoding a username.

---

# 25. GITHUB DESKTOP GUIDE

The Git/GitHub guide should also contain an easier GitHub Desktop workflow:

- create/add local repository;
- review changed files;
- write commit summary;
- commit;
- publish repository;
- create branch;
- switch branch;
- push;
- fetch/pull;
- merge or use GitHub PR.

This is useful when command-line Git is not preferred.

---

# 26. DAILY GIT WORKFLOW

Document a normal feature workflow such as:

1. Check working tree.
2. Update main.
3. Create branch.
4. Make change.
5. Run tests.
6. Review diff.
7. Stage intended files.
8. Commit.
9. Push branch.
10. Open Pull Request.
11. Review checks.
12. Merge.
13. Delete merged feature branch.
14. Pull updated main.

Provide command examples.

---

# 27. GIT RECOVERY GUIDE

Create:

`About-Info/Git-GitHub/GIT_RECOVERY_GUIDE.md`

Explain safe recovery scenarios:

- changed file but not committed;
- staged wrong file;
- committed locally but not pushed;
- need to inspect older version;
- accidental conflict;
- branch created from wrong point;
- recover deleted local branch where practical;
- revert a bad commit.

Prefer safe commands such as `git restore`, `git revert`, and inspecting status/history.

Clearly mark destructive commands.

Do not teach a workflow centered on `reset --hard`.

---

# 28. GITHUB REPOSITORY SETUP GUIDE

Include a separate section or document explaining how to publish the repository later.

Cover:

- creating GitHub repository;
- repository name;
- public vs private consideration;
- connecting remote;
- first push;
- checking README rendering;
- topics/description;
- repository settings;
- default branch;
- branch protection/rulesets.

Recommended later protection for `main`:

- prevent force pushes;
- optionally require pull requests;
- require CI checks before merging once CI is stable.

---

# 29. GITHUB ISSUE / PR SUPPORT

Create:

`.github/PULL_REQUEST_TEMPLATE.md`

Include:

- summary;
- reason;
- affected modules;
- requirement IDs;
- tests performed;
- screenshots for UI changes;
- documentation updated;
- known limitations.

Create lightweight Issue templates for:

- Bug
- Feature request

Avoid excessive process for a one-person project.

---

# 30. GITHUB ACTIONS / CI

Prepare GitHub Actions configuration.

At minimum, eventually provide:

`.github/workflows/ci.yml`

CI should perform suitable checks such as:

- dependency installation;
- unit tests;
- core integration tests;
- lint;
- optional type checks.

Since the main application is Windows-focused, include Windows testing where practical.

Core headless logic may also be tested on another OS if useful.

Do not make CI depend on real monitoring datasets.

---

# 31. WINDOWS BUILD WORKFLOW

Provide a separate Windows build workflow or script.

Possible:

`.github/workflows/build-windows.yml`

and local:

`scripts/build_windows.ps1`

or equivalent.

Build artifacts should not be committed directly into Git history.

Store distributable binaries in:

- GitHub Actions artifacts during testing;
- GitHub Releases for actual releases.

---

# 32. RELEASE SYSTEM

Use Semantic Versioning where practical:

`MAJOR.MINOR.PATCH`

Development examples:

`0.1.0`

`0.2.0`

Stable example:

`1.0.0`

Git tags:

`v0.1.0`

`v1.0.0`

Maintain:

`CHANGELOG.md`

For a release:

1. Ensure tests pass.
2. Update version.
3. Update CHANGELOG.
4. Build Windows package.
5. Verify package.
6. Tag commit.
7. Create GitHub Release.
8. Attach Windows installer/executable and appropriate checksums if implemented.

Support pre-releases for alpha/beta versions.

---

# 33. LICENSE

Do not automatically choose MIT or Apache merely because they are common.

If I have not selected a license, create a clear placeholder such as:

`LICENSE-NOT-SELECTED.md`

and document that a license should be selected before public release.

When I later choose a license, replace it properly.

---

# 34. DEPENDENCY MANAGEMENT

Prefer a modern `pyproject.toml`-based project.

Use:

- pinned/reproducible dependencies;
- clear dev dependencies;
- clean environment setup.

Depending on the selected package manager, include suitable lock or requirements files.

Do not maintain multiple contradictory dependency lists.

README and setup documentation must give exact environment commands.

---

# 35. DEVELOPMENT QUALITY TOOLS

Evaluate and configure suitable tools such as:

- pytest
- Ruff
- type checking where useful
- coverage
- pre-commit

Keep tooling useful rather than excessively strict.

Create easy commands/scripts such as:

`test`

`lint`

`format`

`run`

`build`

so both Codex and humans know the exact verification process.

Record these commands in AGENTS.md.

---

# 36. HOME SCREEN

After launch, display major mode cards/buttons.

Initially:

# Reformat / Transform

and

# Average / Aggregate

Leave visual and architectural space for future modes.

Use:

- large labels;
- large main buttons;
- modern design;
- professional colors;
- good spacing;
- accessible contrast.

Smaller option controls may use smaller text where needed.

Provide theme support where practical:

- Light
- Dark
- System

---

# 37. MAIN WORKFLOW

Typical workflow:

`Mode → File → Inspect → Configure → Preview → Validate → Export → Verify`

Show a progress stepper.

---

# 38. INPUT FILES

Initially support:

- CSV
- TSV
- delimited TXT
- XLSX

XLSX V1:

one worksheet at a time.

If workbook contains several sheets:

- display worksheet selector;
- process the chosen worksheet.

Design the reader so multi-sheet processing can be introduced later.

Allow files to be selected with a file picker or added by local drag and drop.

Support both single-file and multi-file/batch input. For a batch:

- use the first file as the reference;
- require the same file kind, ordered columns, header decision, and text delimiter/quote
  settings, or the same selected XLSX worksheet;
- explain each incompatibility and block configuration until every selected file is compatible;
- preview the reference structure and identify that previews represent the batch reference;
- export and reopen-verify every source independently with source-derived, collision-safe names;
- show per-source success, warning, or failure results without hiding partial batch failures.

After a completed export, offer a clear way to process more similar files while retaining normal
single-file selection.

---

# 39. AUTO-DETECTION

After selecting a file, analyze it.

Detect where practical:

- file type;
- delimiter;
- encoding;
- quote behavior;
- header row;
- column names;
- row count;
- data types;
- likely date columns;
- likely time columns;
- likely DateTime columns;
- likely numeric fields;
- missing-value markers;
- sampling interval;
- timezone information;
- columns that are entirely empty.

All important detection must be overridable.

---

# 40. LARGE FILE SUPPORT

Large files are expected.

Do not assume the entire file fits comfortably in RAM.

Estimate:

- file size;
- approximate row count;
- memory demand.

If unusually large:

show a message.

Use an appropriate backend strategy such as:

- lazy processing;
- streaming;
- chunking;
- Arrow;
- Polars;
- DuckDB;
- temporary local intermediates.

The exact implementation should be selected after benchmarking.

Do not silently truncate.

Operations spanning chunks must remain correct, including:

- gap detection;
- duplicate timestamps;
- period averaging;
- date range;
- first/middle/last preview.

Provide progress indication.

Provide Cancel where safe.

---

# 41. INTERNAL DATA MODEL

Separate:

- raw source value;
- parsed value;
- semantic data type;
- source format;
- output format;
- null state;
- timestamp role;
- source timezone;
- target timezone;
- interval;
- transformation list;
- aggregation instruction;
- output style.

UI strings must not be the source of truth.

Use versioned structured configuration models.

---

# 42. COLUMN MAPPING GRID

After inspection display a comprehensive field mapping screen.

Suggested columns:

| Export | Input Column | Detected Type | Input Format/Profile | Missing % | Output Column | Output Type | Output Format | Transformations | Aggregation |

Additional useful information may be added.

Features:

- horizontal scroll;
- frozen important columns;
- search;
- filtering;
- sorting;
- grouping;
- select all;
- deselect all;
- status icons;
- missing percentage;
- warnings.

Double-click/select a field to open detailed configuration.

---

# 43. COLUMN WIZARD

Provide an optional sequential wizard.

For each column:

1. Show sample values.
2. Show detected data type.
3. Ask for confirmation/change.
4. Show detected input format.
5. Ask for confirmation/change.
6. Suggest output format.
7. Allow output name.
8. Allow transformations.
9. Show live preview.
10. Continue to next field.

---

# 44. DATA TYPES

Support:

- Text
- Integer
- Decimal/Numeric
- Boolean
- Date
- Time
- DateTime
- Duration
- Category/Text-like
- Auto/Unconfirmed

---

# 45. DATE/TIME STRUCTURES

Support:

- combined DateTime;
- Date only;
- Time only;
- separate Date + Time;
- Date + Start Time + End Time;
- Start DateTime + End DateTime;
- Start timestamp + Duration;
- other reasonable combinations.

Default preference:

combined DateTime.

Allow manual selection.

---

# 46. FORMAT DETECTION

Analyze multiple records.

For ambiguous data such as:

`04/05/2026`

do not silently choose if ambiguity remains.

Show possibilities such as:

`MM/dd/yyyy`

`dd/MM/yyyy`

with interpreted samples.

Allow manual override.

---

# 47. DATE/TIME PRESET GROUPS

Prioritize interoperable formats.

Group options conceptually as:

## Recommended / ISO

## OpenAQ

## AQS

## AQCSV / AIRNow

## Regional

## Advanced

## Custom

Show both:

- human-readable profile name;
- pattern.

Examples:

`yyyy-MM-dd`

`yyyy-MM-dd HH:mm`

`yyyy-MM-dd HH:mm:ss`

`yyyy-MM-dd'T'HH:mm:ssXXX`

Support milliseconds, but do not show them as the main defaults unless detected.

---

# 48. FORMAT VS TIMESTAMP SEMANTICS

Do not confuse the printed format with the meaning of a timestamp.

A DateTime profile may contain:

- formatting syntax;
- timezone requirement;
- whether timestamp is interval start;
- interval end;
- midpoint;
- instantaneous;
- inclusive/exclusive interval meaning.

This is essential when supporting environmental-data standards.

---

# 49. TIMESTAMP ROLE

Allow:

- Start of interval
- End of interval
- Midpoint
- Instantaneous
- Unknown/Custom

Also configure sampling duration.

Example:

Start:

`14:00`

Duration:

`1 hour`

Derived:

Start = `14:00`

Mid = `14:30`

End boundary = `15:00`

---

# 50. INTERVAL END NORMALIZATION

Input may contain:

Start = `08:00`

End = `08:59`

For one-hour data, allow user to choose:

- retain supplied end;
- calculate `End = Start + Duration`;
- normalize supplied end using interval semantics;
- custom rule.

If recalculated:

End = `09:00`

Do not implement this as blindly rounding `:59`.

It is semantic interval normalization.

---

# 51. DERIVED START / MID / END FIELDS

Allow optional creation of:

- Start
- Mid
- End

Allow custom output names.

Example:

`Date-Time_Start_Local`

`Date-Time_Mid_Local`

`Date-Time_End_Local`

---

# 52. TIME SHIFT / OFFSET

Provide an independent Time Shift transformation.

Examples:

- +1 hour
- -30 minutes
- +5 minutes
- custom duration

This deliberately changes the timestamp value.

It is not timezone conversion.

---

# 53. TIMEZONE CONVERSION

Provide a dedicated timezone conversion tool.

Source timezone can come from:

- selected fixed timezone;
- timezone column;
- embedded timezone;
- manually entered UTC offset.

Highlight:

- UTC / UTC+00:00
- Asia/Colombo / UTC+05:30

Also provide:

- searchable IANA timezone list;
- manual UTC offset.

Allow source timestamp to remain and create converted fields.

Example:

UTC:

`2025-08-20 08:00`

Asia/Colombo:

`2025-08-20 13:30`

Timezone conversion preserves the instant.

Time Shift and Timezone Conversion must remain separate.

---

# 54. COLUMN MANAGEMENT

Allow:

- rename;
- reorder;
- add;
- remove from output;
- empty field;
- duplicate field;
- derived field;
- calculated field;
- date/time-derived field;
- Index.

Index:

default:

`1, 2, 3...`

Default name:

`Index`

Default location:

first column.

---

# 55. CALCULATED FIELD WIZARD

Provide a safe formula builder.

Do not use unrestricted Python `eval`.

Initial operations may include:

- source field;
- constant;
- +;
- -;
- ×;
- ÷;
- parentheses;
- linear formula `Y = aX + b`.

Future operations may be added through a registry/plugin-like architecture.

---

# 56. PPM / PPB

Provide:

- ppm → ppb: ×1000
- ppb → ppm: ÷1000

The primary intended current use is ppm → ppb.

Allow:

- replace original;
- create new field;
- custom output name;
- sensible automatic header suggestion.

Do not implement ppm ↔ mg/m³ as a built-in V1 feature.

It may later be implemented through an advanced calculated-field/unit-conversion system.

---

# 57. ROUNDING

Default:

No change.

Common controls:

- No change
- 0
- 0.0
- 0.00
- 0.000
- Scientific
- Custom

Example:

`25.679 → 25.68`

for two decimals.

Use arithmetic rounding.

Do not truncate values merely by formatting strings.

---

# 58. LIVE PREVIEW

Every significant transformation should provide sample before/after values.

For example:

Input:

`08/20/2025 08:00`

Output:

`2025-08-20 08:00`

Timezone:

`2025-08-20 08:00 UTC`

→

`2025-08-20 13:30 Asia/Colombo`

Use several sample rows where useful.

---

# 59. INTERNAL NULL MODEL

Use one canonical internal missing-value representation.

Do not internally treat these as unrelated missing states:

- blank
- empty string
- N/A
- NA
- NULL
- -999
- NaN
- None

After user confirmation, normalize source missing markers to the internal missing state.

Output sentinel formatting occurs at export time.

---

# 60. INPUT NULL SETTINGS

On file inspection detect potential missing markers.

Examples:

- blank
- `N/A`
- `NA`
- `NULL`
- `-999`
- custom

Ask what they mean.

Do not automatically interpret `-999` as missing without confirmation.

---

# 61. OUTPUT NULL SETTINGS

Allow one output missing-value policy:

- True blank/null - DEFAULT
- N/A
- -999
- Custom Sentinel

Only one policy should be used for missing measurements in the generated dataset.

Show this setting:

- early in configuration;
- again before processing/export.

Allow override before export.

---

# 62. TRUE NULL CSV/XLSX

If True Null is selected:

CSV/TSV:

Desired:

`value1,,value3`

not:

`value1,"",value3`

for missing measurement data.

XLSX:

write a genuinely blank cell.

Do not write an empty string merely to look blank.

---

# 63. INVALID NUMERIC VALUES

Example:

`23.5`

`24.1`

`ERROR`

`25.0`

Detect invalid values.

Prompt user.

Default suggestion:

treat invalid entry as missing and continue.

Options may include:

- null and continue;
- inspect affected rows;
- stop;
- preserve source text separately.

Include:

`Apply this rule to all similar values in this file`

Record counts/actions in report.

---

# 64. SAMPLING INTERVAL DETECTION

Detect expected interval from timestamp data.

Common options:

- 1 minute
- 5 minutes
- 15 minutes
- 1 hour
- Custom

Show detected interval.

Require confirmation/change before gap generation or averaging.

---

# 65. GAP FILLING

Example:

`08:00`

`09:00`

`11:00`

with:

Interval = 1 hour

detect:

`10:00`

Provide:

`Insert Missing Time Rows`

Present this as an option that is enabled by default and can be deselected. When enabled,
generated measurement values remain the canonical internal null state; the global output
missing-value choice (True Null, N/A, -999, or Custom Sentinel) controls only their displayed
or exported representation. Do not interpolate measurements.

Generated row:

- primary timestamp populated;
- start/mid/end populated;
- timezone-derived timestamps populated;
- Index populated;
- measurement fields null;
- selected stable metadata populated.

No measurement interpolation is required.

---

# 66. GAP ROW METADATA POLICY

Each field may use a gap-fill behavior such as:

- Null
- Carry Stable Metadata
- Fixed Value
- Derived from Timestamp

Auto-suggest stable metadata when a field is effectively constant.

Examples:

`Source`

`Device timezone`

Do not forward-fill pollutant/sensor measurements merely because surrounding rows exist.

---

# 67. REMOVE EMPTY ROWS

Provide secondary options:

- remove if all measurement fields are missing;
- remove if all selected fields are missing;
- remove if any required selected field is missing;
- remove based on selected subset;
- threshold-based advanced rule if useful.

Show:

`Rows that will be removed: N`

before executing.

---

# 68. EXPORT FIELD CHECKBOXES

Before export display every output field.

Default:

- useful populated field → selected;
- partially populated field → selected, show missing %;
- generated useful field → selected;
- 100% empty field → deselected.

User may override.

Do not permanently delete deselected fields from the transformation recipe.

---

# 69. EXAMPLE ACCEPTANCE DATASET

Use the supplied common dataset structure as an important regression/acceptance fixture.

Important expected behavior:

- add one-based Index;
- detect one-hour period;
- convert date format;
- normalize semantic end boundary from `08:59` to `09:00` where configured;
- convert UTC to Asia/Colombo;
- add Local Start;
- add Local Mid;
- add Local End;
- detect missing 10:00 UTC interval;
- insert generated row;
- preserve stable Source/timezone metadata;
- leave measurements genuinely null;
- deselect fully empty columns by default.

Conceptually:

Input:

`08:00`

`09:00`

`11:00`

Output:

`08:00`

`09:00`

`10:00 generated`

`11:00`

For first row:

UTC Start `08:00`

UTC End `09:00`

Local Start `13:30`

Local Mid `14:00`

Local End `14:30`

---

# 70. TRANSFORMATION TEMPLATES

Support local recipes/templates.

Functions:

- Save
- Load
- Import
- Export
- Duplicate
- Rename
- Delete with confirmation

Templates may contain:

- schema expectations;
- column mappings;
- names;
- formats;
- timezone rules;
- timestamp semantics;
- interval;
- gap rules;
- rounding;
- unit conversions;
- calculations;
- column order;
- export fields;
- null policy;
- Excel style;
- averaging settings where relevant.

Store in versioned JSON or similarly structured format.

Do not store actual measurement data in recipes.

---

# 71. TEMPLATE MATCHING

After input analysis compare file schema with stored templates.

Show likely matches.

Example:

`Likely Match - 61 of 64 expected fields found`

Options:

- Apply
- Review
- Ignore

Do not apply a template automatically based only on filename.

---

# 72. AVERAGING MODE

Allow:

any sensible input interval → selected output interval.

Common input:

- 1 minute
- 5 minutes
- 15 minutes
- 1 hour
- Custom

Common output:

- 5 minutes
- 1 hour
- 8 hours
- 24 hours
- 7 days/week
- Calendar Month
- Fixed 30 Days
- Quarter
- Season
- Annual/Calendar Year
- Fixed 1 Year
- Custom where practical

---

# 73. CLOCK INTERVALS

V1 uses standard clock-aligned intervals.

Not rolling by default.

Examples:

1 hour:

`00:00-01:00`

`01:00-02:00`

8 hour:

`00:00-08:00`

`08:00-16:00`

`16:00-24:00`

Design interval alignment as a strategy so Rolling can later be added.

---

# 74. START OF DAY

Default:

`00:00`

Prominent choices:

- 00:00
- 06:00
- 08:00
- Custom

A day starting 06:00 is:

06:00 current date → 06:00 following date.

---

# 75. WEEK / MONTH / 30 DAY / QUARTER / YEAR

Do not treat ambiguous reporting periods as interchangeable.

### Week

Allow week-start selection.

### Calendar Month

Use actual month boundaries.

### 30 Days

Separate from calendar month.

Ask for alignment/anchor.

### Quarter

Provide normal Q1-Q4 preset.

Allow custom quarter definitions.

### Calendar Year

Default January 1.

Allow custom reporting year start.

### Fixed One Year

Keep conceptually distinct where needed.

---

# 76. SEASONS

Season definition must be configurable.

Allow:

- season name;
- start date/month;
- next boundary;
- number of seasons.

Save season sets as templates.

---

# 77. DIRECT APPROACH

Direct Approach:

calculate the statistic directly from valid source/input rows for the target reporting period.

Do not require progressive intermediate averages.

Default completeness:

75%.

The value must be:

- visible;
- editable;
- stored as configuration.

---

# 78. AGGREGATE / INCREMENTAL APPROACH

Incremental Approach:

derive larger periods from lower-level calculated periods.

Possible chain:

`5 min → 1 hour → 8 hour → 24 hour`

The chain must be:

- visible;
- configurable;
- not permanently hardcoded.

Apply completeness at each relevant stage.

---

# 79. COMPLETENESS

Default:

75%.

Concept:

`Availability = Valid expected observations / Expected observations × 100`

Expected count must derive from the configured time interval/boundaries, not merely from rows that happened to be present.

---

# 80. SPECIAL THREE-COMPONENT RULE

Under Incremental aggregation, where there are exactly three component values, allow:

2 of 3

≈66.67%

Examples:

three 8-hour periods → 24-hour result

three months → quarter

Do not automatically apply 2/3 to Direct Approach datasets containing many underlying rows.

Thresholds remain configurable.

---

# 81. COMMON INCREMENTAL RULES

Suggested defaults:

1-hour from minute/5-minute → 75%

8-hour from hourly → 75%

24-hour from hourly → 75%

24-hour from three 8-hour → 2/3 permitted

Weekly from daily → 75%

Monthly from daily → 75%

Quarter/season from daily → 75%

Quarter from 3 monthly → 2/3 permitted

Annual → normally 75%, according to selected source level

---

# 82. INCREMENTAL SIMPLIFICATION

Do not force every intermediate period.

Daily may be calculated directly from hourly.

Monthly may be calculated directly from daily.

Quarter/season may be calculated from daily instead of monthly where selected.

User should understand the selected aggregation chain.

---

# 83. INSUFFICIENT COMPLETENESS

If threshold is not satisfied:

output missing result.

Use selected global missing representation:

- blank/null;
- N/A;
- -999;
- custom.

No status field is required by default.

Final report must state:

- periods evaluated;
- periods accepted;
- periods rejected;
- completeness setting.

---

# 84. STATISTICS

Default:

Arithmetic Mean.

Also support:

- Minimum
- Maximum
- Sum
- Median
- Standard Deviation
- Count

Allow additional strategies later.

---

# 85. SOUND / LEQ

Do not arithmetic-average Leq-style dB metrics.

Provide:

`Energy Average / Leq`

For equal-duration observations:

`Leq = 10 × log10(mean(10^(Li/10)))`

For different durations:

use duration-weighted energy averaging.

Auto-suggest for fields such as:

- LAeq
- LCeq
- LZeq
- Leq

Require confirmation.

Keep acoustic calculations isolated in aggregation strategies.

---

# 86. RAINFALL

Rain amount accumulated over smaller intervals generally uses:

`Sum / Accumulation`

For longer reporting periods, allow:

- sum;
- average of daily totals;
- another explicitly selected statistic.

Do not guess when meaning is ambiguous.

---

# 87. RAIN RATE

Rain Rate is different from Rain Amount.

Suggest arithmetic average for rain rate.

---

# 88. FIELD AGGREGATION CONFIGURATION

Example:

| Field | Suggested Aggregation |
|---|---|
| PM2.5 | Arithmetic Mean |
| Temperature | Arithmetic Mean |
| LAeq | Energy Average |
| Rainfall | Sum |
| Rain Rate | Arithmetic Mean |

Allow user override.

---

# 89. AGGREGATED FIELD NAMES

Offer optional output naming assistance.

Examples:

`PM2.5 (ug/m3) - Mean`

`LAeq (dB) - Energy Avg`

`Rainfall (mm) - Sum`

Allow custom names or no suffix.

---

# 90. AVERAGING TIMEZONE

The user must define the timezone controlling reporting boundaries.

Options:

- UTC
- Asia/Colombo
- timezone from selected field
- other IANA timezone

A local day is not necessarily the same as a UTC day.

Use timezone-aware boundaries.

Handle DST correctly for regions that use it.

---

# 91. INPUT PREVIEW

After reading file show:

- First 5 records
- Middle 5 records
- Last 5 records

Show all columns using scrolling/virtualization.

---

# 92. PRE-EXPORT VERIFICATION

Before processing/export, show:

## Input

First 5

Middle 5

Last 5

## Proposed Output

First 5

Middle 5

Last 5

Allow side-by-side or clearly switchable comparison.

Show all output fields.

Also summarize:

- input rows;
- expected output rows;
- columns;
- added columns;
- deselected columns;
- renamed fields;
- gap rows;
- removed rows;
- time conversions;
- rounding;
- unit conversions;
- null policy;
- averaging configuration.

---

# 93. TRANSFORMATION PLAN

Before execution show a readable plan.

Example:

Input datetime:

`MM/dd/yyyy HH:mm`

Output:

`yyyy-MM-dd HH:mm`

Timestamp role:

Start

Interval:

1 hour

End:

Start + 1 hour

Timezone:

UTC → Asia/Colombo

Mid:

Enabled

Gap fill:

Enabled

Null output:

True Blank

Index:

Enabled

Allow Back/Edit.

---

# 94. OUTPUT FORMATS

Allow:

- CSV
- XLSX
- CSV + XLSX

For XLSX:

## Plain

suffix:

`_P.xlsx`

## Formatted

suffix:

`_F.xlsx`

---

# 95. FORMATTED EXCEL

Offer clean style presets.

Allow configuration such as:

- font;
- size;
- header fill;
- header text color;
- borders;
- alternating rows;
- autofilter;
- freeze header;
- column widths;
- native date/time formats;
- native numeric formats.

Allow custom styles to be saved locally.

---

# 96. OUTPUT FILE NAMES

For Reformatting:

Input:

`xyz.csv`

Example output:

`xyz_2025-01-01_00h00_to_2026-01-01_00h00_RF.csv`

For Excel:

`xyz_..._RF_P.xlsx`

`xyz_..._RF_F.xlsx`

Use selected primary timestamp/date range.

Allow user override.

Sanitize invalid Windows filename characters.

For averaging use a clear configurable suffix, suggested:

`_AVG`

---

# 97. TRANSFORMATION REPORT

After processing display a report containing relevant items such as:

- application version;
- processing date/time;
- input filename;
- outputs;
- input row count;
- output row count;
- input format;
- output format;
- worksheet;
- columns;
- formats;
- timestamp role;
- interval;
- timezone conversion;
- time offsets;
- derived columns;
- renamed/reordered columns;
- excluded fields;
- rounding;
- ppm/ppb conversions;
- calculated fields;
- input null interpretation;
- output null policy;
- generated gap rows;
- removed rows;
- invalid values;
- averaging approach;
- aggregation chain;
- field statistics;
- completeness;
- rejected periods;
- warnings;
- errors;
- post-export verification status.

---

# 98. REPORT EXPORT

Allow supporting outputs such as:

- Transformation Info `.txt`
- Recipe `.json`
- Warning/Error report
- concise processing summary

Use checkboxes.

---

# 99. POST-EXPORT VERIFICATION

Reopen the exported file where practical.

Verify:

- file exists;
- file is readable;
- expected row count;
- expected columns;
- column order;
- no accidental duplicate index;
- first timestamp;
- last timestamp;
- datetime parseability;
- null representation;
- CSV blank fields;
- XLSX genuinely blank cells;
- expected filename;
- expected transformation structure.

Display:

`Passed`

`Passed with Warnings`

or

`Failed`

Never hide a verification failure.

---

# 100. ERROR HANDLING

Centralize error handling.

Handle:

- corrupted input;
- unsupported encoding;
- malformed CSV;
- inconsistent field counts;
- invalid XLSX;
- invalid date;
- invalid timezone;
- mixed numeric types;
- duplicate timestamps;
- disordered timestamps;
- disk-space issues;
- locked output file;
- processing failure.

Show user-friendly messages.

Technical traceback/log can appear under:

`Show Details`

---

# 101. WARNING LEVELS

Use:

- Information
- Warning
- Blocking Error

Examples:

Information:

`Sampling interval detected as 1 hour.`

Warning:

`17 PM2.5 values could not be parsed.`

Blocking:

`Output file cannot be written because it is open.`

---

# 102. NON-DESTRUCTIVE PROCESSING

Never overwrite the original input by default.

Output to a new file.

Use safe temporary/atomic export techniques where practical.

---

# 103. BACK / UNDO / RESET

Provide:

- Back
- Next
- Cancel
- Reset

Use Undo/Redo for configuration edits where reasonably practical.

---

# 104. UX PRINCIPLE

Use progressive disclosure.

Do not show dozens of obscure formats simultaneously.

Example:

## Common

## Recommended

## Profiles

## Advanced

## Custom

Use searchable selectors for:

- timezones;
- format profiles;
- columns;
- templates;
- styles.

---

# 105. SOFTWARE LAYERS

Separate approximately into:

## UI Layer

Screens and controls.

## Application Layer

Workflow coordination.

## Domain Layer

Configuration models and business concepts.

## IO Layer

Readers.

## Transformation Layer

Column transformations.

## Date-Time Layer

Parsing and interval semantics.

## Timezone Layer

Timezone operations.

## Gap Layer

Missing-row regularization.

## Aggregation Layer

Averaging/statistics.

## Validation Layer

Input/output checks.

## Export Layer

CSV/XLSX.

## Reporting Layer

Reports/logs.

## Template Layer

Recipes/styles.

No calculation should be implemented only in UI event handlers.

---

# 106. EXTENSION POINTS

Where appropriate use strategy/registry patterns for concepts such as:

- InputReader
- OutputWriter
- TransformationStrategy
- AggregationStrategy
- DateTimeProfile
- MissingValuePolicy
- IntervalAlignmentStrategy
- ColumnCalculation
- ExportStyle

Avoid over-engineering simple features.

---

# 107. CONFIGURATION-DRIVEN OPTIONS

Centralize mutable lists such as:

- intervals;
- completeness defaults;
- date profiles;
- timezone shortcuts;
- filename patterns;
- aggregation strategies;
- parameter recognition rules;
- missing markers;
- styles.

Do not duplicate these constants throughout code.

---

# 108. ABOUT-INFO STRUCTURE

Create a documentation system broadly resembling:

```text
About-Info/
│
├── README.md
│
├── Human-Docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── USER_GUIDE.md
│   └── FAQ.md
│
├── Architecture/
│   ├── ARCHITECTURE.md
│   ├── MODULE_MAP.md
│   └── EXTENSION_GUIDE.md
│
├── Data-Processing/
│   ├── DATA_PIPELINE_SPEC.md
│   ├── DATE_TIME_DESIGN.md
│   ├── TIMEZONE_DESIGN.md
│   ├── NULL_HANDLING.md
│   ├── GAP_FILLING.md
│   └── AVERAGING_DESIGN.md
│
├── Git-GitHub/
│   ├── GIT_AND_GITHUB_GUIDE.md
│   ├── GIT_RECOVERY_GUIDE.md
│   ├── GITHUB_RELEASE_GUIDE.md
│   └── BRANCHING_AND_COMMITS.md
│
├── Modification-Guides/
│   ├── CODE_MODIFICATION_GUIDE.md
│   ├── UI_MODIFICATION_GUIDE.md
│   ├── ADDING_TRANSFORMATIONS.md
│   └── ADDING_AGGREGATION_METHODS.md
│
├── Vibe-Coding/
│   ├── CODEX_VIBE_CODING_GUIDE.md
│   ├── RESUME_PROMPT.md
│   ├── MODIFICATION_PROMPTS.md
│   └── SESSION_CHECKLIST.md
│
├── Diagrams/
│   ├── ARCHITECTURE.mmd
│   ├── TRANSFORMATION_FLOW.mmd
│   ├── AVERAGING_FLOW.mmd
│   └── GIT_WORKFLOW.mmd
│
├── Machine-Readable/
│   ├── requirements_registry.json
│   ├── transformation_recipe_schema.json
│   ├── format_profiles.json
│   └── default_settings.json
│
└── AI-Handoff/
    ├── CURRENT_STATE.md
    ├── NEXT_STEPS.md
    ├── DECISIONS.md
    ├── KNOWN_ISSUES.md
    ├── TASK_BOARD.md
    └── CHANGELOG.md
```

Use Mermaid or similarly editable text-based diagrams.

---

# 109. REQUIREMENT TRACEABILITY

Use stable requirement IDs.

Examples:

`IO-001`

`DT-001`

`TZ-001`

`GAP-001`

`NULL-001`

`AVG-001`

`EXP-001`

`UX-001`

`GIT-001`

`CODEX-001`

Machine-readable registry may contain:

- ID;
- description;
- module;
- status;
- test reference;
- implementation symbol;
- documentation reference.

Keep traceability lightweight.

---

# 110. TESTING

Use automated tests.

At minimum test:

## Files

- CSV
- TSV
- TXT
- XLSX

## Date/Time

- ISO formats
- regional formats
- ambiguous dates
- milliseconds
- split/combine
- start/mid/end
- end boundary normalization

## Timezone

- UTC
- Asia/Colombo
- timezone conversion
- manual offset
- DST timezone
- offset vs timezone distinction

## Nulls

- blank
- N/A
- -999
- custom sentinel
- CSV true null
- XLSX true blank

## Gap Filling

- interval detection
- one missing interval
- multiple gaps
- metadata carry
- measurement nulls

## Numeric

- rounding
- ppm → ppb
- ppb → ppm
- linear calculation
- invalid numeric value

## Column Operations

- Index
- rename
- reorder
- export selection
- fully empty field deselection

## Averaging

- Direct
- Incremental
- 75%
- 2/3
- mean
- min
- max
- median
- standard deviation
- count
- Leq
- rainfall sum
- rain-rate average

## Export

- filename
- CSV
- plain XLSX
- formatted XLSX
- report
- post-export verification.

---

# 111. SYNTHETIC TEST DATA

Do not require confidential real data.

Create small synthetic fixtures.

Create a sanitized version of the supplied 08:00 / 09:00 / 11:00 example as a permanent regression fixture.

Operational datasets must stay outside Git.

---

# 112. PERFORMANCE TESTS

Create large synthetic datasets.

Measure:

- memory;
- import;
- processing;
- aggregation;
- export.

Do not optimize blindly.

If Excel row limits or practical limits are exceeded:

warn and suggest:

- CSV;
- split output;
- another appropriate format.

---

# 113. VERSIONING

Store application version centrally.

Use semantic-style versions.

Reports must include the software version.

Recipes should include schema/version information.

---

# 114. USER SETTINGS

Persist appropriate preferences locally.

Examples:

- last folder;
- preferred output folder;
- theme;
- preferred Excel style;
- timezone shortcuts;
- window size.

Do not silently reuse a data transformation rule that could alter a new dataset without making it visible.

---

# 115. DEFINITION OF DONE FOR EACH CODING TASK

A Codex task is not complete merely because the code was edited.

For a substantive change:

1. requested behavior implemented;
2. relevant existing behavior preserved;
3. focused tests pass;
4. appropriate regression tests pass;
5. lint/static checks pass where configured;
6. documentation updated;
7. requirement registry updated;
8. CURRENT_STATE updated;
9. CHANGELOG updated;
10. known limitations stated;
11. Git diff reviewed for accidental changes.

---

# 116. PHASED IMPLEMENTATION

Default execution:

`EXECUTION_MODE = PHASED`

One phase at a time.

---

## PHASE 0 - ARCHITECTURE / TECHNOLOGY / REPOSITORY PLAN

Do not build the whole application.

Read this complete specification.

Compare:

- GUI frameworks;
- data engines;
- spreadsheet libraries;
- packaging systems;
- dependency management;
- Windows standalone options.

Provide recommendation.

Also design:

- source layout;
- Git structure;
- AGENTS.md approach;
- About-Info structure;
- test strategy;
- CI strategy;
- packaging strategy;
- large-file strategy;
- transformation recipe model.

Wait for architectural selection unless ONE_SHOT is enabled.

---

## PHASE 1 - REPOSITORY FOUNDATION

Create:

- Git repository structure;
- `.gitignore`;
- `.gitattributes`;
- `.editorconfig`;
- `pyproject.toml`;
- root README;
- AGENTS.md;
- About-Info system;
- AI-Handoff system;
- requirements registry;
- source package;
- test package;
- logging;
- settings;
- centralized error foundation;
- application version;
- initial home screen;
- Reformat card;
- Averaging card;
- future-mode placeholder;
- theme foundation.

Create Git/GitHub documentation.

Verify app launches.

---

## PHASE 2 - FILE INGESTION / PROFILING

Implement:

- CSV
- TSV
- TXT
- XLSX
- worksheet selector
- delimiter detection
- encoding detection
- header detection
- type inference
- datetime detection
- null-marker detection
- likely interval
- empty columns
- row count
- large-file warning
- chunk/lazy strategy
- first/middle/last preview.

Tests required.

---

## PHASE 3 - TRANSFORMATION DOMAIN ENGINE

Implement headless logic:

- rename;
- reorder;
- empty columns;
- duplicate;
- Index;
- rounding;
- ppm/ppb;
- calculated field;
- date parsing;
- date formatting;
- combine/split;
- timestamp role;
- interval;
- start/mid/end;
- time shift;
- timezone conversion;
- format profile registry;
- canonical null model.

Tests before heavy GUI integration.

---

## PHASE 4 - GAP / VALIDATION ENGINE

Implement:

- interval confirmation;
- expected timestamp sequence;
- gaps;
- generated rows;
- metadata policy;
- invalid numeric detection;
- duplicate timestamps;
- chronological validation;
- remove-null rules;
- missing-data configuration.

Test strict true-null behavior.

---

## PHASE 5 - REFORMATTING UI

Implement:

- mapping grid;
- virtualized preview table;
- column wizard;
- sequential wizard;
- format-selector controls;
- profile groups;
- timezone controls;
- start/mid/end controls;
- gap settings;
- live samples;
- export field checkboxes;
- Back;
- Reset;
- Undo/Redo where feasible;
- transformation summary.

Use notification/status components instead of excessive blocking dialogs where appropriate.

---

## PHASE 6 - AVERAGING ENGINE

Implement headless and test:

- any sensible input/output interval;
- clock alignment;
- day start;
- week;
- calendar month;
- 30-day periods;
- quarter;
- season;
- annual;
- Direct;
- Incremental;
- aggregation chain;
- 75%;
- 2/3;
- arithmetic mean;
- min;
- max;
- sum;
- median;
- standard deviation;
- count;
- Leq;
- rainfall;
- rain rate;
- missing results.

---

## PHASE 7 - AVERAGING UI

Implement wizard/configuration for:

- timestamp field;
- timezone;
- input interval;
- target period;
- Direct/Incremental;
- chain;
- thresholds;
- day start;
- quarter;
- season;
- field aggregation rules;
- output names;
- null policy;
- preview.

---

## PHASE 8 - EXPORT / REPORT / TEMPLATE / VERIFICATION

Implement:

- CSV
- XLSX plain
- XLSX formatted
- style editor
- style templates
- RF filenames
- AVG naming
- transformation TXT
- JSON recipes
- error reports
- template save/load/import/export
- matching
- pre-export verification
- post-export reopening/verification.

---

## PHASE 9 - PERFORMANCE / PACKAGING

Benchmark large synthetic data.

Optimize bottlenecks.

Implement:

- source execution;
- Windows development setup;
- Windows build script;
- standalone package;
- installer if selected.

Test on clean Windows environment where feasible.

---

## PHASE 10 - GITHUB / CI / RELEASE READINESS

Finalize:

- CI workflow;
- Windows build workflow;
- issue templates;
- PR template;
- Git documentation;
- GitHub upload guide;
- release guide;
- version/tag process;
- CHANGELOG;
- clean repository test;
- secrets scan/basic check;
- ensure no datasets included.

Do not push to GitHub unless explicitly instructed.

---

# 117. ONE-SHOT MODE

If I add:

`EXECUTION_MODE = ONE_SHOT`

Codex may execute Phases 0-10 sequentially.

After Phase 0, use the recommended architecture unless a blocking issue requires clarification.

Still:

- test each phase;
- update documentation;
- update CURRENT_STATE;
- use logical checkpoints;
- do not leave undocumented half-completed refactors.

If execution is interrupted, the repository must show exactly where to resume.

---

# 118. CONSERVATIVE / LOW-CREDIT MODE

If I add:

`CODEX_WORK_MODE = CONSERVATIVE`

then:

- work on only the requested phase/subtask;
- avoid optional refactors;
- avoid unrelated UI polish;
- run focused tests first;
- update handoff files before expanding scope;
- leave clear continuation instructions.

This mode is useful when Codex usage/credit is limited.

---

# 119. FUTURE MODIFICATION PROMPT

Store this template:

`Treat this as a modification to the existing GDTT repository, not a rebuild. Read AGENTS.md and the relevant About-Info documentation first. Inspect current code and tests. Identify affected requirement IDs and modules. Make the smallest clean change that satisfies the request. Preserve unrelated working functionality. Add/update tests. Run appropriate regression tests. Update relevant documentation, requirements registry, CHANGELOG and AI-Handoff/CURRENT_STATE.md. Do not push or perform destructive Git operations unless explicitly requested.`

---

# 120. FINAL PRINCIPLE

This application is expected to evolve through many Codex sessions.

Therefore:

## Make the first implementation useful, but make the architecture more valuable than the first implementation.

For the end user:

## Ease of use is the highest product priority.

For the data:

## Correct, explicit and verifiable handling of timestamps, intervals, timezones, missing values and aggregation is the highest technical priority.

For the repository:

## Git history, documentation, tests and AI handoff information must make repeated modification safe and understandable.

For Codex:

## Never rely on previous chat history when the repository itself can document the current state.

---

# Owner amendment — 2026-09-15 (PEND-017, GDTT 0.10.1)

Input and output format selectors follow the selected field type. Put Custom near the top with
an editable mask field; numeric/text options must not offer date/time presets. For DateTime,
include extended and compact ISO UTC (Z), numeric UTC offset, hour/minute and full-second forms.
Prefer common extended formats before compact forms. Keep date-only/time-only presets relevant
to their types. Preserve existing profile IDs and explicit saved recipes; review profiles again
after a field-type change. UTC output converts known instants and never guesses a source timezone.
See About-Info/Human-Docs/FORMATTING_AND_APPEARANCE.md for the exact examples and compatibility.
Owner authorizes recoverable cleanup, updated documentation, a new release tag, GitHub source
push and publication of Portable ZIP/installer EXE plus verification assets. Keep previous releases.

## Confirmed About and support update (2026-09-17)

PEND-018: extend only the app's About content with the GitHub repository and Wiki links,
brief licensing and a full-license link, plus a clearly optional Sponsor / Donate section using
https://ko-fi.com/gadash and https://ko-fi.com/s/00a96c800b. Include useful download, issue-reporting
and release-safety links. Preserve existing full License and Components tabs, copyright/Codex
credits and all other app workflows. External pages open only on user selection; no data upload.
Update relevant docs and publish patch 0.10.2 with release tag v0.10.2-rc.1 via the established
verified Windows portable/installer workflow. Unsigned/manual clean-Windows gates remain.
