"""Safe evaluation of a single calculator line.

Security model: we parse with the stdlib `ast` (never eval/exec) and walk an
explicit whitelist of node types. Anything outside the whitelist — attribute
access, subscripts, lambdas, comprehensions, dunder tricks — is rejected before
any value is produced. This is the boundary that makes running user text safe.

Values flow as `Quantity` (see `units.py`): plain numbers are dimensionless
quantities, unit words resolve like constants, and all arithmetic goes through
`units.apply_binop`. Units never become strings, so the whitelist is unchanged.
"""

from __future__ import annotations

import ast
import operator
from collections.abc import Callable

from .errors import (
    EmptyLineError,
    IncompatibleUnitsError,
    UnknownFunctionError,
    UnknownNameError,
    UnsafeExpressionError,
)
from .functions import CONSTANTS, FUNCTIONS
from .inline import scope_key
from .preprocess import (
    _LEADING_OP_RE,
    normalize,
    split_assignment,
    strip_label,
    strip_unknown_words,
    uses_german_comparison,
)
from .result import EvalResult
from .units import (
    DIMLESS,
    TIME,
    UNITS,
    Quantity,
    apply_binop,
    compare,
    convert,
    dimensionless,
    require_number,
    unit_quantity,
)
from .words import BOOL_TEXT

Scope = dict[str, Quantity]

_UNARY_OPS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def evaluate(line: str, scope: Scope) -> EvalResult:
    """Evaluate one line against `scope`; store the result if it is an assignment.

    Never raises: every failure is returned as `EvalResult.fail(...)`.
    """
    try:
        stripped = line.strip()
        if not stripped:
            raise EmptyLineError("empty")

        name, raw_expr = split_assignment(strip_label(stripped))
        expr = normalize(raw_expr)
        # A line starting with a binary operator continues from the running
        # total: "- 4000" -> "$sum - 4000". Only in document context, where the
        # sum key is injected into scope; a bare engine call keeps unary math.
        sum_key = scope_key("sum")
        in_document = sum_key in scope
        if in_document and _LEADING_OP_RE.match(expr) is not None:
            expr = f"{sum_key} {expr}"
        # `continued` means "the running total is already folded into this
        # result", so the document layer replaces the total instead of adding to
        # it. True for both spellings: the implicit "- 4000" and an explicit
        # "$sum - 35%" — adding either back would count the total twice.
        continued = in_document and sum_key in expr
        known = {*scope, *CONSTANTS, *FUNCTIONS, *UNITS, "_pct", "_time", "_to"}
        stripped_expr = strip_unknown_words(expr, known)
        tree = ast.parse(stripped_expr.expr, mode="eval")
        if isinstance(tree.body, ast.Compare):
            if name is not None:
                raise UnsafeExpressionError("cannot assign a comparison")
            return _eval_compare(tree.body, scope, uses_german_comparison(stripped))
        value = _eval_node(tree.body, scope)

        if name is not None:
            scope[name] = value
        return EvalResult.from_quantity(
            value,
            assigned_name=name,
            continued=continued,
            unit_label=_unit_label(stripped_expr.dropped),
        )
    except EmptyLineError:
        return EvalResult.fail("empty")
    except ZeroDivisionError:
        return EvalResult.fail("division by zero")
    except (
        UnknownNameError,
        UnknownFunctionError,
        UnsafeExpressionError,
        IncompatibleUnitsError,
    ) as exc:
        return EvalResult.fail(str(exc))
    except SyntaxError:
        return EvalResult.fail("invalid expression")
    except (ValueError, TypeError, OverflowError) as exc:
        return EvalResult.fail(str(exc))


def _unit_label(dropped: tuple[str, ...]) -> str | None:
    """The display-only unit word for a line, or None.

    Only a single distinct dropped word is a unit ("5 kg + 5 kg" -> "kg");
    mixed words ("1 apple + 2 orange") describe no shared quantity, so the
    result stays unlabelled rather than picking one arbitrarily.
    """
    distinct = set(dropped)
    return dropped[0] if len(distinct) == 1 else None


def _eval_compare(node: ast.Compare, scope: Scope, german: bool) -> EvalResult:
    """A top-level comparison ("a == b") -> localized true/false result.

    Only handled here, never in `_eval_node`, so a Compare nested inside
    arithmetic or a call stays outside the whitelist and is rejected.
    """
    if len(node.ops) != 1:
        raise UnsafeExpressionError("chained comparisons are not supported")
    left = _eval_node(node.left, scope)
    right = _eval_node(node.comparators[0], scope)
    truth = compare(type(node.ops[0]), left, right)
    true_text, false_text = BOOL_TEXT["de" if german else "en"]
    return EvalResult.from_bool(truth, true_text if truth else false_text)


def _eval_node(node: ast.AST, scope: Scope) -> Quantity:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise UnsafeExpressionError("only numbers are allowed")
        return dimensionless(float(node.value))

    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, scope)
        right = _eval_node(node.right, scope)
        return apply_binop(type(node.op), left, right)

    if isinstance(node, ast.UnaryOp):
        unary = _UNARY_OPS.get(type(node.op))
        if unary is None:
            raise UnsafeExpressionError("unsupported operator")
        q = _eval_node(node.operand, scope)
        return Quantity(unary(q.mag), q.dim, q.unit, q.percent)

    if isinstance(node, ast.Name):
        if node.id in scope:
            v = scope[node.id]
            # The document layer injects a plain float ($sum); wrap it.
            return v if isinstance(v, Quantity) else dimensionless(v)
        if node.id in CONSTANTS:
            return dimensionless(CONSTANTS[node.id])
        if node.id in UNITS:
            return unit_quantity(UNITS[node.id])
        raise UnknownNameError(f"unknown name: {node.id}")

    if isinstance(node, ast.Call):
        return _eval_call(node, scope)

    raise UnsafeExpressionError("unsupported expression")


def _eval_call(node: ast.Call, scope: Scope) -> Quantity:
    if not isinstance(node.func, ast.Name):
        raise UnsafeExpressionError("unsupported call")
    if node.keywords:
        raise UnsafeExpressionError("keyword arguments are not allowed")
    name = node.func.id

    if name == "_pct":
        if len(node.args) != 1:
            raise UnsafeExpressionError("percent takes one value")
        return Quantity(_number_arg(node.args[0], scope) / 100.0, DIMLESS, percent=True)
    if name == "_time":
        if len(node.args) != 1:
            raise UnsafeExpressionError("time takes one value")
        return Quantity(_number_arg(node.args[0], scope), TIME)
    if name == "_to":
        if len(node.args) != 2:
            raise UnsafeExpressionError("conversion takes two values")
        return convert(_eval_node(node.args[0], scope), _eval_node(node.args[1], scope))

    func = FUNCTIONS.get(name)
    if func is None:
        raise UnknownFunctionError(f"unknown function: {name}")
    args = [require_number(_eval_node(arg, scope)) for arg in node.args]
    return dimensionless(func(*args))


def _number_arg(node: ast.AST, scope: Scope) -> float:
    """Evaluate an argument that must be a plain number (percent/time literal)."""
    return require_number(_eval_node(node, scope))
