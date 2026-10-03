# Repository working instructions

- Read [REQUIREMENTS.md](REQUIREMENTS.md) for product behavior and acceptance
  criteria, and [ARCHITECTURE.md](ARCHITECTURE.md) for design. Reference those
  documents instead of duplicating their rules here.
- Favor simple, maintainable Python and small changes that the user can review
  and understand. Explain material tradeoffs.
- Stay within the authorized milestone. Do not treat a proposal or pending
  decision as authorization to implement it. Follow the currently authorized
  milestone and stop at its boundary for user review.
- Identify unresolved behavior before implementing dependent choices. Record
  approved product decisions in requirements and design decisions in architecture.
- Verify each implementation milestone against its acceptance criteria using
  independent evidence. Record actual commands and outcomes; do not claim checks
  passed without running them. Use the project-local virtual environment and
  run pytest, Ruff lint/format checks, and mypy as documented in README.
- Keep [README.md](README.md) accurate about what exists and how it can be used.
- Update [AI_ENGINEERING_LOG.md](AI_ENGINEERING_LOG.md) with AI recommendations,
  explicit user decisions, changes, verification evidence, and corrections.
- Do not add unrelated features or dependencies. Do not introduce parallel agent
  work unless the user explicitly requests it.
