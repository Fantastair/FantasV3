"""
封装运行命令的函数。
"""

import sys
import subprocess
from pathlib import Path

from .pprint import pprint, Colors

__all__ = ["cmd_run"]

CWD = Path(__file__).parent.parent


def cmd_run(
    cmd: list[str | Path],
    capture_output: bool = False,
    error_on_output: bool = False,
    cwd: Path = CWD,
) -> str:
    """
    运行一个命令，并且根据参数决定是否捕获输出或者在有输出时视为错误。
    """
    if error_on_output:
        capture_output = True

    norm_cmd = [str(i) for i in cmd]
    pprint(f"> {' '.join(norm_cmd)}", prompt="command", col=Colors.COMMAND)
    try:
        ret = subprocess.run(
            norm_cmd,
            stdout=subprocess.PIPE if capture_output else sys.stdout,
            stderr=subprocess.STDOUT,
            text=capture_output,
            cwd=cwd,
            check=True,
        )
    except FileNotFoundError:
        pprint(f"{norm_cmd[0]}: 未找到指令", prompt="command", col=Colors.ERROR)
        sys.exit(1)

    if ret.stdout:
        print(ret.stdout, end="", flush=True)

    if (error_on_output and ret.stdout) and not ret.returncode:
        # 如果有 stdout 并且存在错误，则设置返回代码为 1
        ret.returncode = 1

    ret.check_returncode()
    return ret.stdout.strip() if capture_output else ""
