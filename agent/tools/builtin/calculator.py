"""计算器工具：执行数学表达式计算。"""

from __future__ import annotations

import ast
import operator
from typing import Any

from ..base import BaseTool

# 允许的运算符
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class CalculatorTool(BaseTool):
    """计算器工具，支持安全的数学表达式求值。"""

    name = "calculator"
    description = "执行数学表达式计算，支持加减乘除、幂、取模等运算"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式，如 '2 + 3 * 4'"},
        },
        "required": ["expression"],
    }

    def run(self, expression: str, **kwargs: Any) -> str:
        try:
            tree = ast.parse(expression, mode="eval")
            result = self._eval_node(tree.body)
            return str(result)
        except Exception as e:
            return f"计算错误: {e}"

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _OPERATORS:
                raise ValueError(f"不支持的运算符: {op_type.__name__}")
            return _OPERATORS[op_type](self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _OPERATORS:
                raise ValueError(f"不支持的一元运算符: {op_type.__name__}")
            return _OPERATORS[op_type](self._eval_node(node.operand))
        raise ValueError(f"不支持的表达式节点: {type(node).__name__}")
