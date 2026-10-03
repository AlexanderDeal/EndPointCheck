# EndpointCheck

A planned small Python command-line API health and latency inspector, also used
as a learning project for an interview about AI-assisted engineering.

**Implementation has not started.** This repository currently contains initial
documentation only. There is no application, working CLI, test suite, Docker
setup, or controlled demonstration API. No installation or run commands are
available yet.

The agreed product will validate JSON before checking GET endpoints with bounded
concurrency and report healthy, slow, failed, or timed-out results in configuration
order. Separate connection and read-inactivity timeouts will not enforce a total
wall-clock deadline. Version one will target small, finite API responses without
enforcing a response-size limit.

## Documentation

- [REQUIREMENTS.md](REQUIREMENTS.md): source of truth for behavior, configuration
  examples, numbered acceptance criteria, and unresolved product decisions.
- [ARCHITECTURE.md](ARCHITECTURE.md): accepted component design, proposed
  dependencies, tradeoffs, milestones, and planned verification.
- [AGENTS.md](AGENTS.md): repository working instructions.
- [AI_ENGINEERING_LOG.md](AI_ENGINEERING_LOG.md): AI recommendations, explicit
  user decisions, and pending verification evidence.

## Implementation roadmap

1. Configuration validation and a minimal validation CLI.
2. Single-endpoint checking.
3. Bounded concurrent orchestration.
4. Complete CLI reporting.
5. Docker and a controlled demonstration API.

Each milestone is intended to be a small, independently verified change for human
review. Usage and verification commands will be documented once they exist.
