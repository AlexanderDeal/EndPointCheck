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

## 2026-10-03 — Milestone two: single-endpoint HTTP checking

**Prompt and authorized scope:** Implement only a checker accepting one validated
endpoint and returning name, URL, outcome, elapsed seconds, optional status, and
optional informative error. Preserve status after partial-body failure; headers
alone do not establish success. Use requests, disabled redirects, separate
connection/read-inactivity limits, monotonic full-body timing, complete body
consumption without retaining the body in results, and cleanup on all paths.
No printing, threads, retries, shared reports, checking CLI, Docker, commit, or
push. Preserve milestone one. Run the full required checks and document evidence.
Human review of milestone two has not occurred.

**Explicit user decisions:** Result evidence, timing/resource behavior,
classification precedence, visible unexpected programming errors, and required
controlled-server cases (including body stalls, refusal, incomplete download,
redirect target avoidance, and regularly arriving data). Simulate connection
timeout; use a controlled clock for equality. Requirements now include AC-18–20
and the partial-body evidence addition to AC-10.

**AI choices and rationale:** Frozen `CheckResult` in `checker.py`, one local
Session per check, 64-KiB streaming chunks discarded after reading, and a local
response hook for status capture and complete consumption. The hook prevents
requests' redirect preparation from consuming a body and handling failures before
the checker sees them. End time is captured immediately on consumption completion
or on a request exception; cleanup is outside the measurement. Catch only
`requests.RequestException`; programming errors propagate through cleanup.
Errors are exception type plus message, or an expected/received-status explanation.

**Dependency and exception evidence:** Installed requests 2.34.2, urllib3 2.8.0,
and types-requests 2.33.0.20260906 in `.venv`. Pin requests and urllib3 at runtime;
urllib3 is explicit because the checker imports its exception type. The stubs
are a development dependency. Inspected installed `Response.iter_content`,
`Session.send`, and `Session.resolve_redirects` with `inspect.getsource` and
consulted official requests source documentation. `iter_content` raises
`ConnectionError(ReadTimeoutError(...))` for a streamed read timeout; a delayed
header raises `ReadTimeout`. Independent real-library tests assert both shapes.
The mapper checks `requests.Timeout` or the typed `ReadTimeoutError` argument
of `requests.ConnectionError`, not message strings or all connection errors.

**Changes:** Added `endpointcheck/checker.py` and `tests/test_checker.py`.
Updated runtime/stub metadata, requirements, architecture, README, and this log.
Config parsing and validation CLI source/tests are unchanged. Test-only server
threads provide controlled HTTP responses; application code starts no threads.
Server fixtures signal stalled handlers to finish, shut down/close the server,
join the thread, and assert termination. Loopback proxy exclusion is test-local.

**Actual commands and final outcomes:**

| Command | Outcome |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pip install requests types-requests` | Installed successfully with approved network access |
| `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"` | Editable installation succeeded with updated metadata |
| `.\.venv\Scripts\python.exe -m pytest` | 171 passed in 6.23 seconds (146 existing + 25 new cases) |
| `.\.venv\Scripts\python.exe -m ruff check .` | All checks passed |
| `.\.venv\Scripts\python.exe -m ruff format --check .` | 13 files already formatted |
| `.\.venv\Scripts\python.exe -m mypy` | No issues in 8 source files, strict mode |
| `git diff --check` | No whitespace errors |

**Intermediate corrections:** Ruff removed an unused import and formatting was
applied. mypy required narrowing the default adapter to `HTTPAdapter` in the
no-retries test. The first full run had 167 passes and a refusal-case failure:
Windows had not reported refusal before the 0.4-second connection limit. Raised
that test's allowance to five seconds; observed refusal in about two seconds.
Added broken/stalled redirect bodies and consumption in the response hook so
redirect preprocessing cannot obscure body failure. Added session/response
cleanup assertions, including visible programming errors during body consumption.
Final checks above passed after these changes.

**Verification scope:** Controlled loopback cases cover fast/slow complete
responses, unexpected status before latency classification, direct redirects
(including expected 302), delayed headers, partial-body stalls, incomplete bodies,
refusal, full-body timing, and trickling data taking longer than the inactivity
limit. Controlled clock tests check below/equal/above threshold. A focused fake
raises `ConnectTimeout` and checks timeout tuple/redirect/stream flags and default
zero retries. Real-network tests use separated timing margins. No public
unreachable-host timeout assumption is used. AC-07–10 and AC-18–20 are exercised
for a single check; queue timing, bounded concurrency, collection/report order,
and unrelated-check isolation remain for later milestones.

**Limitations and assumptions:** Tested on Windows/Python 3.14.7 with these pinned
libraries; exception shapes must be revisited on upgrades. Standard requests
proxy/environment, certificate checking, and decompression remain enabled.
TLS/proxy/internet scenarios are not tested. DNS/connect behavior is not a total
deadline, and regularly arriving data may continue indefinitely. No body-size or
total-duration cap is added. Timing includes requests preparation and decoded
body consumption, but excludes session construction and cleanup. Very large
accepted numeric configuration values may exceed transport limits; this milestone
does not change validation or silently coerce them. Tests/source inspection
provide evidence, not proof of correctness. Full reports/exit codes, concurrency,
and Docker demonstration rules remain unresolved/planned. Milestone-two human
review is pending; no commit or push was performed.

## 2026-10-03 — Independent milestone-two review and commit

**User-reported independent evidence:** Milestone two passed independent source
and test review. Independent verification reported 171 tests passed, Ruff lint
and format checks passed, strict mypy passed, and `git diff --check` passed.
No blocking issues were identified. TLS/proxy behavior remains untested.
These findings provide evidence, not exhaustive correctness. This entry does
not claim the AI performed the independent review or that the user understands
every implementation detail. The review supersedes the pending-review status
in the preceding historical entry.

**Authorization:** Review and stage only milestone-two changes and commit with
`feat: add single-endpoint HTTP health checks`. Do not push or begin milestone
three.

## Future entry outline

- Objective and authorized milestone.
- AI recommendations and their rationale.
- Explicit human decisions, linked to the authoritative document.
- Actual changes and acceptance criteria addressed.
- Verification commands, observed outcomes, and limitations (pending until run).
- Mistakes/corrections and learning or interview reflections.
