# Inline `$`-variables

`$`-prefixed names are **built-in variables** that resolve to an aggregate of the
results **above** the current line. Unlike `/`-commands (which act on the editor
and vanish), a `$`-variable stays in the text and is part of the math — you can
use it inside any expression.

| Variable | Value |
|----------|-------|
| `$sum`   | Total of the results above, within the current group. |

## Groups

A **group** is a contiguous block of lines. A **blank line starts a new group**,
so `$sum` totals only from the last blank line down to the line above it — not
the whole document. This lets one notepad hold several independent tallies.

```
Angebot: 2000
Rabatt: $sum - 5%     -> 1900   (2000 minus 5% of 2000)

Posten: 10
Posten: 20
$sum                  -> 30     (blank line above reset the total)
```

What counts toward the total:

- **Every successful result above** in the group — bare expressions and labeled
  lines alike.
- **Assignments count too**: `price = 20` contributes `20`.
- The current line and everything below it are **excluded** ("above it").
- Error / blank lines contribute nothing (a blank line also resets the group).

## Formatting

A `$`-variable line **inherits the decimal style of its group**. When the line
carries no decimals of its own, it borrows the separator and place-count of the
lines above it, so a `,00` group keeps `,00` down through its total:

```
Angebot: 2000,00 Euro     -> 2000,00
Discount: $sum - 35%      -> 1300,00   (inherits ",00" from the group)
```

Rules:

- Only lines that **reference a `$`-variable** inherit — a plain `5 * 3` is not
  reformatted by a `,00` group.
- A line with **its own decimals wins**: `$sum + 1,5` uses one place, not the
  group's two.
- A group with **no decimals stays integer**: `$sum` over `10` / `20` is `30`.
- A **blank line resets** the inherited style along with the total.

## Autocomplete

Type `$` and the available inline variables are offered as ghost text, exactly
like `/`-command autosuggest — **Tab** fills, works anywhere in a line. See
[commands.md](commands.md#inline-autosuggest) for the full autosuggest behavior.

## Coloring

Inline variables have their own syntax color category, `inline` (default Dracula
orange `#ffb86c`), distinct from user `variable` names. Recolor it with
`/window-inline-color <hex>` or swap the whole palette with `/window-theme`. See
[syntax-coloring.md](syntax-coloring.md).

## Implementation

The design mirrors the postfix-percent (`_pct`) rewrite: a sugar token is
rewritten in preprocessing to a safe internal name, and its value is supplied
through `scope`. No new AST node types, so the evaluator's whitelist (the
security boundary) is untouched.

- `engine/inline.py` — data-only source of truth: `INLINE_VARS` (the names) and
  `scope_key(name)` (`"sum"` → `"_inline_sum"`). Extend the feature by adding a
  name here.
- `engine/preprocess.py` — `normalize()` rewrites each `$name` to `scope_key(name)`
  via `_DOLLAR_RE`. Only defined names are rewritten; a stray `$foo` is left for
  `ast.parse` to reject as an invalid expression. `has_inline_var()` (same regex)
  reports whether a line references a `$`-variable, used for the formatting rule.
- `gui/document_evaluator.py` — `evaluate_document()` is the only layer that knows
  line order. It keeps a per-group running sum, resets it on blank lines, and
  writes it into `scope[_SUM_KEY]` **before** each `evaluate()` call, folding the
  line's own result in afterward. `inherited_styles()` walks the same groups to
  give each `$`-variable line the decimal style to inherit (see
  [Formatting](#formatting)); `format_result()` applies it when the line has no
  decimals of its own.
- `gui/syntax.py` — the `inline` token category and its `$`-token regex group.
- `gui/themes.py` — the `inline` color field, per-theme values, and
  `syntax_colors()` entry.
- `gui/commands.py` — `INLINE_TOKENS` (autocomplete) and the `$`-aware
  `command_at`/`suggest`; the `/window-inline-color` command; `build_copy_text`
  and `last_result_text` thread the inherited style so the clipboard matches the pane.
- Tests: `tests/test_preprocess.py` (rewrite, `has_inline_var`),
  `tests/test_document_evaluator.py` (grouping / reset / assignments / style
  inheritance), `tests/test_syntax.py` (coloring), `tests/test_themes.py`
  (palette), `tests/test_commands.py` (autocomplete, inherited-style copy).

### Adding another inline variable

1. Add its name to `INLINE_VARS` in `engine/inline.py`.
2. Compute its value in `evaluate_document()` and inject it into `scope` under
   `scope_key(name)` (the running-sum loop is the pattern to follow).

Everything else — preprocessing, autocomplete, and coloring — follows from the
shared `INLINE_VARS` with no further wiring.
