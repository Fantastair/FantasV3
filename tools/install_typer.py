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

        pattern = re.compile(r"typer\s*==\s*([\d\.]+)")
        match = pattern.search(requirements_content)
        version = match.group(1)

        pprint(f"正在安装 typer=={version}...", prompt="install_typer")
        cmd_run([sys.executable, "-m", "pip", "install", f"typer=={version}"])

        importlib.import_module("typer")
        importlib.import_module("typing_extensions")

        pprint("typer 已就绪", prompt="install_typer", col=Colors.SUCCESS)
