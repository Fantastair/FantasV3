"""
fantas.window 的 Docstring
"""

from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass

from fantas._vendor.pygame.window import Window as PygameWindow
from fantas._vendor.pygame.constants import WINDOWPOS_UNDEFINED

import fantas

__all__ = (
    "WindowConfig",
    "Window",
    "MultiWindow",
)


@dataclass(slots=True)
class WindowConfig:
    """
    窗口配置数据类，包含创建窗口所需的各种参数。
    Args:
        title (str): 窗口标题。
        window_size (fantas.IntPoint): 窗口尺寸（宽, 高）（像素）。
        window_position (fantas.IntPoint | int): 窗口位置（x, y）或预设常量
            fantas.WINDOWPOS_CENTERED / fantas.WINDOWPOS_UNDEFINED。
        borderless (bool): 窗口是否无边框。
        resizable (bool): 是否可以调整窗口大小。
        fps (int): 窗口帧率。
        mouse_focus (bool): 窗口是否在创建时获得鼠标焦点。
        input_focus (bool): 窗口是否在创建时获得输入焦点。
        allow_high_dpi (bool): 是否允许高 DPI 显示。
    """

    title: str = "Fantas Window"
    window_size: fantas.IntPoint = (1280, 720)
    window_position: fantas.IntPoint | int = WINDOWPOS_UNDEFINED
    borderless: bool = False
    resizable: bool = False
    fps: int = 60
    mouse_focus: bool = True
    input_focus: bool = True
    allow_high_dpi: bool = True

    @property
    def width(self) -> int:
        """窗口的宽度（像素）"""
        return self.window_size[0]

    @property
    def height(self) -> int:
        """窗口的高度（像素）"""
        return self.window_size[1]


class Window(PygameWindow):
    """
    窗口类，每一个实例就是一个窗口。
    """

    # 窗口的调试计时器

    def __init__(self, window_config: WindowConfig) -> None:
        """
        初始化 Window 实例。
        Args:
            window_config (WindowConfig): 窗口配置数据类实例，包含窗口的各种参数。
        """
        # 初始化父类
        super().__init__(
            title=window_config.title,
            size=window_config.window_size,
            position=window_config.window_position,
            borderless=window_config.borderless,
            resizable=window_config.resizable,
            mouse_focus=window_config.mouse_focus,
            input_focus=window_config.input_focus,
            allow_high_dpi=window_config.allow_high_dpi,
        )

        self.running: bool = True  # 窗口运行状态标志
        self.fps: int = window_config.fps  # 窗口帧率设置
        self.screen: fantas.Surface = self.get_surface()  # 窗口的主 Surface 对象
        self.renderer: fantas.Renderer = fantas.Renderer(self)  # 窗口的渲染器对象
        self.root_ui: fantas.WindowRoot = fantas.WindowRoot(
            window=self
        )  # 窗口的根 UI 元素
        self.event_handler: fantas.EventHandler = fantas.EventHandler(
            window=self
        )  # 窗口的事件处理器对象
        self.mouse_magnify_ratio: int = 0

        # 方便访问根 UI 元素的方法
        self.append: Callable[[fantas.UI], None] = self.root_ui.append
        self.insert: Callable[[int, fantas.UI], None] = self.root_ui.insert
        self.remove: Callable[[fantas.UI], None] = self.root_ui.remove
        self.pop: Callable[[int], fantas.UI] = self.root_ui.pop
        self.clear: Callable[[], None] = self.root_ui.clear
        # 方便访问事件处理器的管理监听器方法
        self.add_event_listener = self.event_handler.add_event_listener
        self.remove_event_listener = self.event_handler.remove_event_listener

    def mainloop(self) -> None:
        """
        进入窗口的主事件循环，直到窗口关闭。
        """
        # 简化引用
        tick = fantas.CLOCK.tick
        get = fantas.event.get
        handle_event = self.event_handler.handle_event
        run_framefuncs = fantas.run_framefuncs
        pre_render = self.renderer.pre_render
        render = self.renderer.render
        root_ui = self.root_ui
        screen = self.screen
        flip = self.flip
        # 清空事件队列
        fantas.event.clear()
        # 预生成传递路径缓存
        root_ui.build_pass_path_cache()
        # 主循环
        while self.running:
            # 限制帧率
            tick(self.fps)
            # 处理事件
            for event in get():
                handle_event(event)
            # 运行帧函数
            run_framefuncs()
            # 生成渲染命令
            pre_render(root_ui)
            # 渲染窗口
            render(screen)
            # 更新窗口显示
            flip()
        self.destroy()


