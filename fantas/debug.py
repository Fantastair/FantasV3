"""
调试模块，可以启动一个独立的调试子进程。
"""

import sys
import atexit
import pickle
import threading
import subprocess
import socket
from queue import Queue
from enum import Flag

import fantas

__all__ = (
    "Debug",
    "DebugFlag",
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
    udp_socket: socket.socket = fantas.create_udp_socket(
        port=0, timeout=1.0
    )
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
            str(fantas.get_socket_port(Debug.udp_socket)),
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
        """ 关闭调试窗口子进程。 """
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
        fantas.udp_send_data(
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
            recv, _ = fantas.udp_receive_data(Debug.udp_socket)
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
