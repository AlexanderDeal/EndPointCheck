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

## 2026-10-03 — Milestone three: bounded concurrent orchestration

**Prompt and authorized scope:** Read repository instructions/design, preserve
configuration and checker behavior, and implement only a small runner taking
validated Settings. Submit every endpoint to ThreadPoolExecutor with max_workers;
let queued checks start as workers free up; collect on the main thread and return
configuration order. Ordinary failed/timed-out results must not cancel other
checks. Programming exceptions stay visible; shutdown can wait, without total
deadline or forced cancellation. No load balancer, retries, checking CLI,
report formatting, Docker, commit, or push. Update architecture, README, and
this log; requirements need no behavior changes for this implementation.

**AI implementation choices:** `run_checks` is one function. It maps each
submitted future to its endpoint position, collects values via `as_completed`
on the calling thread, and restores order by index. The intended caller is the
main thread; there is no enforced thread-identity check. Workers return existing
CheckResult objects without printing or sharing a report. All checks are submitted
up front to keep the design small. There is no new dependency or modification
to config, checker, CLI, or their existing tests.

**Changes:** Added `endpointcheck/runner.py` and `tests/test_runner.py`; updated
architecture, README, and this log. No application work beyond milestone three.
Requirements behavior remains unchanged (AC-08 queue exclusion, AC-11 bounded
concurrency/isolation, and AC-12 caller collection/order already apply). Full CLI
reporting remains deferred, so AC-12's reporting portion is not yet implemented.

**Independent observations in tests:**

- Real concurrent loopback server counts active handlers and records its maximum
  under a lock. Seven checks run with each of 1, 2, and 3 workers. Assertions
  check the upper bound and actual overlap when workers >1; one worker gives a
  maximum of one. Final-byte delivery and decrement share the counting lock to
  avoid handler-tail bookkeeping creating artificial overlap.
- Simulated check counters and a bounded barrier observe entire check-call
  concurrency; maximum equals the worker limit. With one worker, start and finish
  records both match configuration order.
- Events hold the first check until a queued third check starts and finishes.
  Recorded completion order is second/third/first, while results return
  first/second/third. Worker identities differ from the main thread; an iterator
  spy records collection on the main thread. No output is produced.
- A real single-worker run returns failed/timed-out/healthy/healthy, preserving
  received statuses, names, and exactly one result per endpoint. Good checks run
  after the ordinary failures rather than being cancelled.
- A simulated RuntimeError propagates rather than yielding a fake result; queued
  work completes during executor shutdown, and worker threads are no longer alive
  after propagation.
- A first simulated check occupies the only worker. Once both futures are
  submitted, an event-controlled helper advances a fake monotonic clock by 100
  seconds before release. The queued check uses the actual HTTP checker/server,
  and records only 0.25 elapsed seconds. This verifies the measurement boundary
  without fragile wall-clock queue timing.
- Test-server event waits and socket writes are bounded; teardown signals waits,
  shuts down the server, joins non-daemon handlers and the server thread, and
  asserts zero active handlers and no surviving server thread. Controller threads
  are also joined; simulation waits/barriers have explicit timeout bounds.

**Actual final verification:**

