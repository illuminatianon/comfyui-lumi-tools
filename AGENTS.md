# AGENTS.md

Instructions for AI coding assistants working on this codebase.

## Project Overview

This is a ComfyUI custom node pack (comfyui-lumi-tools) providing utility nodes for prompt processing, wildcards, and seed management.

- **Language**: Python 3.10+
- **Package Manager**: `uv`
- **Formatter**: `black` (line-length 100)
- **Linter**: `ruff`

## After Every Code Edit

Run formatting and linting after making changes to Python files:

```bash
uv run black .
uv run ruff check --fix .
```

Or run both together:

```bash
uv run black . && uv run ruff check --fix .
```

## Project Structure

```
├── __init__.py           # Node registration (NODE_CLASS_MAPPINGS)
├── nodes/                # Node implementations
│   ├── __init__.py       # Node exports
│   ├── seed.py
│   ├── show_text.py
│   ├── shuffle_prompt.py
│   ├── wildcard_processor.py
│   └── wildcards.py      # Wildcard utilities
├── js/                   # Frontend JavaScript
├── pyproject.toml        # Project config
└── wildcards/            # Default wildcard location (gitignored)
```

## ComfyUI Node Conventions

- All nodes must define `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, and `CATEGORY`
- Node classes are registered in `__init__.py` via `NODE_CLASS_MAPPINGS`
- Display names go in `NODE_DISPLAY_NAME_MAPPINGS`
- Category prefix: `Lumi/`

## Dependencies

Install with:

```bash
uv sync
```

Dev dependencies:

```bash
uv sync --dev
```

## Linting Rules

From `pyproject.toml`:

- Ruff selects: E, F, W, B, I (errors, pyflakes, warnings, bugbear, isort)
- Ignores: E501 (line length - handled by black)
- Excludes: `tmp/` directory

## Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) with semantic-release:

- `feat:` - new features (minor version bump)
- `fix:` - bug fixes (patch version bump)
- `docs:`, `style:`, `refactor:`, `test:`, `ci:`, `chore:` - no version bump

Do NOT commit or push without explicit user permission.

## Testing

Currently no test suite. When adding tests, place them in a `tests/` directory.

## Notes

- The `tmp/` directory is for scratch/reference files and is gitignored
- Wildcard files are gitignored - users configure paths via `extra_model_paths.yaml`
- Frontend JS files in `js/` are served via `WEB_DIRECTORY`

