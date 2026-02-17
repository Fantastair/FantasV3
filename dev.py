"""
这个脚本旨在集成所有可能使用的项目开发指令

本脚本很大程度上学习于 pygame-ce 的 dev.py。感谢 pygame-ce 团队的辛勤工作！
"""

import os
import sys
import argparse
import subprocess
import urllib.request
from enum import Enum
from typing import Any
from pathlib import Path

CWD = Path(__file__).parent

PYGAME_CE_FANTAS_DIR = CWD / "pygame-ce-fantas"
PYGAME_CE_FANTAS_REPO = "https://github.com/Fantastair/pygame-ce.git"
PYGAME_CE_FANTAS_BRANCH = "fantas"

FANTAS_SOURCE_DIR = CWD / "fantas"


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


class PygameStatus(Enum):
    """
    PygameStatus 枚举定义了 pygame-ce (fantas 分支版本) 的安装状态。
    """

    NOT_INSTALLED = 0
    INSTALLED_CORRECTLY = 1
    INSTALLED_INCORRECTLY = 2
    INSTALLED_PYGAME = 3


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


def pprint(arg: str, col: Colors = Colors.YELLOW) -> None:
    """
    pprint 函数用于在终端中打印带有颜色的消息。它根据环境变量和参数决定是否使用颜色，
    并且在输出前添加 [dev.py] 前缀以标识消息来源。
    """
    do_col = has_color()
    start = Colors.BLUE.value if do_col else ""
    mid = col.value if do_col else ""
    end = Colors.RESET.value if do_col else ""
    print(f"{start}[dev.py] {mid}{arg}{end}", flush=True)


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
    pprint(f"> {' '.join(norm_cmd)}", Colors.CYAN)
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
        pprint(f"{norm_cmd[0]}: 未找到指令", Colors.RED)
        sys.exit(1)

    if ret.stdout:
        print(ret.stdout, end="", flush=True)

    if (error_on_output and ret.stdout) and not ret.returncode:
        # 如果有 stdout 并且存在错误，则设置返回代码为 1
        ret.returncode = 1

    ret.check_returncode()
    return ret.stdout.strip() if capture_output else ""


def check_git_clean() -> None:
    """
    检查当前 git 仓库是否存在未提交的更改，如果存在则提示用户先提交这些更改
    """
    pprint("检查 git 仓库状态中 (使用 git)")

    try:
        cmd_run(["git", "--no-pager", "status", "--porcelain"], error_on_output=True)
    except subprocess.CalledProcessError:
        pprint("当前 git 仓库存在未提交的更改，请先提交这些更改", Colors.RED)
        sys.exit(1)


def show_diff_and_help_commit(command: str) -> None:
    """
    显示 git 仓库的更改，并提示用户是否需要自动提交这些更改以继续运行 dev.py
    """
    try:
        cmd_run(["git", "--no-pager", "status", "--porcelain"], error_on_output=True)
    except subprocess.CalledProcessError:
        pprint(f"运行 {command} 命令时产生了上述更改", Colors.RED)
        pprint("是否需要自动添加这些修改并提交一次commit？ (y/n)", Colors.RED)

        answer = input().strip().lower()
        while answer not in ("y", "n"):
            pprint("请输入 y 或 n", Colors.RED)
            answer = input().strip().lower()

        if answer == "y":
            try:
                cmd_run(["git", "add", "."])
                cmd_run(["git", "commit", "-m", f"保存 {command} 命令产生的更改"])
                pprint("更改已提交，请重新运行 dev.py", Colors.GREEN)
            except subprocess.CalledProcessError:
                pprint("自动提交失败，请手动检查更改并提交", Colors.RED)
        else:
            pprint("请手动检查更改并提交，然后重新运行 dev.py", Colors.YELLOW)
        sys.exit(1)


