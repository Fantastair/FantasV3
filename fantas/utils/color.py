"""
提供颜色相关的增强功能。
"""

from __future__ import annotations

import fantas

__all__ = ("get_distinct_blackorwhite",)


def get_distinct_blackorwhite(color: fantas.Color) -> fantas.Color:
    """
    根据输入颜色的亮度，返回一个与之对比鲜明的黑色或白色。

    :param color: 输入颜色
    :type color: fantas.Color
    :return: 与输入颜色对比鲜明的黑色或白色颜色对象
    :rtype: fantas.Color
    """
    h, s, l, a = color.hsla
    return fantas.Color.from_hsla(h, s, 100 if l < 50 else 0, a)
