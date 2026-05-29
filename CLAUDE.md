# Project Coding Standards & AI Instructions

## Core Philosophy
- **Simplicity First:** Code must be readable and maintainable. Avoid "clever" tricks, complex abstractions, or unnecessary patterns. If a feature adds complexity, question if it is truly necessary.
- **Dependency Discipline:**
  - Evaluate every new dependency critically.
  - Do not add dependencies unless strictly necessary.
  - Any decision to add a dependency must be explicitly discussed and justified before implementation.

## Technology Stack
- **Language:** Python 3.14
- **Package/env manager:** uv
- **Test runner:** pytest
- **Linter/formatter/complexity:** ruff (McCabe complexity enabled via `C901`)
- **Type checker:** mypy
- **Config:** `pyproject.toml` is the single config file — no `setup.py`, no `requirements.txt`
- Type hints are expected throughout

## Git Workflow
- Create a new Git branch for every single feature or bug fix.
- Do not commit to `main` or `develop` directly.

## Development Methodology: TDD

**TDD is mandatory. The two phases below are strictly sequential and must never be collapsed into one step.**

### Phase 1 — Write the failing test
- Write only the test. Do not touch implementation code.
- After writing the test, **STOP**. Do not proceed.
- Inform the user: "Failing test written. Please run the test suite and observe the failures."
- Wait for the user to confirm they have seen the failures before doing anything else.
- There are no exceptions to this rule — not for "small fixes," not for "obvious" implementations.

### Phase 2 — Implement (only after user confirms failures observed)
- Write the minimal implementation to make the test pass.
- Run the full test suite (`uv run pytest`). Do not mark the step complete until all tests pass.
- If refactoring is needed, note it explicitly: describe what should be cleaned up and why it was deferred. Do not silently leave technical debt.
- If a shortcut was taken (e.g. hardcoded value, skipped edge case, non-ideal structure), call it out to the user before marking the step complete: state what the shortcut is and what the proper solution would be.

## Code Quality & Review
- **Readability:** Prioritize clear variable names, simple control flow, and explicit logic over brevity.
- **Verification:** Before finalizing any step, run the full quality suite (`uv run pytest`, `uv run ruff check`, `uv run mypy`). Do not mark a step complete until all three pass.
- **Complexity Check:** For every line of code or architectural decision, ask: "Is this necessary?" If the answer is ambiguous, default to the simpler solution.

## Project Structure
- Each project resides in its own isolated directory.
- Documentation specific to the project should be kept in the project root (e.g., `README.md`, `docs/`).
- This `CLAUDE.md` file serves as the primary instruction set for AI assistants working on this codebase.

## Interaction Guidelines for AI
- When proposing a solution, explicitly state if it introduces a new dependency and justify the necessity.
- If a proposed solution seems overly complex, suggest a simpler alternative and explain the trade-offs.
- Always remind the user to run tests before proceeding to the next step.
- If the user asks for a "cool" or "modern" feature that contradicts the "simplicity" rule, gently push back and propose the standard, readable approach.
