# Help window

`/help` opens an in-app help window covering **basics**, **commands**,
**variables**, and **running** (pace/time/distance — see [running.md](running.md)).
Run it like any slash command — type `/help` anywhere in a line and press Enter
(see [commands.md](commands.md)).

## Behaviour

The help window is a **regular, independent top-level window**, not a modal
dialog:

- **Stays open while you calculate** — it is non-modal, so the notepad keeps
  working with the help window beside it.
- **Own taskbar entry**, Alt-Tab target, and **native window management** — drag
  it, resize it, and move it with **Win+Arrow / Aero Snap** like any other
  window. (It is a plain top-level `QWidget`; a `QDialog` would be excluded from
  Aero Snap on Windows.)
- **Single instance** — reopening `/help` raises the existing window instead of
  stacking duplicates; it keeps its size and scroll position.
- **Closes on Esc** or the window's close button. Closing the main window (or
  `/exit`) also closes help and quits the app.
- **Selectable text with a caret** — click-drag or arrow-key through the text and
  copy from it, exactly like the notepad.

### Appearance

The window mirrors the notepad's look, read from the same persisted settings
(see [persistent-settings.md](persistent-settings.md)):

- `window/bg_color` / `window/font_color` — background and text color.
- `window/opacity` — window opacity.
- `window/margin` — text margin.
- `editor/font_point_size` — monospace (Consolas) font size, shared with the
  notepad. **Ctrl++** / **Ctrl+-** (also **Alt+Up** / **Alt+Down**) grow/shrink
  it and persist the new size. Inline code and code blocks scale with the body.

## Localization

Help text is **translated**, not hard-coded. It uses the
[`python-localization`](../../python-localization) library (a zero-dependency
JSON translation loader), wired through a small Qt-free wrapper.

- **Source of truth:** `locales/en.json`. German reference: `locales/de.json`.
  Both are hand-authored; each other `{lang}.json` (if added) is loaded as-is.
- **Language pick:** at startup `main.py` sets the language from the system
  locale (`QLocale.system()`), clamped to a shipped locale, falling back to
  English. So a German Windows shows German help; anything else shows English.
- **Keys** use dot notation (`help.commands.heading`). Missing keys fall back to
  English, then to the key name itself, so a gap is visible rather than blank.

### Add or change help text

1. Edit `locales/en.json` (and `locales/de.json` for German). Keep bodies short
   markdown.
2. If you **add or rename a key**, regenerate the typed key constants:
   `tools\generate_i18n_keys.bat` → rewrites `gui/i18n_keys.py` (the `TK` class).
   `gui/help_content.py` references `TK.HELP_*`, so a renamed key fails fast.

### Add a language

Drop a `locales/<lang>.json` with the same keys (e.g. `locales/fr.json`). It is
picked up automatically for that system locale; untranslated keys fall back to
English.

## Implementation

- `gui/help_window.py` — the `HelpWindow` widget: top-level `QWidget`,
  `QTextBrowser`, theming, font/Esc shortcuts, markdown render.
- `gui/help_content.py` — Qt-free `build_help_markdown()`; assembles the
  translated title + sections into one markdown string (unit-tested,
  `tests/test_help_content.py`).
- `gui/i18n.py` — Qt-free loader wrapper over `python_localization.Localization`:
  `set_language()` / `t()` with an English fallback (unit-tested,
  `tests/test_i18n.py`).
- `gui/i18n_keys.py` — generated `TK` key constants (do not edit by hand).
- `gui/main_window.py` — `_run_command` handles `/help`; `_show_help` shows the
  single instance; `closeEvent` closes it.
- `locales/en.json`, `locales/de.json` — the translated strings.
- `tools/generate_i18n_keys.bat` — regenerates `gui/i18n_keys.py`.
