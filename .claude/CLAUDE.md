# win-gui-inspector

Dev tool for discovering UI elements in Windows applications using pywinauto. Used during development to scan windows, find element IDs/names/types, and export results to YAML/JSON.

## Quick Start

```bash
uv sync                          # Install dependencies
uv sync --extra dev              # Install with dev tools
uv run win-gui-inspector inspect --title "AppName"   # Interactive inspector
uv run win-gui-inspector map --title "AppName"       # Bulk mapper
uv run pytest --tb=short         # Run tests
uv run ruff check src/ tests/    # Lint
uv run ruff format src/ tests/   # Format
uv run mypy src/                 # Type check
```

## Architecture

```
src/win_gui_inspector/
├── __init__.py      # Public API: UIInspector, WindowMapper
├── __main__.py      # python -m win_gui_inspector
├── cli.py           # Argparse CLI: inspect, map subcommands
├── inspector.py     # UIInspector: connect, scan, REPL, YAML export
└── mapper.py        # WindowMapper: discover windows, map elements, JSON export
```

## Key Patterns

- **No runtime deps on any app** -- uses `pywinauto.Desktop`/`Application` directly
- **Two modes**: interactive REPL (inspector) and batch (mapper)
- **Export**: YAML (inspector) and JSON (mapper)
- **UTF-8 output**: `_ensure_utf8_output()` for non-ASCII text on Windows

## Conventions

- Python 3.11+, Windows-only (pywinauto)
- `uv` for dependency management
- `ruff` for linting and formatting
