"""
这个模块不需要导入。
它定义了用于调试的窗口类，在子进程中运行。
"""

from __future__ import annotations

if __name__ == "__main__":
    raise RuntimeError("这个模块不能直接运行。")

import sys
from collections import deque
from typing import ClassVar, Deque, cast

import fantas
from fantas import math as fantas_math

debug_flags = fantas.DebugFlag(int(sys.argv[1]))

windows_title: str

# 如果没有启用任何调试标志，则退出子进程
if debug_flags not in fantas.DebugFlag.ALL:
    sys.exit(0)

# 预加载资源
fantas.colors.load("white")
fantas.colors.load("#e3e3e3", "debug_fg")
fantas.colors.load("#303030", "debug_bg")

fantas.DEFAULTTEXTSTYLE.font = fantas.fonts.DEFAULTSYSFONT
fantas.DEFAULTTEXTSTYLE.size = 20
fantas.DEFAULTTEXTSTYLE.fgcolor = fantas.colors.get("debug_fg")


class Lpf:
    """
    滑动平均 + 一阶低通滤波器类。
    """

    _lpf_map: ClassVar[dict[str, list[Deque[float] | float | int]]] = {}

    @staticmethod
    def flit(name: str, x: float, alpha: float = 0.1, ma_win: int = 3) -> float:
        """
        调用滤波器进行滤波。
        Args:
            name (str): 滤波器名称。
            x (float): 新的数据点。
            alpha (float): 一阶低通滤波系数，范围 0.0 - 1.0，默认值为 0.1。
            ma_win (int): 滑动平均窗口大小，默认值为 3。
        Returns:
            float: 滤波后的结果。
        """
        if name not in Lpf._lpf_map:
            flit = Lpf._lpf_map[name] = [
                deque([0] * ma_win, maxlen=ma_win),
                0,
                alpha,
                ma_win,
            ]
        else:
            flit = Lpf._lpf_map[name]
        buf = cast(Deque[float], flit[0])
        prev = cast(float, flit[1])
        alpha_value = cast(float, flit[2])
        win = cast(int, flit[3])
        buf.append(x)
        flit[1] = alpha_value * sum(buf) / win + (1 - alpha_value) * prev
        return cast(float, flit[1])

    @staticmethod
    def delete_lpf(name: str) -> None:
        """
        删除指定名称的滤波器。
        Args:
            name (str): 滤波器名称。
        """
        if name in Lpf._lpf_map:
            del Lpf._lpf_map[name]


