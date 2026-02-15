"""
提供曲线相关的类和预定义曲线。

.. tip::

    曲线可以来控制动画，轻松实现优秀的非线性动画效果。
    
    当然你也可以用于其他数学用途。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, cast
import math

import fantas

__all__ = (
    "CurveBase",
    "FormulaCurve",
    "CURVE_LINEAR",
    "CURVE_FASTER",
    "CURVE_SLOWER",
    "CURVE_SMOOTH",
)


@dataclass(slots=True, frozen=True)
class CurveBase(ABC):
    """
    曲线抽象基类。

    通过曲线求值的方式是直接调用曲线对象，传入因变量，
    因此子类需要实现 __call__ 方法来定义曲线的具体形状。
    """

    @abstractmethod
    def __call__(self, x: float) -> float:
        """
        计算曲线在给定 x 值处的 y 值。
        
        :param x: 输入的 x 值。
        :type x: float
        :return: 对应的 y 值。
        :rtype: float

        子类需要实现这个方法来定义曲线的具体形状。
        """



formula_globals: dict[str, object] = {
    "math": math,
    "pi": math.pi,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "__builtins__": {"float": float, "int": int},
}


@dataclass(slots=True, frozen=True)
class FormulaCurve(CurveBase):
    """
    使用数学公式定义的曲线。

    .. hint::

        公式曲线在求值时会自动使用缓存，因此不用担心太复杂的求值公式会导致性能问题。

        你可以提前空跑一些可能用到的 x 值来预热缓存。
    """

    formula: str
    """
    用于计算 y 值的数学公式，变量为 x。以及 float 和 int 类型转换函数。
    其他数学函数需要通过 math 模块调用，例如 math.sqrt(x)。
    """

    @fantas.lru_cache_typed(maxsize=65536)
    def __call__(self, x: float) -> float:
        """
        计算曲线在给定 x 值处的 y 值。
        
        :param x: 输入的 x 值。
        :type x: float
        :return: 对应的 y 值。
        :rtype: float
        """
        return cast(float, eval(self.formula, formula_globals, {"x": x}))


CURVE_LINEAR: Callable[[float], float] = lambda x: x  # pylint: disable=invalid-name
"""
线性曲线，y = x

:param x: 输入的 x 值。
:type x: float
:return: 对应的 y 值。
:rtype: float
"""
CURVE_FASTER: Callable[[float], float] = lambda x: x * x  # pylint: disable=invalid-name
"""
渐快曲线，y = x^2

:param x: 输入的 x 值。
:type x: float
:return: 对应的 y 值。
:rtype: float
"""
CURVE_SLOWER: Callable[[float], float] = (  # pylint: disable=invalid-name
    lambda x: 2 * x - x * x
)
"""
渐慢曲线，y = 2x - x^2

:param x: 输入的 x 值。
:type x: float
:return: 对应的 y 值。
:rtype: float
"""
CURVE_SMOOTH: FormulaCurve = FormulaCurve(
    "(1-cos(pi*x))/2"
)  # pylint: disable=invalid-name
"""
平滑曲线，y = (1 - cos(pi * x)) / 2

:param x: 输入的 x 值。
:type x: float
:return: 对应的 y 值。
:rtype: float
"""
