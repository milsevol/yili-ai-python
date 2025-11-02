"""
数学计算工具 - 提供安全的数学表达式计算
"""

import ast
import operator
from typing import Union
from langchain_core.tools import tool


class SafeMathEvaluator:
    """安全的数学表达式求值器"""
    
    # 支持的操作符映射
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Mod: operator.mod,
    }
    
    # 支持的函数
    FUNCTIONS = {
        'abs': abs,
        'round': round,
        'max': max,
        'min': min,
        'sum': sum,
    }
    
    def evaluate(self, expression: str) -> Union[int, float]:
        """安全地计算数学表达式"""
        try:
            # 解析表达式为AST
            tree = ast.parse(expression.strip(), mode='eval')
            return self._eval_node(tree.body)
        except Exception as e:
            raise ValueError(f"表达式解析错误: {str(e)}")
    
    def _eval_node(self, node) -> Union[int, float]:
        """递归求值AST节点"""
        if isinstance(node, ast.Constant):
            # 常量值（数字）
            if isinstance(node.value, (int, float)):
                return node.value
            else:
                raise ValueError(f"不支持的常量类型: {type(node.value)}")
        elif isinstance(node, ast.Name):
            # 变量名（如pi, e等）
            if node.id in {'pi': 3.141592653589793, 'e': 2.718281828459045}:
                return {'pi': 3.141592653589793, 'e': 2.718281828459045}[node.id]
            else:
                raise ValueError(f"不支持的变量: {node.id}")
        elif isinstance(node, ast.BinOp):
            # 二元操作（如加减乘除）
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"不支持的操作符: {type(node.op)}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            # 一元操作（如负号）
            operand = self._eval_node(node.operand)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"不支持的一元操作符: {type(node.op)}")
            return op(operand)
        elif isinstance(node, ast.Call):
            # 函数调用
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name not in self.FUNCTIONS:
                raise ValueError(f"不支持的函数: {func_name}")
            
            args = [self._eval_node(arg) for arg in node.args]
            return self.FUNCTIONS[func_name](*args)
        else:
            raise ValueError(f"不支持的节点类型: {type(node)}")


@tool
def safe_calculator(expression: str) -> str:
    """
    安全的数学计算器
    
    支持基本的数学运算：+, -, *, /, **, %, abs(), round(), max(), min(), sum()
    支持常量：pi, e
    
    示例：
    - 2 + 3 * 4
    - (10 + 5) / 3
    - 2 ** 3
    - abs(-5)
    - round(3.14159, 2)
    """
    try:
        evaluator = SafeMathEvaluator()
        result = evaluator.evaluate(expression)
        
        # 格式化结果
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        elif isinstance(result, float):
            return f"{result:.6g}"  # 最多6位有效数字
        else:
            return str(result)
            
    except Exception as e:
        return f"计算错误: {str(e)}"