def get_poetry_executable() -> Path | None:
    """
    查找 Poetry 可执行文件的路径，首先尝试通过命令行查找，如果失败则遍历常见安装路径
    """
    pprint("查找 Poetry 可执行文件中")
    try:
        # 命令行查找
        subprocess.run(
            ["poetry", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        if sys.platform == "win32":
            poetry_path = cmd_run(["where", "poetry"], capture_output=True)
        else:
            poetry_path = cmd_run(["which", "poetry"], capture_output=True)
        if poetry_path and Path(poetry_path).exists():
            return Path(poetry_path)

    except (subprocess.CalledProcessError, FileNotFoundError):
        # 命令行查找失败，遍历常见路径
        poetry_paths = [
            Path.home() / ".local/bin/poetry",
            Path.home() / ".local/share/pypoetry/venv/bin/poetry",
            Path.home() / ".local/share/pypoetry/venv/Scripts/poetry",
            Path(os.environ.get("APPDATA", Path.home()))
            / "pypoetry/venv/Scripts/poetry",
            Path("/usr/local/bin/poetry"),
            Path("/usr/bin/poetry"),
        ]

        for path in poetry_paths:
            if path.exists() and os.access(path, os.X_OK):
                pprint(f"找到 Poetry 可执行文件：{path}", Colors.GREEN)
                return path
    pprint("未找到 Poetry 可执行文件", Colors.RED)
    return None


def download_poetry_install_script(destination: Path) -> None:
    """
    下载 Poetry 安装管理脚本到指定路径
    """
    if not destination.parent.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)

    if not destination.exists():
        pprint("下载 Poetry 安装管理脚本中")

        urllib.request.urlretrieve("https://install.python-poetry.org/", destination)


def install_poetry() -> Path:
    """
    安装 Poetry，并返回 Poetry 可执行文件的路径
    """
    pprint("安装 Poetry 中")

    install_poetry_script_path = CWD / "tools" / "install_poetry.py"
    download_poetry_install_script(install_poetry_script_path)

    error = False
    try:
        cmd_run([sys.executable, install_poetry_script_path, "-y"])
    except subprocess.CalledProcessError:
        error = True

    path = get_poetry_executable()

    if error or path is None:
        pprint("Poetry 安装失败，请手动安装 Poetry 后重试", Colors.RED)
        sys.exit(1)
    pprint("Poetry 安装成功", Colors.GREEN)

    return path


def uninstall_poetry() -> None:
    """
    卸载 Poetry
    """
    pprint("卸载 Poetry 中")

    install_poetry_script_path = CWD / "tools" / "install_poetry.py"
    download_poetry_install_script(install_poetry_script_path)

    error = False
    try:
        cmd_run([sys.executable, install_poetry_script_path, "-y", "--uninstall"])
    except subprocess.CalledProcessError:
        error = True

    if error or get_poetry_executable() is not None:
        pprint("Poetry 卸载失败，请手动卸载 Poetry 后重试", Colors.RED)
        sys.exit(1)
    pprint("Poetry 卸载成功", Colors.GREEN)


def poetry_install_dependencies(poetry_path: Path) -> None:
    """
    使用 Poetry 安装项目依赖
    """
    pprint("安装项目其他依赖中 (使用 Poetry)")

    try:
        cmd_run([poetry_path, "install", "--no-root"])
    except subprocess.CalledProcessError as e:
        pprint("项目依赖安装失败", Colors.RED)
        raise e


def get_pygame_ce_fantas_status(py: Path) -> PygameStatus:
    """
    检查 pygame-ce (fantas 分支版本) 的安装状态，返回 PygameStatus 枚举值
    """
    pprint("检查 pygame-ce (fantas 分支版本) 安装状态中")

    check_script_path = CWD / "tools" / "check_pygame_ce_fantas.py"

    if not check_script_path.parent.exists():
        check_script_path.parent.mkdir(parents=True, exist_ok=True)

    if not check_script_path.exists():
        check_script_path.write_text(
            """import os
import sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
try:
    import pygame
except ImportError:
    print('0')    # pygame 未安装
    sys.exit(0)
if getattr(pygame, 'IS_CE', False):
    if getattr(pygame, 'IS_FANTAS', False):
        print('1')    # pygame-ce 正确安装
    else:
        print('2')    # pygame-ce 版本不正确
else:
    print('3')    # 安装了非 pygame-ce
"""
        )

    output = cmd_run([py, check_script_path], capture_output=True)
    status = PygameStatus(int(output))

    if status == PygameStatus.NOT_INSTALLED:
        pprint("pygame 未安装")
    elif status == PygameStatus.INSTALLED_CORRECTLY:
        pprint("pygame-ce (fantas 分支版本) 已正确安装", Colors.GREEN)
    elif status == PygameStatus.INSTALLED_INCORRECTLY:
        pprint("pygame-ce 已安装但版本不正确", Colors.RED)
    elif status == PygameStatus.INSTALLED_PYGAME:
        pprint("安装了非 pygame-ce 版本的 pygame", Colors.RED)

    return status


def check_and_update_pygame_ce_fantas() -> None:
    """
    检查 pygame-ce-fantas 仓库是否存在并且在正确的分支上，如果不存在则克隆仓库，
    如果存在但不在正确的分支上则切换分支，并且拉取最新的提交
    """
    pprint("检查 pygame-ce-fantas 仓库中 (使用 git)")

    if not PYGAME_CE_FANTAS_DIR.exists():
        pprint("下载 pygame-ce-fantas 仓库中")

        try:
            cmd_run(
                [
                    "git",
                    "clone",
                    "-b",
                    PYGAME_CE_FANTAS_BRANCH,
                    PYGAME_CE_FANTAS_REPO,
                    str(PYGAME_CE_FANTAS_DIR),
                ]
            )
        except subprocess.CalledProcessError:
            pprint("- 请检查网络连接，是否能访问 GitHub", Colors.MAGENTA)
            pprint("- 或者手动执行命令：", Colors.MAGENTA)
            pprint(
                f"  git clone -b {PYGAME_CE_FANTAS_BRANCH}"
                f" {PYGAME_CE_FANTAS_REPO} {PYGAME_CE_FANTAS_DIR}",
                Colors.CYAN,
            )
            pprint(
                "下载 pygame-ce-fantas 仓库失败，请执行上述检查后重新运行 dev.py",
                Colors.RED,
            )
            sys.exit(1)
    else:
        try:
            branch = cmd_run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                cwd=PYGAME_CE_FANTAS_DIR,
            ).strip()
            if branch != PYGAME_CE_FANTAS_BRANCH:
                pprint(f"切换分支 {branch} -> {PYGAME_CE_FANTAS_BRANCH}")
                cmd_run(
                    ["git", "checkout", PYGAME_CE_FANTAS_BRANCH],
                    cwd=PYGAME_CE_FANTAS_DIR,
                )
        except subprocess.CalledProcessError:
            pprint("- 请检查是否安装 git", Colors.MAGENTA)
            pprint("- 或者手动执行命令：", Colors.MAGENTA)
            pprint(
                f"  git -C {PYGAME_CE_FANTAS_DIR}"
                f" checkout {PYGAME_CE_FANTAS_BRANCH}",
                Colors.CYAN,
            )
            pprint("切换分支失败，请执行上述检查后重新运行 dev.py", Colors.RED)
            sys.exit(1)

    pprint("更新 pygame-ce-fantas 仓库中 (使用 git)")
    try:
        cmd_run(["git", "pull"], cwd=PYGAME_CE_FANTAS_DIR)
    except subprocess.CalledProcessError:
        pprint("- 请检查网络连接，是否能访问 GitHub", Colors.MAGENTA)
        pprint("- 或者手动执行命令：", Colors.MAGENTA)
        pprint(f"  git -C {PYGAME_CE_FANTAS_DIR} pull", Colors.CYAN)
        pprint(
            "更新 pygame-ce-fantas 仓库失败，请执行上述检查后重新运行 dev.py",
            Colors.RED,
        )
        sys.exit(1)


