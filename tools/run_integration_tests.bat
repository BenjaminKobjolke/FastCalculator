@echo off
REM Run only the integration tests (end-to-end lines through the engine).
uv run python -m pytest tests/test_integration.py -v
