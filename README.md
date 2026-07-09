# Calculator

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
- **Word operators (English + German)** — see table below.
- **Functions & constants** — sqrt, trig, logs, rounding, min/max, `pi`, `e`.
- **Window remembers size + position** across launches; if the saved spot is off
  every screen (monitor unplugged / resolution change), it re-centers on the
  primary screen instead of opening off-view.
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
```

## Layout

```
engine/    pure evaluation library (stdlib only, no GUI, no third-party deps)
  preprocess.py  , -> .  ;  postfix % -> _pct(...)  ;  ; -> ,  ;  words  ;  ^ -> **
  evaluator.py   evaluate(line, scope) + ast whitelist walker (security boundary)
  words.py       operator word map (English + German), data-only
  functions.py   whitelisted functions + constants, data-only
  result.py      EvalResult typed return
gui/       PySide6 window + Qt-free document evaluator
main.py    entry point
tests/     pytest unit + integration tests
```

## Dependencies

- Runtime: [PySide6](https://doc.qt.io/qtforpython/) (Qt desktop GUI).
- Dev: ruff, mypy, pytest.
