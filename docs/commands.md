# Slash commands

Type a `/` command in the notepad and press **Enter** to run it. The command is
the `/`-token at the cursor, so it works **anywhere in a line**, with
(`105+ /paste-last-result`) or without (`81+/paste-last-result`) a space before
the slash — not just at the start. Commands act on the editor —
they are not math and produce no result value.

| Command      | What it does                                              |
|--------------|-----------------------------------------------------------|
| `/clear`     | Clear the whole document.                                 |
| `/copy`      | Copy every line as `input = result`, one per line.        |
| `/copy-last` | Copy the value of the last result.                        |
| `/paste-last-result` | Insert the last result at the cursor position.    |
| `/help`      | Open a localized help window (basics, commands, variables). See [help.md](help.md). |
| `/release-notes` | Open a window with localized release notes, newest version first. |
| `/exit`      | Close the calculator (quit the app).                      |
| `/window-opacity <n>` | Set window opacity to `n` percent (clamped 10–100). Persists. |
| `/window-title` | Toggle the title bar (show / hide). Persists. Hidden bar still keeps native Aero Snap / Win+Arrow on Windows. |
| `/window-background-color <hex>` | Set the pane background, e.g. `#282a36`. Persists. |
| `/window-font-color <hex>` | Set the pane text color, e.g. `#f8f8f2`. Persists. |
| `/window-theme <name>` | Apply a preset theme (sets background, font color **and** syntax colors). Persists. |
| `/window-margin <px>` | Set the editor text margin in pixels (default 8). Persists. |
| `/window-highlighting <on\|off>` | Turn syntax coloring on/off (no arg toggles). Persists. |
| `/window-number-color <hex>` | Color of number tokens, e.g. `#bd93f9`. Persists. |
| `/window-operator-color <hex>` | Color of operator tokens (`+`, `mal`, `divided by`, …). Persists. |
| `/window-function-color <hex>` | Color of function/constant tokens (`sqrt`, `pi`, …). Persists. |
| `/window-variable-color <hex>` | Color of variable tokens. Persists. |
| `/window-inline-color <hex>` | Color of inline `$`-variable tokens (`$sum`). Persists. |

## Value commands

`/window-opacity`, `/window-margin`, `/window-background-color`,
`/window-font-color`, `/window-theme`, and the four `/window-*-color` syntax
commands take a value. Pass it inline (`/window-opacity 80`,
`/window-theme dracula`, `/window-number-color #ffb86c`) — or run the command
**with no value** and an input box appears: a number box for opacity and margin, a
hex text box for the colors, and a dropdown of theme names for `/window-theme`.

Preset themes: `dracula`, `nord`, `monokai`, `solarized-dark`, `solarized-light`.
Each preset sets a full palette — background, font color, and the four syntax
token colors.

## Syntax coloring

The notepad tints math tokens as you type. The tokenizer (`gui/syntax.py`) reuses
the engine's own maps, so the colored categories match what the evaluator
understands:

| Category   | Matches                                                              |
|------------|---------------------------------------------------------------------|
| `number`   | numbers incl. `,`/`.` decimals and trailing `%` (`19%`, `100,00`)   |
| `operator` | symbols (`+ - * / ^ % =`) and word operators (`mal`, `divided by`)  |
| `function` | function and constant names (`sqrt`, `min`, `pi`, `e`)              |
| `variable` | any other identifier (assignment names and references)             |
| `inline`   | inline `$`-variables (`$sum`)                                        |

Set an individual color with `/window-<category>-color <hex>`, swap the whole
palette with `/window-theme <name>`, or turn coloring off with
`/window-highlighting off`. `/command` lines are never colored.

See [syntax-coloring.md](syntax-coloring.md) for the full palette and preset
themes. All of these persist across restarts — see
[persistent-settings.md](persistent-settings.md).

## Inline autosuggest

As you type a command, a grayed **ghost** shows the **longest common prefix** of
every command that still matches — so it never mis-guesses which one you mean:

```
/win → /window-      six commands match; the shared "/window-" is ghosted
/e   → /exit         only one match; the whole command is ghosted
```

Press **Tab** to fill the ghost. When several commands still match, Tab also
drops a **stacked list** below the cursor to pick from:

```
/window-
  /window-opacity        ← highlighted
  /window-title
  /window-background-color
  /window-font-color
  /window-theme
  /window-margin
```

| Key         | Action                                                    |
|-------------|-----------------------------------------------------------|
| `Tab`       | Fill the common prefix; open the list if several match; complete fully when one match remains. |
| `↑` / `↓`   | Move the highlight in the list (`↓` also opens it).       |
| `Enter`     | Pick the highlighted command and run it (runs directly when only one matches). |
| `Esc`       | Close the list, or dismiss the ghost.                     |

Keep typing at any time to narrow the list; once a single command remains it
collapses back to a plain ghost. When the common prefix can't extend (e.g. `/c`
matches `/clear`, `/copy`, `/copy-last`), the first `Tab` opens the list at once.

Suggestions appear whenever the trailing word at the cursor starts with `/`, so
normal math is never interrupted. The same ghost/Tab autosuggest also works for
inline `$`-variables — type `$` and `$sum` is offered (see
[syntax.md](syntax.md)).

## Examples

```
5 mal 5
price = 20
price minus 5
/copy            -> clipboard: "5 mal 5 = 25\nprice = 20\nprice minus 5 = 15"
```

```
2 hoch 10
/copy-last       -> clipboard: "1024"
```

```
2 hoch 10
/paste-last-result   -> the command line becomes "1024" in the notepad
```

```
2 hoch 10
100+ /paste-last-result   -> the line becomes "100+ 1024" (only the token is replaced)
```

`/copy` renders assignment lines as-is (`price = 20`) rather than repeating the
value (`price = 20 = 20`).

## Implementation

- `gui/commands.py` — pure command logic (`suggest`, `parse_command`,
  `build_copy_text`, `last_result_text`), unit-tested in `tests/test_commands.py`.
- `gui/command_edit.py` — `CommandEdit`, the notepad widget: ghost-text painting
  and key handling; emits `command_entered(name)`. Removes the whole logical
  block (`StartOfBlock`→`EndOfBlock`) before emitting, so a command that wraps
  across visual rows is fully cleared.
- `gui/main_window.py` — `_run_command` performs the side effects: clipboard
  writes (`/copy`, `/copy-last`) and inserting the last result at the cursor
  (`/paste-last-result`).
- `gui/release_notes.py` — Qt-free markdown builder for `/release-notes`; reads
  `release_notes/<version>/<lang>.json` (falls back to `en.json`), rendered in a
  `MarkdownWindow` (`gui/help_window.py`), the same viewer `/help` uses.
- `gui/frameless_win.py` — `FramelessWindow`, the base window that `/window-title`
  uses to hide the title bar. Instead of Qt's `FramelessWindowHint` (which strips
  the native `WS_CAPTION`/`WS_THICKFRAME` styles and kills Aero Snap / Win+Arrow),
  it keeps the window a normal native window and zeroes the non-client area in the
  `WM_NCCALCSIZE` message, so Windows still snaps and moves it. Non-Windows
  platforms fall back to `FramelessWindowHint`.
