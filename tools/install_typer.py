"""
提供工具函数确保 typer 已经安装
"""

import re
import sys
import importlib
from pathlib import Path

from .pprint import pprint, Colors
from .cmd import cmd_run

__all__ = ["ensure_typer_installed"]

CWD = Path(__file__).parent.parent


def ensure_typer_installed():
    """
    确保 typer 已经安装，如果没有安装则安装它
    """
    try:
        importlib.import_module("typer")
        importlib.import_module("typing_extensions")
    except ImportError:
        pprint("typer 未安装", prompt="install_typer", col=Colors.ERROR)

        requirements_path = CWD / "requirements.txt"
        requirements_content = requirements_path.read_text()

        typer_pattern = re.compile(r"typer\s*==\s*([\d\.]+)")
        match = typer_pattern.search(requirements_content)
        typer_version = match.group(1)

        typing_extensions_pattern = re.compile(r"typing_extensions\s*==\s*([\d\.]+)")
        match = typing_extensions_pattern.search(requirements_content)
        typing_extensions_version = match.group(1)

        pprint(
            f"当前解释器为：{sys.executable}，将要安装 typer({typer_version}) 和 "
            f"typing-extensions({typing_extensions_version})",
            prompt="install_typer",
            col=Colors.WARNING,
        )
        answer = input("建议使用虚拟环境安装，是否继续安装？(y/n): ").strip().lower()
        if answer != "y":
            pprint("安装已取消", prompt="install_typer", col=Colors.ERROR)
            sys.exit(1)

        pprint(f"正在安装 typer=={typer_version}...", prompt="install_typer")
        cmd_run([sys.executable, "-m", "pip", "install", f"typer=={typer_version}"])

        pprint(
            f"正在安装 typing-extensions=={typing_extensions_version}...",
            prompt="install_typer"
        )
        cmd_run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                f"typing-extensions=={typing_extensions_version}"
            ]
        )

        importlib.import_module("typer")
        importlib.import_module("typing_extensions")

        pprint("typer 已就绪", prompt="install_typer", col=Colors.SUCCESS)
