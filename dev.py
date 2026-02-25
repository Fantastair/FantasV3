"""
这个脚本旨在集成所有可能使用的项目开发指令。

本脚本最初很大程度上学习于 pygame-ce 的 dev.py。感谢 pygame-ce 团队的辛勤工作！
在此基础上做了很多现代化修改和功能解耦，增强脚本的可维护性和可复用性。
"""

import sys
import subprocess
from pathlib import Path
from functools import wraps
from typing import TypeAlias
from time import perf_counter_ns as get_time_ns

import typer
from typing_extensions import Annotated

from tools.pprint import pprint, Colors
from tools.cmd import cmd_run
from tools.install_poetry import get_poetry_executable, install_poetry
from tools.get_version import get_version
from tools.install_pygame import install_pygame_ce_for_fantas, PygameStatus

CWD = Path(__file__).parent

FANTAS_SOURCE_DIR = CWD / "fantas"  # fantas 项目的源代码目录
FANTAS_DIST_DIR = CWD / "dist"  # fantas 项目的构建输出目录


def check_git_clean() -> None:
    """
    检查当前 git 仓库是否存在未提交的更改，如果存在则提示用户先提交这些更改
    """
    pprint("检查 git 仓库状态中", prompt="dev")

    try:
        cmd_run(["git", "--no-pager", "status", "--porcelain"], error_on_output=True)
    except subprocess.CalledProcessError:
        pprint(
            "当前 git 仓库存在未提交的更改，请先提交这些更改",
            prompt="dev",
            col=Colors.WARNING,
        )
        sys.exit(1)

    pprint("git 仓库干净", prompt="dev", col=Colors.SUCCESS)


def show_diff_and_help_commit(command: str) -> None:
    """
    显示 git 仓库的更改，并询问用户是否需要自动提交这些更改
    """
    try:
        cmd_run(["git", "--no-pager", "status", "--porcelain"], error_on_output=True)
    except subprocess.CalledProcessError:
        pprint(f"运行 {command} 命令时产生了上述更改", prompt="dev", col=Colors.WARNING)
        pprint(
            "是否需要自动添加这些修改并提交一次commit？ (y/n)",
            prompt="dev",
            col=Colors.TIP,
        )

        answer = input().strip().lower()
        while answer not in ("y", "n"):
            pprint("请输入 y 或 n", prompt="dev", col=Colors.TIP)
            answer = input().strip().lower()

        if answer == "y":
            try:
                cmd_run(["git", "add", "."])
                cmd_run(["git", "commit", "-m", f"保存 {command} 命令产生的更改"])
                pprint(
                    "更改已提交，请重新运行 dev.py", prompt="dev", col=Colors.SUCCESS
                )
            except subprocess.CalledProcessError:
                pprint(
                    "自动提交失败，请手动检查更改并提交", prompt="dev", col=Colors.ERROR
                )
        else:
            pprint(
                "请手动检查更改并提交，然后重新运行 dev.py",
                prompt="dev",
                col=Colors.WARNING,
            )
        sys.exit(1)


def prep_poetry() -> Path:
    """
    准备 Poetry，确保后续命令可以使用 Poetry 来管理依赖

    Returns:
        Poetry 可执行文件的路径
    """
    pprint("准备 Poetry 中", prompt="dev")

    poetry_path = get_poetry_executable()
    if poetry_path is None:
        poetry_path = install_poetry()
    else:
        poetry_path = poetry_path

    pprint(f"Poetry 已就绪 ({poetry_path})", prompt="dev", col=Colors.SUCCESS)

    return poetry_path


def prep_venv(poetry_path: Path, py: Path) -> Path:
    """
    准备虚拟环境，确保后续命令在隔离的环境中运行
    """
    pprint("准备虚拟环境中", prompt="dev")

    cmd_run([poetry_path, "env", "use", py])
    venv_py = cmd_run([poetry_path, "env", "info", "--path"], capture_output=True)
    if sys.platform == "win32":
        venv_py = Path(venv_py) / "Scripts" / "python.exe"
    else:
        venv_py = Path(venv_py) / "bin" / "python"

    pprint(f"虚拟环境已就绪 ({venv_py})", prompt="dev", col=Colors.SUCCESS)

    return venv_py


