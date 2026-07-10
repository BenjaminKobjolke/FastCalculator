# Syntax coloring

The notepad tints math tokens live as you type. Coloring is **on by default**
and covers five token categories. `/command` lines are never colored, and turning
it off (`/window-highlighting off`) leaves the text a single plain color.

The tokenizer (`gui/syntax.py`) reuses the engine's own maps, so the colored
categories always match what the evaluator understands.

## Categories

| Category   | Matches                                                        | Default (Dracula) |
|------------|----------------------------------------------------------------|-------------------|
| `number`   | numbers incl. `,`/`.` decimals and trailing `%` (`19%`, `100,00`) | `#bd93f9`      |
| `operator` | symbols (`+ - * / ^ % =`) and word operators (`mal`, `divided by`) | `#ff79c6`     |
| `function` | function and constant names (`sqrt`, `min`, `pi`, `e`)         | `#8be9fd`         |
| `variable` | any other identifier (assignment names and references)         | `#50fa7b`         |
| `inline`   | inline `$`-variables (`$sum`)                                   | `#ffb86c`         |

## Customizing

Type these in the notepad and press **Enter**. Colors accept `#rgb` or `#rrggbb`;
running a color command with no value opens an input box. Everything persists
across restarts. Full command details in [commands.md](commands.md).

| Command                          | What it does                                             |
|----------------------------------|----------------------------------------------------------|
| `/window-highlighting <on\|off>` | Turn coloring on/off (no arg toggles).                   |
| `/window-number-color <hex>`     | Recolor number tokens.                                   |
| `/window-operator-color <hex>`   | Recolor operator tokens.                                 |
| `/window-function-color <hex>`   | Recolor function/constant tokens.                        |
| `/window-variable-color <hex>`   | Recolor variable tokens.                                 |
| `/window-inline-color <hex>`     | Recolor inline `$`-variable tokens.                      |
| `/window-theme <name>`           | Swap the whole palette (background, font, 4 syntax colors). |

## Preset themes

`/window-theme <name>` applies a full palette. Presets and their four syntax
colors (from `gui/themes.py`):

| Theme             | Background | number    | operator  | function  | variable  | inline    |
|-------------------|------------|-----------|-----------|-----------|-----------|-----------|
| `dracula`         | `#282a36`  | `#bd93f9` | `#ff79c6` | `#8be9fd` | `#50fa7b` | `#ffb86c` |
| `nord`            | `#2e3440`  | `#b48ead` | `#81a1c1` | `#88c0d0` | `#a3be8c` | `#ebcb8b` |
| `monokai`         | `#272822`  | `#ae81ff` | `#f92672` | `#66d9ef` | `#a6e22e` | `#fd971f` |
| `solarized-dark`  | `#002b36`  | `#6c71c4` | `#d33682` | `#268bd2` | `#2aa198` | `#b58900` |
| `solarized-light` | `#fdf6e3`  | `#6c71c4` | `#d33682` | `#268bd2` | `#2aa198` | `#b58900` |

## Persistence

Colors and the on/off flag persist via `QSettings` keys `window/syntax_number`,
`window/syntax_operator`, `window/syntax_function`, `window/syntax_variable`,
`window/syntax_inline`, and `window/highlighting` — see
[persistent-settings.md](persistent-settings.md).

## Implementation

- `gui/syntax.py` — Qt-free tokenizer. `tokenize()` returns `(start, length,
  category)` spans; `CATEGORIES` is the canonical category list. Reuses the engine
  maps `WORD_OPERATORS` (`engine/words.py`), `FUNCTIONS`, `CONSTANTS`
  (`engine/functions.py`) as the source of truth.
- `gui/highlighter.py` — `MathHighlighter(QSyntaxHighlighter)`: owns the
  category→hex palette and on/off flag, loads settings via
  `MathHighlighter.restore()`, and paints in `highlightBlock()`.
- `gui/themes.py` — `Theme` dataclass, the `THEMES` presets, `syntax_colors()`,
  and `is_valid_hex()` (all Qt-free).
- `gui/window_appearance.py` — `Appearance`, the slash-command handlers for
  colors, themes, and highlighting.
- Tests: `tests/test_syntax.py`.
