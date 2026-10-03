# AI engineering log

This log records provenance and evidence. Product rules live in
[REQUIREMENTS.md](REQUIREMENTS.md), design in
[ARCHITECTURE.md](ARCHITECTURE.md), and working instructions in
[AGENTS.md](AGENTS.md).

## 2026-10-01 — Initial design proposal

**Objective:** Inspect the workspace and propose a concise design without
creating files or implementing code.

**Inspection evidence:** Workspace was empty, no Git repository was present,
and no applicable ancestor or repository `AGENTS.md` was found.

**AI recommendations:** Four modules for configuration, single checks,
orchestration, and CLI; simple dataclasses; standard-library thread pooling;
`requests` and `pytest`; separate reviewable milestones. Proposed exit codes
were 0 for healthy, 1 for degraded results, and 2 for invocation/configuration
errors. Exit codes and dependencies remain recommendations, not approved rules.

**Verification:** Product verification pending; no application existed.

## 2026-10-02 — Accepted design and initial documentation

**Explicit user decisions:** Accepted the four-component design, separate
connection/read-inactivity timeouts without a total deadline, monotonic elapsed
time through complete body consumption or request exception, exclusion of worker
queue time, the small/finite-response usage limitation, disabled redirects,
worker-return/main-thread collection, and configuration-order reporting.
The user also specified the exact configuration contract, strict type/unknown
field rejection, no threshold/timeout ordering constraint, and classification
precedence. See requirements for the authoritative details.

**Explicit user scope:** Create only the five initial Markdown documents. Do not
implement application code, install dependencies, or initialize Git. Use the
five milestones recorded in architecture and README.

**AI contribution:** Drafted the documents, numbered acceptance criteria,
concrete examples, verification plans, and remaining questions. Dependency
choices, dataclasses, and testing techniques remain proposed implementation
choices unless explicitly approved later.

**Changes:** Created `REQUIREMENTS.md`, `ARCHITECTURE.md`, `README.md`, `AGENTS.md`,
and this log.

**Verification status:** All application acceptance criteria and milestone
verification results are pending. Documentation inspection confirmed that only
the five requested files exist, the accepted contract and milestones are recorded,
and no working commands or completed features are claimed. This inspection is
not evidence of implemented product behavior.

**Pending user review:** CLI contract and exit codes; name normalization;
URL edge cases; duplicate JSON keys/nonstandard constants; partial-response
error evidence; Docker demonstration acceptance criteria. Dependency versions
and minimum Python version also remain pending.

## 2026-10-03 — Milestone one: configuration validation and minimal CLI

**User prompt and authorization:** Implement only configuration loading,
validation, typed settings, and `python -m endpointcheck validate CONFIG_PATH`.
Adopt strict name/URL/JSON rules and validation exit codes. Use a project-local
environment with pytest, Ruff, and mypy; inspect Python installations. Update all
five documents and verify the requested validation cases. Do not implement HTTP,
threads, reporting, or Docker, install the HTTP dependency, or initialize Git.
The earlier documentation-only authorization is superseded by this prompt.

**Explicit human decisions:** Name whitespace and case-sensitive uniqueness,
HTTP(S)/hostname URLs without surrounding whitespace, credentials, fragments or
invalid ports; localhost/query support without DNS/network; duplicate-key and
nonstandard-constant rejection; positive finite numeric durations excluding
booleans; no defaults, repairs, or timing-order rule; complete validation before
acceptance; CLI exits 0/2 and understandable expected errors without tracebacks.
Requirements are authoritative. No human code review or reflections are claimed.

**AI implementation choices and rationale:** Flat package for a small module CLI;
frozen dataclasses and a tuple for immutable validated settings; JSON hooks for
duplicates/constants; simple validation helpers; first-error reporting instead
of aggregation; argparse for invocation errors. Use UTF-8 files and current
working directory for relative paths. Reject literal URL whitespace/control
characters to avoid parser repair; reject empty ports and use parser port bounds
0–65535. `urlsplit` supplies structural syntax checks without DNS, not exhaustive
RFC/hostname validation. These details are recorded for review.

**Python/environment evidence:** `py --list-paths` could not run because `py`
is absent. `Get-Command` found Python aliases; inspection of the user's local
Python directory found only `pythoncore-3.14-64`. `python --version` reported
3.14.7. An attempted `python list` was not a valid manager command and made no
changes. Selected the installed supported 3.14 line, confirmed against Python's
official version status, and recorded >=3.14 in metadata. Only 3.14.7 is tested.