def prep_pygame(py: Path) -> None:
    """
    准备 pygame-ce (fantas 分支)，确保后续命令可以使用正确版本的 pygame
    """
    required_version = get_version()

    pprint(f"准备 pygame-ce for fantas ({required_version}) 中", prompt="dev")

    pprint("检查安装状态", prompt="dev")
    status = PygameStatus.NOT_INSTALLED
    try:
        import fantas  # pylint: disable=import-outside-toplevel

        version = fantas.pygame.__version__  # pylint: disable=unused-variable
        if version == required_version:
            pprint("已安装", prompt="dev", col=Colors.SUCCESS)
            status = PygameStatus.INSTALLED_CORRECTLY
        else:
            pprint(
                f"版本不匹配 (安装的版本: {version}, 需要的版本: "
                f"{required_version})",
                prompt="dev",
                col=Colors.WARNING,
            )
            status = PygameStatus.INSTALLED_INCORRECTLY
    except ImportError:
        pprint("pygame-ce for fantas 未安装", prompt="dev", col=Colors.WARNING)
    except RuntimeError:
        pprint(
            "版本不匹配 (可能安装了 pygame 或 pygame-ce)",
            prompt="dev",
            col=Colors.WARNING,
        )
        status = PygameStatus.INSTALLED_INCORRECTLY

    if status != PygameStatus.INSTALLED_CORRECTLY:
        install_pygame_ce_for_fantas(py)

    pprint("pygame-ce for fantas 已就绪", prompt="dev", col=Colors.SUCCESS)


def prep_deps(poetry_path: Path) -> None:
    """
    使用 Poetry 安装项目依赖
    """
    pprint("安装开发环境依赖中", prompt="dev")

    try:
        cmd_run([poetry_path, "install", "--no-root"])
    except subprocess.CalledProcessError as e:
        pprint("项目依赖安装失败", prompt="dev", col=Colors.ERROR)
        raise e

    pprint("开发环境已就绪", prompt="dev", col=Colors.SUCCESS)


def prep_all() -> tuple[Path, Path]:
    """
    执行所有准备工作

    Returns:
        一个元组，包含 Poetry 可执行文件的路径和虚拟环境中 Python 可执行文件的路径
    """
    poetry_path = prep_poetry()
    venv_py = prep_venv(poetry_path, sys.executable)
    prep_pygame(venv_py)
    prep_deps(poetry_path)

    return poetry_path, venv_py


def show_time_spent(start_time: int, end_time: int, command: str) -> None:
    units = ("ns", "µs", "ms", "s")
    unit_index = 0
    elapsed_time: float = end_time - start_time
    while elapsed_time >= 1000 and unit_index < len(units) - 1:
        elapsed_time /= 1000
        unit_index += 1
    pprint(
        f"命令 '{command}' 执行成功, 耗时: {elapsed_time:.2f} " f"{units[unit_index]}",
        prompt="dev",
        col=Colors.SUCCESS,
    )


def _format(py: Path, ignore_git: bool) -> None:
    """
    执行 format 子命令，使用 black 格式化代码

    Args:
        py: Python 可执行文件的路径，用于运行 black
        ignore_git: 忽略 git 仓库状态检查
    """
    pprint("格式化代码中", prompt="dev")

    cmd_run([py, "-m", "black", "fantas", "tests", "tools", "dev.py"])

    if not ignore_git:
        show_diff_and_help_commit("format")

    pprint("代码已格式化", prompt="dev", col=Colors.SUCCESS)


