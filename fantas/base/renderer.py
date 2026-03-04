"""
fantas.renderer 的 Docstring
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field

import fantas

__all__ = (
    "Renderer",
    "RenderCommand",
)


@dataclass(slots=True)
class Renderer:
    """
    渲染器类，管理渲染命令队列并执行渲染操作。
    Args:
        window: 关联的窗口对象。
    """

    window: fantas.Window  # 关联的窗口对象

    queue: deque[fantas.RenderCommand] = field(
        default_factory=deque, init=False, repr=False
    )  # 渲染命令队列，左端入右端出

    def pre_render(self, root_ui: fantas.UI) -> None:
        """
        预处理渲染命令，即更新渲染命令队列。
        Args:
            root_ui (fantas.UI): 根 UI 元素。
        """
        self.queue.clear()
        for command in root_ui.create_render_commands():
            self.queue.append(command)

    def render(self, target_surface: fantas.Surface) -> None:
        """
        执行渲染队列中的所有渲染命令。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        for command in self.queue:
            command.render(target_surface)

    def add_command(self, command: fantas.RenderCommand) -> None:
        """
        向渲染队列中添加一个渲染命令。
        Args:
            command (fantas.RenderCommand): 渲染命令对象。
        """
        self.queue.appendleft(command)

    def coordinate_hit_test(self, point: fantas.IntPoint) -> fantas.UI:
        """
        根据给定的坐标点进行命中测试，返回位于该点的最上层 UI 元素。
        Args:
            point (fantas.IntPoint): 坐标点（x, y）。
        Returns:
            fantas.UI: 位于该点的最上层 UI 元素，如果没有命中任何元素则返回根 UI 元素。
        """
        for rc in reversed(self.queue):
            if rc.hit_test(point):
                return rc.creator
        return self.window.root_ui


@dataclass(slots=True)
class RenderCommand(ABC):
    """
    渲染命令基类。
    Args:
        creator: 创建此渲染命令的 UI 元素。
    """

    creator: fantas.UI

    @abstractmethod
    def render(self, target_surface: fantas.Surface) -> None:
        """
        执行渲染操作，将渲染结果绘制到目标 Surface 上。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """

    @abstractmethod
    def hit_test(self, point: fantas.IntPoint) -> bool:
        """
        命中测试，判断给定的坐标点是否在此渲染命令的区域内。
        Args:
            point (fantas.IntPoint): 坐标点（x, y）。
        Returns:
            bool: 如果点在区域内则返回 True，否则返回 False。
        """
