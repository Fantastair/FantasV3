from __future__ import annotations
from dataclasses import dataclass
from copy import copy

import fantas

__all__ = (
    "TextStyle",
    "LabelStyle",
)


@dataclass(slots=True)
class TextStyle:
    """
    文本样式类。
    Args:
        font        : 字体
        size        : 字体大小
        fgcolor     : 文本颜色
        style_flag  : 文本风格标志
        line_spacing: 行间距
    """

    font: fantas.Font = fantas.DEFAULTFONT
    size: float = 16.0
    fgcolor: fantas.ColorLike = "black"
    style_flag: fantas.TextStyleFlag = fantas.TEXTSTYLEFLAG_DEFAULT
    line_spacing: float = 4.0

    def copy(self) -> TextStyle:
        """创建并返回当前 TextStyle 实例的副本"""
        return copy(self)

    def get_lineheight(self) -> float:
        """获取文本行高（包含行间距）"""
        return self.font.get_sized_height(self.size) + self.line_spacing

    def set_lineheight(self, lineheight: float) -> None:
        """设置文本行高（包含行间距）"""
        self.line_spacing = lineheight - self.font.get_sized_height(self.size)

    line_height = property(get_lineheight, set_lineheight)


fantas.DEFAULTTEXTSTYLE = TextStyle()  # 初始化默认文本样式


@dataclass(slots=True)
class LabelStyle:
    """
    Label 样式类。
    Args:
        bgcolor                   : 背景颜色（填充，None 表示无背景填充）
        fgcolor                   : 前景颜色（边框）
        border_width              : 边框宽度
        border_radius             : 边框圆角半径，0 表示直角
        border_radius_top_left    : 左上角圆角半径，-1 表示使用 border_radius 的值
        border_radius_top_right   : 右上角圆角半径，-1 表示使用 border_radius 的值
        border_radius_bottom_left : 左下角圆角半径，-1 表示使用 border_radius 的值
        border_radius_bottom_right: 右下角圆角半径，-1 表示使用 border_radius 的值
    """

    bgcolor: fantas.ColorLike | None = "white"
    fgcolor: fantas.ColorLike = "black"
    border_width: int | float = 0
    border_radius: int | float = 0
    border_radius_top_left: int | float = -1
    border_radius_top_right: int | float = -1
    border_radius_bottom_left: int | float = -1
    border_radius_bottom_right: int | float = -1

    def copy(self) -> LabelStyle:
        """创建并返回当前 LabelStyle 实例的副本"""
        return copy(self)


fantas.DEFAULTLABELSTYLE = LabelStyle()  # 初始化默认 Label 样式