def build_and_install_pygame_ce_fantas(py: Path) -> None:
    """
    构建并安装 pygame-ce (fantas 分支版本)
    """
    pprint("安装 pygame-ce (fantas 分支版本) 中")
    try:
        cmd_run([py, "-m", "pip", "install", "."], cwd=PYGAME_CE_FANTAS_DIR)
    except subprocess.CalledProcessError as e:
        pprint("pygame-ce (fantas 分支版本) 安装失败", Colors.RED)
        raise e


def uninstall_pygame_ce_fantas(py: Path, status: PygameStatus) -> None:
    """
    卸载 pygame 或 pygame-ce
    """
    pprint(
        f"卸载 {'pygame' if status == PygameStatus.INSTALLED_PYGAME else 'pygame-ce'}"
        " 中 (使用 pip)"
    )
    try:
        cmd_run(
            [
                py,
                "-m",
                "pip",
                "uninstall",
                "-y",
                "pygame" if status == PygameStatus.INSTALLED_PYGAME else "pygame-ce",
            ]
        )
    except subprocess.CalledProcessError as e:
        pprint(
            f"{'pygame' if status == PygameStatus.INSTALLED_PYGAME else 'pygame-ce'}"
            " 卸载失败",
            Colors.RED,
        )
        raise e


def delete_directory(path: Path) -> None:
    """
    删除一个目录及其所有内容
    """
    if path.is_dir():
        for item in path.iterdir():
            if item.is_dir():
                delete_directory(item)
            else:
                item.unlink()
        path.rmdir()


