"""
其他杂项工具。
"""

import platform
from pathlib import Path
from typing import Callable, ParamSpec, TypeVar, cast

from functools import lru_cache, wraps
from dataclasses import dataclass, field

import fantas

__all__ = (
    "platform",
    "lru_cache_typed",
    "set_cursor",
    "image_convert_hook",
    "image_convert_alpha_hook",
    "AnimationHelper",
)



P = ParamSpec("P")
R = TypeVar("R")


# 类型装饰器以支持类型注解的 lru_cache
def lru_cache_typed(
    maxsize: int = 128, typed: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    生成一个保留原函数类型签名的 LRU 缓存装饰器。
    Args:
        maxsize (int): 缓存的最大数目。
        typed (bool) : 是否区分不同类型的参数。
    Returns:
        Callable: 装饰器函数。
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        @lru_cache(maxsize=maxsize, typed=typed)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        return cast(Callable[P, R], wrapper)

    return decorator


# 光标样式映射表
cursor_map = {
    "^": fantas.SYSTEM_CURSOR_ARROW,
    "I": fantas.SYSTEM_CURSOR_IBEAM,
    "O": fantas.SYSTEM_CURSOR_WAIT,
    "+": fantas.SYSTEM_CURSOR_CROSSHAIR,
    "^O": fantas.SYSTEM_CURSOR_WAITARROW,
    "\\": fantas.SYSTEM_CURSOR_SIZENWSE,
    "/": fantas.SYSTEM_CURSOR_SIZENESW,
    "-": fantas.SYSTEM_CURSOR_SIZEWE,
    "|": fantas.SYSTEM_CURSOR_SIZENS,
    "^+": fantas.SYSTEM_CURSOR_SIZEALL,
    "0": fantas.SYSTEM_CURSOR_NO,
    "h": fantas.SYSTEM_CURSOR_HAND,
}


def set_cursor(style: str) -> None:
    """设置鼠标光标样式。
    Args:
        style (str): 光标样式字符串，支持以下值：
        ^ : 默认箭头光标
        I : 文本输入光标
        O : 等待光标
        + : 十字准星光标
        ^O: 等待箭头光标
        (反斜杠): 斜向调整大小光标（左上-右下）
        / : 斜向调整大小光标（右上-左下）
        - : 水平调整大小光标
        | : 垂直调整大小光标
        ^+: 全向调整大小光标
        0 : 禁止操作光标
        h : 手形光标
    """
    fantas.mouse.set_cursor(cursor_map.get(style, fantas.SYSTEM_CURSOR_ARROW))


def image_convert_hook(surface: fantas.Surface) -> fantas.Surface:
    """图像转换钩子函数，将图像转换为与显示器兼容的格式。"""
    return surface.convert()


def image_convert_alpha_hook(surface: fantas.Surface) -> fantas.Surface:
    """图像转换钩子函数，将图像转换为与显示器兼容的格式。"""
    return surface.convert_alpha()


@dataclass(slots=True)
class AnimationHelper:
    """
    动画资源辅助类。
    """

    frames: list[fantas.Surface] = field(repr=False)  # 动画帧列表
    cumulative_times: list[float] = field(
        repr=False
    )  # 累积时间列表，cumulative_times[i] 表示第 i 帧的开始时间（单位：ns）

    def __init__(
        self,
        path: Path,
        hook: Callable[[fantas.Surface], fantas.Surface] = image_convert_hook,
    ) -> None:
        """
        初始化动画资源辅助类。
        Args:
            path (Path): 动画文件路径。
            hook (Callable[[fantas.Surface], fantas.Surface], optional):
                图像转换钩子函数，默认为 image_convert_hook。
        """
        self.frames = []
        self.cumulative_times = []
        animation = fantas.image.load_animation(path)
        self.cumulative_times = [0.0]
        for frame, duration in animation:
            self.frames.append(hook(frame))
            self.cumulative_times.append(self.cumulative_times[-1] + duration * 1e6)
