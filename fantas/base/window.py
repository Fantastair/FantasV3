"""
fantas.window 的 Docstring
"""

from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import cast

from fantas._vendor.pygame.window import Window as PygameWindow

import fantas

__all__ = (
    "WindowConfig",
    "Window",
    "MultiWindow",
    "DebugTimer",
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
    window_position: fantas.IntPoint | int = fantas.WINDOWPOS_UNDEFINED
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
        self.clock: fantas.time.Clock = fantas.time.Clock()  # 用于控制帧率的时钟对象
        self.screen: fantas.Surface = self.get_surface()  # 窗口的主 Surface 对象
        self.renderer: fantas.Renderer = fantas.Renderer(self)  # 窗口的渲染器对象
        self.root_ui: fantas.WindowRoot = fantas.WindowRoot(
            window=self
        )  # 窗口的根 UI 元素
        self.event_handler: fantas.EventHandler = fantas.EventHandler(
            window=self
        )  # 窗口的事件处理器对象
        self.debug_timer: DebugTimer | None = None
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
        tick = self.clock.tick
        get = fantas.event.get
        handle_event = self.event_handler.handle_event
        run_framefuncs = fantas.run_framefuncs
        pre_render = self.renderer.pre_render
        render = self.renderer.render
        root_ui = self.root_ui
        screen = self.screen
        flip = self.flip
        # 设置帧函数的时钟对象引用
        fantas.set_framefunc_clock(self.clock)
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

    def mainloop_debug(self) -> None:
        """
        以调试模式进入窗口的主事件循环，直到窗口关闭。
        """
        # 简化引用
        tick = self.clock.tick
        get = fantas.event.get
        handle_event = self.event_handler.handle_event
        run_framefuncs = fantas.run_framefuncs
        pre_render = self.renderer.pre_render
        render = self.renderer.render
        root_ui = self.root_ui
        screen = self.screen
        flip = self.flip
        EVENTLOG = fantas.DebugFlag.EVENTLOG  # pylint: disable=invalid-name
        TIMERECORD = fantas.DebugFlag.TIMERECORD  # pylint: disable=invalid-name
        DEBUGRECEIVED = fantas.DEBUGRECEIVED  # pylint: disable=invalid-name
        send_debug_data = fantas.Debug.send_debug_data
        # 设置帧函数的时钟对象引用
        fantas.set_framefunc_clock(self.clock)
        # 清空事件队列
        fantas.event.clear()
        # 预生成传递路径缓存
        root_ui.build_pass_path_cache()

        # === 调试 ===
        # 监听调试输出事件
        self.add_event_listener(
            fantas.DEBUGRECEIVED, root_ui, True, self.handle_debug_received_event
        )
        # 监听鼠标移动事件
        if fantas.DebugFlag.MOUSEMAGNIFY in fantas.Debug.debug_flag:
            self.mouse_magnify_ratio = 8
            self.add_event_listener(
                fantas.MOUSEMOTION, root_ui, True, self.debug_send_mouse_surface
            )
        # 创建调试计时器
        self.debug_timer = debug_timer = DebugTimer()
        record = debug_timer.record
        # === 调试 ===

        # 主循环
        while self.running:
            # 限制帧率
            tick(self.fps)

            # === 调试 ===
            record("Idle")
            # === 调试 ===

            # 处理事件
            for event in get():

                # === 调试 ===
                # 发送事件信息到调试窗口
                record("Event")
                if EVENTLOG in fantas.Debug.debug_flag and event.type != DEBUGRECEIVED:
                    send_debug_data(str(event), prompt="EventLog")
                record("Debug")
                # === 调试 ===

                handle_event(event)

            # === 调试 ===
            record("Event")
            # === 调试 ===

            # 运行帧函数
            run_framefuncs()

            # === 调试 ===
            record("FrameFunc")
            # === 调试 ===

            # 生成渲染命令
            pre_render(root_ui)

            # === 调试 ===
            record("PreRender")
            # === 调试 ===

            # 渲染窗口
            render(screen)
            # 更新窗口显示
            flip()

            # === 调试 ===
            record("Render")
            # 发送计时记录到调试窗口
            if TIMERECORD in fantas.Debug.debug_flag:
                send_debug_data(debug_timer.time_records, prompt="TimeRecord")
            # 清空计时记录
            debug_timer.clear()
            # === 调试 ===

        self.destroy()

    def handle_debug_received_event(self, _: fantas.Event) -> None:
        """
        处理从调试窗口接收到输出信息的事件。
        """
        debug_timer = cast(DebugTimer, self.debug_timer)
        debug_timer.record("Event")
        while not fantas.Debug.queue.empty():
            data = fantas.Debug.queue.get()
            if data[0] == "CloseDebugWindow":
                fantas.Debug.delete_debug_flag(data[1])
            elif data[0] == "SetMouseMagnifyRatio":
                self.mouse_magnify_ratio = data[1]
            else:
                print(f"[{data[0]}]", end="")
                for d in data[1:]:
                    print(f" {d}", end="")
                print()
        debug_timer.record("Debug")

    def debug_send_mouse_surface(self, event: fantas.Event) -> None:
        """
        发送当前鼠标所在位置的 Surface 截图到调试窗口。
        Args:
            event (fantas.Event): 触发此事件的 fantas.Event 实例。
        """
        # 获取鼠标位置附近的 Surface 截图
        debug_timer = cast(DebugTimer, self.debug_timer)
        debug_timer.record("Event")
        size = 256 // self.mouse_magnify_ratio
        pos = list(event.pos)
        pos[0] = fantas.math.clamp(pos[0], 0, self.size[0] - 1)
        pos[1] = fantas.math.clamp(pos[1], 0, self.size[1] - 1)
        rect = fantas.Rect(
            event.pos[0] - size // 2, event.pos[1] - size // 2, size, size
        )
        rect.left = max(rect.left, 0)
        rect.top = max(rect.top, 0)
        rect.right = min(rect.right, self.size[0])
        rect.bottom = min(rect.bottom, self.size[1])
        # 发送到调试窗口
        fantas.Debug.send_debug_data(
            pos[0] - rect.left,
            pos[1] - rect.top,
            self.screen.subsurface(rect).convert_alpha().get_buffer().raw,
            prompt="MouseMagnify",
        )
        debug_timer.record("Debug")


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
        self.clock: fantas.time.Clock = fantas.time.Clock()  # 用于控制帧率的时钟对象
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
        tick = self.clock.tick
        get = fantas.event.get
        windows = self.windows
        run_framefuncs = fantas.run_framefuncs
        # 设置帧函数的时钟对象引用
        fantas.set_framefunc_clock(self.clock)
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
                # print(event, flush=True)
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

    def mainloops_debug(self) -> None:
        """
        以调试模式进入所有管理窗口的主事件循环，直到所有窗口关闭。
        """
        # === 调试 ===
        # 创建调试计时器
        debug_timer = DebugTimer()
        # === 调试 ===

        # 简化引用
        tick = self.clock.tick
        get = fantas.event.get
        windows = self.windows
        run_framefuncs = fantas.run_framefuncs
        record = debug_timer.record
        EVENTLOG = fantas.DebugFlag.EVENTLOG  # pylint: disable=invalid-name
        TIMERECORD = fantas.DebugFlag.TIMERECORD  # pylint: disable=invalid-name
        DEBUGRECEIVED = fantas.DEBUGRECEIVED  # pylint: disable=invalid-name
        send_debug_data = fantas.Debug.send_debug_data
        # 设置帧函数的时钟对象引用
        fantas.set_framefunc_clock(self.clock)
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

            # === 调试 ===
            # 共用计时器
            window.debug_timer = debug_timer
            # 监听调试输出事件
            window.add_event_listener(
                fantas.DEBUGRECEIVED,
                window.root_ui,
                True,
                window.handle_debug_received_event,
            )
            # 监听鼠标移动事件
            if fantas.DebugFlag.MOUSEMAGNIFY in fantas.Debug.debug_flag:
                window.add_event_listener(
                    fantas.MOUSEMOTION,
                    window.root_ui,
                    True,
                    window.debug_send_mouse_surface,
                )
            # === 调试 ===
        # === 调试 ===
        # 重置调试计时器
        debug_timer.reset()
        # === 调试 ===

        # 主循环
        while windows:
            # 限制帧率
            tick(self.fps)

            # === 调试 ===
            record("Idle")
            # === 调试 ===

            # 处理事件
            for event in get():

                # === 调试 ===
                # 发送事件信息到调试窗口
                record("Event")
                if EVENTLOG in fantas.Debug.debug_flag and event.type != DEBUGRECEIVED:
                    send_debug_data(str(event), "EventLog")
                record("Debug")
                # === 调试 ===

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

            # === 调试 ===
            record("Event")
            # === 调试 ===

            # 运行帧函数
            run_framefuncs()

            # === 调试 ===
            record("FrameFunc")
            # === 调试 ===

            # 渲染所有窗口
            for window in windows.values():
                # 生成渲染命令
                window.renderer.pre_render(window.root_ui)

                # === 调试 ===
                record("PreRender")
                # === 调试 ===

                # 渲染窗口
                window.renderer.render(window.screen)
                # 更新窗口显示
                window.flip()

                # === 调试 ===
                record("Render")
                # === 调试 ===

            # === 调试 ===
            # 发送计时记录到调试窗口
            if TIMERECORD in fantas.Debug.debug_flag:
                send_debug_data(debug_timer.time_records, "TimeRecord")
            # 清空计时记录
            debug_timer.clear()
            # === 调试 ===


@dataclass(slots=True)
class DebugTimer:
    """
    调试计时器类，用于测量代码执行时间。
    """

    last_time: int = field(
        default_factory=fantas.get_time_ns, init=False, repr=False
    )  # 上一次记录的时间点（纳秒）
    time_records: dict[str, int] = field(
        default_factory=dict, init=False
    )  # 记录的时间数据字典

    def record(self, label: str) -> None:
        """
        记录从上一次调用 record 方法到当前的时间差，并累计到指定标签的时间记录中。
        Args:
            label (str): 用于标识时间记录的标签。
        """
        current_time = fantas.get_time_ns()
        self.time_records[label] = (
            self.time_records.get(label, 0) + current_time - self.last_time
        )
        self.last_time = current_time

    def reset(self) -> None:
        """
        重置计时器，清空所有时间记录并更新上一次记录的时间点为当前时间。
        """
        self.time_records.clear()
        self.last_time = fantas.get_time_ns()

    def clear(self) -> None:
        """
        清空所有时间记录，但不更新上一次记录的时间点。
        """
        self.time_records.clear()
