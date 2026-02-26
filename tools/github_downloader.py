"""
下载 GitHub Release 的封装
"""

import os
import sys
import json
import zipfile
import platform
import urllib.request
from typing import Any
from pathlib import Path

from .pprint import pprint, Colors

__all__ = ("GithubReleaseDownloader",)

CWD = Path(__file__).parent.parent


class GithubReleaseDownloader:
    """
    提供从 GitHub Release 下载 whl 文件的功能
    """

    HEADERS = {  # GitHub API 需要的请求头
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "WHL-Downloader/1.0",
    }

    def __init__(self, owner: str, repo: str):
        """
        初始化下载器，设置 GitHub 仓库的所有者和名称

        Args:
            owner: GitHub 用户名或组织名
            repo: GitHub 仓库名
        """

        self.owner = owner
        self.repo = repo
        self.REPO_URL = f"https://api.github.com/repos/{owner}/{repo}"

        pprint(
            f"初始化 GitHub Release 下载器 (仓库: {owner}/{repo})",
            prompt="GithubReleaseDownloader",
            col=Colors.SUCCESS,
        )

    def get_src_dir_list(self) -> set[Path]:
        """
        获取当前 tmp 目录下的源代码目录集合

        Returns:
            返回 tmp 目录下的所有源代码目录路径集合
        """
        return set((CWD / "tmp").glob(f"{self.owner}-{self.repo}-*"))

    def get_json(self, url: str) -> dict[str, Any]:
        """
        发送请求获取 JSON 数据

        Args:
            url: API URL
        Returns:
            返回解析后的 JSON 数据
        Raises:
            Exception: 如果请求失败或者返回非 200 状态码，则抛出异常
        """
        pprint(f"请求 URL: {url}", prompt="GithubReleaseDownloader")

        req = urllib.request.Request(url, headers=self.HEADERS)
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                pprint(
                    "Release 未找到，请检查仓库名和版本号是否正确",
                    prompt="GithubReleaseDownloader",
                    col=Colors.ERROR,
                )
            elif e.code == 403:
                pprint(
                    "API 限制 exceeded. 建议稍后再试",
                    prompt="GithubReleaseDownloader",
                    col=Colors.ERROR,
                )
            else:
                pprint(
                    f"API 请求失败: {e}",
                    prompt="GithubReleaseDownloader",
                    col=Colors.ERROR,
                )
            sys.exit(1)

    def get_release_by_tag(self, tag: str) -> dict[str, Any]:
        """
        通过 tag 获取 release 信息

        Args:
            tag: Release 的 tag 名称
        Returns:
            返回 release 的 JSON 数据
        """
        pprint(f"获取 release 信息 (tag: {tag})", prompt="GithubReleaseDownloader")

        url = f"{self.REPO_URL}/releases/tags/{tag}"
        return self.get_json(url)

    def get_latest_release(self) -> dict[str, Any]:
        """
        获取最新 release 信息

        Returns:
            返回最新 release 的 JSON 数据
        """
        pprint("获取最新 release 信息", prompt="GithubReleaseDownloader")

        url = f"{self.REPO_URL}/releases/latest"
        result = self.get_json(url)
        tsg = result["tag_name"]

        pprint(
            f"最新 release tag: {tsg}",
            prompt="GithubReleaseDownloader",
            col=Colors.INFO,
        )

        return result

    def list_whl_assets(self, tag: str | None = None) -> list[dict[str, Any]]:
        """
        从 release 数据中筛选出所有 whl 文件

        Args:
            tag: 可选的 release tag，如果不指定则获取最新 release
        Returns:
            包含 whl 文件信息的列表，每个元素包含 name, browser_download_url, size 等
        """
        pprint("获取 whl 文件列表", prompt="GithubReleaseDownloader")

        if tag is None:
            release_data = self.get_latest_release()
        else:
            release_data = self.get_release_by_tag(tag)

        assets = release_data.get("assets", [])
        whl_assets = [asset for asset in assets if asset["name"].endswith(".whl")]
        return whl_assets

    def auto_select_whl(self, tag: str | None = None) -> dict[str, Any] | None:
        """
        自动选择与当前系统兼容的 whl 文件

        Args:
            tag: 可选的 release tag，如果不指定则获取最新 release
        Returns:
            返回与当前系统兼容的 whl 文件信息，如果没有找到兼容的文件则返回 None
        """
        arch_mapping = {
            "x86_64": ["x86_64", "amd64"],
            "amd64": ["x86_64", "amd64"],
            "aarch64": ["aarch64"],
            "arm64": ["aarch64"],
            "i386": ["i686"],
            "i686": ["i686"],
        }
        os_keywords = {"windows": ["win"], "linux": ["manylinux"], "darwin": ["macosx"]}

        os_name = platform.system().lower()
        machine = platform.machine().lower()
        py_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
        current_archs = arch_mapping.get(machine, [machine])
        target_os_keywords = os_keywords.get(os_name, [])

        assets_list = self.list_whl_assets(tag)

        for asset in assets_list:
            whl_name = asset["name"].lower()
            # 检查 Python 版本匹配
            if py_version not in whl_name:
                continue
            # 检查系统匹配
            if all(os_kw not in whl_name for os_kw in target_os_keywords):
                continue
            # 检查架构匹配
            if "macosx" not in whl_name and all(
                arch not in whl_name for arch in current_archs
            ):
                continue
            # 找到匹配项，返回下载链接
            return asset
        return None

    def download_file(self, url: str, target: Path, show_progress: bool = True) -> bool:
        """
        下载文件并保存到指定路径

        Args:
            url: 文件的下载链接
            target: 文件保存的目标路径
            show_progress: 是否显示下载进度条
        Returns:
            下载成功返回 True，失败返回 False
        """
        if "CI" in os.environ:
            show_progress = False

        pprint(f"下载文件: {url} -> {target}", prompt="GithubReleaseDownloader")

        try:
            req = urllib.request.Request(url, headers=self.HEADERS)

            with urllib.request.urlopen(req, timeout=60) as response:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 64 * 1024

                target.parent.mkdir(parents=True, exist_ok=True)

                with target.open("wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        if show_progress:
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                process_bar = (
                                    "=" * int(percent / 2)
                                    + ">"
                                    + "." * (50 - int(percent / 2))
                                )
                                pprint(
                                    f"[{process_bar}] {percent:.1f}% ({downloaded}/"
                                    f"{total_size} bytes)",
                                    prompt="GithubReleaseDownloader",
                                    col=Colors.INFO,
                                    restart=True,
                                )
                            else:
                                pprint(
                                    f"下载中... {downloaded} bytes / (总大小未知)",
                                    prompt="GithubReleaseDownloader",
                                    col=Colors.INFO,
                                    restart=True,
                                )
            if show_progress:
                print()
            return True

        except Exception as e:
            if target.exists():
                target.unlink()
            pprint(
                f"\n下载失败 {url}: {e}",
                prompt="GithubReleaseDownloader",
                col=Colors.ERROR,
            )
        return False

    def download_source_code(
        self, tag: str | None = None, target_dir: Path = CWD / "tmp"
    ) -> Path | None:
        """
        下载 release 的源代码 zip 包并解压到指定目录

        Args:
            tag: 可选的 release tag，如果不指定则下载最新 release
            target_dir: 解压后的文件保存目录
        Returns:
            下载并解压成功返回解压后的目录路径，失败返回 None
        """

        pprint("下载 release 的源代码压缩包 (zip)", prompt="GithubReleaseDownloader")

        if tag is None:
            release_data = self.get_latest_release()
        else:
            release_data = self.get_release_by_tag(tag)

        source_url = release_data.get("zipball_url")
        if source_url is None:
            pprint(
                "未找到源代码压缩包的下载链接",
                prompt="GithubReleaseDownloader",
                col=Colors.ERROR,
            )
            return None

        file_name = f"{self.repo}-{release_data['tag_name']}-source.zip"

        tmp_file = CWD / "tmp" / file_name
        target_dir.mkdir(parents=True, exist_ok=True)

        pre_src_dirs = self.get_src_dir_list()
        if tmp_file.exists() or self.download_file(source_url, tmp_file):
            with zipfile.ZipFile(tmp_file, "r") as zip_ref:
                zip_ref.extractall(target_dir)
            src_dirs = self.get_src_dir_list()
            return list(src_dirs - pre_src_dirs)[0] if src_dirs - pre_src_dirs else None
        return None

    def auto_download_whl(
        self, tag: str | None = None, target_dir: Path = CWD / "tmp"
    ) -> Path | None:
        """
        自动下载 release 中系统对应的 whl 文件到指定目录

        Args:
            tag: 可选的 release tag，如果不指定则下载最新 release
            target_dir: 下载的 whl 文件保存目录
        Returns:
            下载成功返回下载的 whl 文件路径，失败返回 None
        """
        pprint(
            "自动选择匹配当前系统的 whl 文件并下载", prompt="GithubReleaseDownloader"
        )

        whl = self.auto_select_whl(tag)
        if whl is None:
            pprint(
                "未找到与当前系统兼容的 whl 文件",
                prompt="GithubReleaseDownloader",
                col=Colors.ERROR,
            )
            return None

        pprint(
            f"找到匹配的 whl 文件: {whl['name']}",
            prompt="GithubReleaseDownloader",
            col=Colors.SUCCESS,
        )

        url = whl["browser_download_url"]

        target_file: Path = target_dir / whl["name"]
        pprint(str(target_file), prompt="GithubReleaseDownloader", col=Colors.INFO)

        if target_file.exists():
            return target_file
        return target_file if self.download_file(url, target_file) else None

    def download_all_whl(
        self, tag: str | None = None, target_dir: Path = CWD / "tmp"
    ) -> list[Path]:
        """
        下载 release 中的所有 whl 文件到指定目录

        Args:
            tag: 可选的 release tag，如果不指定则下载最新 release
            target_dir: 下载的 whl 文件保存目录
        Returns:
            下载成功返回下载的 whl 文件路径列表，失败返回空列表
        """
        pprint("下载 release 中的所有 whl 文件", prompt="GithubReleaseDownloader")

        whl_assets = self.list_whl_assets(tag)
        downloaded_files = []

        for whl in whl_assets:
            url = whl["browser_download_url"]
            target_file: Path = target_dir / whl["name"]

            if target_file.exists() or self.download_file(url, target_file):
                downloaded_files.append(target_file)
            else:
                pprint(
                    f"下载失败: {whl['name']}",
                    prompt="GithubReleaseDownloader",
                    col=Colors.ERROR,
                )
                sys.exit(1)

        return downloaded_files
