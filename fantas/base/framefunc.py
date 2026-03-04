"""
framefunc.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import fantas
from .misc import generate_unique_id

__all__ = (
    "run_framefuncs",
    "FrameFuncBase",
    "FramerBase",
    "TimerBase",
)


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
        default_factory=generate_unique_id, init=False
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
