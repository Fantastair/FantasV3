"""
这个脚本旨在集成所有可能使用的项目开发指令

本脚本很大程度上学习于 pygame-ce 的 dev.py。感谢 pygame-ce 团队的辛勤工作！
"""

import os
import re
import sys
import argparse
import subprocess
import urllib.request
from enum import Enum
from typing import Any
from pathlib import Path
from time import perf_counter_ns as get_time_ns

CWD = Path(__file__).parent

PYGAME_CE_FANTAS_SRCDIR = CWD / "pygame-ce-fantas"
PYGAME_CE_FANTAS_REPO = "https://github.com/Fantastair/pygame-ce.git"
PYGAME_CE_FANTAS_BRANCH = "fantas"

FANTAS_SOURCE_DIR = CWD / "fantas"

PYGAME_CE_FANTAS_INSTALL_DIR = FANTAS_SOURCE_DIR / "_vendor"
PYGAME_COMMIT_HASH_FILE = FANTAS_SOURCE_DIR / "_vendor" / "pygame" / "commit_hash"
PYGAME_LOCK_HASH_FILE = CWD / "pygame.lock"

DIST_DIR = CWD / "dist"


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
    PygameStatus 枚举定义了 pygame-ce (fantas 分支) 的安装状态。
    """

    NOT_INSTALLED = 0
    INSTALLED_CORRECTLY = 1
    INSTALLED_INCORRECTLY = 2


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


def get_poetry_executable() -> Path | None:
    """
    查找 Poetry 可执行文件的路径，首先尝试通过命令行查找，如果失败则遍历常见安装路径
    """
    pprint("- 查找 Poetry 可执行文件")
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


def get_pygame_commit_hash(path: Path) -> str | None:
    """
    从文件中读取 commit 哈希值，如果文件不存在或者格式不正确则返回 None
    """
    if not path.exists():
        return None

    with path.open() as f:
        content = f.read()
        match = re.search(r'commit_hash\s*=\s*"([a-fA-F0-9]+)"', content)
        if match:
            return match.group(1)
    return None


def set_pygame_commit_hash(path: Path, commit_hash: str) -> None:
    """
    将 commit 哈希值写入文件，如果文件不存在则创建文件
    """
    content = f'''# pygame-ce for fantas 的版本锁定文件，不需要手动修改
commit_hash = "{commit_hash}"'''
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(content)


def delete_pygame_ce_for_fantas() -> None:
    """
    删除 pygame-ce for fantas
    """
    for path in FANTAS_SOURCE_DIR.glob("pygame*/"):
        delete_file_or_dir(path)


def checkout_pygame_ce_for_fantas(commit_hash: str | None) -> None:
    """
    切换到指定版本的 pygame-ce for fantas
    """
    pprint("- 检查 pygame-ce for fantas 源代码")

    if not PYGAME_CE_FANTAS_SRCDIR.exists():
        pprint("  # 下载源代码", Colors.RED)
        try:
            cmd_run(
                [
                    "git",
                    "clone",
                    "-b",
                    PYGAME_CE_FANTAS_BRANCH,
                    PYGAME_CE_FANTAS_REPO,
                    PYGAME_CE_FANTAS_SRCDIR,
                ]
            )
        except subprocess.CalledProcessError:
            pprint("  * 请检查网络连接，是否能访问 GitHub", Colors.MAGENTA)
            pprint("  * 或者手动执行命令：", Colors.MAGENTA)
            pprint(
                f"  > git clone -b {PYGAME_CE_FANTAS_BRANCH}"
                f" {PYGAME_CE_FANTAS_REPO} {PYGAME_CE_FANTAS_SRCDIR}",
                Colors.CYAN,
            )
            pprint(
                "下载 pygame-ce-fantas 仓库失败，请执行上述检查后重新运行 dev.py",
                Colors.RED,
            )
            sys.exit(1)
    pprint(
        f"  # 源代码已下载，切换到版本 {commit_hash[:7] if commit_hash else '最新'}",
        Colors.GREEN,
    )
    try:
        cmd_run(
            ["git", "pull", "origin", PYGAME_CE_FANTAS_BRANCH],
            cwd=PYGAME_CE_FANTAS_SRCDIR,
        )
        if commit_hash is not None:
            cmd_run(
                ["git", "-c", "advice.detachedHead=false", "checkout", commit_hash],
                cwd=PYGAME_CE_FANTAS_SRCDIR,
            )
    except subprocess.CalledProcessError:
        pprint("  * 请检查网络连接，是否能访问 GitHub", Colors.MAGENTA)
        pprint("  * 或者手动执行命令：", Colors.MAGENTA)
        pprint(
            f"  > git -c advice.detachedHead=false checkout {commit_hash} && git pull"
            f" origin {PYGAME_CE_FANTAS_BRANCH}",
            Colors.CYAN,
        )
        pprint(
            f"切换到版本 {commit_hash[:7] if commit_hash else '最新'} 失败，请执行上述"
            "检查后重新运行 dev.py",
            Colors.RED,
        )
        sys.exit(1)

    pprint("  pygame-ce for fantas 源代码已就绪", Colors.GREEN)


def install_pygame_ce_for_fantas(py: Path, commit_hash: str | None) -> str:
    """
    安装 pygame-ce for fantas
    """
    checkout_pygame_ce_for_fantas(commit_hash)

    pprint(
        f"- 安装 pygame-ce for fantas ({commit_hash[:7] if commit_hash else '最新'})"
    )

    delete_pygame_ce_for_fantas()
    try:
        cmd_run(
            [
                py,
                "-m",
                "pip",
                "install",
                PYGAME_CE_FANTAS_SRCDIR,
                "--target",
                PYGAME_CE_FANTAS_INSTALL_DIR,
            ]
        )
    except subprocess.CalledProcessError as e:
        pprint("pygame-ce for fantas 安装失败", Colors.RED)
        raise e

    if commit_hash is None:
        try:
            commit_hash = cmd_run(
                ["git", "rev-parse", "HEAD"],
                cwd=PYGAME_CE_FANTAS_SRCDIR,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            pprint("pygame-ce for fantas 版本信息获取失败", Colors.RED)
            sys.exit(1)

    set_pygame_commit_hash(PYGAME_COMMIT_HASH_FILE, commit_hash)

    pprint(
        f"  # pygame-ce for fantas (版本: {commit_hash[:7] if commit_hash else '最新'})"
        " 已安装",
        Colors.GREEN,
    )

    return commit_hash


def delete_file_or_dir(path: Path) -> None:
    """
    删除指定路径的文件或目录，如果是目录则递归删除其中的内容
    """
    if path.is_dir():
        for item in path.iterdir():
            if item.is_dir():
                delete_file_or_dir(item)
            else:
                item.unlink()
        path.rmdir()
    elif path.exists():
        path.unlink()


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

    def check_git_clean(self) -> None:
        """
        检查当前 git 仓库是否存在未提交的更改，如果存在则提示用户先提交这些更改
        """
        if self.args.get("ignore_git", False):
            pprint("忽略 git 仓库状态检查", Colors.BLUE)
            return

        pprint("检查 git 仓库状态中 (使用 git)")

        try:
            cmd_run(
                ["git", "--no-pager", "status", "--porcelain"], error_on_output=True
            )
        except subprocess.CalledProcessError:
            pprint("当前 git 仓库存在未提交的更改，请先提交这些更改", Colors.RED)
            sys.exit(1)

        pprint("git 仓库干净", Colors.GREEN)

    def show_diff_and_help_commit(self, command: str) -> None:
        """
        显示 git 仓库的更改，并提示用户是否需要自动提交这些更改以继续运行 dev.py
        """
        if self.args.get("ignore_git", False):
            pprint("忽略 git 仓库状态检查", Colors.BLUE)
            return

        try:
            cmd_run(
                ["git", "--no-pager", "status", "--porcelain"], error_on_output=True
            )
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
        parser.add_argument(
            "--ignore-git", "-i", action="store_true", help="忽略 git 仓库状态检查"
        )

        # build 命令
        subparsers.add_parser("build", help="安装项目 (可编辑安装)")

        # install 命令
        subparsers.add_parser("install", help="构建并安装项目 (常规安装)")

        # update 命令
        subparsers.add_parser("update", help="更新项目依赖")

        # docs 命令
        docs_parser = subparsers.add_parser("docs", help="生成文档")
        docs_parser.add_argument(
            "--full",
            "-f",
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
            "--full",
            "-f",
            action="store_true",
            help="强制生成完整文档，忽略之前的缓存。",
        )
        auto_parser.add_argument(
            "--install", action="store_true", help="使用常规安装而不是可编辑安装"
        )

        # clean 命令
        subparsers.add_parser("clean", help="清理项目构建缓存和临时文件")

        args = parser.parse_args()
        self.args = vars(args)

        # 如果没有指定子命令，则默认为 auto
        if not self.args["command"]:
            self.args["command"] = "auto"

    def prep_poetry(self) -> None:
        """
        准备 Poetry，确保后续命令可以使用 Poetry 来管理依赖
        """
        pprint("准备 Poetry 中")

        poetry_path = get_poetry_executable()
        if poetry_path is None:
            self.poetry_path = install_poetry()
        else:
            self.poetry_path = poetry_path

        pprint(f"Poetry 已就绪 ({self.poetry_path})", Colors.GREEN)

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

        pprint(f"虚拟环境已就绪 ({self.venv_py})", Colors.GREEN)

    def prep_pygame(self) -> None:
        """
        准备 pygame-ce (fantas 分支)，确保后续命令可以使用正确版本的 pygame
        """
        pprint("准备 pygame-ce for fantas 中")

        pprint("- 检查 pygame-ce (fantas 分支) 安装状态")
        status = PygameStatus.INSTALLED_CORRECTLY
        try:
            import fantas  # pylint: disable=import-outside-toplevel

            pygame = fantas.pygame  # pylint: disable=unused-variable
            pprint("  # pygame 已安装", Colors.GREEN)
        except ImportError:
            pprint("  # pygame 未安装", Colors.RED)
            status = PygameStatus.NOT_INSTALLED
        except RuntimeError:
            pprint("  # pygame 安装不正确", Colors.RED)
            status = PygameStatus.INSTALLED_INCORRECTLY

        if status == PygameStatus.INSTALLED_CORRECTLY:
            pprint("- 检查 pygame-ce (fantas 分支) 版本")
            commit_hash = get_pygame_commit_hash(PYGAME_COMMIT_HASH_FILE)
            lock_hash = get_pygame_commit_hash(PYGAME_LOCK_HASH_FILE)
            if commit_hash is None:
                pprint("  # 无法确定版本", Colors.RED)
                install_pygame_ce_for_fantas(self.venv_py, lock_hash)
            elif lock_hash is None:
                pprint(f"  # 锁定版本: {commit_hash[:7]}", Colors.GREEN)
                set_pygame_commit_hash(PYGAME_LOCK_HASH_FILE, commit_hash)
            elif commit_hash != lock_hash:
                pprint(
                    f"  # 需要切换版本 {commit_hash[:7]} -> {lock_hash[:7]}", Colors.RED
                )
                install_pygame_ce_for_fantas(self.venv_py, lock_hash)
            else:
                pprint(f"  # 版本正确 {commit_hash[:7]}", Colors.GREEN)
        else:
            lock_hash = get_pygame_commit_hash(PYGAME_LOCK_HASH_FILE)
            commit_hash = install_pygame_ce_for_fantas(self.venv_py, lock_hash)
            set_pygame_commit_hash(PYGAME_LOCK_HASH_FILE, commit_hash)

        pprint("pygame-ce for fantas 已就绪", Colors.GREEN)

    def prep_deps(self) -> None:
        """
        使用 Poetry 安装项目依赖
        """
        pprint("安装开发环境依赖中 (使用 Poetry)")

        try:
            cmd_run([self.poetry_path, "install", "--no-root"])
        except subprocess.CalledProcessError as e:
            pprint("项目依赖安装失败", Colors.RED)
            raise e

        pprint("开发环境已就绪", Colors.GREEN)

    def cmd_build(self) -> None:
        """
        执行 build 子命令，使用 Poetry 安装项目到虚拟环境中 (可编辑安装)
        """
        pprint("安装项目中 (可编辑安装)")

        try:
            cmd_run([self.poetry_path, "install"])
        except subprocess.CalledProcessError:
            pprint("项目安装失败", Colors.RED)
            sys.exit(1)

        pprint(
            f"项目已安装 (可编辑安装), 改动 {FANTAS_SOURCE_DIR} 中的代码实时生效",
            Colors.GREEN,
        )

    def cmd_install(self) -> None:
        """
        执行 install 子命令，使用 Poetry 构建项目并安装生成的 wheel 包 (常规安装)
        """
        pprint("构建项目中")

        delete_file_or_dir(DIST_DIR)

        try:
            cmd_run([self.poetry_path, "build", "-f", "wheel"])
        except subprocess.CalledProcessError:
            pprint("项目构建失败", Colors.RED)
            sys.exit(1)

        pprint(f"项目已构建 ({DIST_DIR})", Colors.GREEN)
        pprint("安装项目中 (常规安装)")

        wheel_files = list(DIST_DIR.glob("*.whl"))
        if not wheel_files:
            pprint("未找到生成的 wheel 文件", Colors.RED)
            sys.exit(1)

        try:
            cmd_run(
                [
                    self.venv_py,
                    "-m",
                    "pip",
                    "install",
                    wheel_files[0],
                    "--force-reinstall",
                ]
            )
        except subprocess.CalledProcessError:
            pprint("项目安装失败", Colors.RED)
            sys.exit(1)

        pprint(f"项目已安装 ({wheel_files[0]})", Colors.GREEN)

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
            "--quiet",
        ]
        if full:
            cmd.append("-E")
        try:
            cmd_run(cmd, error_on_output=True)
        except subprocess.CalledProcessError:
            pprint("文档生成失败，请检查 Sphinx 输出的错误信息", Colors.RED)
            sys.exit(1)

        pprint("文档已生成 (docs/build/html/index.html)", Colors.GREEN)

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
                "dev.py",
                "--output-format=colorized",
            ]
        )

        pprint("代码质量检查已通过", Colors.GREEN)

    def cmd_stubs(self) -> None:
        """
        执行 stubs 子命令，使用 mypy 进行静态类型检查
        """
        pprint("执行静态类型检查中 (使用 mypy)")

        cmd_run([self.venv_py, "-m", "mypy"])

        pprint("类型检查已通过", Colors.GREEN)

    def cmd_format(self) -> None:
        """
        执行 format 子命令，使用 black 格式化代码
        """
        pprint("格式化代码中 (使用 black)")

        cmd_run([self.venv_py, "-m", "black", "fantas", "tests", "dev.py"])

        self.show_diff_and_help_commit("format")

        pprint("代码已格式化", Colors.GREEN)

    def cmd_test(self) -> None:
        """
        执行 test 子命令，使用 pytest 运行测试
        """
        mod = [f"tests/test_{m}.py" for m in self.args.get("mod", [])]

        if mod:
            mods_arg = " ".join(mod)
            pprint(f"测试模块 ({mods_arg}) 中 (使用 pytest)")
            cmd_run([self.venv_py, "-m", "pytest", *mod])
        else:
            pprint("测试所有模块中 (使用 pytest)")
            cmd_run([self.venv_py, "-m", "pytest"])

        pprint("测试已通过", Colors.GREEN)

    def cmd_auto(self) -> None:
        """
        自动运行所有检查和测试，然后构建并安装项目
        """
        self.cmd_format()
        self.cmd_stubs()
        self.cmd_lint()
        self.cmd_docs()
        self.cmd_test()
        if not self.args.get("install", False):
            self.cmd_build()
        else:
            self.cmd_install()

    def cmd_clean(self) -> None:
        """
        清理项目构建缓存和临时文件
        """
        pprint("清理项目构建缓存和临时文件中")

        for pattern in (
            "build",
            "tmp",
            ".mypy_cache",
            "__pycache__",
            ".pytest_cache",
            "pygame-ce-fantas",
            "_vendor/pygame",
            "_vendor/pygame**",
            ".coverage",
        ):
            for path in CWD.glob(f"**/{pattern}"):
                delete_file_or_dir(path)

    def cmd_update(self) -> None:
        """
        更新项目依赖
        """
        pprint("更新项目依赖中 (使用 Poetry)")

        try:
            cmd_run([self.poetry_path, "update"])
        except subprocess.CalledProcessError:
            pprint("项目依赖更新失败", Colors.RED)
            sys.exit(1)

        pprint("更新 pygame-ce for fantas 中")

        delete_file_or_dir(PYGAME_LOCK_HASH_FILE)
        delete_file_or_dir(PYGAME_COMMIT_HASH_FILE)

        self.prep_pygame()

        pprint("项目依赖已更新", Colors.GREEN)

    def run(self) -> None:
        """
        运行开发命令的主流程
        """
        start_time = get_time_ns()

        self.parse_args()

        self.check_git_clean()

        pprint(f"运行子命令 '{self.args['command']}'")

        if self.args["command"] == "clean":
            self.cmd_clean()
        else:
            try:
                self.prep_poetry()
                self.prep_venv()
                self.prep_pygame()
                self.prep_deps()
                func = getattr(self, f"cmd_{self.args['command']}")
                func()
            except subprocess.CalledProcessError as e:
                pprint(f"程序异常退出，错误代码 {e.returncode}", Colors.RED)
                sys.exit(e.returncode)
            except KeyboardInterrupt:
                pprint("程序被用户中断", Colors.RED)
                sys.exit(1)

        end_time = get_time_ns()
        units = ("ns", "µs", "ms", "s")
        unit_index = 0
        elapsed_time: float = end_time - start_time
        while elapsed_time >= 1000 and unit_index < len(units) - 1:
            elapsed_time /= 1000
            unit_index += 1
        pprint(
            f"子命令 '{self.args['command']}' 执行成功, 耗时: {elapsed_time:.2f} "
            f"{units[unit_index]}",
            Colors.GREEN,
        )

        if self.py != self.venv_py:
            pprint(
                f"当前环境 ({self.py}) 与虚拟环境 ({self.venv_py}) 不同，"
                "建议使用虚拟环境: ",
                Colors.MAGENTA,
            )
            if sys.platform == "win32":
                pprint(f"  > {self.venv_py.parent}\\Scripts\\activate", Colors.CYAN)
            else:
                pprint(f"  > source {self.venv_py.parent}/bin/activate", Colors.CYAN)


if __name__ == "__main__":
    Dev().run()
