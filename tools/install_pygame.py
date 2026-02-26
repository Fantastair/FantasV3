"""
提供安装 pygame-ce for fantas 的封装
"""

import sys
import shutil
import subprocess
from enum import Enum
from pathlib import Path

from .pprint import Colors, pprint
from .github_downloader import GithubReleaseDownloader
from .cmd import cmd_run

__all__ = [
    "install_pygame_ce_for_fantas",
    "PygameStatus",
    "delete_pygame_ce_for_fantas",
    "download_all_pygame_ce_for_fantas",
]

CWD = Path(__file__).parent.parent

PYGAME_CE_FOR_FANTAS_OWNER = "Fantastair"  # pygame-ce for fantas 仓库的所有者
PYGAME_CE_FOR_FANTAS_REPO = "pygame-ce"  # pygame-ce for fantas 仓库的名称

FANTAS_SOURCE_DIR = CWD / "fantas"  # fantas 项目的源代码目录

PYGAME_CE_FOR_FANTAS_INSTALL_DIR = (
    FANTAS_SOURCE_DIR / "_vendor"
)  # pygame-ce for fantas 的安装目录，安装后会在这个目录下生成一个 pygame 包


def delete_file_or_dir(path: Path) -> None:
    """
    删除指定路径的文件或目录
    """
    abs_path = path.resolve()

    if not abs_path.exists():
        return

    try:
        if abs_path.is_file() or abs_path.is_symlink():
            abs_path.unlink(missing_ok=True)
        elif abs_path.is_dir():
            shutil.rmtree(abs_path)
    except PermissionError:
        raise PermissionError(f"权限不足，无法删除：{abs_path}")
    except OSError as e:
        raise OSError(f"删除失败：{abs_path}，错误信息：{e}")


class PygameStatus(Enum):
    """
    PygameStatus 枚举定义了 pygame-ce (fantas 分支) 的安装状态。
    """

    NOT_INSTALLED = 0
    INSTALLED_CORRECTLY = 1
    INSTALLED_INCORRECTLY = 2


def install_pygame_ce_for_fantas(py: Path, tag: str | None = None) -> None:
    """
    安装 pygame-ce for fantas

    Args:
        py: Python 可执行文件的路径，用于安装 pygame-ce for fantas
        tag: 可选的 release tag，如果不指定则安装最新 release
    """
    pprint("安装 pygame-ce for fantas 中", prompt="dev")

    delete_pygame_ce_for_fantas()

    downloader = GithubReleaseDownloader(
        PYGAME_CE_FOR_FANTAS_OWNER, PYGAME_CE_FOR_FANTAS_REPO
    )

    downloaded_whl = downloader.auto_download_whl(tag)
    if downloaded_whl is not None:
        try:
            cmd_run(
                [
                    py,
                    "-m",
                    "pip",
                    "install",
                    downloaded_whl,
                    "--target",
                    PYGAME_CE_FOR_FANTAS_INSTALL_DIR,
                ]
            )
            return
        except subprocess.CalledProcessError:
            delete_file_or_dir(downloaded_whl)

    pprint(
        "通过 whl 文件安装 pygame-ce for fantas 失败，尝试下载并安装源代码",
        prompt="dev",
        col=Colors.WARNING,
    )

    downloaded_source = downloader.download_source_code(tag)
    if downloaded_source is not None:
        try:
            cmd_run(
                [
                    py,
                    "-m",
                    "pip",
                    "install",
                    downloaded_source,
                    "--target",
                    PYGAME_CE_FOR_FANTAS_INSTALL_DIR,
                ]
            )
            return
        except subprocess.CalledProcessError:
            delete_file_or_dir(downloaded_source)
            pass

    pprint(
        "通过 pip 安装 pygame-ce for fantas 失败，尝试使用 dev.py 安装",
        prompt="dev",
        col=Colors.WARNING,
    )

    if downloaded_source is not None:
        try:
            delete_file_or_dir(downloaded_source / "dist")
            cmd_run([py, "dev.py", "build", "--wheel"], cwd=downloaded_source)
            wheel_files = list((downloaded_source / "dist").glob("*.whl"))
            if wheel_files:
                cmd_run(
                    [
                        py,
                        "-m",
                        "pip",
                        "install",
                        wheel_files[0],
                        "--target",
                        PYGAME_CE_FOR_FANTAS_INSTALL_DIR,
                    ]
                )
                return
        except subprocess.CalledProcessError:
            pass

    pprint(
        "pygame-ce for fantas 安装失败，未找到兼容的 whl 文件，也无法下载并安装源代码",
        prompt="dev",
        col=Colors.ERROR,
    )
    sys.exit(1)


def delete_pygame_ce_for_fantas() -> None:
    """
    删除已安装的 pygame-ce for fantas
    """
    for path in PYGAME_CE_FOR_FANTAS_INSTALL_DIR.glob("pygame*/"):
        delete_file_or_dir(path)


def download_all_pygame_ce_for_fantas(tag: str | None, target_dir: Path) -> list[Path]:
    """
    下载 pygame-ce for fantas 的所有版本的 whl 文件
    """
    downloader = GithubReleaseDownloader(
        PYGAME_CE_FOR_FANTAS_OWNER, PYGAME_CE_FOR_FANTAS_REPO
    )
    return downloader.download_all_whl(tag, target_dir)
