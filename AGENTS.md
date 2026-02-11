# AGENTS.md

Instructions for AI coding assistants working on this repository.

## Scope

- Applies to the entire repository.
- Follow any nested `AGENTS.md` files if added later.

## Project Overview

- ComfyUI custom node pack (Python 3.10+).
- Package manager: `uv`.
- Formatting: `black` (line length 100).
- Linting: `ruff` (E, F, W, B, I; ignores E501).

## Key Paths

- `__init__.py`: node registration and mappings.
- `nodes/`: Python node implementations.
- `js/`: frontend JS served by `WEB_DIRECTORY`.
- `wildcards/`: default wildcard folder (gitignored).
- `tmp/`: scratch area (gitignored).

## Setup

Install runtime deps:
```bash
uv sync
```

Install dev deps:
```bash
uv sync --dev
```

## Build / Package

- No build step required for local ComfyUI usage.
- For packaging a wheel:
```bash
uv build
```
- Alternative:
```bash
python -m build
```

## Format and Lint (run after Python edits)

Format:
```bash
uv run black .
```
Lint (auto-fix safe issues):
```bash
uv run ruff check --fix .
```
Run both:
```bash
uv run black . && uv run ruff check --fix .
```

## Tests

- No test suite is currently present.
- If tests are added, place them in `tests/`.
- Suggested default runner:
```bash
uv run pytest
```
- Run a single test file:
```bash
uv run pytest tests/test_file.py
```
- Run a single test by name/pattern:
```bash
uv run pytest -k "pattern"
```
- Run a single test function:
```bash
uv run pytest tests/test_file.py::test_name
```

## ComfyUI Node Conventions

- Each node class defines `INPUT_TYPES`, `RETURN_TYPES`, `RETURN_NAMES`, `FUNCTION`, and `CATEGORY`.
- Use `CATEGORY` prefix `Lumi/` (e.g., `Lumi/Prompt`).
- Register nodes in `__init__.py` via `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`.
- Prefer human-readable `DESCRIPTION` strings on nodes.
- Use `IS_CHANGED` for dynamic inputs (wildcards, provider configs).
- For widgets updated at runtime, send feedback via `PromptServer` when available.

## Code Style Guidelines

### Imports

- Use standard library imports first, then third-party, then local (`from .foo import bar`).
- Keep imports sorted; `ruff` enforces isort rules.
- Use `from __future__ import annotations` in new node files when adding type hints.

### Formatting

- Follow `black` defaults (line length 100).
- Avoid manual alignment; let the formatter decide.

### Typing

- Add type hints for public functions and node `FUNCTION` methods.
- Use concrete container types (`list[str]`, `dict[str, Any]`).
- For ComfyUI node outputs, return tuples matching `RETURN_TYPES`.
- Prefer `Optional[T]` for nullable values and document behavior in docstrings.

### Naming

- Node classes use `Lumi` prefix and `CamelCase`.
- Methods referenced by `FUNCTION` are lower_snake_case verbs.
- Constants are UPPER_SNAKE_CASE.
- Avoid one-letter variables except for small loop indices.

### Error Handling

- Validate user-configured inputs early and raise `ValueError` with clear messages.
- Wrap external API calls with `try/except` and raise `RuntimeError` on failures.
- Preserve exceptions with `raise ... from e` for traceability.
- Avoid swallowing errors silently; log and re-raise.

### Logging and Secrets

- Use `logging` for operational messages; avoid printing.
- Never log API keys or sensitive configuration.
- For provider nodes, store API keys only in memory and avoid serialization.

### Networking

- External requests use `requests` with timeouts.
- Keep base URLs and headers defined close to usage.

### Filesystem

- Use `pathlib.Path` for path manipulation when possible.
- Create directories with `mkdir(..., exist_ok=True)`.
- Avoid writing into gitignored `wildcards/` unless explicitly needed.

## Commit Guidance

- Conventional Commits are required (`feat:`, `fix:`, etc.).
- Do not commit or push without explicit user permission.

## Cursor / Copilot Rules

- No `.cursor` rules or `.github/copilot-instructions.md` were found in this repo.

## Notes

- `tmp/` is safe for scratch work and is ignored by git.
- Wildcard paths can also be configured via `extra_model_paths.yaml` or `LUMI_WILDCARDS_PATH`.
- JS assets in `js/` are served via `WEB_DIRECTORY`.
