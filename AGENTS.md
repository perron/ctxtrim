# AGENTS.md

Instructions for coding agents (Claude Code, Codex, Cursor, Grok Bot, and similar) working in this repository.

## What this repo is

`ctxtrim` is a small Python 3.10+ command-line tool to trim logs, HTML, Markdown, and JSON down to a token budget. It has no required runtime dependencies and no API key. Layout:

- `ctxtrim/cli.py` — the implementation and the `main()` entry point (exit code is an `int`)
- `ctxtrim/__main__.py` — `python -m ctxtrim`
- `ctxtrim/__init__.py` — `__version__`
- `tests/test_ctxtrim.py` — pytest suite
- `pyproject.toml` — packaging, the `ctxtrim` script, and the `dev` extra (`pytest`)
- `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `PROOF.md` — human docs

ctxtrim/cli.py detects a format and trims to a budget. Output must never exceed the budget. tests/test_ctxtrim.py covers HTML/JSON/log strategies and tiny budgets.

## How to run tests

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
ctxtrim --help
ctxtrim --version
```

`pip install .` in a fresh virtualenv must leave `ctxtrim` on `PATH`.

## Conventions

- Keep changes small. Match the existing style: standard library, type hints, `argparse`, exit codes documented in the README.
- If you add behavior, add a test for it. Prefer tests of user-visible behavior over tests of internals.
- Do not add network calls, API keys, or telemetry.
- Do not copy source from other tools. This is a clean-room project.
- If a README, SECURITY.md, or Limits section would become untrue, update it in the same change.
- Do not commit secrets. For `ctxtrim`, also do not commit local store/journal/database files (see `.gitignore`).
- Token estimates in this family of tools, when present, are `ceil(utf-8 bytes / 4)`. Do not describe them as a vendor tokenizer.

## If you are using the tool rather than changing it

Install it from this checkout or from `pip install git+https://github.com/perron/ctxtrim.git`, then follow the 30-second quick start in the README. The README Limits section is the contract for what this release does and does not do.
