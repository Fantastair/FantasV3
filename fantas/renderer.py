"""
fantas.renderer 的 Docstring
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable
from typing import cast
from dataclasses import dataclass, field

import fantas

__all__ = (
    "Renderer",
    "RenderCommand",
    "SurfaceRenderCommand",
    "ColorFillCommand",
    "ColorBackgroundFillCommand",
    "LabelRenderCommand",
    "TextRenderCommand",
    "QuarterCircleRenderCommand",
    "LinearGradientRenderCommand",
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
            command (fantas.RenderCommand): 渲染命令对象，必须实现 render(target_surface) 方法。
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


@dataclass(slots=True)
class SurfaceRenderCommand(RenderCommand):
    """
    Surface 渲染命令类。
    Args:
        surface  : 要渲染的 Surface 对象。
        fill_mode: 填充模式。
        dest_rect: 目标矩形区域。
    """

    surface: fantas.Surface = field(init=False)
    dest_rect: fantas.Rect = field(init=False)
    fill_mode: fantas.FillMode = field(init=False)

    affected_area: fantas.Rect = field(init=False, repr=False)  # 受影响的矩形区域

    def render(self, target_surface: fantas.Surface) -> None:
        """
        执行渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        surface_render_command_render_map[self.fill_mode](self, target_surface)

    def hit_test(self, point: fantas.IntPoint) -> bool:
        """
        命中测试。
        Args:
            point (fantas.IntPoint): 坐标点（x, y）。
        Returns:
            bool: 如果点在区域内则返回 True，否则返回 False。
        """
        return self.affected_area.collidepoint(point)

    def render_ignore(self, target_surface: fantas.Surface) -> None:
        """
        执行 IGNORE 填充模式的渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        self.affected_area = target_surface.blit(self.surface, self.dest_rect)

    def render_scale(self, target_surface: fantas.Surface) -> None:
        """
        执行 SCALE 填充模式的渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        rect = self.affected_area = self.dest_rect
        target_surface.blit(fantas.transform.scale(self.surface, rect.size), rect)

    def render_smoothscale(self, target_surface: fantas.Surface) -> None:
        """
        执行 SMOOTHSCALE 填充模式的渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        rect = self.affected_area = self.dest_rect
        target_surface.blit(fantas.transform.smoothscale(self.surface, rect.size), rect)

    def render_repeat(self, target_surface: fantas.Surface) -> None:
        """
        执行 REPEAT 填充模式的渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        rect = self.affected_area = self.dest_rect
        surface = self.surface
        if isinstance(rect, fantas.FRect):
            rect = fantas.Rect(rect)
        left, top, width, height = rect
        w, h = surface.get_size()
        # 计算重复次数并绘制
        row_count, height_remain = divmod(height, h)
        col_count, width_remain = divmod(width, w)
        for row in range(row_count):
            for col in range(col_count):
                target_surface.blit(surface, (left + col * w, top + row * h))
        top_row = top + row_count * h
        left_col = left + col_count * w
        # 绘制剩余部分
        if height_remain > 0:
            for col in range(left, left_col, w):
                target_surface.blit(surface, (col, top_row), (0, 0, w, height_remain))
        if width_remain > 0:
            for row in range(top, top_row, h):
                target_surface.blit(surface, (left_col, row), (0, 0, width_remain, h))
        if height_remain > 0 and width_remain > 0:
            target_surface.blit(
                surface, (left_col, top_row), (0, 0, width_remain, height_remain)
            )

    def render_fitmin(self, target_surface: fantas.Surface) -> None:
        """
        执行 FITMIN 填充模式的渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        w, h = self.surface.get_size()
        left, top, width, height = self.dest_rect
        scale = min(width / w, height / h)
        # 计算缩放后尺寸并居中绘制
        w = round(w * scale)
        h = round(h * scale)
        self.affected_area = target_surface.blit(
            fantas.transform.smoothscale(self.surface, (w, h)),
            (left + (width - w) // 2, top + (height - h) // 2),
        )

    def render_fitmax(self, target_surface: fantas.Surface) -> None:
        """
        执行 FITMAX 填充模式的渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        w, h = self.surface.get_size()
        left, top, width, height = self.affected_area = self.dest_rect
        scale = max(width / w, height / h)
        # 计算缩放后尺寸并居中绘制
        w = round(w * scale)
        h = round(h * scale)
        scaled_surface = fantas.transform.smoothscale(self.surface, (w, h))
        target_surface.blit(
            scaled_surface,
            (left, top),
            ((w - width) // 2, (h - height) // 2, width, height),
        )


# SurfaceRenderCommand 渲染映射表
surface_render_command_render_map: dict[
    fantas.FillMode, Callable[[SurfaceRenderCommand, fantas.Surface], None]
] = {
    fantas.FillMode.IGNORE: SurfaceRenderCommand.render_ignore,
    fantas.FillMode.SCALE: SurfaceRenderCommand.render_scale,
    fantas.FillMode.SMOOTHSCALE: SurfaceRenderCommand.render_smoothscale,
    fantas.FillMode.REPEAT: SurfaceRenderCommand.render_repeat,
    fantas.FillMode.FITMIN: SurfaceRenderCommand.render_fitmin,
    fantas.FillMode.FITMAX: SurfaceRenderCommand.render_fitmax,
}


@dataclass(slots=True)
class ColorFillCommand(RenderCommand):
    """
    颜色填充命令类。
    Args:
        dest_rect: 目标矩形区域。
        color    : 填充颜色。
    """

    dest_rect: fantas.Rect = field(init=False)
    color: fantas.ColorLike = field(init=False)
    blend_flag: fantas.BlendFlag = field(init=False)

    def render(self, target_surface: fantas.Surface) -> None:
        """
        执行填充操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        target_surface.fill(self.color, self.dest_rect, self.blend_flag)

    def hit_test(self, point: fantas.IntPoint) -> bool:
        """
        命中测试。
        Args:
            point (fantas.IntPoint): 坐标点（x, y）。
        Returns:
            bool: 如果点在区域内则返回 True，否则返回 False。
        """
        return self.dest_rect.collidepoint(point)


@dataclass(slots=True)
class ColorBackgroundFillCommand(RenderCommand):
    """
    颜色背景填充命令类。
    Args:
        color: 填充颜色。
    """

    color: fantas.ColorLike = field(init=False)

    def render(self, target_surface: fantas.Surface) -> None:
        """
        执行填充操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        target_surface.fill(self.color)

    def hit_test(self, point: fantas.IntPoint) -> bool:
        """
        命中测试。
        Args:
            point (fantas.IntPoint): 坐标点（x, y）。
        Returns:
            bool: 如果点在区域内则返回 True，否则返回 False。
        """
        return True


@dataclass(slots=True)
class LabelRenderCommand(RenderCommand):
    """
    矩形标签渲染命令类。
    Args:
        style: 标签样式。
        rect : 渲染区域。
    """

    style: fantas.LabelStyle = field(init=False)
    rect: fantas.Rect = field(init=False)

    def render(self, target_surface: fantas.Surface) -> None:
        """
        执行渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        s = self.style
        rect = self.rect
        bw = s.border_width
        if bw > 0:
            fantas.draw.aarect(
                target_surface,
                s.fgcolor,
                rect,
                bw,
                s.border_radius,
                s.border_radius_top_left,
                s.border_radius_top_right,
                s.border_radius_bottom_left,
                s.border_radius_bottom_right,
            )
            rect = rect.inflate(-2 * bw, -2 * bw)
        if s.bgcolor is not None:
            if (
                s.border_radius_top_left >= 0
                or s.border_radius_top_right >= 0
                or s.border_radius_bottom_left >= 0
                or s.border_radius_bottom_right >= 0
            ):
                fantas.draw.aarect(
                    target_surface,
                    s.bgcolor,
                    rect,
                    0,
                    s.border_radius - bw,
                    max(0, s.border_radius_top_left - bw),
                    max(0, s.border_radius_top_right - bw),
                    max(0, s.border_radius_bottom_left - bw),
                    max(0, s.border_radius_bottom_right - bw),
                )
            else:
                fantas.draw.aarect(
                    target_surface,
                    s.bgcolor,
                    rect,
                    0,
                    s.border_radius - bw,
                    s.border_radius_top_left - bw,
                )

    def hit_test(self, point: fantas.IntPoint) -> bool:
        """
        命中测试。
        Args:
            point (fantas.IntPoint): 坐标点（x, y）。
        Returns:
            bool: 如果点在区域内则返回 True，否则返回 False。
        """
        return self.rect.collidepoint(point)


@dataclass(slots=True)
class TextRenderCommand(RenderCommand):
    """
    文本渲染命令类。
    Args:
        text      : 文本内容。
        align_mode: 对齐模式。
        style     : 文本样式。
        rect      : 渲染区域。
    """

    text: str = field(init=False)
    align_mode: fantas.AlignMode = field(init=False)
    style: fantas.TextStyle = field(init=False)
    rect: fantas.Rect = field(init=False)
    offset: fantas.IntPoint = field(init=False)

    affected_rects: list[fantas.Rect] = field(
        default_factory=list, init=False, repr=False
    )  # 受影响的矩形区域列表

    def render(self, target_surface: fantas.Surface) -> None:
        """
        执行多行文本渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 文本为空则不渲染
        if not self.text:
            return
        # 执行渲染
        text_render_command_render_map[self.align_mode](self, target_surface)

    def hit_test(self, point: fantas.IntPoint) -> bool:
        """
        命中测试。
        Args:
            point (fantas.IntPoint): 坐标点（x, y）。
        Returns:
            bool: 如果点在区域内则返回 True，否则返回 False。
        """
        for rect in self.affected_rects:
            if rect.collidepoint(point):
                return True
        return False

    def render_left(self, target_surface: fantas.Surface) -> None:
        """
        左对齐渲染。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        s = self.style
        size = s.size
        font = s.font
        ar = self.affected_rects
        ar_append = ar.append
        rect = self.rect
        font_ascender = font.get_sized_ascender(size)
        font_descender = font.get_sized_descender(size)
        line_height = font.get_sized_height(size) + s.line_spacing
        # 清空受影响矩形列表
        ar.clear()
        # 计算换行结果
        wraps = s.font.auto_wrap(s.style_flag, s.size, self.text, self.rect.width)
        # 计算渲染原点及范围
        origin_x = rect.left + self.offset[0]
        origin_y = (
            rect.centery
            - (len(wraps) * line_height - s.line_spacing) // 2
            + font_ascender
            + self.offset[1]
        )
        full_min_y = rect.top + font_ascender  # 全部可见时的最小 y 坐标
        full_max_y = rect.bottom + font_descender  # 全部可见时的最大 y 坐标
        part_min_y = full_min_y - line_height  # 部分可见时的最小 y 坐标
        part_max_y = full_max_y + line_height  # 部分可见时的最大 y 坐标
        # 执行渲染
        for text, _ in wraps:
            if full_min_y <= origin_y <= full_max_y:  # 完全可见，正常渲染
                ar_append(
                    font.render_to(
                        target_surface,
                        (origin_x, origin_y),
                        text,
                        s.fgcolor,
                        style=s.style_flag,
                        size=size,
                    )
                )
            elif part_min_y < origin_y < part_max_y:  # 部分可见，裁剪渲染
                sf, rt = font.render(text, s.fgcolor, style=s.style_flag, size=size)
                rt.topleft = (origin_x - rt.left, origin_y - rt.top)
                r = rt.clip(rect)
                ar_append(
                    target_surface.blit(
                        sf, r.topleft, (0, r.top - rt.top, r.width, r.height)
                    )
                )
            origin_y += line_height

    def render_center(self, target_surface: fantas.Surface) -> None:
        """
        居中对齐渲染。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        s = self.style
        size = s.size
        font = s.font
        ar = self.affected_rects
        ar_append = ar.append
        rect = self.rect
        font_ascender = font.get_sized_ascender(size)
        font_descender = font.get_sized_descender(size)
        line_height = font.get_sized_height(size) + s.line_spacing
        # 清空受影响矩形列表
        ar.clear()
        # 计算换行结果
        wraps = s.font.auto_wrap(s.style_flag, s.size, self.text, self.rect.width)
        # 计算渲染原点及范围
        origin_x = rect.left + self.offset[0]
        origin_y = (
            rect.centery
            - (len(wraps) * line_height - s.line_spacing) // 2
            + font_ascender
            + self.offset[1]
        )
        full_min_y = rect.top + font_ascender  # 全部可见时的最小 y 坐标
        full_max_y = rect.bottom + font_descender  # 全部可见时的最大 y 坐标
        part_min_y = full_min_y - line_height  # 部分可见时的最小 y 坐标
        part_max_y = full_max_y + line_height  # 部分可见时的最大 y 坐标
        # 执行渲染
        for text, width in wraps:
            if full_min_y <= origin_y <= full_max_y:  # 完全可见，正常渲染
                ar_append(
                    font.render_to(
                        target_surface,
                        (origin_x + (rect.width - width) // 2, origin_y),
                        text,
                        s.fgcolor,
                        style=s.style_flag,
                        size=size,
                    )
                )
            elif part_min_y < origin_y < part_max_y:  # 部分可见，裁剪渲染
                sf, rt = font.render(text, s.fgcolor, style=s.style_flag, size=size)
                rt.topleft = (
                    origin_x + (rect.width - width) // 2 - rt.left,
                    origin_y - rt.top,
                )
                r = rt.clip(rect)
                ar_append(
                    target_surface.blit(
                        sf, r.topleft, (0, r.top - rt.top, r.width, r.height)
                    )
                )
            origin_y += line_height

    def render_right(self, target_surface: fantas.Surface) -> None:
        """
        右对齐渲染。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        s = self.style
        size = s.size
        font = s.font
        ar = self.affected_rects
        ar_append = ar.append
        rect = self.rect
        font_ascender = font.get_sized_ascender(size)
        font_descender = font.get_sized_descender(size)
        line_height = font.get_sized_height(size) + s.line_spacing
        # 清空受影响矩形列表
        ar.clear()
        # 计算换行结果
        wraps = s.font.auto_wrap(s.style_flag, s.size, self.text, self.rect.width)
        # 计算渲染原点及范围
        origin_x = rect.left + self.offset[0]
        origin_y = (
            rect.centery
            - (len(wraps) * line_height - s.line_spacing) // 2
            + font_ascender
            + self.offset[1]
        )
        full_min_y = rect.top + font_ascender  # 全部可见时的最小 y 坐标
        full_max_y = rect.bottom + font_descender  # 全部可见时的最大 y 坐标
        part_min_y = full_min_y - line_height  # 部分可见时的最小 y 坐标
        part_max_y = full_max_y + line_height  # 部分可见时的最大 y 坐标
        # 执行渲染
        for text, width in wraps:
            if full_min_y <= origin_y <= full_max_y:  # 完全可见，正常渲染
                ar_append(
                    font.render_to(
                        target_surface,
                        (origin_x + rect.width - width, origin_y),
                        text,
                        s.fgcolor,
                        style=s.style_flag,
                        size=size,
                    )
                )
            elif part_min_y < origin_y < part_max_y:  # 部分可见，裁剪渲染
                sf, rt = font.render(text, s.fgcolor, style=s.style_flag, size=size)
                rt.topleft = (
                    origin_x + rect.width - width - rt.left,
                    origin_y - rt.top,
                )
                r = rt.clip(rect)
                ar_append(
                    target_surface.blit(
                        sf, r.topleft, (0, r.top - rt.top, r.width, r.height)
                    )
                )
            origin_y += line_height

    def render_top(self, target_surface: fantas.Surface) -> None:
        """
        顶部对齐渲染。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        s = self.style
        size = s.size
        font = s.font
        ar = self.affected_rects
        ar_append = ar.append
        rect = self.rect
        font_ascender = font.get_sized_ascender(size)
        font_descender = font.get_sized_descender(size)
        line_height = font.get_sized_height(size) + s.line_spacing
        # 清空受影响矩形列表
        ar.clear()
        # 计算换行结果
        wraps = s.font.auto_wrap(s.style_flag, s.size, self.text, self.rect.width)
        # 计算渲染原点及范围
        origin_x = rect.left + self.offset[0]
        origin_y = rect.top + font_ascender + self.offset[1]
        full_min_y = rect.top + font_ascender  # 全部可见时的最小 y 坐标
        full_max_y = rect.bottom + font_descender  # 全部可见时的最大 y 坐标
        part_min_y = full_min_y - line_height  # 部分可见时的最小 y 坐标
        part_max_y = full_max_y + line_height  # 部分可见时的最大 y 坐标
        # 执行渲染
        for text, width in wraps:
            if full_min_y <= origin_y <= full_max_y:  # 完全可见，正常渲染
                ar_append(
                    font.render_to(
                        target_surface,
                        (origin_x + (rect.width - width) // 2, origin_y),
                        text,
                        s.fgcolor,
                        style=s.style_flag,
                        size=size,
                    )
                )
            elif part_min_y < origin_y < part_max_y:  # 部分可见，裁剪渲染
                sf, rt = font.render(text, s.fgcolor, style=s.style_flag, size=size)
                rt.topleft = (
                    origin_x + (rect.width - width) // 2 - rt.left,
                    origin_y - rt.top,
                )
                r = rt.clip(rect)
                ar_append(
                    target_surface.blit(
                        sf, r.topleft, (0, r.top - rt.top, r.width, r.height)
                    )
                )
            origin_y += line_height

    def render_bottom(self, target_surface: fantas.Surface) -> None:
        """
        底部对齐渲染。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        s = self.style
        size = s.size
        font = s.font
        ar = self.affected_rects
        ar_append = ar.append
        rect = self.rect
        font_ascender = font.get_sized_ascender(size)
        font_descender = font.get_sized_descender(size)
        line_height = font.get_sized_height(size) + s.line_spacing
        # 清空受影响矩形列表
        ar.clear()
        # 计算换行结果
        wraps = s.font.auto_wrap(s.style_flag, s.size, self.text, self.rect.width)
        # 计算渲染原点及范围
        origin_x = rect.left + self.offset[0]
        origin_y = (
            rect.bottom
            - len(wraps) * line_height
            + s.line_spacing
            + font_ascender
            + self.offset[1]
        )
        full_min_y = rect.top + font_ascender  # 全部可见时的最小 y 坐标
        full_max_y = rect.bottom + font_descender  # 全部可见时的最大 y 坐标
        part_min_y = full_min_y - line_height  # 部分可见时的最小 y 坐标
        part_max_y = full_max_y + line_height  # 部分可见时的最大 y 坐标
        # 执行渲染
        for text, width in wraps:
            if full_min_y <= origin_y <= full_max_y:  # 完全可见，正常渲染
                ar_append(
                    font.render_to(
                        target_surface,
                        (origin_x + (rect.width - width) // 2, origin_y),
                        text,
                        s.fgcolor,
                        style=s.style_flag,
                        size=size,
                    )
                )
            elif part_min_y < origin_y < part_max_y:  # 部分可见，裁剪渲染
                sf, rt = font.render(text, s.fgcolor, style=s.style_flag, size=size)
                rt.topleft = (
                    origin_x + (rect.width - width) // 2 - rt.left,
                    origin_y - rt.top,
                )
                r = rt.clip(rect)
                ar_append(
                    target_surface.blit(
                        sf, r.topleft, (0, r.top - rt.top, r.width, r.height)
                    )
                )
            origin_y += line_height

    def render_topleft(self, target_surface: fantas.Surface) -> None:
        """
        左上对齐渲染。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        s = self.style
        size = s.size
        font = s.font
        ar = self.affected_rects
        ar_append = ar.append
        rect = self.rect
        font_ascender = font.get_sized_ascender(size)
        font_descender = font.get_sized_descender(size)
        line_height = font.get_sized_height(size) + s.line_spacing
        # 清空受影响矩形列表
        ar.clear()
        # 计算换行结果
        wraps = s.font.auto_wrap(s.style_flag, s.size, self.text, self.rect.width)
        # 计算渲染原点及范围
        origin_x = rect.left + self.offset[0]
        origin_y = rect.top + font_ascender + self.offset[1]
        full_min_y = rect.top + font_ascender  # 全部可见时的最小 y 坐标
        full_max_y = rect.bottom + font_descender  # 全部可见时的最大 y 坐标
        part_min_y = full_min_y - line_height  # 部分可见时的最小 y 坐标
        part_max_y = full_max_y + line_height  # 部分可见时的最大 y 坐标
        # 执行渲染
        for text, _ in wraps:
            if full_min_y <= origin_y <= full_max_y:  # 完全可见，正常渲染
                ar_append(
                    font.render_to(
                        target_surface,
                        (origin_x, origin_y),
                        text,
                        s.fgcolor,
                        style=s.style_flag,
                        size=size,
                    )
                )
            elif part_min_y < origin_y < part_max_y:  # 部分可见，裁剪渲染
                sf, rt = font.render(text, s.fgcolor, style=s.style_flag, size=size)
                rt.topleft = (origin_x - rt.left, origin_y - rt.top)
                r = rt.clip(rect)
                ar_append(
                    target_surface.blit(
                        sf, r.topleft, (0, r.top - rt.top, r.width, r.height)
                    )
                )
            origin_y += line_height

    def render_topright(self, target_surface: fantas.Surface) -> None:
        """
        右上对齐渲染。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        # 简化引用
        s = self.style
        size = s.size
        font = s.font
        ar = self.affected_rects
        ar_append = ar.append
        rect = self.rect
        font_ascender = font.get_sized_ascender(size)
        font_descender = font.get_sized_descender(size)
        line_height = font.get_sized_height(size) + s.line_spacing
        # 清空受影响矩形列表
        ar.clear()
        # 计算换行结果
        wraps = s.font.auto_wrap(s.style_flag, s.size, self.text, self.rect.width)
        # 计算渲染原点及范围
        origin_x = rect.left + self.offset[0]
        origin_y = rect.top + font_ascender + self.offset[1]
        full_min_y = rect.top + font_ascender  # 全部可见时的最小 y 坐标
        full_max_y = rect.bottom + font_descender  # 全部可见时的最大 y 坐标
        part_min_y = full_min_y - line_height  # 部分可见时的最小 y 坐标
        part_max_y = full_max_y + line_height  # 部分可见时的最大 y 坐标
        # 执行渲染
        for text, width in wraps:
            if full_min_y <= origin_y <= full_max_y:  # 完全可见，正常渲染
                ar_append(
                    font.render_to(
                        target_surface,
                        (origin_x + rect.width - width, origin_y),
                        text,
                        s.fgcolor,
                        style=s.style_flag,
                        size=size,
                    )
                )
            elif part_min_y < origin_y < part_max_y:  # 部分可见，裁剪渲染
                sf, rt = font.render(text, s.fgcolor, style=s.style_flag, size=size)
                rt.topleft = (
                    origin_x + rect.width - width - rt.left,
                    origin_y - rt.top,
                )
                r = rt.clip(rect)
                ar_append(
                    target_surface.blit(
                        sf, r.topleft, (0, r.top - rt.top, r.width, r.height)
                    )
                )
            origin_y += line_height

    def render_bottomleft(self, target_surface: fantas.Surface) -> None:
        """
        左下对齐渲染。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        s = self.style
        size = s.size
        font = s.font
        ar = self.affected_rects
        ar_append = ar.append
        rect = self.rect
        font_ascender = font.get_sized_ascender(size)
        font_descender = font.get_sized_descender(size)
        line_height = font.get_sized_height(size) + s.line_spacing
        # 清空受影响矩形列表
        ar.clear()
        # 计算换行结果
        wraps = s.font.auto_wrap(s.style_flag, s.size, self.text, self.rect.width)
        # 计算渲染原点及范围
        origin_x = rect.left + self.offset[0]
        origin_y = (
            rect.bottom
            - len(wraps) * line_height
            + s.line_spacing
            + font_ascender
            + self.offset[1]
        )
        full_min_y = rect.top + font_ascender  # 全部可见时的最小 y 坐标
        full_max_y = rect.bottom + font_descender  # 全部可见时的最大 y 坐标
        part_min_y = full_min_y - line_height  # 部分可见时的最小 y 坐标
        part_max_y = full_max_y + line_height  # 部分可见时的最大 y 坐标
        # 执行渲染
        for text, _ in wraps:
            if full_min_y <= origin_y <= full_max_y:  # 完全可见，正常渲染
                ar_append(
                    font.render_to(
                        target_surface,
                        (origin_x, origin_y),
                        text,
                        s.fgcolor,
                        style=s.style_flag,
                        size=size,
                    )
                )
            elif part_min_y < origin_y < part_max_y:  # 部分可见，裁剪渲染
                sf, rt = font.render(text, s.fgcolor, style=s.style_flag, size=size)
                rt.topleft = (origin_x - rt.left, origin_y - rt.top)
                r = rt.clip(rect)
                ar_append(
                    target_surface.blit(
                        sf, r.topleft, (0, r.top - rt.top, r.width, r.height)
                    )
                )
            origin_y += line_height

    def render_bottomright(self, target_surface: fantas.Surface) -> None:
        """
        右下对齐渲染。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        # 简化引用
        s = self.style
        size = s.size
        font = s.font
        ar = self.affected_rects
        ar_append = ar.append
        rect = self.rect
        font_ascender = font.get_sized_ascender(size)
        font_descender = font.get_sized_descender(size)
        line_height = font.get_sized_height(size) + s.line_spacing
        # 清空受影响矩形列表
        ar.clear()
        # 计算换行结果
        wraps = s.font.auto_wrap(s.style_flag, s.size, self.text, self.rect.width)
        # 计算渲染原点及范围
        origin_x = rect.left + self.offset[0]
        origin_y = (
            rect.bottom
            - len(wraps) * line_height
            + s.line_spacing
            + font_ascender
            + self.offset[1]
        )
        full_min_y = rect.top + font_ascender  # 全部可见时的最小 y 坐标
        full_max_y = rect.bottom + font_descender  # 全部可见时的最大 y 坐标
        part_min_y = full_min_y - line_height  # 部分可见时的最小 y 坐标
        part_max_y = full_max_y + line_height  # 部分可见时的最大 y 坐标
        # 执行渲染
        for text, width in wraps:
            if full_min_y <= origin_y <= full_max_y:  # 完全可见，正常渲染
                ar_append(
                    font.render_to(
                        target_surface,
                        (origin_x + rect.width - width, origin_y),
                        text,
                        s.fgcolor,
                        style=s.style_flag,
                        size=size,
                    )
                )
            elif part_min_y < origin_y < part_max_y:  # 部分可见，裁剪渲染
                sf, rt = font.render(text, s.fgcolor, style=s.style_flag, size=size)
                rt.topleft = (
                    origin_x + rect.width - width - rt.left,
                    origin_y - rt.top,
                )
                r = rt.clip(rect)
                ar_append(
                    target_surface.blit(
                        sf, r.topleft, (0, r.top - rt.top, r.width, r.height)
                    )
                )
            origin_y += line_height


# TextRenderCommand 渲染映射表
text_render_command_render_map: dict[
    fantas.AlignMode, Callable[[TextRenderCommand, fantas.Surface], None]
] = {
    fantas.AlignMode.TOP: TextRenderCommand.render_top,
    fantas.AlignMode.LEFT: TextRenderCommand.render_left,
    fantas.AlignMode.RIGHT: TextRenderCommand.render_right,
    fantas.AlignMode.BOTTOM: TextRenderCommand.render_bottom,
    fantas.AlignMode.CENTER: TextRenderCommand.render_center,
    fantas.AlignMode.TOPLEFT: TextRenderCommand.render_topleft,
    fantas.AlignMode.TOPRIGHT: TextRenderCommand.render_topright,
    fantas.AlignMode.BOTTOMLEFT: TextRenderCommand.render_bottomleft,
    fantas.AlignMode.BOTTOMRIGHT: TextRenderCommand.render_bottomright,
}

# 象限映射表
quadrant_map: dict[fantas.Quadrant, dict[str, bool]] = {
    fantas.Quadrant.TOPRIGHT: {"draw_top_right": True},
    fantas.Quadrant.TOPLEFT: {"draw_top_left": True},
    fantas.Quadrant.BOTTOMLEFT: {"draw_bottom_left": True},
    fantas.Quadrant.BOTTOMRIGHT: {"draw_bottom_right": True},
}


@dataclass(slots=True)
class QuarterCircleRenderCommand(RenderCommand):
    """
    四分之一圆渲染命令类。
    Args:
        color    : 圆的颜色。
        center   : 圆心位置。
        radius   : 圆的半径，≥ 1。
        width    : 圆边框宽度，≥ 0，0 表示填充。
        quadrant : 象限。
    """

    color: fantas.ColorLike = "black"
    center: fantas.Point = (0, 0)
    radius: int | float = 8
    width: int = 0
    quadrant: fantas.Quadrant = fantas.Quadrant.TOPRIGHT

    def render(self, target_surface: fantas.Surface) -> None:
        """
        执行四分之一圆渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        fantas.draw.aacircle(
            target_surface,
            self.color,
            self.center,
            self.radius,
            width=self.width,
            **quadrant_map[self.quadrant],
        )

    def hit_test(self, point: fantas.Point) -> bool:
        """
        命中测试。
        Args:
            point (fantas.Point): 坐标点（x, y）。
        Returns:
            bool: 如果点在区域内则返回 True，否则返回 False。
        """
        # 计算相对坐标
        dx = point[0] - self.center[0]
        dy = point[1] - self.center[1]
        # 符号测试
        if not fantas.Quadrant.has_point(self.quadrant, (dx, dy)):
            return False
        # 距离测试
        return self.radius * self.radius >= dx * dx + dy * dy >= self.width * self.width


@dataclass(slots=True)
class LinearGradientRenderCommand(RenderCommand):
    """
    线性渐变渲染命令类。
    Args:
        rect       : 渲染区域。
        start_color: 起始颜色。
        end_color  : 结束颜色。
        start_pos  : 起始位置。
        end_pos    : 结束位置。
    """

    rect: fantas.Rect = field(init=False)
    start_color: fantas.ColorLike = field(init=False)
    end_color: fantas.ColorLike = field(init=False)
    start_pos: fantas.Vector2 = field(init=False)
    end_pos: fantas.Vector2 = field(init=False)

    cache_dirty: bool = field(default=True, init=False, repr=False)  # 缓存是否脏标志
    surface_cache: fantas.Surface = field(
        default=None, init=False, repr=False
    )  # type: ignore[assignment]  # 表面缓存
    last_pix: int = field(default=0, init=False, repr=False)  # 上次渲染的坐标

    def render(self, target_surface: fantas.Surface) -> None:
        """
        执行线性渐变渲染操作。
        Args:
            target_surface (fantas.Surface): 目标 Surface 对象。
        """
        start_color = cast(fantas.Color, self.start_color)
        end_color = cast(fantas.Color, self.end_color)
        # 检查缓存是否脏
        if self.cache_dirty:
            # 重新生成缓存
            self.cache_dirty = False
            if (
                self.surface_cache is None
                or self.surface_cache.get_size() != self.rect.size
            ):
                if start_color.a == 255 and end_color.a == 255:
                    self.surface_cache = fantas.Surface(self.rect.size)
                else:
                    self.surface_cache = fantas.Surface(
                        self.rect.size, flags=fantas.SRCALPHA
                    )
            if not isinstance(self.start_pos, fantas.Vector2):
                self.start_pos = fantas.Vector2(self.start_pos)
            if not isinstance(self.end_pos, fantas.Vector2):
                self.end_pos = fantas.Vector2(self.end_pos)
            # 选择渲染方法
            linear_gradient_render_command_render_map[
                ((self.start_pos.y == self.end_pos.y) << 1)
                | (self.start_pos.x == self.end_pos.x)
            ](self)
        # 绘制缓存到目标表面
        target_surface.blit(self.surface_cache, self.rect)

    def hit_test(self, point: fantas.IntPoint) -> bool:
        """
        命中测试。
        Args:
            point (fantas.IntPoint): 坐标点（x, y）。
        Returns:
            bool: 如果点在区域内则返回 True，否则返回 False。
        """
        return self.rect.collidepoint(point)

    def render_horizontal(self) -> None:
        """
        执行水平线性渐变渲染操作。
        """
        start_color = cast(fantas.Color, self.start_color)
        end_color = cast(fantas.Color, self.end_color)
        left_x = self.rect.left - self.start_pos.x
        x2_x1 = self.end_pos.x - self.start_pos.x
        with fantas.PixelArray(self.surface_cache) as pix:
            for x in range(self.rect.width):
                col = start_color.lerp(
                    end_color, fantas.math.clamp((x + left_x) / x2_x1, 0, 1)
                )
                pix[x, :] = col  # type: ignore[index]

    def render_vertical(self) -> None:
        """
        执行垂直线性渐变渲染操作。
        """
        start_color = cast(fantas.Color, self.start_color)
        end_color = cast(fantas.Color, self.end_color)
        top_y = self.rect.top - self.start_pos.y
        y2_y1 = self.end_pos.y - self.start_pos.y
        with fantas.PixelArray(self.surface_cache) as pix:
            for y in range(self.rect.height):
                col = start_color.lerp(
                    end_color, fantas.math.clamp((y + top_y) / y2_y1, 0, 1)
                )
                pix[:, y] = col  # type: ignore[index]

    def render_any_angle(self) -> None:
        """
        执行任意角度线性渐变渲染操作。
        """
        start_color = cast(fantas.Color, self.start_color)
        end_color = cast(fantas.Color, self.end_color)
        # 分步绘制时间点
        t = fantas.get_time_ns()
        # 计算xy方向的步长
        v: fantas.Vector2 = self.end_pos - self.start_pos
        v_length = v.length()
        x_step = fantas.Vector2(1, 0).dot(v) / v_length
        y_step = fantas.Vector2(0, 1).dot(v) / v_length
        # 执行渲染
        with fantas.PixelArray(self.surface_cache) as pix:
            for x in range(self.last_pix, self.rect.width):
                for y in range(self.rect.height):
                    pix[x, y] = start_color.lerp(  # type: ignore[index]
                        end_color,
                        fantas.math.clamp(
                            (
                                (x + self.rect.left - self.start_pos.x) * x_step
                                + (y + self.rect.top - self.start_pos.y) * y_step
                            )
                            / v_length,
                            0,
                            1,
                        ),
                    )
                    # 单次绘制时间超过 10 毫秒，则标记缓存为脏并记录当前位置，退出绘制
                    if fantas.get_time_ns() - t > 10_000_000:
                        self.cache_dirty = True
                        self.last_pix = x
                        return
        self.last_pix = 0

    def render_coinside(self) -> None:
        """
        执行起点和终点重合的线性渐变渲染操作。
        """
        start_color = cast(fantas.Color, self.start_color)
        end_color = cast(fantas.Color, self.end_color)
        self.surface_cache.fill(start_color.lerp(end_color, 0.5), self.rect)


linear_gradient_render_command_render_map: dict[
    int, Callable[[LinearGradientRenderCommand], None]
] = {
    0b00: LinearGradientRenderCommand.render_any_angle,
    0b01: LinearGradientRenderCommand.render_vertical,
    0b10: LinearGradientRenderCommand.render_horizontal,
    0b11: LinearGradientRenderCommand.render_coinside,
}
