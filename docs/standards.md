# BLUX-cA Repository Standards

This document summarizes the house style used across `ca.py`, `ca/cli.py`, and related modules. New code should align with these conventions.

## CLI Conventions
- Use [Typer](https://typer.tiangolo.com/) for subcommands. Group related commands via `typer.Typer` and attach with `add_typer`.
- Default output is concise and human-readable. Prefer Rich tables or `console.print_json` when structured output is needed.
- Non-zero exit codes signal user-facing errors; raise `typer.Exit(code=1)` or `SystemExit(1)` after printing a clear message.
- Provide `--help` for every command and avoid hidden flags. Respect environment overrides such as `DATASET_DIR`, `BASE_MODEL`, and `RUN_NAME` when present.

## Logging and Output
- Rely on lightweight logging: Rich console output for user-facing flows; `print` only for simple scripts. Avoid noisy debug logs unless explicitly requested.
- For background helpers, prefer the standard `logging` module with INFO defaults and DEBUG gated by env flags.

## Configuration
- Store defaults in versioned YAML (e.g., `train/configs/`).
- Precedence: environment variables > CLI flags > config file defaults.
- Validate configuration early and fail fast with actionable error text.

## Error Handling
- Catch expected user errors (missing paths, invalid config) and present actionable messages before exiting non-zero.
- Let unexpected exceptions propagate to aid debugging during development.

## Paths and Filesystem
- Use `pathlib.Path` for all filesystem interactions and support execution from any working directory.
- Resolve repo-relative paths via `Path(__file__).resolve()` parents when needed instead of relying on CWD.
- Write generated artifacts to `runs/` (gitignored) and avoid committing binaries or checkpoints.

## Code Style
- Target Python 3.10+ with type hints on public functions and return types.
- Keep functions small and focused. Include brief module and function docstrings describing intent and behavior.
- Follow `black` formatting and `ruff` lint rules defined in `pyproject.toml`.

## Testing and Tooling
- Provide `python -m compileall`-clean code for scripts.
- Add smoke checks for CLI entrypoints (`blux-ca --help`, doctor checks, training `--help`).
- Use pytest for automated tests; keep smoke tests fast and GPU-optional.
