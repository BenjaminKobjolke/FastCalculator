# CLAUDE.md — Calculator

Numi-style desktop calculator. `,` and `.` are both the decimal point; English +
German word operators; live multi-line notepad (PySide6).

## Rules sources

Full rules: `D:\GIT\BenjaminKobjolke\claude-code\coding-rules\COMMON_RULES.md`
and `PYTHON_RULES.md`. Key points enforced here:

- **uv** manages the env; `pyproject.toml` is the single source of truth; commit `uv.lock`.
- Python pinned `>=3.11,<3.13`.
- Type hints on all public APIs. `mypy --strict` + `ruff` must pass (`update.bat`).
- Typed returns, never bag-of-keys dicts across boundaries → `EvalResult` (`engine/result.py`).
- Central logger `AppLogger` (`app_logger.py`); never `print()` or `logging.getLogger` directly.
- Max 300 lines per file. No god classes.
- TDD: write failing tests first, then implement. Unit **and** integration tests (`tests/`).
- KISS / DRY / YAGNI.

## Architecture

- `engine/` — pure, stdlib-only expression engine. **No GUI, no third-party imports.**
  - `preprocess.py` — `,`→`.`, `;`→`,`, word operators (longest-match), `^`→`**`.
  - `evaluator.py` — `evaluate(line, scope)`; `ast.parse` + **whitelist walker** (the security boundary). Never `eval`/`exec`.
  - `words.py` / `functions.py` — data-only maps; extend by adding entries.
- `gui/` — `document_evaluator.py` is **Qt-free** (unit-tested); `main_window.py` is the PySide6 window.
- `main.py` — entry point.

## Conventions specific to this project

- `,` and `.` are always the decimal point. Multi-arg functions therefore use
  `;` as the argument separator (`min(3;9;1)`), rewritten to `,` in preprocessing.
- `^` is power (rewritten to `**`), never bitwise XOR.
- The AST walker whitelist is the security boundary — new node types are rejected
  by default. Add to the whitelist only with matching security-rejection tests.
- Variable scope is owned by the caller (GUI), passed into `evaluate()`; the
  engine holds no global state.

## Commands

```
install.bat                      # setup + tests
start.bat                        # run GUI
tools\run_tests.bat              # unit tests
tools\run_integration_tests.bat  # integration tests
update.bat                       # deps upgrade + ruff + mypy + tests
```

## Code Analysis

After implementing new features or making significant changes, run the code analysis:

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\calculator'; cmd /c '.\tools\analyze_code.bat'"
```

Results are written to `code_analysis_results/` as **per-rule CSV files** (e.g.
`max_lines_per_file.csv`, `ruff_analyze.csv`, `pmd_duplicates.csv`) — a missing
CSV means that rule found nothing. Fix any reported issues before committing.
Auto-fix Ruff issues with `tools\fix_ruff_issues.bat` (preview:
`fix_ruff_issues_dry_run.bat`).
