"""
framefunc.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Callable
from abc import ABC, abstractmethod
from typing import Any

import fantas

__all__ = (
    "set_framefunc_clock",
    "run_framefuncs",
    "FrameFuncBase",
    "FramerBase",
    "TimerBase",
    "FrameTrigger",
    "TimeTrigger",
    "KeyFrameBase",
    "AttrKeyFrame",
    "ColorKeyframe",
    "PointKeyFrame",
)

# 简化引用
clamp = fantas.math.clamp
lerp = fantas.math.lerp

# 时钟对象引用
CLOCK: fantas.time.Clock | None = None


def set_framefunc_clock(new_clock: fantas.time.Clock) -> None:
    """
    设置全局时钟对象。

    Args:
        new_clock (Clock): 新的时钟对象。
    """
    global CLOCK  # pylint: disable=global-statement
    CLOCK = new_clock


# 帧函数字典
framefunc_dict: dict[int, FrameFuncBase] = {}


def run_framefuncs() -> None:
    """
    运行所有已启动的帧函数。
    """
    for func_id, framefunc in tuple(framefunc_dict.items()):
        if framefunc.call():
            framefunc_dict.pop(func_id)


@dataclass(slots=True)
class FrameFuncBase(ABC):
    """
    帧函数基类，用于定义帧函数接口。
    """

    func_id: int = field(
        default_factory=fantas.generate_unique_id, init=False
    )  # 唯一标识 ID

    def start(self) -> None:
        """
        启动帧函数。
        """
        framefunc_dict[self.func_id] = self

    def stop(self) -> None:
        """
        停止帧函数。
        """
        framefunc_dict.pop(self.func_id, None)

    def is_started(self) -> bool:
        """
        检查帧函数是否已启动。

        Returns:
            bool: 如果帧函数已启动则返回 True，否则返回 False。
        """
        return self.func_id in framefunc_dict

    @abstractmethod
    def call(self) -> bool:
        """
        帧函数调用接口。
        Returns:
            bool: 返回 True 可以自动停止帧函数，返回 False 则继续运行。
        """


@dataclass(slots=True)
class FramerBase(FrameFuncBase):
    """
    定帧器基类，会在启动一定帧数后自动停止。
    """

    duration_frames: int = field(default=0, init=False)  # 持续帧数
    current_frame: int = field(init=False)  # 当前帧数

    def start(self) -> None:
        """
        启动定帧器。
        """
        FrameFuncBase.start(self)
        self.current_frame = 0

    def call(self) -> bool:
        """
        定帧器的帧函数调用接口。

        Returns:
            bool: 如果定帧器已达到持续帧数则返回 True，否则返回 False。
        """
        self.current_frame += 1
        if self.current_frame >= self.duration_frames:
            return True
        return False

    def set_duration_frames(self, duration_frames: int) -> None:
        """
        设置持续帧数。

        Args:
            duration_frames (int): 持续帧数。
        """
        self.duration_frames = duration_frames


@dataclass(slots=True)
class TimerBase(FrameFuncBase):
    """
    定时器基类，会在启动一定时间后自动停止。
    """

    duration_ns: int | float = field(default=0, init=False)  # 持续时间（纳秒）
    start_time: int = field(init=False)  # 开始时间（纳秒）

    def start(self) -> None:
        """
        启动定时器。
        """
        FrameFuncBase.start(self)
        self.start_time = fantas.get_time_ns()

    def call(self) -> bool:
        """
        定时器的帧函数调用接口。

        Returns:
            bool: 如果定时器已达到持续时间则返回 True，否则返回 False。
        """
        if fantas.get_time_ns() - self.start_time >= self.duration_ns:
            return True
        return False

    def set_duration_ns(self, duration: int | float) -> None:
        """
        设置持续时间。

        Args:
            duration (int | float): 持续时间（纳秒）。
        """
        self.duration_ns = duration

    def set_duration_us(self, duration: int | float) -> None:
        """
        设置持续时间。

        Args:
            duration (int | float): 持续时间（微秒）。
        """
        self.duration_ns = duration * 1000

    def set_duration_ms(self, duration: int | float) -> None:
        """
        设置持续时间。

        Args:
            duration (int | float): 持续时间（毫秒）。
        """
        self.duration_ns = duration * 1_000_000

    def set_duration_s(self, duration: int | float) -> None:
        """
        设置持续时间。

        Args:
            duration (int | float): 持续时间（秒）。
        """
        self.duration_ns = duration * 1_000_000_000


@dataclass(slots=True)
class FrameTrigger(FramerBase):
    """
    帧触发器类，用于在指定的帧数后触发一个函数。
    """

    func: Callable[..., Any] = field(init=False)  # 触发函数
    args: tuple[Any, ...] = field(init=False)  # 触发函数的位置参数
    kwargs: dict[str, Any] = field(init=False)  # 触发函数的关键字参数

    def bind(self, func: Callable[..., Any], /, *args: Any, **kwargs: Any) -> None:
        """
        绑定触发函数及其参数。

        Args:
            func   (Callable): 触发函数。
            args   (tuple)   : 触发函数的位置参数。
            kwargs (dict)    : 触发函数的关键字参数。
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def call(self) -> bool:
        """
        帧触发器的帧函数调用接口。

        Returns:
            bool: 如果触发器已完成则返回 True，否则返回 False。
        """
        if FramerBase.call(self):
            self.func(*self.args, **self.kwargs)
            return True
        return False


@dataclass(slots=True)
class TimeTrigger(TimerBase):
    """
    时间触发器类，用于在指定的时间后触发一个函数。
    """

    func: Callable[..., Any] = field(init=False)  # 触发函数
    args: tuple[Any, ...] = field(init=False)  # 触发函数的位置参数
    kwargs: dict[str, Any] = field(init=False)  # 触发函数的关键字参数

    def bind(self, func: Callable[..., Any], /, *args: Any, **kwargs: Any) -> None:
        """
        绑定触发函数及其参数。

        Args:
            func   (Callable): 触发函数。
            args   (tuple)   : 触发函数的位置参数。
            kwargs (dict)    : 触发函数的关键字参数。
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def call(self) -> bool:
        """
        时间触发器的帧函数调用接口。

        Returns:
            bool: 如果触发器已完成则返回 True，否则返回 False。
        """
        if TimerBase.call(self):
            self.func(*self.args, **self.kwargs)
            return True
        return False


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
            if CLOCK is not None:
                # 需要把 start_time 往前调整一帧的时间，否则重启后的动画会有一帧的停顿
                fps = CLOCK.get_fps()
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
