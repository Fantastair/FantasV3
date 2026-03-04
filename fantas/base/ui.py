"""
fantas.ui 的 Docstring
"""

from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Iterator

import fantas
from .nodebase import NodeBase
from .misc import generate_unique_id

__all__ = (
    "UI",
    "BlankUI",
    "WindowRoot",
)


@dataclass(slots=True)
class UI(NodeBase["UI"]):
    """显示元素基类。"""

    ui_id: fantas.UIid = field(
        default_factory=generate_unique_id, init=False
    )  # 唯一标识 ID

    def create_render_commands(
        self, offset: fantas.Point = (0, 0)
    ) -> Iterator[fantas.RenderCommand]:
        """
        创建渲染命令列表，由子类实现，本方法会遍历子节点并生成渲染命令。
        Args:
            offset (fantas.Point): 当前元素的偏移位置，用于计算子元素的绝对位置。
        Yields:
            RenderCommand: 渲染命令对象。
        """
        for child in self.children:
            yield from child.create_render_commands(offset)


@dataclass(slots=True)
class BlankUI(UI):
    """空显示元素类。"""

    rect: fantas.Rect | fantas.FRect

    def create_render_commands(
        self, offset: fantas.Point = (0, 0)
    ) -> Iterator[fantas.RenderCommand]:
        """
        创建渲染命令列表，由子类实现，本方法会遍历子节点并生成渲染命令。
        Args:
            offset (fantas.Point): 当前元素的偏移位置，用于计算子元素的绝对位置。
        Yields:
            RenderCommand: 渲染命令对象。
        """
        yield from UI.create_render_commands(self, self.rect.move(offset).topleft)


@dataclass(slots=True)
class WindowRoot(UI):
    """
    窗口根元素类。
    Args:
        window: 指向所属窗口。
    """

    window: fantas.Window
    rect: fantas.Rect = field(init=False)  # 窗口矩形区域

    def __post_init__(self) -> None:
        self.rect = fantas.Rect((0, 0), self.window.size)

    def update_rect(self) -> None:
        """更新窗口矩形区域。"""
        self.rect.size = self.window.size