class EventLogWindow(fantas.Window):
    """事件日志窗口类。"""

    size: tuple[int, int]
    min_size: ClassVar[tuple[int, int]] = (512, 288)

    def __init__(self) -> None:
        super().__init__(
            fantas.WindowConfig(
                title=f"{windows_title} | 事件日志",
                window_size=(600, 400),
                window_position=(0, 0),
                resizable=True,
                mouse_focus=False,
                input_focus=False,
                allow_high_dpi=True,
            )
        )
        self.background = fantas.ColorBackground(fantas.colors.get("debug_bg"))
        self.append(self.background)

        self.text = fantas.Text(
            "",
            fantas.Rect(10, 0, self.size[0] - 20, self.size[1]),
            align_mode=fantas.AlignMode.BOTTOMLEFT,
        )
        if fantas.platform.system() == "Linux":
            self.text.offset = (self.text.offset[0], self.text.offset[1] - 3)
        self.background.append(self.text)

        self.lines: deque[str] = deque(maxlen=64)
        self.add_event_listener(
            fantas.WINDOWRESIZED, self.root_ui, True, self.handle_windowresized_event
        )
        self.add_event_listener(
            fantas.WINDOWCLOSE, self.root_ui, True, self.handle_windowclose_event
        )

        self.log_kf = fantas.AttrKeyFrame(
            self.text.rect, "height", self.size[1], fantas.CURVE_SLOWER
        )
        self.log_kf.start_value = self.size[1]
        self.log_kf.set_duration_ms(300)

    def log_event(self, event_str: str) -> None:
        """
        记录事件日志。
        Args:
            event_str (str): 事件信息字符串。
        """
        # 添加新事件到日志列表
        self.lines.append(event_str)
        self.text.text = "\n---\n".join(self.lines)
        # 调整文本区域高度（目的是保持新文本添加后原来的文本位置不变，然后通过关键帧动画平滑过渡）
        s = self.text.text_style
        self.text.rect.height += (
            len(
                s.font.auto_wrap(
                    s.style_flag, s.size, event_str, round(self.text.rect.width)
                )
            )
            + 1
        ) * s.line_height
        self.log_kf.set_duration_ms(
            fantas_math.lerp(75, 325, self.size[1] / self.text.rect.height)
        )
        self.log_kf.start()

    def handle_windowresized_event(self, event: fantas.Event) -> bool:
        """
        处理窗口大小改变事件。
        Args:
            event (fantas.Event): 窗口大小改变事件对象。
        """
        event.x = max(event.x, EventLogWindow.min_size[0])
        event.y = max(event.y, EventLogWindow.min_size[1])
        if self.size != (event.x, event.y):
            self.size = (event.x, event.y)
        self.text.rect.width = event.x - 20
        self.text.rect.height = event.y
        self.log_kf.end_value = self.log_kf.start_value = event.y
        return False

    def handle_windowclose_event(self, _: fantas.Event) -> bool:
        """
        处理窗口关闭事件。
        """
        fantas.Debug.send_debug_data(
            fantas.DebugFlag.EVENTLOG, prompt="CloseDebugWindow"
        )
        return False


