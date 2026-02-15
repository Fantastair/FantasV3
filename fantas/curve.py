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
    抽象基类，表示一个曲线。
    """

    @abstractmethod
    def __call__(self, x: float) -> float:
        """
        计算曲线在给定 x 值处的 y 值。

        Args:
            x (float): 输入的 x 值。

        Returns:
            float: 对应的 y 值。
        """
        pass


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

    Args:
        formula: 用于计算 y 值的数学公式，变量为 x。
    """

    formula: str

    @fantas.lru_cache_typed(maxsize=65536)
    def __call__(self, x: float) -> float:
        """
        计算曲线在给定 x 值处的 y 值。

        Args:
            x (float): 输入的 x 值。

        Returns:
            float: 对应的 y 值。
        """
        return cast(float, eval(self.formula, formula_globals, {"x": x}))


# 预定义曲线
# 线性曲线，y = x
CURVE_LINEAR: Callable[[float], float] = lambda x: x
# 渐快曲线，y = x^2
CURVE_FASTER: Callable[[float], float] = lambda x: x * x
# 渐慢曲线，y = 2x - x^2
CURVE_SLOWER: Callable[[float], float] = lambda x: 2 * x - x * x
# 平滑曲线，y = (1 - cos(pi * x)) / 2
CURVE_SMOOTH: FormulaCurve = FormulaCurve("(1-cos(pi*x))/2")