def _stubs(py: Path) -> None:
    """
    执行 stubs 子命令，使用 mypy 进行静态类型检查

    Args:
        py: Python 可执行文件的路径，用于运行 mypy
    """
    pprint("执行静态类型检查中", prompt="dev")

    try:
        cmd_run([py, "-m", "mypy"])
    except subprocess.CalledProcessError:
        pprint("类型检查未通过，请检查", prompt="dev", col=Colors.ERROR)
        sys.exit(1)

    pprint("类型检查已通过", prompt="dev", col=Colors.SUCCESS)


def _lint(py: Path) -> None:
    """
    执行 lint 子命令，使用 pylint 进行代码质量检查

    Args:
        py: Python 可执行文件的路径，用于运行 pylint
    """
    pprint("分析代码质量中", prompt="dev")

    cmd_run([py, "-m", "pylint", "fantas", "--output-format=colorized"])

    pprint("代码质量检查已通过", prompt="dev", col=Colors.SUCCESS)


def _docs(py: Path, full: bool) -> None:
    """
    执行 docs 子命令，使用 Sphinx 生成文档
    """
    pprint(f"生成文档中 (参数 {full=})", prompt="dev")

    _static_dir = CWD / "docs" / "source" / "_static"
    _static_dir.mkdir(parents=True, exist_ok=True)
    _templates_dir = CWD / "docs" / "source" / "_templates"
    _templates_dir.mkdir(parents=True, exist_ok=True)

    cmd: list[str | Path] = [
        py,
        "-m",
        "sphinx",
        "-b",
        "html",
        "docs/source",
        "docs/build/html",
        "--quiet",
    ]
    if full:
        cmd.append("-E")
    try:
        cmd_run(cmd, error_on_output=True)
    except subprocess.CalledProcessError:
        pprint(
            "文档生成失败，请检查 Sphinx 输出的错误信息", prompt="dev", col=Colors.ERROR
        )
        sys.exit(1)

    pprint("文档已生成 (docs/build/html/index.html)", prompt="dev", col=Colors.SUCCESS)


def _test(py: Path, mod: list[Path]) -> None:
    """
    执行 test 子命令，使用 pytest 运行测试

    Args:
        py: Python 可执行文件的路径，用于运行 pytest
        mod: 要测试的模块路径列表，如果列表为空则测试所有模块
    """
    try:
        if mod:
            mods_arg = " ".join([m.name for m in mod])
            pprint(f"测试模块 ({mods_arg}) 中", prompt="dev")
            cmd_run([py, "-m", "pytest", *mod])
        else:
            pprint("测试所有模块中", prompt="dev")
            cmd_run([py, "-m", "pytest"])
    except subprocess.CalledProcessError:
        pprint("测试未通过，请检查", prompt="dev", col=Colors.ERROR)
        sys.exit(1)

    pprint("测试已通过", prompt="dev", col=Colors.SUCCESS)


def _build(poetry_path: Path, py: Path, target: Path, install: bool) -> None:
    """
    执行 build 子命令，使用 Poetry 构建项目

    Args:
        poetry_path: Poetry 可执行文件的路径，用于运行 Poetry 构建项目
        py: Python 可执行文件的路径，用于安装构建后的项目
    """
    pprint("构建项目中", prompt="dev")

    try:
        cmd_run(
            [
                poetry_path,
                "build",
                "-f",
                "wheel",
                "--clean",
                "--output",
                target,
                "--no-interaction",
            ]
        )
    except subprocess.CalledProcessError:
        pprint("项目构建失败", prompt="dev", col=Colors.ERROR)
        sys.exit(1)

    wheel_files = list(target.glob("*.whl"))
    if not wheel_files:
        pprint("未找到生成的 wheel 文件", prompt="dev", col=Colors.ERROR)
        sys.exit(1)

    pprint(f"项目已构建 ({wheel_files[0]})", prompt="dev", col=Colors.SUCCESS)

    if not install:
        return

    pprint("安装项目中 (常规安装)", prompt="dev")

    try:
        cmd_run([py, "-m", "pip", "install", wheel_files[0], "--force-reinstall"])
    except subprocess.CalledProcessError:
        pprint("项目安装失败", prompt="dev", col=Colors.ERROR)
        sys.exit(1)

    pprint(f"项目已安装 ({wheel_files[0]})", prompt="dev", col=Colors.SUCCESS)