class MultiWindow:
    """
    多窗口管理类，用于管理多个窗口实例。
    """

    def __init__(self, *windows: Window, fps: int = 60) -> None:
        """
        初始化 MultiWindow 实例。
        Args:
            *windows (Window): 可变数量的 Window 实例，表示要管理的多个窗口。
        """
        self.fps: int = fps  # 窗口帧率设置
        self.windows: dict[int, Window] = {
            window.id: window for window in windows
        }  # 管理的窗口字典，键为窗口 ID，值为 Window 实例
        self.running: bool = True  # 多窗口运行状态标志

    def append(self, window: Window) -> None:
        """
        添加一个窗口到管理列表中。
        Args:
            window (Window): 要添加的 Window 实例。
        """
        self.windows[window.id] = window

    def pop(self, window: Window) -> Window | None:
        """
        从管理列表中移除一个窗口。
        Args:
            window (Window): 要移除的 Window 实例。
        Returns:
            Window | None: 如果窗口存在则返回被移除的 Window 实例，否则返回 None。
        """
        return self.windows.pop(window.id, None)

    def get_window(self, window_id: int) -> Window | None:
        """
        根据窗口 ID 获取对应的窗口实例。
        Args:
            window_id (int): 窗口的唯一标识符 ID。
        Returns:
            Window | None: 如果找到对应的窗口则返回 Window 实例，否则返回 None。
        """
        return self.windows.get(window_id, None)

    def handle_window_close_event(self, event: fantas.Event) -> None:
        """
        处理窗口关闭事件，将对应的窗口从管理列表中移除。
        Args:
            event (fantas.Event): 触发此事件的 fantas.Event 实例。
        """
        window = self.pop(event.window)
        if window is not None:
            window.destroy()
        if not self.windows:
            self.running = False

    def auto_place_windows(self, padding: int = 0) -> None:
        """
        自动布局所有管理的窗口，尽量减少重叠面积。
        Args:
            padding (int, optional): 窗口之间的间距，默认为 0 像素。
        """
        screen_size = fantas.display.get_desktop_sizes()[0]

        left = padding
        top = padding
        bottom = top

        for window in self.windows.values():
            if window.size[0] + left + padding * 2 > screen_size[0]:
                left = padding
                top = bottom
            window.position = (left + padding, top + padding)
            left += window.size[0] + padding
            bottom = max(bottom, top + window.size[1] + padding)

    def mainloops(self) -> None:
        """
        进入所有管理窗口的主事件循环，直到所有窗口关闭。
        """
        # 简化引用
        tick = fantas.CLOCK.tick
        get = fantas.event.get
        windows = self.windows
        run_framefuncs = fantas.run_framefuncs
        # 清空事件队列
        fantas.event.clear()
        window: Window | None
        for window in windows.values():
            # 预生成传递路径缓存
            window.root_ui.build_pass_path_cache()
            # 注册关闭事件监听器
            window.add_event_listener(
                fantas.WINDOWCLOSE, window.root_ui, True, self.handle_window_close_event
            )
        # 主循环
        while self.running:
            # 限制帧率
            tick(self.fps)
            # 处理事件
            for event in get():
                # 如果事件关联到特定窗口，则只传递给该窗口，否则传递给所有窗口
                if hasattr(event, "window"):
                    window = event.window
                else:
                    window = None
                if window is not None:
                    window.event_handler.handle_event(event)
                else:
                    for window in windows.values():
                        window.event_handler.handle_event(event)
            # 运行帧函数
            run_framefuncs()
            # 渲染所有窗口
            for window in windows.values():
                # 生成渲染命令
                window.renderer.pre_render(window.root_ui)
                # 渲染窗口
                window.renderer.render(window.screen)
                # 更新窗口显示
                window.flip()
