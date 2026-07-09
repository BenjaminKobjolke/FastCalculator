# Slash commands

Type a `/` command on its own line in the notepad and press **Enter** to run it.
Commands act on the editor — they are not math and produce no result value.

| Command      | What it does                                              |
|--------------|-----------------------------------------------------------|
| `/clear`     | Clear the whole document.                                 |
| `/copy`      | Copy every line as `input = result`, one per line.        |
| `/copy-last` | Copy the value of the last result.                        |
| `/paste-last-result` | Insert the last result at the cursor position.    |
| `/exit`      | Close the calculator (quit the app).                      |

## Inline autosuggest

As you type a command, a grayed **ghost** completion appears after the cursor:

```
/c̲l̲e̲a̲r̲          you typed "/c", the rest is suggested
```

| Key         | Action                                        |
|-------------|-----------------------------------------------|
| `Tab`       | Accept the suggestion (fills the command).    |
| `↑` / `↓`   | Cycle through matching commands.              |
| `Esc`       | Dismiss the suggestion.                       |
| `Enter`     | Accept (if a suggestion is showing) and run the command. |

Suggestions only appear for lines that start with `/`, so normal math is never
interrupted.

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

`/copy` renders assignment lines as-is (`price = 20`) rather than repeating the
value (`price = 20 = 20`).

## Implementation

- `gui/commands.py` — pure command logic (`suggest`, `parse_command`,
  `build_copy_text`, `last_result_text`), unit-tested in `tests/test_commands.py`.
- `gui/command_edit.py` — `CommandEdit`, the notepad widget: ghost-text painting
  and key handling; emits `command_entered(name)`.
- `gui/main_window.py` — `_run_command` performs the clipboard side effects.
