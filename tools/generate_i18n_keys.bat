@echo off
REM Regenerate the TK translation-key constants class from the English locale.
REM Run after adding/renaming keys in locales\en.json.
uv run python -m python_localization.cli locales\en.json -o gui\i18n_keys.py -c TK