def _install(poetry_path: Path) -> None:
    """
    执行 install 子命令，使用 Poetry 安装项目 (可编辑安装)
    """
    pprint("安装项目中 (可编辑安装)", prompt="dev")

    try:
        cmd_run([poetry_path, "install"])
    except subprocess.CalledProcessError:
        pprint("项目安装失败", prompt="dev", col=Colors.ERROR)
        sys.exit(1)

    pprint(
        f"项目已安装 (可编辑安装), 链接到 {FANTAS_SOURCE_DIR} 中的代码",
        prompt="dev",
        col=Colors.SUCCESS,
    )


app = typer.Typer(
    help="""
项目开发命令集成。你可以在子命令后添加 --help 来获取每个子命令的使用帮助。
""",
    add_completion=False,
)

IgnoreGitOption: TypeAlias = Annotated[
    bool, typer.Option("--ignore-git", "-i", help="忽略 git 仓库状态检查")
]


def command(func):

    @app.command()
    @wraps(func)
    def command_func(*args, ignore_git: IgnoreGitOption = False, **kwargs):
        start_time = get_time_ns()
        pprint(f"运行命令 '{func.__name__}'", prompt="dev", col=Colors.INFO)

        if not ignore_git:
            check_git_clean()

        result = func(*args, ignore_git=ignore_git, **kwargs)

        end_time = get_time_ns()
        show_time_spent(start_time, end_time, func.__name__)
        return result

    return command_func


@command
def format(ignore_git: IgnoreGitOption = False) -> None:
    """
    格式化代码
    """
    _, venv_py = prep_all()
    _format(venv_py, ignore_git)


@command
def stubs(ignore_git: IgnoreGitOption = False) -> None:
    """
    静态类型检查
    """
    if not ignore_git:
        check_git_clean()

    _, venv_py = prep_all()
    _stubs(venv_py)


@command
def lint(ignore_git: IgnoreGitOption = False) -> None:
    """
    代码质量检查
    """
    if not ignore_git:
        check_git_clean()

    _, venv_py = prep_all()
    _lint(venv_py)


@command
def docs(
    full: Annotated[
        bool, typer.Option("--full", "-f", help="重新生成完整文档，忽略之前的缓存")
    ] = False,
    ignore_git: IgnoreGitOption = False,
) -> None:
    """
    生成文档
    """
    if not ignore_git:
        check_git_clean()

    _, venv_py = prep_all()
    _docs(venv_py, full)


@command
def test(
    mod: Annotated[
        list[Path],
        typer.Argument(help="要测试的模块路径。如果不提供，则测试所有模块。"),
    ] = [],
    ignore_git: IgnoreGitOption = False,
) -> None:
    """
    运行测试
    """
    if not ignore_git:
        check_git_clean()

    _, venv_py = prep_all()
    _test(venv_py, mod)


@command
def build(
    target: Annotated[Path, typer.Argument(help="whl 文件输出目录")] = FANTAS_DIST_DIR,
    install: Annotated[
        bool, typer.Option(help="构建完成后安装项目 (常规安装)")
    ] = False,
    ignore_git: IgnoreGitOption = False,
) -> None:
    """
    构建项目
    """
    if not ignore_git:
        check_git_clean()

    poetry_path, venv_py = prep_all()
    _build(poetry_path, venv_py, target, install)


@command
def install(ignore_git: IgnoreGitOption = False) -> None:
    """
    安装项目 (可编辑安装)
    """
    if not ignore_git:
        check_git_clean()

    poetry_path, _ = prep_all()
    _install(poetry_path)


if __name__ == "__main__":
    app()
