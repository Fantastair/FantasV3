"""
提供增强型函数 pprint，用于在终端中打印带有颜色的消息。
"""

import os
from enum import Enum

__all__ = ["Colors", "pprint"]


class Colors(Enum):
    """
    Colors 枚举定义了用于终端输出的颜色代码。它提供了一种方便的方式来在终端中使用颜色，
    以增强输出的可读性和视觉效果。
    """

    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    ERROR = RED
    SUCCESS = GREEN
    WARNING = YELLOW
    INFO = BLUE
    TIP = MAGENTA
    COMMAND = CYAN
    DEFAULT = WHITE


# 参考链接 https://docs.python.org/3.13/using/cmdline.html#controlling-color
def has_color() -> bool:
    """
    has_color 函数用于判断当前环境是否支持颜色输出。
    """
    # 最高优先级
    python_colors = os.environ.get("PYTHON_COLORS", "").strip()
    if python_colors == "1":
        return True
    if python_colors == "0":
        return False

    # 第二高优先级
    if "NO_COLOR" in os.environ:
        return False

    # 第三高优先级
    if "FORCE_COLOR" in os.environ:
        return True

    # 最低优先级
    return os.environ.get("TERM", "").strip().lower() != "dumb"


def pprint(
    arg: str,
    prompt: str = "pprint",
    col: Colors = Colors.DEFAULT,
    wrap: bool = True,
    restart: bool = False,
) -> None:
    """
    pprint 函数用于在终端中打印带有颜色的消息。

    Args:
        arg: 要打印的消息内容
        prompt: 消息前缀，默认为 "pprint"
        col: 消息的颜色，默认为默认颜色
        wrap: 是否在消息末尾添加换行符，默认为 True
        restart: 是否从头输出（此项为 True 时，wrap 自动强制为 False，会从头覆盖输出）
            适合用于显示进度条等需要覆盖输出的场景
    """
    do_col = has_color()
    start = Colors.BLUE.value if do_col else ""
    mid = col.value if do_col else ""
    end = Colors.RESET.value if do_col else ""
    if restart:
        print(f"\r{start}[{prompt}] {mid}{arg}{end}", end="", flush=True)
    elif wrap:
        print(f"{start}[{prompt}] {mid}{arg}{end}", flush=True)
    else:
        print(f"{start}[{prompt}] {mid}{arg}{end}", end="", flush=True)
