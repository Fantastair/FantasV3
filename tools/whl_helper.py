"""
提供修改 whl 文件的工具函数
"""

import os
import re
import shutil
import zipfile
from pathlib import Path

__all__ = [
    "unzip_file",
    "zip_dir",
    "get_wheel_content",
    "set_wheel_content",
    "content_to_items",
    "items_to_content",
    "get_tag_from_items",
]

CWD = Path(__file__).parent.parent


def unzip_file(file: Path) -> Path:
    """
    解压文件到临时目录

    Args:
        file: 文件的路径
    Returns:
        解压后的目录路径
    """
    if not file.exists():
        raise FileNotFoundError(f"解压文件不存在: {file}")

    TARGET_DIR = CWD / "tmp" / file.stem
    TARGET_DIR.parent.mkdir(parents=True, exist_ok=True)

    if TARGET_DIR.exists():
        # 删除已存在的临时目录，避免解压失败
        shutil.rmtree(TARGET_DIR, ignore_errors=True)

    try:
        with zipfile.ZipFile(file, "r") as zip_ref:
            zip_ref.testzip()
            zip_ref.extractall(TARGET_DIR)
    except zipfile.BadZipFile as e:
        raise RuntimeError(f"解压失败：{file} 不是有效的 ZIP 文件") from e
    except Exception as e:
        raise RuntimeError(f"解压文件 {file} 时出错：{str(e)}") from e

    return TARGET_DIR


def zip_dir(dir_path: Path, output_file: Path) -> None:
    """
    将目录压缩为文件

    Args:
        dir_path: 要压缩的目录路径
        output_file: 输出的文件路径
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"待压缩目录不存在: {dir_path}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"{dir_path} 不是一个有效的目录")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    file_path = Path(root) / file
                    if not file_path.exists():
                        continue
                    arcname = file_path.relative_to(dir_path)
                    zip_ref.write(file_path, arcname)
    except Exception as e:
        raise RuntimeError(f"压缩目录 {dir_path} 时出错：{str(e)}") from e


def get_wheel_content(file_dir: Path) -> str:
    """
    获取目录下 WHEEL 文件内容

    Args:
        file_dir: whl 文件解压后的目录路径
    Returns:
        WHEEL 文件的内容
    """
    WHEEL_FILE = list(file_dir.glob("*.dist-info/WHEEL"))[0]
    return WHEEL_FILE.read_text(encoding="utf-8")


def set_wheel_content(file_dir: Path, content: str) -> None:
    """
    设置目录下 WHEEL 文件内容

    Args:
        file_dir: whl 文件解压后的目录路径
        content: 要写入 WHEEL 文件的内容
    """
    WHEEL_FILE = list(file_dir.glob("*.dist-info/WHEEL"))[0]
    WHEEL_FILE.write_text(content, encoding="utf-8")


def content_to_items(content: str) -> list[list[str]]:
    """
    从 whl 文件的 WHEEL 文件中获取所有 key-value 对

    Args:
        content: WHEEL 文件的内容
    Returns:
        key-value 对列表
    """
    items = []
    for line in content.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            items.append([key.strip(), value.strip()])
    return items


def items_to_content(items: list[list[str, str]]) -> str:
    """
    将 key-value 对列表转换为 WHEEL 文件内容

    Args:
        items: key-value 对列表
    Returns:
        WHEEL 文件内容
    """
    return "\n".join(f"{key}: {value}" for key, value in items) + "\n\n"


def get_tag_from_items(items: list[list[str]]) -> str:
    """
    从 key-value 对列表中获取 tag 字段，并进行处理
    """
    tag = ".".join([i[1] for i in reversed(items) if i[0] == "Tag"])
    pattern = r"\.cp.+?-cp.+?-"
    tag = re.sub(pattern, ".", tag)
    return tag
