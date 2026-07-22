# FastCalculator

A Numi-style desktop calculator. Type math in a notepad on the left; results
appear live on the right, one per line. Unlike Numi, it treats `.` and `,`
**identically** as the decimal point (German-friendly), and it understands
natural-language operators in **English and German**.

## Features

- **Live multi-line notepad** — every line is evaluated as you type; the result
  shows on the same row on the right.
- **`,` and `.` are both the decimal point**: `3,5 + 1,5` = `5`.
- **Percent (`%`)** — Numi-style: `100 * 19%` = `19`, `100 + 19%` = `119`,
  `100 - 19%` = `81`, `100 / 50%` = `200`, bare `19%` = `0.19`. Plain modulo
  (`10 % 3` = `1`) still works — `%` is percent only when nothing follows it.
- **Output mirrors your decimal style** — if the line uses explicit decimals,
  the result copies the separator and place count: `100.00 + 19%` = `119.00`,
  `100,00 + 19%` = `119,00`.
- **Variables across lines** — assign once, reuse below:
  ```
  x = 10
  x hoch 2      -> 100
  price = 20
  price minus 5 mal 2   -> 10
  ```
- **Comparisons** — `==` `!=` `<` `>` `<=` `>=` (and the words `equals` /
  `ist gleich`) answer `true`/`false` — in German (`wahr`/`falsch`) when the
  German phrase is used. Unit-aware: `5 km == 5000 m` → `true`. A single `=`
  stays assignment. See [docs/comparisons.md](docs/comparisons.md).
- **Inline `$`-variables** — `$sum` totals the results above it (within the
  current group; a blank line starts a new group):
  ```
  Angebot: 2000
  Rabatt: $sum - 5%   -> 1900
  ```
  Type `$` to autocomplete. See [docs/inline-variables.md](docs/inline-variables.md).
- **Running units** — distances (`km`/`mi`/`m`) and times (`mm:ss`, `h:mm:ss`)
  carry their unit, so pace, finish time and speed just work:
  `50:00 / 10 km` = `5:00 /km`, `10 km / 50:00` = `12 km/h`, `10 km in mi` =
  `6.214 mi`. See [docs/running.md](docs/running.md).
- **Word operators (English + German)** — see table below.
- **Functions & constants** — sqrt, trig, logs, rounding, min/max, `pi`, `e`.
- **Syntax coloring** — numbers, operators, functions, variables, and inline
  `$`-variables are tinted live as you type. Pick a preset with `/window-theme`,
  recolor a single token category with `/window-number-color` (and friends), or
  turn it off with `/window-highlighting off`. See
  [docs/syntax-coloring.md](docs/syntax-coloring.md).
- **Window remembers size + position** across launches; if the saved spot is off
  every screen (monitor unplugged / resolution change), it re-centers on the
  primary screen instead of opening off-view.
- **Built-in help** — `/help` opens a localized help window (English/German, from
  the system locale) that stays open beside the notepad. See
  [docs/help.md](docs/help.md).
- **Safe by construction** — expressions are parsed with Python's `ast` and
  walked against a strict node whitelist. No `eval`/`exec`, no attribute access,
  no imports, no dunder tricks.

## Operators

| Symbol | Words (English)              | Words (German)          |
|--------|------------------------------|-------------------------|
| `*`    | `times`, `multiplied by`     | `mal`                   |
| `+`    | `plus`, `add`                | `plus`                  |
| `-`    | `minus`, `less`              | `minus`                 |
| `/`    | `divided by`, `over`         | `geteilt durch`, `durch`|
| `^`    | `to the power of`            | `hoch`                  |
| `%`    | `modulo`, `mod`              | `modulo`, `mod`         |
| `==`   | `equals`                     | `ist gleich`            |

Words are case-insensitive. Longest phrase wins (`divided by` beats `over`).
Parentheses and unary minus work as expected: `-(2 + 3) * 4`.

`%` is dual-purpose: modulo when it has a right operand (`10 % 3`), percent when
it doesn't (`19%`, `100 + 19%`). Percent applies to the left side for `+`/`-`
and is just `value/100` for `*`/`/`.

Examples:
```
5 times 5          -> 25
5 mal 5            -> 25
10 divided by 3    -> 3.333333333
10 geteilt durch 2 -> 5
2 to the power of 10 -> 1024
2 hoch 3           -> 8
17 mod 5           -> 2
```

## Functions

`sqrt` `sin` `cos` `tan` `log` (base 10) `ln` (natural log) `round` `abs`
`min` `max` `floor` `ceil`

Constants: `pi`, `e`.

```
sqrt(16)   -> 4
ln(e)      -> 1
round(3,7) -> 4
abs(-9)    -> 9
```

### Multi-argument functions use `;`

Because `,` is a decimal point here, separate function arguments with `;`:

```
min(3;9;1)   -> 1
max(2,5; 7)  -> 7
```

## Setup

Requires [uv](https://docs.astral.sh/uv/). Python 3.11 or 3.12.

```
install.bat        # create venv, install deps, run tests
start.bat          # launch the GUI
```

## Development

```
tools\run_tests.bat              # unit tests
tools\run_integration_tests.bat  # end-to-end tests
update.bat                       # upgrade deps, ruff, mypy, tests
tools\build.bat                  # PyInstaller onefile -> dist\FastCalculator.exe
tools\create_media\create_demos.bat  # record demos (en+de) -> tools\create_media\output\demos\<name>\<lang>\
```

Releases (version bump, release notes, publish): see
[docs/CREATE_NEW_RELEASE.md](docs/CREATE_NEW_RELEASE.md).

### Automation demos

`uv run python main.py --automation-demo 1` plays a scripted, recordable demo
(animated typing, then exits). Used by the automated-application-screenshots
tool to record GIF/MP4 demos and stills; the full contract (`--automation-demo-port`,
`-width`, `-height`, socket events) is documented in that repo's
`docs/AUTOMATION_INTERFACE.md`. Playback machinery comes from the
`automated-screenshot-connector` path dependency
(`../automated-application-screenshots-python-connector`); only the demo
scripts live here (`demo/scripts.py`). Demo runs use a wiped temp settings
namespace, so your real settings stay untouched.

Demos record once per language (`--automation-demo-language` sets the UI
language, overriding the OS locale). Typed demo text is localized through
`{placeholder}`s in the scripts, filled from
`tools/create_media/texts/<lang>.json` (passed as `--automation-demo-texts`).
Adding a language: create `texts/<lang>.json`, add the code to `"languages"`
in `tools/create_media/fastcalculator.json` — no code changes.

## Layout

```
engine/    pure evaluation library (stdlib only, no GUI, no third-party deps)
  preprocess.py  , -> .  ;  $sum -> _inline_sum  ;  postfix % -> _pct(...)  ;  ; -> ,  ;  words  ;  ^ -> **
  evaluator.py   evaluate(line, scope) + ast whitelist walker (security boundary)
  words.py       operator word map (English + German), data-only
  functions.py   whitelisted functions + constants, data-only
  inline.py      inline $-variable names ($sum, ...), data-only
  result.py      EvalResult typed return
gui/       PySide6 window + Qt-free document evaluator
demo/      automation-demo scripts (playback machinery: automated-screenshot-connector)
main.py    entry point
tests/     pytest unit + integration tests
```

## Dependencies

- Runtime: [PySide6](https://doc.qt.io/qtforpython/) (Qt desktop GUI).
- Dev: ruff, mypy, pytest.
