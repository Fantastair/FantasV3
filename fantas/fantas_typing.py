"""
提供 fantas 模块中使用的类型别名，或把某些 pygame 类型重新导出以供 fantas 使用。
"""

from typing import TypeAlias, Callable

__all__ = (
    "Surface",
    "PixelArray",
    "RectLike",
    "Rect",
    "FRect",
    "ColorLike",
    "Color",
    "Point",
    "IntPoint",
    "FileLike",
    "Event",
    "EventType",
    "UIid",
    "ListenerKey",
    "ListenerFunc",
    "ListenerDict",
    "QuadrantMask",
    "TextStyleFlag",
    "BlendFlag",
    "Vector2",
    "Vector3",
)

from fantas._vendor.pygame import (
    Surface,
    PixelArray,
    Rect,
    FRect,
    Color,
    Event,
    Vector2,
    Vector3,
)

from fantas._vendor.pygame.typing import RectLike, ColorLike, Point, IntPoint, FileLike

EventType: TypeAlias = int  # 事件类型

UIid: TypeAlias = int  # UI 元素唯一标识类型
ListenerKey: TypeAlias = tuple[EventType, UIid, bool]  # 监听器键类型
ListenerFunc: TypeAlias = Callable[[Event], bool | None]  # 监听器函数类型
ListenerDict: TypeAlias = dict[ListenerKey, list[ListenerFunc]]  # 监听器字典类型

QuadrantMask: TypeAlias = int  # 象限掩码类型，是 fantas.Quadrant 通过或运算得到的值

TextStyleFlag: TypeAlias = (
    int  # 文本风格标志类型，加粗、斜体等，TEXTSTYLEFLAG_* 常量或它们的 或运算 结果
)

BlendFlag: TypeAlias = int  # 混合标志类型，BLEND_* 常量