| Command | Outcome |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest` | 181 passed in 6.78 seconds (171 existing + 10 runner cases) |
| `.\.venv\Scripts\python.exe -m ruff check .` | All checks passed |
| `.\.venv\Scripts\python.exe -m ruff format --check .` | 15 files already formatted |
| `.\.venv\Scripts\python.exe -m mypy` | No issues in 10 source files, strict mode |
| `git diff --check` | No whitespace errors |

**Intermediate corrections:** Ruff removed an unused import; formatting applied
with `ruff format .`. Initial strict mypy identified test references to imported
runner attributes that were not explicitly exported; tests now reference the
original checker/as_completed imports while patching runner lookups. Focused
runner tests passed (10 cases). Strengthened queue-time synchronization to require
both submissions before releasing the first worker, and serialized server final
byte/count decrement to remove counter-tail ambiguity. All final checks passed
after these refinements.

**Limitations and pending decisions:** Server request counts measure handler
activity, not DNS, TCP setup, all client-side computation, or cleanup. Simulated
whole-check counters complement this observation; neither exhausts scheduler
behavior. Queue exclusion uses a controlled clock, not a performance benchmark.
Caller-thread collection assumes application calls from the main thread. The
executor bounds active checks but all futures are queued at once (O(endpoint
count) storage). Programming errors may surface only after shutdown waits for
running/queued checks; no full result list is promised in that case. No total
deadline/cancellation is added; indefinitely arriving data can occupy a worker
and delay shutdown. TLS/proxy behavior remains untested, and verification is on
the existing Windows/Python 3.14.7 environment. Passing checks provide evidence,
not exhaustive correctness. Human review of milestone three is pending.
Complete CLI reporting/exit codes and Docker/demo behavior remain for later
milestones. No commit or push was performed.

## 2026-10-03 — Independent milestone-three review and commit

**User-reported independent evidence:** Milestone three passed independent source
and test review. Independent checks reported 181 tests passed, Ruff lint and
format checks passed, strict mypy passed, and `git diff --check` passed. No
blocking issues were identified. This records the user's reported review rather
than claiming the AI performed it. It supersedes the pending-review status in
the preceding historical entry.

**Limits:** These findings are evidence, not exhaustive correctness. Server
counters observe handler activity, not every client stage; controlled clock
tests establish timing boundaries rather than real queue-performance estimates.
Verification remains on Windows/Python 3.14.7; TLS/proxy behavior is untested.
Executor shutdown may wait for running/queued checks, with no total deadline or
forced cancellation. Independent review does not remove these limitations.

**Authorization:** Review and stage only milestone-three changes, then commit
with `feat: add bounded concurrent endpoint checks`. Do not push or begin
milestone four.

## 2026-10-04 — Milestone four: checking CLI, reports, and installed command

**Prompt and authorization:** Read instructions/requirements/design; preserve
validator, checker, and runner behavior. Add installed `endpointcheck validate`
and `endpointcheck check`, retaining equivalent module commands. Create a
project.scripts entry to the existing main function and actually reinstall.
Checking must validate before running, report in configuration order, return
0 for all healthy, 1 for any completed nonhealthy result, and 2 for expected
input/file/invocation errors. Programming exceptions stay visible. Agree/report
the supplied plain-text evidence/counts/safe-display contract in requirements
before implementation. Add subprocess tests for both entry points and bounded
server observations, run all checks, and update documentation. No Docker,
retries, JSON output, new dependencies, commit, or push. Stop for review.

**Explicit user decisions:** Command names and equivalent entry points; whole-file
validation before runner invocation; ordered reports, health exit codes, output
streams, preserved status/error evidence, zero body output, four summary counts
including zeros, control escaping in names/URLs/errors, and classification from
the existing unrounded result. Requirements were updated before code changes
with this contract and AC-21–25.

**AI design choices:** A focused pure `reporting.py` formats blocks and a summary,
with `unavailable` for absent status and seconds rounded to three decimals.
Printable characters remain readable; nonprintable Unicode/terminal controls
use visible Python backslash escapes, with literal backslashes escaped to avoid
ambiguity. The small argparse subclass sanitizes invocation error messages;
expected configuration/file errors are sanitized too. Only loading errors are
caught as expected user errors. The CLI invokes the unchanged runner on the main
thread and decides exit 0/1 from outcomes, never formatted times. The existing
main function is shared by module invocation and project.scripts.

**Changes:** Updated `cli.py`, `pyproject.toml`, requirements, architecture,
README, and this log; added `reporting.py`, `test_reporting.py`, and
`test_check_cli.py`. Adjusted the old invalid-subcommand fixture from `check` to
`unknown` now that check is legitimate. Validator/checker/runner source is
unchanged; no runtime/development dependencies were added.

**Actual setup and manual verification:**

| Command | Outcome |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"` | Reinstalled successfully with approved access for isolated build tooling |
| `.\.venv\Scripts\endpointcheck.exe --help` | Exit 0; both validate and check listed |
| `.\.venv\Scripts\endpointcheck.exe validate examples/config.json` | Exit 0; `Configuration valid: 1 endpoint(s).` |
| `.\.venv\Scripts\python.exe -m endpointcheck validate examples/config.json` | Same success output and exit 0 |

Verified the installed `.venv/Scripts/endpointcheck.exe` exists. Checking commands
were exercised by subprocess tests using actual generated configuration paths
and controlled localhost URLs, rather than assuming a demonstration API exists
at the README sample's port 8000.

