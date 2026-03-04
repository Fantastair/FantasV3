"""
关键帧模块，用于在一定时间内按比例调用一个函数。
"""

from abc import ABC, abstractmethod
from typing import Any, Callable
from dataclasses import dataclass, field

import fantas
from fantas import TimerBase

__all__ = (
    "KeyFrameBase",
    "AttrKeyFrame",
    "ColorKeyframe",
    "PointKeyFrame",
)


# 简化引用
clamp = fantas.math.clamp
lerp = fantas.math.lerp


@dataclass(slots=True)
class KeyFrameBase(TimerBase, ABC):
    """
    关键帧基类，用于在指定的时间内按比例调用一个函数。
    """

    def call(self) -> bool:
        ratio = clamp((fantas.get_time_ns() - self.start_time) / self.duration_ns, 0, 1)
        self.tick(ratio)
        return TimerBase.call(self)

    @abstractmethod
    def tick(self, ratio: float) -> None:
        """
        关键帧的时间点调用接口。

        Args:
            ratio (float): 当前时间点与总时间的比例。
        """


@dataclass(slots=True)
class AttrKeyFrame(KeyFrameBase):
    """
    属性关键帧类，用于修改对象的属性。
    Args:
        obj       : 目标对象。
        attr      : 目标属性名。
        end_value : 结束值。
        map_curve : 映射曲线。
    """

    obj: object = field(compare=False)
    attr: str = field(compare=False)
    end_value: float = field(compare=False)
    map_curve: Callable[[float], float] = field(
        compare=False, default=fantas.CURVE_LINEAR
    )

    start_value: float = field(init=False, compare=False)  # 起始值，在启动时设置

    def start(
        self,
        start_value: Any = None,
        restart: bool = False,
    ) -> None:
        """
        启动属性关键帧。

        Args:
            start_value (float, optional): 起始值。为 None 则使用当前属性值作为起始值。
            restart (bool): 重复启动关键帧时是否重新获取当前属性值作为起始值。
        """
        KeyFrameBase.start(self)
        if not (self.is_started() and restart):
            if start_value is None:
                self.start_value = getattr(self.obj, self.attr)
            else:
                self.start_value = start_value
            if fantas.CLOCK is not None:
                # 需要把 start_time 往前调整一帧的时间，否则重启后的动画会有一帧的停顿
                fps = fantas.CLOCK.get_fps()
                self.start_time -= round(1_000_000_000 / fps) if fps > 0 else 0

    def tick(self, ratio: float) -> None:
        """
        在指定的时间点修改对象的属性。

        Args:
            ratio (float): 当前时间点与总时间的比例。
        """
        setattr(
            self.obj,
            self.attr,
            lerp(self.start_value, self.end_value, self.map_curve(ratio), False),
        )


@dataclass(slots=True)
class ColorKeyframe(AttrKeyFrame):
    """
    颜色关键帧类，用于修改对象的颜色属性。
    """

    end_value: fantas.Color = field(compare=False)  # type: ignore [assignment]
    start_value: fantas.Color = field(
        init=False, compare=False
    )  # type: ignore [assignment]  # 起始值，在启动时设置

    def start(
        self, start_value: fantas.Color | None = None, restart: bool = False
    ) -> None:
        """
        启动颜色关键帧。

        Args:
            start_value (Color, optional): 起始值。为 None 则使用当前属性值作为起始值。
            restart (bool): 重复启动关键帧时是否重新获取当前属性值作为起始值。
        """
        AttrKeyFrame.start(self, start_value, restart)
        if not isinstance(self.start_value, fantas.Color):
            self.start_value = fantas.Color(self.start_value)

    def tick(self, ratio: float) -> None:
        """
        在指定的时间点修改对象的颜色属性。

        Args:
            ratio (float): 当前时间点与总时间的比例。
        """
        setattr(
            self.obj,
            self.attr,
            self.start_value.lerp(self.end_value, clamp(self.map_curve(ratio), 0, 1)),
        )


@dataclass(slots=True)
class PointKeyFrame(AttrKeyFrame):
    """
    点关键帧类，用于修改对象的点属性。
    """

    end_value: fantas.Vector2 = field(compare=False)  # type: ignore [assignment]
    start_value: fantas.Vector2 = field(
        init=False, compare=False
    )  # type: ignore [assignment]  # 起始值，在启动时设置

    def start(self, start_value: Any = None, restart: bool = False) -> None:
        """
        启动点关键帧。

        Args:
            start_value (Point, optional): 起始值。为 None 则使用当前属性值作为起始值。
            restart (bool): 重复启动关键帧时是否重新获取当前属性值作为起始值。
        """
        AttrKeyFrame.start(self, start_value, restart)
        if not isinstance(self.start_value, fantas.Vector2):
            self.start_value = fantas.Vector2(self.start_value)

    def tick(self, ratio: float) -> None:
        """
        在指定的时间点修改对象的点属性。

        Args:
            ratio (float): 当前时间点与总时间的比例。
        """
        setattr(
            self.obj,
            self.attr,
            self.start_value.lerp(self.end_value, clamp(self.map_curve(ratio), 0, 1)),
        )
