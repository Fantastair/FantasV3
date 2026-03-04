"""
调试模块，可以启动一个独立的调试子进程。
"""

import sys
import atexit
import pickle
import socket
import threading
import subprocess
from enum import Flag
from queue import Queue
from typing import Callable
from dataclasses import dataclass, field

import fantas
from .udp import *

__all__ = (
    "Debug",
    "DebugFlag",
    "DebugTimer",
    "window_mainloop_debug",
    "multiwindow_mainloop_debug",
)


class DebugFlag(Flag):
    """调试选项标志枚举。"""

    EVENTLOG = 1
    """ 事件日志 """
    TIMERECORD = 2
    """ 时间记录 """
    MOUSEMAGNIFY = 4
    """ 鼠标放大镜 """

    ALL = EVENTLOG | TIMERECORD | MOUSEMAGNIFY
    """ 全部调试选项 """
    NONE = 0
    """ 无调试选项 """


debug_received_event: fantas.Event = fantas.Event(fantas.DEBUGRECEIVED)


class Debug:
    """
    调试工具类，提供启动调试窗口、发送调试数据等功能。
    """

    process: subprocess.Popen[str] | None = None
    """ 调试窗口子进程对象 """
    queue: Queue[tuple] = Queue()  # type: ignore[type-arg]
    """ 调试子进程返回队列 """
    debug_flag: DebugFlag = DebugFlag.NONE
    """ 当前调试选项标志 """
    udp_socket: socket.socket = create_udp_socket(port=0, timeout=1.0)
    """ UDP 通信套接字 """
    reading: bool = False
    """ 是否正在读取子进程输出 """
    debug_port: int = 0
    """ 调试窗口子进程的接收端口号 """

    @staticmethod
    def start_debug(
        flag: DebugFlag = DebugFlag.ALL, windows_title: str = "fantas 调试窗口"
    ) -> None:
        """
        启动调试窗口子进程。

        :param flag: 调试选项标志，默认为 DebugFlag.ALL。
        :type flag: DebugFlag
        :param windows_title: 调试窗口标题，默认为 "fantas 调试窗口"。
        :type windows_title: str
        """
        # 先关闭已有的调试窗口
        Debug.close_debug()
        # 启动后台线程读取子进程输出
        Debug.start_read_thread()

        cmd = [
            sys.executable,
            "-m",
            "fantas.debug_window",
            str(flag.value),
            windows_title,
            str(get_socket_port(Debug.udp_socket)),
        ]

        # 启动子进程
        try:
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,  # 接收信息通信管道
                text=True,  # 文本模式，自动编码/解码
                bufsize=1,  # 行缓冲
                # env=env,  # 子进程环境变量
            ) as process:
                Debug.process = process
                # 子进程运行后会返回端口号
                line = Debug.process.stdout.readline() if Debug.process.stdout else None
                if line:
                    # 获取调试端口号
                    Debug.set_sendto_port(int(line.rstrip("\n")))
                    # 记录当前调试选项标志
                    Debug.debug_flag = flag
        except FileNotFoundError as e:
            raise RuntimeError(f"命令{cmd}出错，无法启动调试窗口:") from e

    @staticmethod
    def close_debug() -> None:
        """关闭调试窗口子进程。"""
        if Debug.process is not None:
            Debug.process.kill()
            Debug.process.wait()
            Debug.reading = False

    @staticmethod
    def set_sendto_port(port: int) -> None:
        """
        设置调试窗口进程的接收端口号。

        :param port: 目标端口号。
        :type port: int
        """
        Debug.debug_port = port

    @staticmethod
    def send_debug_data(*data: object, prompt: str = "Debug") -> None:
        """
        发送调试数据到调试窗口子进程。

        :param data: 要发送的调试数据对象。
        :type data: object
        :param prompt: 调试提示信息。
        :type prompt: str
        """
        udp_send_data(
            Debug.udp_socket,
            pickle.dumps((prompt, *data)),
            ("127.0.0.1", Debug.debug_port),
        )

    @staticmethod
    def read_debug_data() -> None:
        """
        从调试窗口子进程读取输出信息并放入队列。
        """
        while Debug.reading:
            recv, _ = udp_receive_data(Debug.udp_socket)
            if recv is not None:
                if Debug.queue.empty():
                    Debug.queue.put(pickle.loads(recv))
                    fantas.event.post(debug_received_event)
                else:
                    Debug.queue.put(pickle.loads(recv))
            else:
                # 避免忙等待
                fantas.time.delay(100)

    @staticmethod
    def start_read_thread() -> None:
        """
        启动读取调试窗口子进程输出的后台线程。
        """
        Debug.reading = True
        threading.Thread(target=Debug.read_debug_data, daemon=True).start()

    @staticmethod
    def add_debug_flag(flag: DebugFlag) -> None:
        """
        添加指定的调试选项标志。

        :param flag: 要添加的调试选项标志。
        :type flag: DebugFlag
        """
        Debug.debug_flag |= flag

    @staticmethod
    def delete_debug_flag(flag: DebugFlag) -> None:
        """
        删除指定的调试选项标志。

        :param flag: 要删除的调试选项标志。
        :type flag: DebugFlag
        """
        Debug.debug_flag &= ~flag