**Final verification commands/outcomes:**

| Command | Outcome |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest` | 224 passed in 20.23 seconds (181 previous cases plus 43 new cases) |
| `.\.venv\Scripts\python.exe -m ruff check .` | All checks passed |
| `.\.venv\Scripts\python.exe -m ruff format --check .` | 18 files already formatted |
| `.\.venv\Scripts\python.exe -m mypy` | No issues in 13 source files, strict mode |
| `git diff --check` | No whitespace errors |

**Corrections:** Initial mypy check identified that argparse's `error` override
must return `Never`, not `None`; corrected its annotation. Applied formatting
with Ruff. Focused reporting/checking subprocess tests passed, then added further
body-failure and control-containing invocation cases before the final full run.

**Evidence and acceptance coverage:** Both launcher and module subprocesses run
from temporary working directories outside the repository root, using the
editable installation. Assertions verify all-healthy/mixed runs, exit 0/1/2,
stdout/stderr, endpoint order/details, received 200 after stalled/broken body,
unavailable status before headers, all four summary counts including zeros,
safe control-containing names, and no response-body output. Invalid JSON,
boolean worker limits, and an invalid later endpoint yield no report and zero
received test-server requests. Validation also yields zero received requests.
Existing guarded validator tests still pass. Help/error behavior is compared
exactly between entry points; real checking output comparison ignores independent
measured durations. Synthetic results independently specify exact report output,
error/URL/control escaping, and a slow 0.50001-second result displayed as 0.500
but still exiting 1. A simulated programming bug propagates without a report.
This addresses AC-21–25 and completes the CLI-reporting portion of AC-12.

**Limits and assumptions:** Server counters observe received HTTP requests, not
all DNS/socket activity; combined source review and existing guarded tests support
network-free validation without claiming an exhaustive audit. URL controls are
already invalid configuration; formatter URL safety is tested with synthetic
results. Test subprocesses explicitly select UTF-8; unusual host console encodings
are not comprehensively tested. Safe display is not redaction: URLs/error messages
may include query data. The existing small finite-response assumption, no total
deadline/cancellation guarantee, and untested TLS/proxy scenarios still apply.
Only Windows/Python 3.14.7 and the existing pinned dependencies were verified.
Passing tests/types/lint are evidence, not exhaustive correctness. Human review
of milestone four is pending. Docker/demo scenarios and stricter exotic URL
syntax decisions remain deferred. No commit or push was performed.

## 2026-10-04 — Independent milestone-four review and commit

**User-reported independent evidence:** Milestone four passed independent source
and test review. Independent checks reported 224 tests passed, Ruff lint and
format checks passed, strict mypy passed, and `git diff --check` passed. No
blocking issues were identified. This records the user's evidence, not an
AI-performed independent review or exhaustive correctness. It supersedes the
pending-review status in the preceding historical entry.

**Continuing limitations:** TLS/proxy behavior remains untested. Test subprocesses
select UTF-8; unusual console encodings remain incompletely verified. Server
observations and the passing checks do not exhaust all inputs, terminal behavior,
or network paths. The existing timeout and executor shutdown limitations remain.

**Authorization and staging scope:** Commit only milestone-four source, tests,
metadata, and documentation changes with
`feat: add checking CLI and readable health reports`. Leave the newly observed
untracked `examples/manual-invalid.json` outside this commit. Do not push or begin
milestone five.

## 2026-10-05 — Milestone five: packaging and controlled demonstration

**User prompt and authorization:** Implement milestone five only: check Docker,
Compose and daemon first; preserve inspector behavior; provide two services, a
concurrent controlled API, readiness, mixed and all-healthy scenarios, non-root
normal-install images, build-context exclusions, local/container verification
and documentation. Do not install Docker, change machine settings, commit or
push. Stop for review. The full prompt is in the conversation; approved product
behavior is recorded as AC-26–29 in requirements rather than duplicated here.

**Explicit user decisions:** Standard-library demo preferred; service-name
networking, health-gated startup, finite bodies, flushed timeout headers,
specified delays/timeouts, four mixed workers, expected report order/classifications
and exit codes, no default host ports, no inspector persistence/retries/deadlines.

**AI design recommendations and rationale:** A separate `demo_api` package keeps
demonstration behavior out of the inspector. One multi-target Dockerfile avoids
duplicating base/user setup; normal installation creates the existing launcher.
Python 3.14 slim follows metadata and uses a moving patch tag rather than an
unverified digest. UID/GID 10001 is an implementation choice. An allowlist
`.dockerignore` limits context to needed inputs. `/ready` checks startup only.
Healthy/error thresholds are five seconds and connect timeouts two seconds;
these provide generous local timing margins without changing agreed inspector
semantics. The healthy scenario contains one healthy endpoint. Operational
commands remain explicitly unverified until real container execution.

**Changes:** Added Dockerfile, Compose file, `.dockerignore`, `demo_api` server,
two readable demo configurations, focused demo tests and DEMO.md. Expanded strict
mypy scope to demo code. Updated requirements, architecture and README. Existing
inspector source and AGENTS.md were preserved. The unrelated untracked
`examples/manual-invalid.json` was left untouched.

**Actual environment checks:** `docker --version` reported 29.8.1;
`docker compose version` reported 5.5.1. Sandbox Docker commands could not read
the user's Docker config; a read-only elevated `docker info` confirmed the real
`desktop-linux` context and failed because the Docker Desktop Linux daemon pipe
was absent. No daemon was started or settings changed. Elevated
`docker compose -p endpointcheck-m5-review config --quiet` exited 0 without
warnings. No images, containers or networks were created; cleanup was therefore
unnecessary. Build/run/network/readiness/user/installation checks inside actual
containers were not run and remain unverified.

**Actual verification:**

| Command | Observed result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest tests/test_demo_api.py -s` | Final focused run: 11 passed in 5.73 seconds, no warnings; two mixed reports (inspector exit 1 each), one healthy report (inspector exit 0). Earlier `-q -s` runs are covered by corrections below. |
| `.\.venv\Scripts\python.exe -m pytest` | 235 passed in 26.20 seconds, no warnings |
| `.\.venv\Scripts\python.exe -m ruff check .` | All checks passed |
| `.\.venv\Scripts\python.exe -m ruff format --check .` | 22 files already formatted |
| `.\.venv\Scripts\python.exe -m mypy` | Strict mode: no issues in 16 source files |
| `git diff --check` | Exit 0, no whitespace errors; Git emitted normal LF/CRLF conversion notices |