**Changes:** Added `endpointcheck/config.py`, `cli.py`, module entry point/package
marker, parameterized config tests, subprocess CLI tests, `pyproject.toml`, and
`examples/config.json`. Updated requirements, architecture, README, AGENTS, and
this log. No runtime dependencies, HTTP implementation, or later milestone work.

**Actual setup commands/outcomes:**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pytest ruff mypy
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Environment creation and editable installation succeeded. Initial tool download
was blocked by sandbox networking, then succeeded with approved network access.
Installed pytest 9.1.1, Ruff 0.16.10, and mypy 2.4.0. Direct tool versions are
pinned; transitive dependencies/build tooling are not locked. `pip show requests`
reported that requests is not installed.

**Actual verification commands/outcomes (final implementation):**

| Command | Outcome |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest` | 146 passed, 1.39 seconds |
| `.\.venv\Scripts\python.exe -m ruff check .` | All checks passed |
| `.\.venv\Scripts\python.exe -m ruff format --check .` | 11 files already formatted |
| `.\.venv\Scripts\python.exe -m mypy` | No issues in 6 source files, strict mode |
| `.\.venv\Scripts\python.exe -m endpointcheck validate examples/config.json` | Exit 0; `Configuration valid: 1 endpoint(s).` |
| `.\.venv\Scripts\python.exe -m endpointcheck --help` | Help printed; exit 0 |
| `git diff --check` | No whitespace errors |

**Corrections during verification:** Initial pytest run had 137 passes and nine
setup errors from inaccessible system temp storage; moved its temporary directory
to ignored `.pytest_cache/tmp`, then reran successfully. Initial Ruff run found
import ordering, an implicit subprocess check setting, and a redundant union
under inherited lint settings. Sorted imports, explicitly set `check=False`, and
defined a focused repository lint rule set (E4/E7/E9/F/I) instead of inheriting
external tool policy. Formatting was applied with `ruff format .`.

**Acceptance evidence:** Tests address AC-01 (validation portion), AC-02–06,
and AC-13–17: valid single/multiple endpoints, raw duplicate-key JSON at both
levels, malformed JSON/constants, exact structures/fields, worker/name/URL/status
boundaries, every timing field, threshold above both timeouts, second-endpoint
rejection, and subprocess streams/exit codes including missing/directory/invalid
encoding files and invocation errors. Negative field fixtures change one field
from a valid configuration. AC-07–12 remain pending for later milestones.

**Zero-network evidence and limits:** Reviewed validator imports/call paths;
source search found only `urllib.parse.urlsplit`, no request client or socket/DNS
invocation. A test replaces socket construction and common DNS functions with
failure guards while loading a valid nonexistent-host configuration. This
supports the reviewed/exercised paths, not every possible network mechanism or
future change. Dependencies were downloaded during setup; that is distinct from
validation. Passing tests/types/lint are evidence, not proof of correctness; no
coverage percentage is offered as such.

**Remaining limitations/decisions:** UTF-8 and URL syntax interpretation need
human review; uncommon hostname/percent-escape cases are not comprehensively
validated. Python's integer parsing has its own extreme-input limit. No file-size
cap, all-errors aggregation, or exhaustive input-space validation is claimed.
Cross-version/platform testing and a transitive dependency lock are absent.
HTTP library selection, partial-response error evidence, full reporting/exit
codes, and Docker demonstration behavior remain pending. User review of this
milestone is pending; no commit or push was performed for it.

## 2026-10-03 — Independent review and milestone-one commit

**Independent review reported by the user:** Milestone one passed independent
review. All 146 tests passed; Ruff lint and format checks, strict mypy, and diff
checks passed. Independent cases rejected duplicate JSON keys, boolean worker
limits, and overflowing timing values. These are additional verification
evidence, not proof of correctness. The commands and cases were reported by the
user; this entry does not claim the AI performed that independent review.

**Authorization:** Record the review, inspect all tracked/untracked milestone-one
changes, stage only source, tests, example configuration, project metadata, and
the five updated documents, and commit with
`feat: add strict configuration validation and CLI`. Do not push or start
milestone two. This review supersedes the pending-review status in the previous
historical entry.

## Future entry outline

- Objective and authorized milestone.
- AI recommendations and their rationale.
- Explicit human decisions, linked to the authoritative document.
- Actual changes and acceptance criteria addressed.
- Verification commands, observed outcomes, and limitations (pending until run).
- Mistakes/corrections and learning or interview reflections.
