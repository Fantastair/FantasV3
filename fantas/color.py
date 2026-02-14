from __future__ import annotations

import fantas

__all__ = ("get_distinct_blackorwhite",)


def get_distinct_blackorwhite(color: fantas.Color) -> fantas.Color:
    """
    获取与当前颜色形成高对比度的黑色或白色颜色对象。
    Args:
        color (Color): 原颜色对象。
    Returns:
        Color: 生成的高对比度颜色对象。
    """
    # 提取原颜色的HSLA值
    h, s, l, a = color.hsla
    # 返回新的颜色对象
    return fantas.Color.from_hsla(h, s, 100 if l < 50 else 0, a)