**Observed local output:** The first focused mixed run used ephemeral loopback
port 53530, reporting healthy 200 at 0.007 seconds, slow 200 at 0.605 seconds,
failed 500 at 0.006 seconds with expected/received status error, and timed out
200 at 0.296 seconds with a streamed-body `ConnectionError` read-timeout message.
Summary was `healthy=1, slow=1, failed=1, timed out=1`. Repeat used port 53536 and
the same classifications/order/counts. Healthy-only used port 53542, status 200,
0.015 seconds and summary `healthy=1, slow=0, failed=0, timed out=0`.
Subprocess return codes were 1, 1 and 0 respectively; pytest's wrapper exit
code was separate. These were real local CLI processes, not container output.
The final focused rerun again returned 1, 1 and 0 without warnings: ports
54904/54910 for mixed and 54916 for healthy, with identical outcomes/counts;
first mixed durations were 0.005/0.623/0.004/0.312 seconds and healthy-only 0.019.

**Independent observations and coverage:** Direct `http.client` tests observe
finite bodies/statuses, delayed slow headers and flushed timeout headers before
body delivery. Event-controlled delay holds two actual HTTP handlers open while
readiness completes, establishing overlap without scheduling-time comparisons.
Real delays are verified separately. Local CLI integration validates original
service-name configs, then substitutes only loopback host/port in temporary
copies. It verifies order, outcomes, counts, status retention and exit codes
across repeated mixed runs. A client disconnect is observed without stderr
tracebacks after joining handlers. Fixture/client waits are bounded, and
non-daemon handler threads are joined. These checks address local AC-26–27;
AC-28–29 have source/configuration evidence but need runtime container evidence.

**Failures and corrections:** Initial direct HTTP tests incorrectly treated
`HTTPConnection` as a context manager, causing eight test failures and mypy
errors. Replaced that with `contextlib.closing` and explicit IPv4 host/server
port. An initial successful focused run then warned because a fixture closed
the listening socket before stopping its serving loop. Corrected shutdown order;
the final full suite passed without that warning. Ruff removed an unused import
and formatted the new tests/server.

