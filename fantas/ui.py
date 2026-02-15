from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Iterator
from typing import cast

import fantas

__all__ = (
    "UI",
    "BlankUI",
    "WindowRoot",
    "ColorBackground",
    "Label",
    "Image",
    "Text",
    "TextLabel",
    "LinearGradientLabel",
    "Animation",
)


@dataclass(slots=True)
class UI(fantas.NodeBase["UI"]):
    """显示元素基类。"""

    ui_id: fantas.UIID = field(
        default_factory=fantas.generate_unique_id, init=False
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

    rect: fantas.Rect | fantas.IntRect

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
    rect: fantas.IntRect = field(init=False)  # 窗口矩形区域

    def __post_init__(self) -> None:
        self.rect = fantas.IntRect((0, 0), self.window.size)

    def update_rect(self) -> None:
        """更新窗口矩形区域。"""
        self.rect.size = self.window.size


@dataclass(slots=True)
class ColorBackground(UI):
    """
    纯色背景类。
    Args:
        bgcolor: 背景颜色。
    """

    bgcolor: fantas.ColorLike = "black"

    command: fantas.ColorBackgroundFillCommand = field(
        init=False, repr=False
    )  # 颜色填充命令

    def __post_init__(self) -> None:
        """初始化 ColorBackground 实例"""
        self.command = fantas.ColorBackgroundFillCommand(creator=self)

    def create_render_commands(
        self, offset: fantas.Point = (0, 0)
    ) -> Iterator[fantas.RenderCommand]:
        """
        创建渲染命令列表
        Args:
            offset (fantas.Point): 当前元素的偏移位置，用于计算子元素的绝对位置。
        Yields:
            RenderCommand: 渲染命令对象。
        """
        # 设置背景颜色
        self.command.color = self.bgcolor
        # 生成自己的渲染命令
        yield self.command
        # 生成子元素的渲染命令
        yield from UI.create_render_commands(self)


@dataclass(slots=True)
class Label(UI):
    """
    纯色矩形标签类。
    Args:
        rect       : 矩形区域。
        label_style: 标签样式。
        box_mode   : 盒子模式。
    """

    rect: fantas.Rect | fantas.IntRect
    label_style: fantas.LabelStyle = field(
        default_factory=fantas.DEFAULTLABELSTYLE.copy
    )
    box_mode: fantas.BoxMode = fantas.BoxMode.INSIDE

    command: fantas.LabelRenderCommand = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """初始化 Label 实例"""
        self.command = fantas.LabelRenderCommand(creator=self)

    def create_render_commands(
        self, offset: fantas.Point = (0, 0)
    ) -> Iterator[fantas.RenderCommand]:
        """
        创建渲染命令列表
        Args:
            offset (fantas.Point): 当前元素的偏移位置，用于计算子元素的绝对位置。
        Yields:
            RenderCommand: 渲染命令对象。
        """
        # 简化引用
        bw = self.label_style.border_width
        # 计算渲染命令矩形和偏移位置
        if isinstance(self.rect, fantas.Rect):
            rect = fantas.IntRect(self.rect).move(offset)
        else:
            rect = self.rect.move(offset)
        if bw > 0:
            if self.box_mode is fantas.BoxMode.OUTSIDE:
                rect.inflate_ip(2 * bw, 2 * bw)
            elif self.box_mode is fantas.BoxMode.INOUTSIDE:
                rect.inflate_ip(bw, bw)
        self.command.rect = rect
        # 设置渲染命令样式
        self.command.style = self.label_style
        # 生成渲染命令
        yield self.command
        # 生成子元素的渲染命令
        yield from UI.create_render_commands(self, rect.topleft)


@dataclass(slots=True)
class Image(UI):
    """
    图像显示类。
    Args:
        surface  : 显示的 Surface 对象。
        rect     : 矩形区域。
        fill_mode: 填充模式。
    """

    surface: fantas.Surface
    rect: fantas.Rect | fantas.IntRect = None  # type: ignore[assignment]
    fill_mode: fantas.FillMode = fantas.FillMode.IGNORE

    command: fantas.SurfaceRenderCommand = field(init=False, repr=False)  # 渲染命令对象

    def __post_init__(self) -> None:
        """初始化 Image 实例"""
        self.command = fantas.SurfaceRenderCommand(creator=self)
        if self.rect is None:
            self.rect = fantas.Rect((0, 0), self.surface.get_size())

    def create_render_commands(
        self, offset: fantas.Point = (0, 0)
    ) -> Iterator[fantas.RenderCommand]:
        """
        创建渲染命令列表
        Args:
            offset (fantas.Point): 当前元素的偏移位置，用于计算子元素的绝对位置。
        Yields:
            RenderCommand: 渲染命令对象。
        """
        # 生成 Surface 渲染命令
        c = self.command
        c.surface = self.surface
        c.fill_mode = self.fill_mode
        # 调整矩形区域
        if isinstance(self.rect, fantas.Rect):
            c.dest_rect = fantas.IntRect(self.rect).move(offset)
        else:
            c.dest_rect = self.rect.move(offset)
        yield c
        # 生成子元素的渲染命令
        yield from UI.create_render_commands(self, c.dest_rect.topleft)


@dataclass(slots=True)
class Text(UI):
    """
    文本显示类。
    Args:
        text      : 显示的文本内容。
        text_style: 文本样式。
        rect      : 文本显示区域。
        align_mode: 对齐模式。
        offset    : 文本偏移位置。
    """

    children: None = field(
        default=None, init=False, repr=False
    )  # type: ignore[assignment]  # 纯色文本不包含子元素

    rect: fantas.Rect
    text: str = "text"
    text_style: fantas.TextStyle = field(default_factory=fantas.DEFAULTTEXTSTYLE.copy)
    align_mode: fantas.AlignMode = fantas.AlignMode.LEFT
    offset: fantas.IntPoint = field(default_factory=lambda: [0, 0])

    command: fantas.TextRenderCommand = field(init=False, repr=False)  # 渲染命令

    def __post_init__(self) -> None:
        """初始化 ColorText 实例"""
        self.command = fantas.TextRenderCommand(creator=self)

    def create_render_commands(
        self, offset: fantas.Point = (0, 0)
    ) -> Iterator[fantas.RenderCommand]:
        """
        创建渲染命令列表。
        Args:
            offset (fantas.Point): 当前元素的偏移位置，用于计算子元素的绝对位置。
        Yields:
            RenderCommand: 渲染命令对象.
        """
        # 仅当文本非空时才生成渲染命令
        if not self.text:
            return
        # 简化引用
        rc = self.command
        # 设置文本显示区域
        if isinstance(self.rect, fantas.Rect):
            rc.rect = fantas.IntRect(self.rect).move(offset)
        else:
            rc.rect = self.rect.move(offset)
        # 设置文本内容
        rc.text = self.text
        # 设置文本样式
        rc.style = self.text_style
        # 设置对齐模式
        rc.align_mode = self.align_mode
        # 设置偏移位置
        rc.offset = self.offset
        # 生成渲染命令
        yield rc

    def _get_lineheight(self) -> int:
        """获取文本行高（包含行间距）"""
        return (
            self.text_style.font.get_sized_height(self.text_style.size)
            + self.text_style.line_spacing
        )

    def _set_lineheight(self, lineheight: int) -> None:
        """设置文本行高（包含行间距）"""
        self.text_style.line_spacing = (
            lineheight - self.text_style.font.get_sized_height(self.text_style.size)
        )

    line_height = property(_get_lineheight, _set_lineheight)


@dataclass(slots=True)
class TextLabel(UI):
    """
    纯色矩形文本标签类。
    Args:
        rect       : 矩形区域。
        text       : 显示的文本内容。
        text_style : 文本样式。
        label_style: 标签样式。
        align_mode : 对齐模式。
        box_mode   : 盒子模式。
        offset     : 文本偏移位置。
    """

    rect: fantas.Rect | fantas.IntRect

    text: str = "text"
    text_style: fantas.TextStyle = field(default_factory=fantas.DEFAULTTEXTSTYLE.copy)
    label_style: fantas.LabelStyle = field(
        default_factory=fantas.DEFAULTLABELSTYLE.copy
    )
    align_mode: fantas.AlignMode = fantas.AlignMode.LEFT
    box_mode: fantas.BoxMode = fantas.BoxMode.INSIDE
    offset: fantas.IntPoint = field(default_factory=lambda: [0, 0])

    label_command: fantas.LabelRenderCommand = field(
        init=False, repr=False
    )  # 标签渲染命令
    text_command: fantas.TextRenderCommand = field(
        init=False, repr=False
    )  # 文本渲染命令

    def __post_init__(self) -> None:
        """初始化 TextLabel 实例"""
        self.text_command = fantas.TextRenderCommand(creator=self)
        self.label_command = fantas.LabelRenderCommand(creator=self)

    def create_render_commands(
        self, offset: fantas.Point = (0, 0)
    ) -> Iterator[fantas.RenderCommand]:
        # 简化引用
        lrc = self.label_command
        trc = self.text_command
        bw = self.label_style.border_width
        # 计算渲染命令矩形
        if isinstance(self.rect, fantas.Rect):
            rect = fantas.IntRect(self.rect).move(offset)
        else:
            rect = self.rect.move(offset)
        if bw > 0:
            if self.box_mode is fantas.BoxMode.OUTSIDE:
                lrc.rect = rect.inflate(2 * bw, 2 * bw)
                trc.rect = rect
            elif self.box_mode is fantas.BoxMode.INOUTSIDE:
                lrc.rect = rect.inflate(bw, bw)
                trc.rect = rect.inflate(-bw, -bw)
            else:
                lrc.rect = rect
                trc.rect = rect.inflate(-2 * bw, -2 * bw)
        else:
            lrc.rect = trc.rect = rect
        # 设置标签样式
        lrc.style = self.label_style
        # 生成标签渲染命令
        yield lrc
        # 仅当文本非空时才生成文本渲染命令
        if self.text:
            # 设置文本内容
            trc.text = self.text
            # 设置对齐模式
            trc.align_mode = self.align_mode
            # 设置文本样式
            trc.style = self.text_style
            # 设置偏移位置
            trc.offset = self.offset
            # 生成渲染命令
            yield trc
        # 生成子元素的渲染命令
        yield from UI.create_render_commands(self, offset)


@dataclass(slots=True)
class LinearGradientLabel(UI):
    """
    线性渐变标签类。
    Args:
        rect       : 矩形区域。
        start_color: 起始颜色。
        end_color  : 结束颜色。
        start_pos  : 起始位置。
        end_pos    : 结束位置。
    """

    rect: fantas.Rect | fantas.IntRect
    start_color: fantas.ColorLike
    end_color: fantas.ColorLike
    start_pos: fantas.Point
    end_pos: fantas.Point

    command: fantas.LinearGradientRenderCommand = field(
        init=False, repr=False
    )  # 渲染命令对象

    def __post_init__(self) -> None:
        """初始化 LinearGradientLabel 实例"""
        self.command = fantas.LinearGradientRenderCommand(creator=self)

    def create_render_commands(
        self, offset: fantas.Point = (0, 0)
    ) -> Iterator[fantas.RenderCommand]:
        """
        创建渲染命令列表
        Args:
            offset (fantas.Point): 当前元素的偏移位置，用于计算子元素的绝对位置。
        Yields:
            RenderCommand: 渲染命令对象。
        """
        # 计算渲染命令矩形
        if isinstance(self.rect, fantas.Rect):
            rect = fantas.IntRect(self.rect).move(offset)
        else:
            rect = self.rect.move(offset)
        # 简化引用
        c = self.command
        # 设置渲染命令属性
        c.rect = rect
        c.start_color = self.start_color
        c.end_color = self.end_color
        c.start_pos = fantas.Vector2(self.start_pos[0] + offset[0], self.start_pos[1] + offset[1])
        c.end_pos = fantas.Vector2(self.end_pos[0] + offset[0], self.end_pos[1] + offset[1])
        # 生成渲染命令
        yield c
        # 生成子元素的渲染命令
        yield from UI.create_render_commands(self, offset)

    def mark_dirty(self) -> None:
        """标记渲染缓存为脏"""
        self.command.cache_dirty = True
        self.command.last_pix = 0


@dataclass(slots=True)
class Animation(UI):
    """
    动画显示类。
    Args:
        animation_helper: 动画资源辅助对象。
        rect            : 矩形区域。
        fill_mode       : 填充模式。
        loops           : 循环次数，0 表示无限循环。
    """

    animation_helper: fantas.AnimationHelper
    rect: fantas.Rect | fantas.IntRect
    fill_mode: fantas.FillMode = fantas.FillMode.IGNORE
    loops: int = 1

    started: bool = field(default=False, init=False, repr=False)  # 动画是否已开始
    last_time: int = field(init=False, repr=False)  # 上次更新时间（单位：ns）
    cumulative_time: int | float = field(
        default=0, init=False, repr=False
    )  # 累积播放时间（单位：ns）
    current_frame_index: int = field(default=0, init=False, repr=False)  # 当前帧索引
    command: fantas.SurfaceRenderCommand = field(init=False, repr=False)  # 渲染命令对象

    def __post_init__(self) -> None:
        """初始化 Animation 实例"""
        self.command = fantas.SurfaceRenderCommand(creator=self)

    def create_render_commands(
        self, offset: fantas.Point = (0, 0)
    ) -> Iterator[fantas.RenderCommand]:
        """
        创建渲染命令列表
        Args:
            offset (fantas.Point): 当前元素的偏移位置，用于计算子元素的绝对位置。
        Yields:
            RenderCommand: 渲染命令对象。
        """
        # 计算渲染命令矩形
        if isinstance(self.rect, fantas.Rect):
            rect = fantas.IntRect(self.rect).move(offset)
        else:
            rect = self.rect.move(offset)
        # 简化引用
        c = self.command
        # 计算当前帧索引
        if self.started:
            # 记录当前时间
            now = fantas.get_time_ns()
            # 更新累积播放时间
            self.cumulative_time += now - self.last_time
            # 更新上次更新时间
            self.last_time = now
            # 如果累积播放时间超过当前帧的结束时间，则更新当前帧索引
            while (
                self.cumulative_time
                >= self.animation_helper.cumulative_times[self.current_frame_index + 1]
            ):
                # 指向下一帧
                self.current_frame_index += 1
                # 如果已经是最后一帧
                if self.current_frame_index >= len(self.animation_helper.frames) - 1:
                    # 如果需要重复播放
                    if self.loops != 1:
                        # 重新回到第一帧
                        self.current_frame_index = 0
                        # 减去一轮的累积时间
                        self.cumulative_time -= self.animation_helper.cumulative_times[
                            -1
                        ]
                        # 如果循环次数不为 0，则减少一次循环次数
                        if self.loops != 0:
                            self.loops -= 1
                    # 如果不需要循环播放，则停在最后一帧
                    else:
                        self.current_frame_index = len(self.animation_helper.frames) - 1
                        # 停止动画播放
                        self.started = False
                        break
        # 设置渲染命令属性
        c.surface = self.animation_helper.frames[self.current_frame_index]
        c.dest_rect = rect
        c.fill_mode = self.fill_mode
        # 生成渲染命令
        yield c
        # 生成子元素的渲染命令
        yield from UI.create_render_commands(self, offset)

    def play(self) -> None:
        """开始播放动画"""
        self.started = True
        self.last_time = fantas.get_time_ns()

    def pause(self) -> None:
        """暂停动画播放"""
        self.started = False
        self.cumulative_time += fantas.get_time_ns() - self.last_time

    def set_frame(self, frame_index: int) -> None:
        """
        设置当前帧索引。
        Args:
            frame_index (int): 帧索引。
        """
        if frame_index < 0 or frame_index >= len(self.animation_helper.frames):
            raise IndexError("帧索引超出范围。")
        self.current_frame_index = frame_index
        self.cumulative_time = self.animation_helper.cumulative_times[frame_index]
