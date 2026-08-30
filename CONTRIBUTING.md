# Contributing to Elide Threat Intelligence

Thanks for your interest in improving this project. This document explains how to propose changes.

## Ways to contribute

- **Report a problem** — a broken source URL, a false positive, or a domain that should be added or removed.
- **Propose a source** — suggest a new tracker or ad list (it must be openly licensed and compatible with GPL-3.0).
- **Improve the engine** — code quality, performance, documentation.

## Ground rules

- The build engine (`process_lists.py`) must remain **standard library only** — no third-party runtime dependencies.
- Do **not** hand-edit `final_blocklist.txt`. It is a generated artifact; change the sources or logic in `process_lists.py` instead.
- Keep the output format stable: `TAG<space>domain`, one entry per line, sorted, LF line endings. Downstream apps depend on it.
- New sources must be publicly available and license-compatible. Add attribution in the README.

## Development workflow

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feature/short-description
   ```
2. Make your change. If you touch the engine, run it locally and confirm the output:
   ```bash
   python process_lists.py
   ```
3. Verify the per-category counts printed at the end look sane, and that `final_blocklist.txt` still has the `TAG domain` shape.
4. Commit with a clear, imperative message (e.g. `Add native.tv tracker source`).
5. Open a pull request against `main` and fill in the PR template.

## Commit style

- Use short, imperative subject lines (max ~70 chars).
- Explain the *why* in the body when the change isn't obvious.

## Code style

- Follow PEP 8. Keep functions small and documented with docstrings.
- Prefer clear names over cleverness.
- A `.editorconfig` is provided; please keep it enabled.
