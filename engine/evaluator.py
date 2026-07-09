"""Safe evaluation of a single calculator line.

Security model: we parse with the stdlib `ast` (never eval/exec) and walk an
explicit whitelist of node types. Anything outside the whitelist — attribute
access, subscripts, lambdas, comprehensions, dunder tricks — is rejected before
any value is produced. This is the boundary that makes running user text safe.
"""

from __future__ import annotations

import ast
import operator
from collections.abc import Callable

from .errors import (
    EmptyLineError,
    UnknownFunctionError,
    UnknownNameError,
    UnsafeExpressionError,
)
from .functions import CONSTANTS, FUNCTIONS
from .preprocess import normalize, split_assignment
from .result import EvalResult

Scope = dict[str, float]


class _Percent(float):
    """A number typed with a trailing '%'. Its float value is already p/100
    (so 19% == 0.19), which makes '*' and '/' correct for free; '+' and '-'
    get special handling in BinOp so "100+19%" means 100 + 19% of 100."""

    __slots__ = ()


_BINARY_OPS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

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

        name, raw_expr = split_assignment(stripped)
        tree = ast.parse(normalize(raw_expr), mode="eval")
        value = float(_eval_node(tree.body, scope))

        if name is not None:
            scope[name] = value
            return EvalResult.ok(value, assigned_name=name)
        return EvalResult.ok(value)
    except EmptyLineError:
        return EvalResult.fail("empty")
    except ZeroDivisionError:
        return EvalResult.fail("division by zero")
    except (UnknownNameError, UnknownFunctionError, UnsafeExpressionError) as exc:
        return EvalResult.fail(str(exc))
    except SyntaxError:
        return EvalResult.fail("invalid expression")
    except (ValueError, TypeError, OverflowError) as exc:
        return EvalResult.fail(str(exc))


def _eval_node(node: ast.AST, scope: Scope) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise UnsafeExpressionError("only numbers are allowed")
        return float(node.value)

    if isinstance(node, ast.BinOp):
        op = _BINARY_OPS.get(type(node.op))
        if op is None:
            raise UnsafeExpressionError("unsupported operator")
        left = _eval_node(node.left, scope)
        right = _eval_node(node.right, scope)
        if isinstance(right, _Percent) and isinstance(node.op, (ast.Add, ast.Sub)):
            return op(left, left * float(right))
        return op(left, right)

    if isinstance(node, ast.UnaryOp):
        unary = _UNARY_OPS.get(type(node.op))
        if unary is None:
            raise UnsafeExpressionError("unsupported operator")
        return unary(_eval_node(node.operand, scope))

    if isinstance(node, ast.Name):
        if node.id in scope:
            return scope[node.id]
        if node.id in CONSTANTS:
            return CONSTANTS[node.id]
        raise UnknownNameError(f"unknown name: {node.id}")

    if isinstance(node, ast.Call):
        return _eval_call(node, scope)

    raise UnsafeExpressionError("unsupported expression")


def _eval_call(node: ast.Call, scope: Scope) -> float:
    if not isinstance(node.func, ast.Name):
        raise UnsafeExpressionError("unsupported call")
    if node.keywords:
        raise UnsafeExpressionError("keyword arguments are not allowed")
    if node.func.id == "_pct":
        if len(node.args) != 1:
            raise UnsafeExpressionError("percent takes one value")
        return _Percent(_eval_node(node.args[0], scope) / 100.0)
    func = FUNCTIONS.get(node.func.id)
    if func is None:
        raise UnknownFunctionError(f"unknown function: {node.func.id}")
    args = [_eval_node(arg, scope) for arg in node.args]
    return float(func(*args))
