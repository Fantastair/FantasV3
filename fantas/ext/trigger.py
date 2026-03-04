"""
提供触发器，用于定时或定帧触发一个函数。
"""

from typing import Any, Callable
from dataclasses import dataclass, field

from fantas import FramerBase, TimerBase

__all__ = (
    "FrameTrigger",
    "TimeTrigger",
)


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
