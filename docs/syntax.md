# Writing equations

Every line in the notepad is evaluated on its own; the result shows in the pane
on the right. A line can be bare math, or math wrapped in words — both compute.

## Numbers

- **`,` and `.` are both the decimal point.** `3,5` and `3.5` are the same.
- Because `,` is a decimal point, multi-argument functions use `;` to separate
  arguments: `min(3;9;1)`.
- The result mirrors your input's decimal style: `100,00 + 19%` reads back as
  `119,00` (comma, two places). A `$sum` line with no decimals of its own inherits
  the style of the group above it — see [inline-variables.md](inline-variables.md#formatting).

## Operators

| You type | Meaning | Example | Result |
|----------|---------|---------|--------|
| `+` | add | `5 + 5` | `10` |
| `-` | subtract | `9 - 4` | `5` |
| `*` | multiply | `6 * 7` | `42` |
| `x` between two numbers | multiply | `10 x 10` / `10x10` | `100` |
| `/` | divide | `9 / 2` | `4.5` |
| `%` after a number | percent | see below | |
| `%` between numbers | modulo (remainder) | `10 % 3` | `1` |
| `^` | power | `2 ^ 8` | `256` |
| `( )` | grouping | `(2 + 3) * 4` | `20` |
| `-` prefix | negative | `-(3 + 4)` | `-7` |

### Percent

`%` right after a number is Numi-style percent:

| Example | Result | Reads as |
|---------|--------|----------|
| `19%` | `0.19` | 19 percent |
| `100 + 19%` | `119` | 100 plus 19% of 100 |
| `100 - 19%` | `81` | 100 minus 19% of 100 |
| `100 * 19%` | `19` | 100 × 0.19 |
| `100 / 50%` | `200` | 100 ÷ 0.5 |

## Word operators (English + German)

Type the operator as a word instead of a symbol. Case-insensitive.

| Words | Symbol |
|-------|--------|
| `multiplied by`, `times`, `mal` | `*` |
| `plus`, `add` | `+` |
| `minus`, `less` | `-` |
| `divided by`, `geteilt durch`, `durch`, `over` | `/` |
| `to the power of`, `hoch` | `^` |
| `modulo`, `mod` | `%` |

Examples: `5 times 5` → `25`, `10 divided by 2` → `5`, `2 hoch 3` → `8`,
`5 mal 5` → `25`.

## Functions and constants

Whitelisted only — anything else is rejected.

**Functions:** `sqrt` `sin` `cos` `tan` `log` (base 10) `ln` (natural) `round`
`abs` `min` `max` `floor` `ceil`.

**Constants:** `pi`, `e`.

Examples: `sqrt(16)` → `4`, `min(3;9;1)` → `1`, `round(3,7)` → `4`,
`ln(e)` → `1`.

## Variables

Assign with a single `=` (bare name on the left), then reuse the name on any
later line. Scope runs top-to-bottom, so editing an earlier line updates every
line that depends on it.

```
x = 10
x hoch 2      -> 100
price = 20
price minus 5 mal 2   -> 10
```

## Inline variables (`$`)

`$`-prefixed names are built-in variables that reference an aggregate of the
results **above** the line. They stay in the text (unlike `/`-commands) and can
be used inside any expression.

| Variable | Value |
|----------|-------|
| `$sum` | Total of the results above, within the current group. |

A **group** is a contiguous block of lines; a **blank line starts a new group**,
so `$sum` totals only from the last blank line down to the line above it.
Assignments count toward the total.

```
Angebot: 2000
Rabatt: $sum - 5%     -> 1900   (2000 minus 5% of 2000)

Posten: 10
Posten: 20
$sum                  -> 30     (the blank line above reset the total)
```

Type `$` to autocomplete the available inline variables (Tab fills, same as
`/`-commands). They get their own syntax color, too. Full reference:
[inline-variables.md](inline-variables.md).

## Running units (pace, time, distance, speed)

Distances (`km`, `mi`, `m`) and times (`mm:ss`, `h:mm:ss`, or `min`/`h`/`s`)
carry their unit through the math, so running calculations work directly:

```
50:00 / 10 km      -> 5:00 /km      (time ÷ distance = pace)
10 km / 50:00      -> 12 km/h       (distance ÷ time = speed)
3:22 * 42 km       -> 2:21:24       (a time × a distance-count = finish time)
10 km in mi        -> 6.214 mi      (convert with in/to)
```

The unit words `km mi m min h s kmh mph` become **reserved names**. Full
reference: [running.md](running.md).

## Labels and unit text

Math can share a line with plain text — the text is ignored, the math computes.

### Leading label

Any words followed by a colon are a label:

```
Price: 5 + 5          -> 10
Tax: 100 * 1,19       -> 119,00
Sum: 3 + 4 + 5        -> 12
```

The label must contain a letter and its colon must not follow a digit, so a time
literal like `12:30` (and the `50:00` in `10 km / 50:00`) is **not** read as a
label — it stays a time. See [running.md](running.md).

### Trailing / unit text

An **unknown** word attached right after a value is treated as noise and dropped
(known running units like `km` are kept — see [running.md](running.md)):

```
5 + 5 apples          -> 10
5 kg + 5 kg           -> 10
3 * 4 widgets         -> 12
budget = 100
budget + 20 dollars   -> 120
```

Only a **single** word per value is dropped, and only when it directly follows a
number, `)`, or `.`. A word in operand position stays — so `cost + 5` with an
undefined `cost` still reports "unknown name" rather than silently computing.
Multi-word units (`5 square feet`) drop only the last word.

## Lines that produce nothing

These render blank (no result), by design:

- Blank lines and pure text headers (`Shopping list`, `Notes:`).
- Anything the parser can't turn into a value (`@#$`). (A time like `12:30` now
  *does* compute — see [running.md](running.md).)
- Unknown names or functions (`foo + 1`, `bar(2)`).
- Anything outside the whitelist (attribute access, lambdas, comprehensions) —
  these are rejected as a security measure, never executed.

## Slash commands

`/`-commands (e.g. `/clear`, `/copy`) act on the editor and are not math. See
[commands.md](commands.md).