class Dev:
    """
    Dev 类封装了所有开发相关的命令和流程。它负责解析命令行参数，准备虚拟环境，
    检查和安装依赖，并执行对应的子命令。
    """

    def __init__(self) -> None:
        self.py: Path = Path(sys.executable)
        self.venv_py: Path
        self.poetry_path: Path
        self.args: dict[str, Any] = {}

    def parse_args(self) -> None:
        """
        解析命令行参数，设置 self.args 字典
        """
        parser = argparse.ArgumentParser(
            description=(
                "项目开发命令集成。"
                "你可以在子命令后添加 -h/--help 来获取每个子命令的使用帮助。"
            )
        )
        subparsers = parser.add_subparsers(dest="command", help="子命令，默认为 auto")

        # build 命令
        build_parser = subparsers.add_parser(
            "build", help="构建并安装项目 (默认为可编辑安装)"
        )
        build_parser.add_argument(
            "--install", action="store_true", help="使用常规安装而不是可编辑安装"
        )

        # update 命令
        subparsers.add_parser(
            "update", help="更新项目依赖和编译后端 (会清空大部分缓存)"
        )

        # docs 命令
        docs_parser = subparsers.add_parser("docs", help="生成文档")
        docs_parser.add_argument(
            "--full",
            "--full-docs",
            action="store_true",
            help=("强制生成完整文档，忽略之前的缓存。"),
        )

        # test 命令
        test_parser = subparsers.add_parser("test", help="运行测试")
        test_parser.add_argument(
            "mod",
            nargs="*",
            help=("要测试的模块名称列表。如果不提供任何模块，将测试所有模块。"),
        )

        # lint 命令
        subparsers.add_parser("lint", help="检查代码")

        # stubs 命令
        subparsers.add_parser("stubs", help="生成并校验类型提示")

        # format 命令
        subparsers.add_parser("format", help="格式化代码")

        # auto 命令
        auto_parser = subparsers.add_parser(
            "auto", help="自动运行所有检查和测试，然后构建并安装项目"
        )
        auto_parser.add_argument(
            "--full-docs",
            action="store_true",
            help="强制生成完整文档，忽略之前的缓存。",
        )
        auto_parser.add_argument(
            "--install", action="store_true", help="使用常规安装而不是可编辑安装"
        )

        # clean 命令
        subparsers.add_parser("clean", help="清理项目构建缓存和临时文件")

        # remove 命令
        remove_parser = subparsers.add_parser("remove", help="移除整个项目")
        remove_parser.add_argument(
            "--include-venv", "-i-v", action="store_true", help="是否同时移除虚拟环境"
        )

        args = parser.parse_args()
        self.args = vars(args)

        # 如果没有指定子命令，则默认为 auto
        if not self.args["command"]:
            self.args["command"] = "auto"

    def prep_venv(self) -> None:
        """
        准备虚拟环境，确保后续命令在隔离的环境中运行
        """
        pprint("准备虚拟环境中 (使用 Poetry)")

        cmd_run([self.poetry_path, "env", "use", self.py])
        venv_py = cmd_run(
            [self.poetry_path, "env", "info", "--path"], capture_output=True
        )
        if sys.platform == "win32":
            self.venv_py = Path(venv_py) / "Scripts" / "python.exe"
        else:
            self.venv_py = Path(venv_py) / "bin" / "python"

    # def cmd_build(self):
    #     pass

    # def cmd_update(self):
    #     pass

    def cmd_docs(self) -> None:
        """
        执行 docs 子命令，使用 Sphinx 生成文档
        """
        full = self.args.get("full", False)

        pprint(f"生成文档中 (参数 {full=})")

        cmd: list[str | Path] = [
            self.venv_py,
            "-m",
            "sphinx",
            "-b",
            "html",
            "docs/source",
            "docs/build/html",
        ]
        if full:
            cmd.append("-E")
        try:
            cmd_run(cmd, error_on_output=True)
        except subprocess.CalledProcessError:
            pprint("文档生成失败，请检查 Sphinx 输出的错误信息", Colors.RED)
            sys.exit(1)

    def cmd_lint(self) -> None:
        """
        执行 lint 子命令，使用 pylint 进行代码质量检查
        """
        pprint("分析代码质量中 (使用 pylint)")

        cmd_run(
            [
                self.venv_py,
                "-m",
                "pylint",
                "fantas",
                "--output-format=colorized",
            ]
        )

    def cmd_stubs(self) -> None:
        """
        执行 stubs 子命令，使用 mypy 进行静态类型检查
        """
        pprint("执行静态类型检查中 (使用 mypy)")

        cmd_run(
            [self.venv_py, "-m", "mypy", CWD, "--config-file", CWD / "pyproject.toml"]
        )

    def cmd_format(self) -> None:
        """
        执行 format 子命令，使用 black 格式化代码
        """
        pprint("格式化代码中 (使用 black)")

        cmd_run([self.venv_py, "-m", "black", "."])

        # show_diff_and_help_commit("format")

    # def cmd_test(self):
    #     mod = self.args.get("mod", [])

    #     if mod:
    #         pprint(f"测试模块 ({' '.join(mod)}) 中")
    #         for i in mod:
    #             cmd_run([self.py, "-m", f"fantas.tests.{i}_test"])
    #     else:
    #         pprint("测试所有模块中")
    #         cmd_run([self.py, "-m", "fantas.tests"])

    def cmd_auto(self) -> None:
        """
        自动运行所有检查和测试，然后构建并安装项目
        """
        self.cmd_format()
        self.cmd_stubs()
        self.cmd_lint()
        self.cmd_docs()
        # self.cmd_test()
        # if self.args.install:
        #     self.cmd_install()
        # else:
        #     self.cmd_build()

    def cmd_clean(self) -> None:
        """
        清理项目构建缓存和临时文件
        """
        pprint("清理项目构建缓存和临时文件中")

        for pattern in ("build", "tmp", ".mypy_cache", "__pycache__"):
            for path in CWD.glob(f"**/{pattern}"):
                delete_directory(path)

    def run(self) -> None:
        """
        运行开发命令的主流程
        """
        # check_git_clean()

        self.parse_args()

        pprint(f"运行子命令 '{self.args['command']}'")

        try:
            poetry_path = get_poetry_executable()
            if poetry_path is None:
                self.poetry_path = install_poetry()
            else:
                self.poetry_path = poetry_path

            self.prep_venv()

            pygame_status = get_pygame_ce_fantas_status(self.venv_py)
            if pygame_status != PygameStatus.INSTALLED_CORRECTLY:
                if pygame_status == PygameStatus.INSTALLED_INCORRECTLY:
                    uninstall_pygame_ce_fantas(self.venv_py, pygame_status)
                check_and_update_pygame_ce_fantas()
                build_and_install_pygame_ce_fantas(self.venv_py)

            poetry_install_dependencies(self.poetry_path)

            func = getattr(self, f"cmd_{self.args['command']}")
            func()

        except subprocess.CalledProcessError as e:
            pprint(f"程序异常退出，错误代码 {e.returncode}", Colors.RED)
            sys.exit(e.returncode)
        except KeyboardInterrupt:
            pprint("程序被用户中断", Colors.RED)
            sys.exit(1)

        pprint(f"子命令 '{self.args['command']}' 执行成功", Colors.GREEN)


if __name__ == "__main__":
    Dev().run()