**Limits and review status:** No claim of exhaustive correctness or human review
of milestone five. Docker daemon absence prevents actual image builds, Linux
runtime/non-root/normal-install checks, service-name DNS, Compose startup gates,
container inspector output/exit codes and cleanup verification. Local socket
observations do not cover every client activity stage; disconnect behavior is
platform dependent. Moving image/build-tool versions are not fully reproducible.
The demo server is not hardened for hostile clients. Existing small finite-body,
no total deadline/cancellation, TLS/proxy and console-encoding limitations remain.
No milestone-five product ambiguity blocks this implementation; future stricter
URL syntax policy remains pending in requirements. User review and later real
container verification remain required. No commit or push was performed.

## 2026-10-05 — Milestone-five container runtime verification

**User authorization:** Docker is now running. Follow DEMO.md; build both images,
run mixed twice and healthy once; verify readiness, service networking, actual
inspector exits/outcomes/status evidence and UID 10001; update supported claims
and clean up only this project's resources. No commit or push.

**Actual commands and results:** Commands ran from the repository with the user
Docker context (elevated tool execution was needed to access Docker). First,
`docker info --format '{{.ServerVersion}}'` returned 29.8.1. Project-scoped
`docker compose -p endpointcheck-demo ps -a`, `docker ps -a --filter
name=endpointcheck-demo-healthy` and `docker network ls --filter
name=endpointcheck-demo` showed the documented resource names unused.

- `docker compose -p endpointcheck-demo config --quiet`: exit 0.
- `docker compose -p endpointcheck-demo build`: exit 0, both targets built.
  Normal pip installation built the endpointcheck wheel and installed pinned
  requests/urllib3. Python base resolved to digest
  `sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151`.
- `docker compose -p endpointcheck-demo up --abort-on-container-exit
  --exit-code-from inspector`: wrapper exit 1, captured immediately in
  `$mixedWrapperExit`. `docker compose -p endpointcheck-demo ps -aq inspector`
  supplied the ID; `docker inspect --format '{{.State.ExitCode}}' $inspectorId`
  returned actual inspector exit 1. `docker compose -p endpointcheck-demo logs
  inspector` confirmed the report. Outcomes healthy/slow/failed/timed out in
  configuration order, statuses 200/200/500/200, durations
  0.005/0.606/0.006/0.303 seconds, summary one each.
- `docker compose -p endpointcheck-demo up --force-recreate
  --abort-on-container-exit --exit-code-from inspector`: repeat wrapper exit 1
  and inspected inspector exit 1. Same order/outcomes/statuses/counts; durations
  0.005/0.605/0.003/0.302 seconds. Error was expected 200/received 500;
  timeout error was streamed `ConnectionError` read timeout for `demo-api:8000`.
- `docker compose -p endpointcheck-demo up -d --wait demo-api`: exit 0, healthy.
  `docker compose -p endpointcheck-demo run --name endpointcheck-demo-healthy
  inspector check /app/demo/all-healthy.json`: wrapper exit 0, captured in
  `$healthyWrapperExit`. `docker inspect --format '{{.State.ExitCode}}'
  endpointcheck-demo-healthy`: actual inspector exit 0. Report healthy 200,
  0.004 seconds, summary healthy=1, slow=0, failed=0, timed out=0.

**Runtime evidence:** `docker inspect` health-log/start timestamps established
readiness before inspector execution. First successful `/ready` check ended
21:20:13.776875695Z; inspector started 21:20:14.271858391Z. Repeat check ended
21:20:42.521971891Z; inspector started 21:20:43.018827390Z. Compose also printed
API Healthy before Inspector Starting. Post-stop health status was unhealthy;
that does not negate the successful startup observations. Reports used original
`http://demo-api:8000` URLs, with no local substitutions or published host ports.

During repeat, a bounded polling observer ran `docker top
endpointcheck-demo-inspector-1 -eo uid,pid,args` and the equivalent API command.
Live processes: UID 10001, PID 1049, installed endpointcheck launcher; UID 10001,
PID 974, `python -m demo_api.server`. Container config also specified
10001:10001. `docker compose -p endpointcheck-demo exec demo-api id -u`
returned 10001; `exec demo-api python --version` returned Python 3.14.8.