class TimeRecordWindow(fantas.Window):
    """时间记录窗口类。"""

    size: tuple[int, int]
    time_category: ClassVar[dict[str, str]] = {
        "Event": "事件处理",
        "FrameFunc": "帧函数",
        "PreRender": "预渲染",
        "Render": "渲染",
        "Debug": "调试",
        "Idle": "空闲",
    }
    for key in time_category:
        Lpf.flit(f"{key}Time", 0, 0.05, 5)
        Lpf.flit(f"{key}Ratio", 0, 0.05, 5)
    Lpf.flit("FPS", 0, 0.05, 5)
    fantas.colors.load("#e74c3c", "Event_legend_color")
    fantas.colors.load("#3498db", "FrameFunc_legend_color")
    fantas.colors.load("#9b59b6", "PreRender_legend_color")
    fantas.colors.load("#f1c40f", "Render_legend_color")
    fantas.colors.load("#7d7d7d", "Debug_legend_color")
    fantas.colors.load("#2ecc71", "Idle_legend_color")

    min_width: ClassVar[int] = 400
    fix_height: ClassVar[int] = 230

    def __init__(self) -> None:
        super().__init__(
            fantas.WindowConfig(
                title=f"{windows_title} | 时间记录",
                window_size=(TimeRecordWindow.min_width, TimeRecordWindow.fix_height),
                window_position=(0, 0),
                resizable=True,
                mouse_focus=False,
                input_focus=False,
                allow_high_dpi=True,
            )
        )

        self.background = fantas.ColorBackground(fantas.colors.get("debug_bg"))
        self.root_ui.append(self.background)

        self.fps_text = fantas.Text("FPS: 0.0", fantas.Rect(8, 6, 110, 30))
        self.background.append(self.fps_text)
        if fantas.platform.system() == "Linux":
            self.fps_text.offset = (
                self.fps_text.offset[0],
                self.fps_text.offset[1] - 3,
            )

        self.legend_text = fantas.Text(
            "",
            rect=fantas.Rect(
                50,
                70
                - fantas.DEFAULTTEXTSTYLE.font.get_sized_ascender(
                    fantas.DEFAULTTEXTSTYLE.size
                ),
                100,
                30 * len(TimeRecordWindow.time_category) + 1,
            ),
        )
        self.legend_text.text_style.line_height = 30
        if fantas.platform.system() == "Linux":
            self.legend_text.offset = (
                self.legend_text.offset[0],
                self.legend_text.offset[1] - 3,
            )
        text = ""
        for i, (key, desc) in enumerate(TimeRecordWindow.time_category.items()):
            legend_color = fantas.colors.get(f"{key}_legend_color")
            legend = fantas.Label(rect=fantas.Rect(10, 50 + i * 30, 20, 20))
            legend.label_style.bgcolor = legend_color
            legend.label_style.fgcolor = fantas.colors.get("debug_fg")
            legend.label_style.border_width = 2
            self.background.append(legend)
            text += f"{desc}\n"
        self.legend_text.text = text.strip()
        self.background.append(self.legend_text)
        self.times: dict[str, float] = {
            key: 0.0 for key in TimeRecordWindow.time_category
        }
        self.time_text = fantas.Text(
            "",
            fantas.Rect(
                160,
                70
                - fantas.DEFAULTTEXTSTYLE.font.get_sized_ascender(
                    fantas.DEFAULTTEXTSTYLE.size
                ),
                100,
                30 * len(TimeRecordWindow.time_category) + 1,
            ),
        )
        self.time_text.text_style.line_spacing = 1
        self.time_text.text_style.line_height = 30
        if fantas.platform.system() == "Linux":
            self.time_text.offset = (
                self.time_text.offset[0],
                self.time_text.offset[1] - 3,
            )
        self.background.append(self.time_text)
        self.ratios: dict[str, float] = {
            key: 0.0 for key in TimeRecordWindow.time_category
        }
        self.time_ratio_bars: dict[str, tuple[fantas.Label, fantas.Label]] = {}
        for i, key in enumerate(TimeRecordWindow.time_category.keys()):
            bar1 = fantas.Label(rect=fantas.Rect(100, 10, 100, 20))
            bar1.label_style.bgcolor = fantas.colors.get(f"{key}_legend_color")
            self.background.append(bar1)
            bar2 = fantas.Label(
                rect=fantas.Rect(260, 50 + i * 30, self.size[0] - 270, 20)
            )
            bar2.label_style.bgcolor = fantas.colors.get(f"{key}_legend_color")
            bar2.label_style.border_radius_top_right = (
                bar2.label_style.border_radius_bottom_right
            ) = 4
            self.background.append(bar2)
            self.time_ratio_bars[key] = (bar1, bar2)
        bar1.label_style.border_radius_top_right = (
            bar1.label_style.border_radius_bottom_right
        ) = 4
        self.add_event_listener(
            fantas.WINDOWRESIZED, self.root_ui, True, self.handle_windowresized_event
        )
        self.add_event_listener(
            fantas.WINDOWCLOSE, self.root_ui, True, self.handle_windowclose_event
        )

    def update_fps(self, fps: float) -> None:
        """
        更新帧率显示。
        Args:
            fps (float): 当前帧率值。
        """
        self.fps_text.text = f"FPS: {Lpf.flit('FPS', fps):.2f}"

    def update_time_records(self, time_dict: dict[str, int]) -> None:
        """
        更新时间记录显示。
        Args:
            time_dict (dict[str, int]): 包含时间记录的字典，单位ns。
        """
        total_time = sum(time_dict.values())
        self.update_fps(1e9 / total_time if total_time > 0 else 0.0)
        for key, time in time_dict.items():
            self.times[key] = Lpf.flit(f"{key}Time", time / 1e6)  # 转换为毫秒
            self.ratios[key] = Lpf.flit(
                f"{key}Ratio", time / total_time if total_time > 0 else 0.0
            )
        self.time_text.text = "\n".join(
            [f"{time:.2f} ms" for time in self.times.values()]
        )
        x = 120
        width = self.size[0] - x - 10
        for key, bars in self.time_ratio_bars.items():
            bars[0].rect.left = x
            bars[0].rect.width = round(width * self.ratios[key])
            bars[1].rect.width = self.ratios[key] * (self.size[0] - 270)
            x += bars[0].rect.width
        self.time_ratio_bars["Idle"][0].rect.width += (
            self.size[0] - 10 - x
        )  # 修正舍入误差

    def handle_windowresized_event(self, event: fantas.Event) -> bool:
        """
        处理窗口大小改变事件。
        Args:
            event (fantas.Event): 窗口大小改变事件对象。
        """
        event.x = max(event.x, TimeRecordWindow.min_width)
        if self.size != (event.x, TimeRecordWindow.fix_height):
            self.size = (event.x, TimeRecordWindow.fix_height)
        return False

    def handle_windowclose_event(self, _: fantas.Event) -> bool:
        """
        处理窗口关闭事件。
        """
        fantas.Debug.send_debug_data(
            fantas.DebugFlag.TIMERECORD, prompt="CloseDebugWindow"
        )
        return False


