"""
一个简单的脚本，读取项目根目录下的 pyproject.toml，并打印其中指定的项目版本。
本脚本学习于 pygame-ce 项目，感谢 pygame-ce 团队的贡献！
"""

import sys
import tomllib
from pathlib import Path

base_dir = Path(__file__).parents[1]
config_file = base_dir / "pyproject.toml"
config_text = config_file.read_text()

conf = tomllib.loads(config_text)


def get_version(package: str = "fantas", macros: bool = False) -> str | list[str]:
    """
    获取项目版本字符串，或者如果传入了 macros=True，则返回宏定义列表。
    Args:
        package: 要获取版本的包名，默认为 "fantas"，也可以是 "pygame-ce"
        macros: 是否返回宏定义列表，默认为 False
    Returns:
        如果 macros=False，返回版本字符串；如果 macros=True，返回宏定义列表
    """
    if package == "fantas":
        version: str = conf["tool"]["poetry"]["version"]
    elif package == "pygame-ce":
        version: str = conf["tool"]["pygame"]["metadata"]["version"]

    _splits = version.split(".")

    if len(_splits) == 3:
        _splits.append('""')
    elif len(_splits) == 4:
        _splits[3] = f'".{_splits[3]}"'
    else:
        raise ValueError("Invalid version!")

    if macros:
        version_macros = tuple(
            zip(
                (
                    "PG_MAJOR_VERSION",
                    "PG_MINOR_VERSION",
                    "PG_PATCH_VERSION",
                    "PG_VERSION_TAG",
                ),
                _splits,
            )
        )
        return [f"-D{key}={value}" for key, value in version_macros]
    return version
