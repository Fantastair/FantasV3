"""
提供 fantas 模块中使用的类型别名，或把某些 pygame 类型重新导出以供 fantas 使用。
"""

from typing import TypeAlias, Callable
import pygame

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

from pygame import Surface  # 表面类
from pygame import PixelArray  # 像素数组类

RectLike: TypeAlias = pygame.typing.RectLike  # 矩形类型
from pygame import Rect, FRect  # 矩形类

ColorLike: TypeAlias = pygame.typing.ColorLike  # 颜色类型
from pygame import Color  # 颜色类

Point: TypeAlias = pygame.typing.Point  # 点类
IntPoint: TypeAlias = pygame.typing.IntPoint  # 整数点类

FileLike: TypeAlias = pygame.typing.FileLike  # 文件类

from pygame.event import Event  # 事件类

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

Vector2 = pygame.math.Vector2  # 二维向量类
Vector3 = pygame.math.Vector3  # 三维向量类
