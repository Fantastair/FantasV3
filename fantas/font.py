"""
fantas.font 的 Docstring
"""

from __future__ import annotations
from bisect import bisect_right
from collections.abc import Sequence
from typing import Any, Callable

from fantas._vendor import pygame
from fantas._vendor.pygame import freetype
from fantas._vendor.pygame.sysfont import SysFont as _SysFont

import fantas

__all__ = (
    "Font",
    "SysFont",
    "get_font_by_id",
    "DEFAULTFONT",
)


class Font(freetype.Font):
    """Fantas3 字体类，继承自 pygame.freetype.Font，添加唯一 ID 属性，并支持通过 ID 查找字体实例。"""

    def __init__(
        self,
        file: fantas.FileLike | None,
        size: float = 0,
        font_index: int = 0,
        resolution: int = 0,
        ucs4: bool = False,
    ) -> None:
        """
        初始化 Font 实例。
        Args:
            file (fantas.FileLike | None): 字体文件路径或文件对象，或 None 表示使用默认字体。
            size (float): 字体大小，默认为 0。
            font_index (int): 字体索引，默认为 0。
            resolution (int): 分辨率，默认为 0。
            ucs4 (int): 是否使用 UCS4 编码，默认为 False。
        """
        super().__init__(file, size, font_index, resolution, ucs4)
        self.font_id: int = fantas.generate_unique_id()
        font_dict[self.font_id] = self

    def __del__(self) -> None:
        if self.font_id in font_dict:
            del font_dict[self.font_id]

    def __hash__(self) -> int:
        return hash(self.font_id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Font) and self.font_id == other.font_id

    get_rect: Callable[..., fantas.Rect] = fantas.lru_cache_typed(maxsize=65536)(
        pygame.freetype.Font.get_rect
    )

    @fantas.lru_cache_typed(maxsize=65536)
    def _get_width_char_kerning(
        self, style_flag: fantas.TextStyleFlag, size: float, char_pair: str
    ) -> int:
        """
        获取字距调整后的字符宽度。
        Args:
            style_flag (fantas.TextStyleFlag): 字体样式标志。
            size       (float)               : 字体大小。
            char_pair  (str)                 : 字符对，包含目标字符和前一个字符。
        Returns:
            int: 字符宽度（像素）。
        """
        return round(
            self.get_rect(char_pair, style_flag, size=size).width
            - self.get_rect(char_pair[0], style_flag, size=size).width
        )

    @fantas.lru_cache_typed(maxsize=65536)
    def get_widthes(
        self, style_flag: fantas.TextStyleFlag, size: float, text: str
    ) -> tuple[int, ...]:
        """
        获取指定样式文本的宽度度量信息。
        Args:
            style_flag (fantas.TextStyleFlag): 字体样式标志。
            size       (float)               : 字体大小。
            text       (str)                 : 要测量的文本内容。
        Returns:
            tuple[int]: 字体度量信息列表，每一个元素对应文本中字符的右侧坐标（从 0 开始）。
        """
        # 初始化度量信息列表
        widthes: list[int] = [self.get_rect(text[0], style_flag, size=size).width]
        # 简化引用
        append = widthes.append
        # 逐字计算度量信息
        for i in range(0, len(text) - 1):
            append(
                self._get_width_char_kerning(style_flag, size, text[i : i + 2])
                + widthes[-1]
            )
        # 返回度量信息元组（节省缓存空间，并防篡改）
        return tuple(widthes)

    @fantas.lru_cache_typed(maxsize=65536)
    def auto_wrap(
        self, style_flag: fantas.TextStyleFlag, size: float, text: str, width: int
    ) -> tuple[tuple[str, int], ...]:
        """
        自动换行文本。
        Args:
            style_flag (fantas.TextStyleFlag): 字体样式标志。
            size       (float)               : 字体大小。
            text       (str)                 : 要测量的文本内容。
            width      (int)                 : 最大宽度限制。
        Returns:
            换行后的文本行列表，每行包含文本内容和宽度。
        """
        results: list[tuple[str, int]] = []
        append = results.append
        for t in text.splitlines():
            line_width: Sequence[int] = (
                self.get_widthes(style_flag, size, t) if t else [0]
            )
            # 如果整行宽度小于等于区域宽度则直接添加
            if line_width[-1] <= width:
                append((t, line_width[-1]))
                continue
            # 否则拆行
            last_index = 0
            _width = width
            while last_index < len(t):
                line_index = bisect_right(line_width, _width, lo=last_index)
                if line_index == last_index:
                    line_index += 1
                append(
                    (
                        t[last_index:line_index],
                        line_width[line_index - 1]
                        - (line_width[last_index - 1] if last_index > 0 else 0),
                    )
                )
                last_index = line_index
                _width = line_width[line_index - 1] + width
        return tuple(results)


pygame.freetype.Font = Font  # type: ignore[assignment, misc]


def SysFont(  # pylint: disable=invalid-name
    name: Any, size: float = 16.0
) -> Font | Any:
    """
    创建并返回一个系统字体的 Font 实例。
    Args:
        name        : 字体名称。
        size (float): 字体大小，默认为 16.0。
    Returns:
        Font: 创建的字体实例。
    """
    return _SysFont(name, size, constructor=constructor)


def constructor(
    fontpath: fantas.FileLike | None, size: float, _: bool, __: bool
) -> Font:
    """字体构造函数，用于 SysFont 创建 Font 实例。"""
    return Font(fontpath, size)


font_dict: dict[int, Font] = {}  # 字体 ID 到字体实例的映射字典


def get_font_by_id(font_id: int) -> Font | None:
    """
    通过字体 ID 获取字体实例。
    Args:
        font_id (int): 字体的唯一 ID。
    Returns:
        Font | None: 对应 ID 的字体实例，如果不存在则返回 None。
    """
    return font_dict.get(font_id, None)


DEFAULTFONT: fantas.Font = Font(None)
""" 默认字体 """
DEFAULTFONT.origin = True  # pylint: disable=attribute-defined-outside-init
DEFAULTFONT.kerning = True  # pylint: disable=attribute-defined-outside-init
