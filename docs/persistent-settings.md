# Persistent settings

The app stores a handful of values with `QSettings` (org `BenjaminKobjolke`,
app `Calculator`), so they survive a restart. On Windows these live in the
registry under `HKEY_CURRENT_USER\Software\BenjaminKobjolke\Calculator`.

| Key | Meaning | Default | Read by | Written by |
|-----|---------|---------|---------|-----------|
| `window/geometry` | window size and position | primary-screen centered | `_restore_geometry` | `closeEvent` |
| `editor/font_point_size` | notepad font size (pt) | `12` | `MainWindow.__init__` | `_change_font_size` |
| `window/frameless` | title bar hidden | `True` (hidden) | `_restore_window_chrome` | `/window-title` (`_toggle_title`) |
| `window/opacity` | window opacity, percent (clamped 10–100) | `100` (opaque) | `_restore_window_chrome` | `/window-opacity` (`_set_opacity`) |
| `window/bg_color` | pane background, hex (`#rrggbb`) | unset → Qt palette | `_restore_colors` | `/window-background-color`, `/window-theme` |
| `window/font_color` | pane text color, hex (`#rrggbb`) | unset → Qt palette | `_restore_colors` | `/window-font-color`, `/window-theme` |
| `window/margin` | editor text margin, px (clamped 0–200) | `8` | `_restore_margin` | `/window-margin` (`_set_margin`) |

All keys are read/written in `gui/main_window.py`. Opacity is clamped to
**10–100** (`clamp_opacity`) so the window can never become fully invisible —
a frameless, transparent window would be unrecoverable.

See `docs/commands.md` for the `/window-opacity` and `/window-title` commands.
