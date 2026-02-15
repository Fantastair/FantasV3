"""
这个脚本旨在集成所有可能使用的项目开发指令

本脚本很大程度上学习于 pygame-ce 的 dev.py。感谢 pygame-ce 团队的辛勤工作！
"""

import os
import sys
import shutil
import argparse
import subprocess
from enum import Enum
from typing import Any
from pathlib import Path

CWD = Path(__file__).parent

PYGAME_CE_FANTAS_DIR = CWD / "pygame-ce-fantas"
PYGAME_CE_FANTAS_REPO = "https://github.com/Fantastair/pygame-ce.git"
PYGAME_CE_FANTAS_BRANCH = "fantas"

FANTAS_SOURCE_DIR = CWD / "fantas"


class Colors(Enum):
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


class PygameStatus(Enum):
    NOT_INSTALLED = 0
    INSTALLED_CORRECTLY = 1
    INSTALLED_INCORRECTLY = 2
    INSTALLED_PYGAME = 3


# 参考链接 https://docs.python.org/3.13/using/cmdline.html#controlling-color
def has_color() -> bool:
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
    pprint("检查 git 仓库状态中 (使用 git)")

    try:
        cmd_run(["git", "--no-pager", "status", "--porcelain"], error_on_output=True)
    except subprocess.CalledProcessError:
        pprint("当前 git 仓库存在未提交的更改，请先提交这些更改", Colors.RED)
        sys.exit(1)


def show_diff_and_help_commit(command: str) -> None:
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
    if not destination.parent.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)

    if not destination.exists():
        pprint("下载 Poetry 安装管理脚本中")
        import urllib.request

        urllib.request.urlretrieve("https://install.python-poetry.org/", destination)


def install_poetry() -> Path:
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
    pprint("安装项目依赖中 (使用 Poetry)")

    try:
        cmd_run([poetry_path, "install", "--no-root"])
    except subprocess.CalledProcessError as e:
        pprint("项目依赖安装失败", Colors.RED)
        raise e


def get_pygame_ce_fantas_status(py: Path) -> PygameStatus:
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
        pprint(f"- 或者手动执行命令：", Colors.MAGENTA)
        pprint(f"  git -C {PYGAME_CE_FANTAS_DIR} pull", Colors.CYAN)
        pprint(
            "更新 pygame-ce-fantas 仓库失败，请执行上述检查后重新运行 dev.py",
            Colors.RED,
        )
        sys.exit(1)


def build_and_install_pygame_ce_fantas(py: Path) -> None:
    pprint("安装 pygame-ce (fantas 分支版本) 中")
    try:
        cmd_run([py, "-m", "pip", "install", "."], cwd=PYGAME_CE_FANTAS_DIR)
    except subprocess.CalledProcessError as e:
        pprint("pygame-ce (fantas 分支版本) 安装失败", Colors.RED)
        raise e


def uninstall_pygame_ce_fantas(py: Path, status: PygameStatus) -> None:
    pprint(
        f"卸载 {'pygame' if status == PygameStatus.INSTALLED_PYGAME else 'pygame-ce'} 中 (使用 pip)"
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
            f"{'pygame' if status == PygameStatus.INSTALLED_PYGAME else 'pygame-ce'} 卸载失败",
            Colors.RED,
        )
        raise e


class Dev:
    def __init__(self) -> None:
        self.py: Path = Path(sys.executable)
        self.args: dict[str, Any] = {}

    # def cmd_install(self):
    #     pass

    # def cmd_build(self):
    #     pass

    # def cmd_update(self):
    #     pass

    # def cmd_docs(self, full: bool = None):
    #     full = self.args.get("full", False) if full is None else full

    #     pprint(f"生成文档中 (参数 {full=})")
    #     extra_args = ["full_generation"] if full else []
    #     cmd_run([self.py, "buildconfig/make_docs.py", *extra_args])

    #     if "CI" in os.environ:
    #         show_diff_and_help_commit("docs")

    def cmd_lint(self) -> None:
        pprint("检查代码中 (使用 pylint)")

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
        pprint("执行静态类型检查中 (使用 mypy)")

        cmd_run(
            [self.venv_py, "-m", "mypy", CWD, "--config-file", CWD / "pyproject.toml"]
        )

    def cmd_format(self) -> None:
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
        self.cmd_format()
        self.cmd_stubs()
        self.cmd_lint()
        # self.cmd_docs(full=self.args.full_docs)
        # self.cmd_test()
        # if self.args.install:
        #     self.cmd_install()
        # else:
        #     self.cmd_build()

    def parse_args(self) -> None:
        parser = argparse.ArgumentParser(
            description=(
                "项目开发命令集成。"
                "你可以在子命令后添加 -h/--help 来获取每个子命令的使用帮助。"
            )
        )
        subparsers = parser.add_subparsers(dest="command", help="子命令，默认为 auto")

        # install 命令
        subparsers.add_parser("install", help="构建并安装项目 (常规安装)")

        # build 命令
        subparsers.add_parser("build", help="构建并安装项目 (可编辑安装)")

        # update 命令
        subparsers.add_parser(
            "update", help="更新项目依赖和编译后端 (会清空大部分缓存)"
        )

        # docs 命令
        docs_parser = subparsers.add_parser("docs", help="生成文档")
        docs_parser.add_argument(
            "--full",
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
        pprint("准备虚拟环境中 (使用 Poetry)")

        cmd_run([self.poetry_path, "env", "use", self.py])
        venv_py = cmd_run(
            [self.poetry_path, "env", "info", "--path"], capture_output=True
        )
        if sys.platform == "win32":
            self.venv_py = Path(venv_py) / "Scripts" / "python.exe"
        else:
            self.venv_py = Path(venv_py) / "bin" / "python"

    def run(self) -> None:
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
            if not pygame_status == PygameStatus.INSTALLED_CORRECTLY:
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