atexit.register(Debug.close_debug)


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


def window_mainloop_debug(window: fantas.Window) -> None:
    """
    以调试模式进入窗口的主事件循环，直到窗口关闭。
    """
    # 简化引用
    tick = fantas.CLOCK.tick
    get = fantas.event.get
    handle_event = window.event_handler.handle_event
    run_framefuncs = fantas.run_framefuncs
    pre_render = window.renderer.pre_render
    render = window.renderer.render
    root_ui = window.root_ui
    screen = window.screen
    flip = window.flip
    EVENTLOG = DebugFlag.EVENTLOG  # pylint: disable=invalid-name
    TIMERECORD = DebugFlag.TIMERECORD  # pylint: disable=invalid-name
    DEBUGRECEIVED = fantas.DEBUGRECEIVED  # pylint: disable=invalid-name
    # 清空事件队列
    fantas.event.clear()
    # 预生成传递路径缓存
    root_ui.build_pass_path_cache()

    # === 调试 ===
    # 监听调试输出事件
    window.add_event_listener(
        fantas.DEBUGRECEIVED,
        root_ui,
        True,
        create_window_debug_listener(window, handle_debug_received_event),
    )
    # 监听鼠标移动事件
    if DebugFlag.MOUSEMAGNIFY in Debug.debug_flag:
        window.mouse_magnify_ratio = 8
        window.add_event_listener(
            fantas.MOUSEMOTION,
            root_ui,
            True,
            create_window_debug_listener(window, debug_send_mouse_surface),
        )
    # 创建调试计时器
    window.debug_timer = debug_timer = DebugTimer()  # type: ignore[attr-defined]
    record = debug_timer.record
    # === 调试 ===

    # 主循环
    while window.running:
        # 限制帧率
        tick(window.fps)

        # === 调试 ===
        record("Idle")
        # === 调试 ===

        # 处理事件
        for event in get():

            # === 调试 ===
            # 发送事件信息到调试窗口
            record("Event")
            if EVENTLOG in Debug.debug_flag and event.type != DEBUGRECEIVED:
                Debug.send_debug_data(str(event), prompt="EventLog")
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
        if TIMERECORD in Debug.debug_flag:
            Debug.send_debug_data(debug_timer.time_records, prompt="TimeRecord")
        # 清空计时记录
        debug_timer.clear()
        # === 调试 ===

    window.destroy()


