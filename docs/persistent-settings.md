# Persistent settings

The app stores a handful of values with `QSettings` (org `BenjaminKobjolke`,
app `FastCalculator`), so they survive a restart. On Windows these live in the
registry under `HKEY_CURRENT_USER\Software\BenjaminKobjolke\FastCalculator`.

| Key | Meaning | Default | Read by | Written by |
|-----|---------|---------|---------|-----------|
| `window/geometry` | window size and position | primary-screen centered | `_restore_geometry` | `closeEvent` |
| `editor/font_point_size` | notepad font size (pt) | `12` | `MainWindow.__init__` | `_adjust_font` |
| `window/frameless` | title bar hidden (via `FramelessWindow.set_frameless`) | `True` (hidden) | `_restore_window_chrome` | `/window-title` (`_toggle_title`) |
| `window/opacity` | window opacity, percent (clamped 10–100) | `100` (opaque) | `_restore_window_chrome` | `/window-opacity` (`_set_opacity`) |
| `window/bg_color` | pane background, hex (`#rrggbb`) | unset → Qt palette | `_restore_colors` | `/window-background-color`, `/window-theme` |
| `window/font_color` | pane text color, hex (`#rrggbb`) | unset → Qt palette | `_restore_colors` | `/window-font-color`, `/window-theme` |
| `window/margin` | editor text margin, px (clamped 0–200) | `8` | `EditorPrefs.restore_margin` | `/window-margin` (`EditorPrefs.set_margin`) |
| `window/round_decimals` | max decimals for displayed results (clamped 0–10) | unset → full precision | `EditorPrefs.restore_round` | `/round` (`EditorPrefs.set_round`; `/round off` removes the key) |
| `window/highlighting` | syntax coloring on/off | `True` (on) | `_restore_syntax` | `/window-highlighting` (`_set_highlighting`) |
| `window/syntax_number` | number token color, hex | `#bd93f9` (Dracula) | `_restore_syntax` | `/window-number-color`, `/window-theme` |
| `window/syntax_operator` | operator token color, hex | `#ff79c6` | `_restore_syntax` | `/window-operator-color`, `/window-theme` |
| `window/syntax_function` | function/constant token color, hex | `#8be9fd` | `_restore_syntax` | `/window-function-color`, `/window-theme` |
| `window/syntax_variable` | variable token color, hex | `#50fa7b` | `_restore_syntax` | `/window-variable-color`, `/window-theme` |
| `window/syntax_inline` | inline `$`-variable token color, hex | `#ffb86c` | `_restore_syntax` | `/window-inline-color`, `/window-theme` |
| `document/text` | notepad contents (autosaved while typing, on exit; `/clear` resets it) | `""` (empty) | `MainWindow.__init__` | `_save_document` (debounced `textChanged` + `closeEvent`) |
| `document/cursor` | cursor character offset in the notepad | `0` | `MainWindow.__init__` | `_save_document` |

Keys are read/written in `gui/main_window.py`, `gui/window_prefs.py`
(`EditorPrefs`: margin, rounding) and `gui/window_appearance.py`
(`Appearance`: colors, themes). Opacity is clamped to
**10–100** (`clamp_opacity`, `gui/window_limits.py`) so the window can never
become fully invisible — a frameless, transparent window would be unrecoverable.

The results pane has no fixed width: `_update_results_width` derives it from the
current font metrics and document margin (`results_width`, `gui/font_scale.py`)
and re-runs on startup, zoom (`_adjust_font`) and `/window-margin`, so restored
large fonts never clip the results.

## Document restore

`document/text` and `document/cursor` reload the notepad on startup:

- Text is autosaved ~800 ms after typing stops (single-shot `QTimer` on
  `textChanged`) and flushed on exit via `closeEvent`, so a crash loses at most
  the last unsaved keystrokes.
- On launch `MainWindow.__init__` restores the text, moves the cursor to the
  saved offset (clamped to text length), then calls `_recalculate()` once so the
  results pane is populated immediately — no need to edit a line first.
- Cursor offset only changes with `textChanged`; arrow-key-only moves are
  captured on exit by `closeEvent`.
- `/clear` empties the document, which saves an empty string — the cleared
  state persists.

See `docs/commands.md` for the `/window-opacity` and `/window-title` commands.