Additional inspector probes used `docker compose -p endpointcheck-demo run --rm
--no-deps --entrypoint python inspector -c ...`: `os.getuid()` and `/proc/1/status`
reported 10001, and `socket.gethostbyname('demo-api')` returned 172.19.0.2.
Initial metadata lookup from /app found source-tree metadata, so repeated with
`--workdir /tmp`. The latter probe printed installed module path
`/usr/local/lib/python3.14/site-packages/endpointcheck/__init__.py`, distribution
directory `/usr/local/lib/python3.14/site-packages`, and direct_url.json with
`dir_info: {}` (no editable flag), confirming normal installation independently
of source-directory imports.

Exact probe commands (in addition to the documented DEMO.md sequence):

```powershell
docker compose -p endpointcheck-demo exec demo-api id -u
docker compose -p endpointcheck-demo exec demo-api python --version
docker compose -p endpointcheck-demo run --rm --no-deps --entrypoint python inspector -c "import os, socket, importlib.metadata; print('uid=', os.getuid()); print('demo-api=', socket.gethostbyname('demo-api')); print('distribution=', importlib.metadata.distribution('endpointcheck').locate_file('')); print('pid1=', open('/proc/1/status').read().split('Uid:')[1].splitlines()[0])"
docker compose -p endpointcheck-demo run --rm --no-deps --workdir /tmp --entrypoint python inspector -c "import endpointcheck, importlib.metadata; d=importlib.metadata.distribution('endpointcheck'); print('module=', endpointcheck.__file__); print('distribution=', d.locate_file('')); print('direct_url=', d.read_text('direct_url.json'))"
```

**Corrections and observations:** No source/container changes were needed.
Updated current README, REQUIREMENTS, ARCHITECTURE and DEMO claims from unverified
to verified only for these scenarios; historical evidence remains unchanged.
Build pip emitted its usual root-install warning during image construction;
runtime processes were verified non-root. Extra one-off probes warned that the
named healthy container was an orphan; it was our known stopped test container,
and we removed it explicitly rather than using broad orphan cleanup. Compose
stopped API with exit 137 after each mixed run. That is an API shutdown
observation, not inspector failure; graceful SIGTERM handling is not implemented
and this limitation is now documented. Readiness remains a startup observation.

**Cleanup:** `docker rm endpointcheck-demo-healthy` and
`docker compose -p endpointcheck-demo down` succeeded. Probe containers used
`--rm`. Final `docker ps -a --filter
label=com.docker.compose.project=endpointcheck-demo` and `docker network ls
--filter label=com.docker.compose.project=endpointcheck-demo` returned no rows.
Only this verification's containers/network were removed. Built images and
build cache were retained for subsequent demo use; no global prune.

**Scope and limitations:** Runtime evidence now covers AC-28–29's controlled
build/install/non-root/network/readiness/outcome requirements and repeats AC-27
in containers. It does not prove exhaustive correctness, failure recovery,
cross-platform reproducibility, TLS/proxy behavior or unusual console encodings.
No Python/configuration code changed in this follow-up; the previously recorded
235-test/static-check run remains the source verification evidence. Final
`git diff --check` after documentation updates exited 0 with no whitespace errors
(normal LF/CRLF conversion notices only). No human milestone-five
review is claimed; no commit or push was performed.

## 2026-10-05 — Milestone-five acceptance and commit authorization

The user explicitly accepted milestone five and authorized a commit with
`feat: add reproducible Docker API demo`. This records acceptance only: the user
did not provide actual manual run evidence, so no human-performed runtime checks
are claimed. Earlier local and container verification remains AI-performed
evidence, not exhaustive correctness. Historical pending-review statements are
superseded by this acceptance.

Review and stage only milestone-five packaging, demo code/configurations/tests,
metadata and documentation. Preserve the documented missing graceful SIGTERM
handling and observed API exit 137. Leave unrelated
`examples/manual-invalid.json` untracked. Do not add features or push.

## Future entry outline

- Objective and authorized milestone.
- AI recommendations and their rationale.
- Explicit human decisions, linked to the authoritative document.
- Actual changes and acceptance criteria addressed.
- Verification commands, observed outcomes, and limitations (pending until run).
- Mistakes/corrections and learning or interview reflections.