class MouseMagnifyWindow(fantas.Window):
    """鼠标放大镜窗口类。"""

    def __init__(self) -> None:
        super().__init__(
            fantas.WindowConfig(
                title=f"{windows_title} | 鼠标放大镜",
                window_size=(256, 320),
                window_position=(0, 0),
                mouse_focus=False,
                input_focus=False,
                allow_high_dpi=True,
            )
        )

        self.background = fantas.ColorBackground(fantas.colors.get("debug_bg"))
        self.root_ui.append(self.background)

        self.ratio: int = 8
        self.cursor_color: fantas.Color = fantas.colors.get("debug_fg")
        self.text = fantas.Text(
            f"放大倍数：{self.ratio}x\n鼠标颜色：{self.cursor_color}",
            fantas.Rect(10, 0, 190, 64),
        )
        self.text.text_style.line_height = 32
        if fantas.platform.system() == "Linux":
            self.text.offset = (self.text.offset[0], self.text.offset[1] - 3)
        self.background.append(self.text)

        self.mouse_shot_img = fantas.Image(
            surface=fantas.Surface((256 // self.ratio, 256 // self.ratio)),
            rect=fantas.Rect(0, 0, 256, 256),
            fill_mode=fantas.FillMode.SCALE,
        )
        self.mouse_shot_img.rect.bottom = self.size[1]
        self.background.append(self.mouse_shot_img)

        self.cursor = fantas.Label(fantas.Rect(0, 0, self.ratio, self.ratio))
        self.cursor.label_style.bgcolor = None
        self.cursor.label_style.border_width = 1
        self.mouse_shot_img.append(self.cursor)
        self.cursor.rect.center = (
            self.mouse_shot_img.rect.width / 2,
            self.mouse_shot_img.rect.height / 2,
        )
        self.cursor_color_label = fantas.Label(fantas.Rect(0, 0, 48, 48))
        self.cursor_color_label.label_style.border_width = 2
        self.cursor_color_label.label_style.fgcolor = fantas.colors.get("debug_fg")
        self.cursor_color_label.rect.midright = (self.size[0] - 10, 32)
        self.background.append(self.cursor_color_label)

        self.add_event_listener(
            fantas.WINDOWCLOSE, self.root_ui, True, self.handle_windowclose_event
        )
        self.add_event_listener(
            fantas.MOUSEWHEEL, self.mouse_shot_img, True, self.handle_mousewheel_event
        )

    def update_text(self) -> None:
        """
        更新文本显示内容。
        """
        self.text.text = (
            f"放大倍数: {self.ratio}x\n鼠标颜色：{self.cursor_color.hex[:-2].upper()}"
        )

    def update_mouse_shot(self, x: int, y: int, surface_bytes: bytes) -> None:
        """
        更新鼠标截图 Surface。
        Args:
            x (int): 鼠标截图的 X 坐标。
            y (int): 鼠标截图的 Y 坐标.
            surface_bytes (bytes): 鼠标截图的 Surface 字节数据。
        """
        self.mouse_shot_img.surface.get_buffer().write(surface_bytes)
        self.cursor.rect.left = x * self.ratio
        self.cursor.rect.top = y * self.ratio
        self.cursor_color = self.mouse_shot_img.surface.get_at((x, y))
        self.cursor.label_style.fgcolor = fantas.get_distinct_blackorwhite(
            self.cursor_color
        )
        self.cursor_color_label.label_style.bgcolor = self.cursor_color
        self.update_text()

    def handle_windowclose_event(self, _: fantas.Event) -> bool:
        """
        处理窗口关闭事件。
        """
        fantas.Debug.send_debug_data(
            fantas.DebugFlag.MOUSEMAGNIFY, prompt="CloseDebugWindow"
        )
        return False

    def handle_mousewheel_event(self, event: fantas.Event) -> bool:
        """
        处理鼠标滚轮事件。
        Args:
            event (fantas.Event): 鼠标滚轮事件对象。
        """
        last_ratio = self.ratio
        if event.y > 0:
            self.ratio = min(self.ratio * 2, 32)
        elif event.y < 0:
            self.ratio = max(self.ratio // 2, 4)
        if self.ratio == last_ratio:
            return False
        fantas.Debug.send_debug_data(self.ratio, prompt="SetMouseMagnifyRatio")
        new_surface = fantas.Surface((256 // self.ratio, 256 // self.ratio))
        new_surface.blit(self.mouse_shot_img.surface, (0, 0))
        self.mouse_shot_img.surface = new_surface
        self.cursor.rect.size = (self.ratio, self.ratio)
        self.update_text()
        return False


def handle_debugreceived_event(_: fantas.Event) -> bool:
    """
    处理接收到的调试命令事件。
    """
    while not fantas.Debug.queue.empty():
        data = fantas.Debug.queue.get()
        prompt = data[0]
        if prompt == "EventLog" and event_log_window is not None:
            event_log_window.log_event(data[1])
        elif prompt == "TimeRecord" and time_record_window is not None:
            time_record_window.update_time_records(data[1])
        elif prompt == "MouseMagnify" and mouse_magnify_window is not None:
            mouse_magnify_window.update_mouse_shot(data[1], data[2], data[3])
    return True


# 存储所有调试窗口的列表
windows: list[fantas.Window] = []
# 调试窗口标题
windows_title = sys.argv[2]

event_log_window: EventLogWindow | None = None
time_record_window: TimeRecordWindow | None = None
mouse_magnify_window: MouseMagnifyWindow | None = None

# 如果启用了事件日志调试标志，则创建事件日志窗口
if fantas.DebugFlag.EVENTLOG in debug_flags:
    event_log_window = EventLogWindow()
    windows.append(event_log_window)
# 如果启用了时间记录调试标志，则创建时间记录窗口
if fantas.DebugFlag.TIMERECORD in debug_flags:
    time_record_window = TimeRecordWindow()
    windows.append(time_record_window)
# 如果启用了鼠标放大调试标志，则创建鼠标放大窗口
if fantas.DebugFlag.MOUSEMAGNIFY in debug_flags:
    mouse_magnify_window = MouseMagnifyWindow()
    windows.append(mouse_magnify_window)
# 注册接收调试命令事件的处理器
for window in windows:
    window.add_event_listener(
        fantas.DEBUGRECEIVED, window.root_ui, True, handle_debugreceived_event
    )
# 创建调试窗口
debug_windows = fantas.MultiWindow(*windows)
debug_windows.auto_place_windows(10)

# 设置主程序端口号
fantas.Debug.set_sendto_port(int(sys.argv[3]))
# 启动读取调试命令的后台线程
fantas.Debug.start_read_thread()
# 返回调试窗口的 UDP 端口号给主程序
print(fantas.get_socket_port(fantas.Debug.udp_socket), flush=True)

# 运行调试窗口主循环
debug_windows.mainloops()
