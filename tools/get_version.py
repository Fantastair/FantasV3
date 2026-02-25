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
version: str = conf["tool"]["pygame"]["metadata"]["version"]

_splits = version.split(".")

# handle optional dev tag
if len(_splits) == 3:
    _splits.append('""')
elif len(_splits) == 4:
    _splits[3] = f'".{_splits[3]}"'
else:
    raise ValueError("Invalid version!")

version_short = ".".join(_splits[:3])
version_macros = tuple(
    zip(
        ("PG_MAJOR_VERSION", "PG_MINOR_VERSION", "PG_PATCH_VERSION", "PG_VERSION_TAG"),
        _splits,
    )
)


def get_version(macros: bool = False) -> str | list[str]:
    """
    获取项目版本字符串，或者如果传入了 macros=True，则返回宏定义列表。
    """
    if macros:
        return [f"-D{key}={value}" for key, value in version_macros]
    return version


if __name__ == "__main__":
    print(
        "\n".join(f"-D{key}={value}" for key, value in version_macros)
        if "--macros" in sys.argv
        else version
    )
