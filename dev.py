"""
这个脚本旨在集成所有可能使用的项目开发指令。

本脚本很大程度上学习于 pygame-ce 的 dev.py。感谢 pygame-ce 团队的辛勤工作！
"""

import os
import re
import sys
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


# 参考链接 https://docs.python.org/3.13/using/cmdline.html#controlling-color
def has_color():
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


def pprint(arg: str, col: Colors = Colors.YELLOW):
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


def show_diff_and_help_commit(command: str):
    try:
        cmd_run(["git", "status", "--porcelain", "--no-pager"], error_on_output=True)
    except subprocess.CalledProcessError:
        try:
            cmd_run(["git", "diff", "--no-pager"])
        finally:
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


def is_poetry_installed():
    pprint("检查 Poetry 是否安装中")
    try:
        # 命令行检查
        result = subprocess.run(
            ["poetry", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return "Poetry (version" in result.stdout

    except (subprocess.CalledProcessError, FileNotFoundError):
        # 如果命令行检查失败，尝试在常见路径中查找 Poetry 可执行文件
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
                os.environ["PATH"] += os.pathsep + os.path.dirname(path)
                return True
        return False


def download_poetry_install_script(destination: Path):
    if not destination.parent.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)

    if not destination.exists():
        pprint("下载 Poetry 安装管理脚本中")
        import urllib.request

        urllib.request.urlretrieve("https://install.python-poetry.org/", destination)


def install_poetry():
    pprint("安装 Poetry 中")

    install_poetry_script_path = CWD / "tmp" / "install_poetry.py"
    download_poetry_install_script(install_poetry_script_path)

    error = False
    try:
        cmd_run([sys.executable, install_poetry_script_path, "-y"])
    except subprocess.CalledProcessError:
        error = True

    if error or not is_poetry_installed():
        pprint("Poetry 安装失败，请手动安装 Poetry 后重试", Colors.RED)
        sys.exit(1)
    pprint("Poetry 安装成功", Colors.GREEN)


def uninstall_poetry():
    pprint("卸载 Poetry 中")

    install_poetry_script_path = CWD / "tmp" / "install_poetry.py"
    download_poetry_install_script(install_poetry_script_path)

    error = False
    try:
        cmd_run([sys.executable, install_poetry_script_path, "-y", "--uninstall"])
    except subprocess.CalledProcessError:
        error = True

    if error or is_poetry_installed():
        pprint("Poetry 卸载失败，请手动卸载 Poetry 后重试", Colors.RED)
        sys.exit(1)
    pprint("Poetry 卸载成功", Colors.GREEN)


def poetry_install_dependencies():
    pprint("安装项目依赖中 (使用 Poetry)")

    try:
        cmd_run(["poetry", "install", "--no-root"])
    except subprocess.CalledProcessError as e:
        pprint("项目依赖安装失败", Colors.RED)
        raise e


def get_pygame_ce_fantas_status(py: Path) -> PygameStatus:
    pprint("检查 pygame-ce (fantas 分支版本) 安装状态中")

    check_script_path = CWD / "tmp" / "check_pygame_ce_fantas.py"

    if not check_script_path.parent.exists():
        check_script_path.parent.mkdir(parents=True, exist_ok=True)

    if not check_script_path.exists():
        check_script_path.write_text(
            """
import os
import sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
try:
    import pygame
except ImportError:
    print('0')    # pygame 未安装
    sys.exit(0)
if getattr(pygame, 'IS_FANTAS', False):
    print('1')    # pygame 正确安装
else:
    print('2')    # pygame 版本不正确
"""
        )

    output = cmd_run([py, check_script_path], capture_output=True)
    status = PygameStatus(int(output))

    if status == PygameStatus.NOT_INSTALLED:
        pprint("pygame 未安装")
    elif status == PygameStatus.INSTALLED_CORRECTLY:
        pprint("pygame-ce (fantas 分支版本) 已正确安装", Colors.GREEN)
    else:
        pprint("pygame 已安装但版本不正确", Colors.RED)

    return status


def check_and_update_pygame_ce_fantas():
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
        pprint(f"- 或者手动执行命令：git -C {PYGAME_CE_FANTAS_DIR} pull", Colors.CYAN)
        pprint(
            "更新 pygame-ce-fantas 仓库失败，请执行上述检查后重新运行 dev.py",
            Colors.RED,
        )
        sys.exit(1)


def build_and_install_pygame_ce_fantas(py: Path):
    pprint("构建并安装 pygame-ce (fantas 分支版本) 中 (第一次构建可能会比较慢)")

    try:
        cmd_run(
            [py, "dev.py", "build", "--wheel", "--stripped"], cwd=PYGAME_CE_FANTAS_DIR
        )
    except subprocess.CalledProcessError as e:
        pprint("构建或安装 pygame-ce (fantas 分支版本) 失败", Colors.RED)
        raise e


def uninstall_pygame_ce_fantas(py: Path):
    pprint("卸载 pygame 中 (使用 pip)")
    try:
        cmd_run([py, "-m", "pip", "uninstall", "-y", "pygame"])
    except subprocess.CalledProcessError as e:
        pprint("pygame 卸载失败", Colors.RED)
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

    # def cmd_lint(self):
    #     pprint("检查代码中 (使用 pylint)")

    #     cmd_run([self.py, "-m", "pylint", "fantas", "docs"])

    # def cmd_stubs(self):
    #     pprint("生成并校验类型提示中 (使用 mypy)")

    #     cmd_run([self.py, "buildconfig/stubs/gen_stubs.py"])

    #     show_diff_and_help_commit("stubs")

    #     cmd_run([self.py, "buildconfig/stubs/stubcheck.py"])

    def cmd_format(self):
        pprint("格式化代码中 (使用 black)")

        cmd_run([self.venv_py, "-m", "black", "."])

        show_diff_and_help_commit("format")

    # def cmd_test(self):
    #     mod = self.args.get("mod", [])

    #     if mod:
    #         pprint(f"测试模块 ({' '.join(mod)}) 中")
    #         for i in mod:
    #             cmd_run([self.py, "-m", f"fantas.tests.{i}_test"])
    #     else:
    #         pprint("测试所有模块中")
    #         cmd_run([self.py, "-m", "fantas.tests"])

    def cmd_auto(self):
        self.cmd_format()
        # self.cmd_docs(full=self.args.full_docs)
        # self.cmd_stubs()
        # self.cmd_lint()
        # self.cmd_test()
        # if self.args.install:
        #     self.cmd_install()
        # else:
        #     self.cmd_build()

    def parse_args(self):
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

    def prep_venv(self):
        pprint("准备虚拟环境中 (使用 Poetry)")

        cmd_run(["poetry", "env", "use", self.py])
        venv_py = cmd_run(["poetry", "env", "info", "--path"], capture_output=True)
        if sys.platform == "win32":
            self.venv_py = Path(venv_py) / "Scripts" / "python.exe"
        else:
            self.venv_py = Path(venv_py) / "bin" / "python"

    def run(self):
        self.parse_args()

        pprint(f"运行子命令 '{self.args['command']}'")

        try:
            if not is_poetry_installed():
                install_poetry()

            self.prep_venv()

            pygame_status = get_pygame_ce_fantas_status(self.venv_py)
            if not pygame_status == PygameStatus.INSTALLED_CORRECTLY:
                if pygame_status == PygameStatus.INSTALLED_INCORRECTLY:
                    uninstall_pygame_ce_fantas(self.venv_py)
                check_and_update_pygame_ce_fantas()
                build_and_install_pygame_ce_fantas(self.venv_py)

            poetry_install_dependencies()

            func = getattr(self, f"cmd_{self.args['command']}")
            func()
        except subprocess.CalledProcessError as e:
            pprint(f"程序异常退出，错误代码 {e.returncode}", Colors.RED)
            sys.exit(e.returncode)
        except KeyboardInterrupt:
            pprint("程序被用户中断", Colors.RED)
            sys.exit(1)

        pprint("命令执行成功", Colors.GREEN)


if __name__ == "__main__":
    Dev().run()