def multiwindow_mainloop_debug(multiwindow: fantas.MultiWindow) -> None:
    """
    以调试模式进入所有管理窗口的主事件循环，直到所有窗口关闭。
    """
    # === 调试 ===
    # 创建调试计时器
    debug_timer = DebugTimer()
    # === 调试 ===

    # 简化引用
    tick = fantas.CLOCK.tick
    get = fantas.event.get
    windows = multiwindow.windows
    run_framefuncs = fantas.run_framefuncs
    record = debug_timer.record
    EVENTLOG = DebugFlag.EVENTLOG  # pylint: disable=invalid-name
    TIMERECORD = DebugFlag.TIMERECORD  # pylint: disable=invalid-name
    DEBUGRECEIVED = fantas.DEBUGRECEIVED  # pylint: disable=invalid-name
    send_debug_data = Debug.send_debug_data
    # 清空事件队列
    fantas.event.clear()
    window: fantas.Window | None
    for window in windows.values():
        # 预生成传递路径缓存
        window.root_ui.build_pass_path_cache()
        # 注册关闭事件监听器
        window.add_event_listener(
            fantas.WINDOWCLOSE,
            window.root_ui,
            True,
            multiwindow.handle_window_close_event,
        )

        # === 调试 ===
        # 共用计时器
        window.debug_timer = debug_timer  # type: ignore[attr-defined]
        # 监听调试输出事件
        window.add_event_listener(
            fantas.DEBUGRECEIVED,
            window.root_ui,
            True,
            create_window_debug_listener(window, handle_debug_received_event),
        )
        # 监听鼠标移动事件
        if DebugFlag.MOUSEMAGNIFY in Debug.debug_flag:
            window.add_event_listener(
                fantas.MOUSEMOTION,
                window.root_ui,
                True,
                create_window_debug_listener(window, debug_send_mouse_surface),
            )
        # === 调试 ===
    # === 调试 ===
    # 重置调试计时器
    debug_timer.reset()
    # === 调试 ===

    # 主循环
    while windows:
        # 限制帧率
        tick(multiwindow.fps)

        # === 调试 ===
        record("Idle")
        # === 调试 ===

        # 处理事件
        for event in get():

            # === 调试 ===
            # 发送事件信息到调试窗口
            record("Event")
            if EVENTLOG in Debug.debug_flag and event.type != DEBUGRECEIVED:
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
        if TIMERECORD in Debug.debug_flag:
            send_debug_data(debug_timer.time_records, "TimeRecord")
        # 清空计时记录
        debug_timer.clear()
        # === 调试 ===


def create_window_debug_listener(
    window: fantas.Window,
    listener: Callable[[fantas.Window, fantas.Event], bool | None],
) -> fantas.ListenerFunc:
    """
    从函数创建特定于窗口的事件监听器。
    """

    def debug_listener(event: fantas.Event) -> bool | None:
        return listener(window, event)

    return debug_listener


def handle_debug_received_event(window: fantas.Window, _: fantas.Event) -> None:
    """
    处理从调试窗口接收到输出信息的事件。
    """
    debug_timer: DebugTimer = window.debug_timer  # type: ignore[attr-defined]
    debug_timer.record("Event")
    while not Debug.queue.empty():
        data = Debug.queue.get()
        if data[0] == "CloseDebugWindow":
            Debug.delete_debug_flag(data[1])
        elif data[0] == "SetMouseMagnifyRatio":
            window.mouse_magnify_ratio = data[1]
        else:
            print(f"[{data[0]}]", end="")
            for d in data[1:]:
                print(f" {d}", end="")
            print()
    debug_timer.record("Debug")


def debug_send_mouse_surface(window: fantas.Window, event: fantas.Event) -> None:
    """
    发送当前鼠标所在位置的 Surface 截图到调试窗口。
    Args:
        event (fantas.Event): 触发此事件的 fantas.Event 实例。
    """
    # 获取鼠标位置附近的 Surface 截图
    debug_timer: DebugTimer = window.debug_timer  # type: ignore[attr-defined]
    debug_timer.record("Event")
    size = 256 // window.mouse_magnify_ratio
    pos = list(event.pos)
    pos[0] = fantas.math.clamp(pos[0], 0, window.size[0] - 1)
    pos[1] = fantas.math.clamp(pos[1], 0, window.size[1] - 1)
    rect = fantas.Rect(event.pos[0] - size // 2, event.pos[1] - size // 2, size, size)
    rect.left = max(rect.left, 0)
    rect.top = max(rect.top, 0)
    rect.right = min(rect.right, window.size[0])
    rect.bottom = min(rect.bottom, window.size[1])
    # 发送到调试窗口
    Debug.send_debug_data(
        pos[0] - rect.left,
        pos[1] - rect.top,
        window.screen.subsurface(rect).convert_alpha().get_buffer().raw,
        prompt="MouseMagnify",
    )
    debug_timer.record("Debug")
