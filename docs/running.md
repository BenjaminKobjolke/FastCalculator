# Running calculations (pace, time, distance, speed)

FastCalculator tracks **units** for running math, so pace, finish time and speed
work directly — no manual second-conversions. Distances and times carry their
unit through arithmetic; the result is shown in the natural unit.

```
50:00 / 10 km             -> 5:00 /km        (time ÷ distance = pace)
4:30 min/km * 42.195 km   -> 3:09:53         (pace × distance = finish time)
10 km / 50:00             -> 12 km/h         (distance ÷ time = speed)
10 km in mi               -> 6.214 mi
```

## Distances

| Unit | Aliases |
|------|---------|
| `km` | `kms`, `kilometer(s)`, `kilometre(s)` |
| `mi` | `mile`, `miles` |
| `m`  | `meter(s)`, `metre(s)` |

Write a number then the unit: `10 km`, `42.195 km`, `5 mi`, `400 m`.
Compatible distances add and auto-convert, taking the **right** operand's unit:

```
5 mi + 3 km      -> 11.05 km
```

## Times

Type a clock literal — `mm:ss` or `h:mm:ss` (1–2 digit fields):

```
50:00        -> 50:00       (50 min)
1:23:45      -> 1:23:45
12:30        -> 12:30       (12 min 30 s)
```

Or a duration word — `min`, `h`, `s` — which you can chain (adjacent durations
add):

```
30 min       -> 30:00
1 h 30 min   -> 1:30:00
```

A time result always renders as `h:mm:ss` (or `m:ss` under an hour).

## Pace = time ÷ distance

Divide a time by a distance. The suffix `/km` or `/mi` (with an optional `min`)
is shorthand for "per that distance":

```
50:00 / 10 km      -> 5:00 /km
3:22 / 1 km        -> 3:22 /km
4:30 min/km        -> 4:30 /km        (a pace literal on its own)
```

## Finish time = pace × distance

Multiply a pace by a distance to get the total time:

```
4:30 min/km * 42.195 km   -> 3:09:53
```

A **plain time** multiplied by a distance also works — the distance's number is
the multiplier, and the result stays a time. So all of these agree:

```
3:22 * 42        -> 2:21:24
3:22 * 42 km     -> 2:21:24
3:22 /km * 42 km -> 2:21:24
```

This is why, under a lone time line, a leading-operator continuation just works:

```
3:22
* 42 km          -> 2:21:24
```

## Speed = distance ÷ time

```
10 km / 50:00    -> 12 km/h
```

Enter a speed directly with `km/h` (`kmh`, `kph`) or `mph`: `12 km/h`, `7 mph`.

## Converting units — `in` / `to`

Re-express a result in another unit of the same kind:

```
10 km in mi          -> 6.214 mi
5:00 /km in min/mi   -> 8:03 /mi        (pace between systems)
12 km/h in mph       -> 7.456 mph
```

Targets: distance (`km`, `mi`, `m`), speed (`km/h`, `mph`), pace (`/km`, `/mi`,
`min/km`, `min/mi`). Converting time units is a no-op (time always shows as a
clock).

## `$sum` and leading operators carry units

Within a group, `$sum` and leading-operator lines (`* 2`, `- 5 km`) continue from
a **unit-aware** running total:

```
5 km
3 km
$sum             -> 8 km

marathon = 42.195 km
50:00 / 10 km
marathon * 5:00 /km    (use variables to reuse units across lines)
```

A group of one unit sums with that unit. Mixing incompatible units in one `$sum`
group is undefined — the total restarts from the incompatible line rather than
erroring. See [inline-variables.md](inline-variables.md).

## Reserved names

Because units resolve like constants, these words are **reserved** and cannot be
used as variable names: `km mi m min h s kmh mph`. `min` still works as the
`min(…)` function — the reservation only affects it as a bare name.

Unknown trailing words (`kg`, `apples`, `dollars`) are **not** units: they are
dropped from the math and kept only as a display label, so `5 kg + 5 kg` = `10 kg`
— a plain number that happens to print `kg`, with no dimension and no conversion.
See [syntax.md](syntax.md).

## Under the hood

The engine stays `float`-free of GUI code and keeps its `ast` whitelist intact —
units are modeled as **whitelisted names**, never strings.

- `engine/units.py` — the `Quantity` value type (a magnitude in canonical base
  units — metre, second — plus a `(length, time)` dimension), the `UNITS`
  registry, `apply_binop` (dimensional algebra, incl. the `time × distance`
  rule), `convert`, and `render` (→ display magnitude + `kind` + unit label).
  A dimensionless `Quantity` compares equal to a plain number, so non-running
  math is unchanged.
- `engine/preprocess.py` — `normalize()` rewrites surface syntax into whitelisted
  names/calls: time literals → `_time(<seconds>)`, unit words → `(<n> * <name>)`,
  pace suffix → `/ <name>`, `in`/`to` → `_to(<expr>, <name>)`. A unit word is
  rewritten only when known, so unknown trailing words still get stripped.
- `engine/evaluator.py` — the walker returns `Quantity`; unit names resolve like
  constants; `_time`/`_to` are special-cased calls beside `_pct`. No new AST node
  types, so the security boundary is unchanged.
- `engine/result.py` — `EvalResult` carries `kind`, `unit`, and the raw
  `quantity` (so `$sum` can keep units).
- `gui/document_evaluator.py` — `format_result` renders each `kind` (`time`,
  `pace`, `distance`, `speed`); `evaluate_document` keeps the `$sum` running total
  as a `Quantity`.
- Tests: `tests/test_units.py` (algebra), `tests/test_preprocess.py` (rewrites),
  `tests/test_integration.py` (end-to-end table), `tests/test_document_evaluator.py`
  (display + `$sum`).

### Adding a unit

Add an entry to `UNITS` in `engine/units.py` and, if it has a surface spelling
that differs, to the alias/target tables in `engine/preprocess.py`. Distance,
time, speed and pace kinds already render; a genuinely new dimension also needs a
default display unit and a `render` branch.
