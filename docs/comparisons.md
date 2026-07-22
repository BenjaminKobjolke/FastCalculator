# Comparisons (`==`, `equals`, `ist gleich`)

A comparison line evaluates to **true or false** instead of a number. A single
`=` is still assignment — `helena = benni` copies benni's value into helena.
To compare, use `==` (or a word form):

```
helena = 3000
benni = 3000
helena == benni          -> true
helena ist gleich benni  -> wahr
```

| You type | Meaning |
|----------|---------|
| `==`, `equals`, `ist gleich` | equal |
| `!=` | not equal |
| `<` / `>` | less / greater than |
| `<=` / `>=` | less / greater or equal |

## Output language

The result matches the language of the input: a line comparing with the German
phrase `ist gleich` shows `wahr` / `falsch`; everything else shows
`true` / `false`. Copy (`/copy`) uses the same word the pane shows.

## Units and tolerance

Comparisons are **unit-aware** — both sides are compared in canonical units, so
`5 km == 5000 m` and `50:00 == 50 min` are `true`. Comparing
dimension-incompatible values (`5 km == 5`) is an error (the pane stays blank,
like other errors).

Equality tolerates float noise: `0,1 + 0,2 == 0,3` is `true`. A percent literal
compares by its plain value (`19% == 0,19` is `true`); the Numi `100 + 19%`
rule never applies inside a comparison.

## What is rejected

- **Assigning a comparison**: `x = 5 == 5` errors ("cannot assign a comparison") —
  variables hold numbers, not booleans.
- **Chained comparisons**: `1 < 2 < 3` errors.
- **Comparisons inside arithmetic or calls**: `(1 == 1) + 1`, `sqrt(1 == 1)` are
  rejected by the whitelist.
- A comparison line contributes **nothing to `$sum`** and does not restart the
  group — see [inline-variables.md](inline-variables.md).

## Implementation

- `engine/units.py` — `compare()`: dimension check + `math.isclose` equality on
  canonical magnitudes; ordering via `operator.lt/gt/le/ge`.
- `engine/evaluator.py` — a top-level `ast.Compare` is handled by
  `_eval_compare()`; `_eval_node` (the whitelist walker, the security boundary)
  never sees a Compare, so nested/chained forms stay rejected by default.
- `engine/words.py` — `equals` / `ist gleich` → `==` in `WORD_OPERATORS`
  (rewritten in preprocessing like every word operator; colored for free by
  `gui/syntax.py`), plus the `BOOL_TEXT` language map.
- `engine/preprocess.py` — `uses_german_comparison()` reads the raw line before
  word rewriting erases the language.
- `engine/result.py` — `EvalResult.from_bool()`: `kind="bool"`, the localized
  word in `text`, `value` 1/0, `quantity=None` (so `$sum` skips it).
- `gui/document_evaluator.py` — `format_result()` returns `result.text` verbatim
  for bool results (no decimal styling).
- Tests: `tests/test_units.py`, `tests/test_preprocess.py`,
  `tests/test_evaluator.py` (incl. security rejections),
  `tests/test_document_evaluator.py`, `tests/test_copy_text.py`,
  `tests/test_syntax.py`.
