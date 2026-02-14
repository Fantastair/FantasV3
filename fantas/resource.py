from __future__ import annotations
from pathlib import Path
from typing import Generic, TypeVar
from collections.abc import Callable
from dataclasses import dataclass, field

import fantas

__all__ = (
    "images",
    "fonts",
    "colors",
    "animations",
)

T = TypeVar("T")


@dataclass(slots=True)
class ResourceLoader(Generic[T]):
    """资源加载器抽象基类。"""

    _resources: dict[str, T] = field(default_factory=dict, init=False)

    def get(self, name: str) -> T:
        """
        根据名称获取已加载的资源。
        Args:
            name (str): 资源名称。
        Returns:
            T: 已加载的资源对象。
        Raises:
            KeyError: 如果资源未加载则引发此异常。
        """
        if name not in self._resources:
            raise KeyError(f"资源 '{name}' 未加载。")
        return self._resources[name]

    def set(self, name: str, resource: T):
        """
        手动设置资源。
        Args:
            name (str): 资源名称。
            resource (T): 资源对象。
        """
        self._resources[name] = resource


@dataclass(slots=True)
class ImageLoader(ResourceLoader[fantas.Surface]):
    """图像资源加载器。"""

    def load_bitmap(
        self,
        path: Path,
        alias: str = None,
        hook: Callable[[fantas.Surface], fantas.Surface] = fantas.image_convert_hook,
    ):
        """
        加载位图图像资源。
        Args:
            path (Path): 图像文件路径。
            alias (str, optional): 资源别名，默认为 None，使用文件名作为资源名称。
            hook (Callable[[fantas.Surface], fantas.Surface], optional): 图像转换钩子函数，默认为 image_convert_hook。
        """
        if not isinstance(path, Path):
            path = Path(path)
        self._resources[alias if alias else path.stem] = hook(fantas.image.load(path))

    def load_svg(
        self,
        path: Path,
        alias: str = None,
        size: int = 64,
        hook: Callable[[fantas.Surface], fantas.Surface] = fantas.image_convert_hook,
    ):
        """
        加载 SVG 图像资源。
        Args:
            path (Path): SVG 文件路径。
            alias (str, optional): 资源别名，默认为 None，使用文件名作为资源名称。
            size (int, optional): 图像最长边大小，默认为 64 像素。
            hook (Callable[[fantas.Surface], fantas.Surface], optional): 图像转换钩子函数，默认为 image_convert_alpha_hook。
        """
        if not isinstance(path, Path):
            path = Path(path)
        self._resources[alias if alias else path.stem] = hook(
            fantas.image.load_sized_svg(path, size)
        )


images = ImageLoader()


@dataclass(slots=True)
class FontLoader(ResourceLoader[fantas.Font]):
    """字体资源加载器。"""

    def load(self, path: Path, alias: str = None):
        """
        加载字体资源。
        Args:
            path (Path): 字体文件路径。
            alias (str, optional): 资源别名，默认为 None，使用文件名作为资源名称。
        """
        if not isinstance(path, Path):
            path = Path(path)
        font = fantas.Font(path)
        font.origin = True
        font.kerning = True
        self._resources[alias if alias else path.stem] = font

    _default_sysfont: fantas.Font | None = None

    def get_default_sysfont(self) -> fantas.Font:
        """获取默认系统字体。"""
        if self._default_sysfont is None:
            self._default_sysfont = fantas.SysFont(
                ("Noto Sans CJK SC", "PingFang SC", "Simhei", "Microsoft YaHei"), 16
            )
            self._default_sysfont.origin = True
            self._default_sysfont.kerning = True
        return self._default_sysfont

    def set_default_sysfont(self, font: fantas.Font):
        """设置默认系统字体。"""
        self._default_sysfont = font

    DEFAULTSYSFONT = property(get_default_sysfont, set_default_sysfont)


fonts = FontLoader()


@dataclass(slots=True)
class ColorLoader(ResourceLoader[fantas.Color]):
    """颜色资源加载器。"""

    def load(self, color: str, name: str = None):
        """
        加载颜色资源。
        Args:
            color (str): 颜色字符串（如 "#RRGGBBAA" 或 "red"）。
            name (str, optional): 资源名称，默认为 None，使用颜色字符串作为资源名称。
        """
        self._resources[name if name else color] = fantas.Color(color)

    def load_preset_colors(self):
        """加载预设颜色。"""
        from pygame import colordict

        for name, color in colordict.THECOLORS.items():
            self._resources[name] = fantas.Color(color)


colors = ColorLoader()


class AnimationLoader(ResourceLoader[fantas.AnimationHelper]):
    """动画资源加载器。"""

    def load(
        self,
        path: Path,
        alias: str = None,
        hook: Callable[[fantas.Surface], fantas.Surface] = fantas.image_convert_hook,
    ):
        if not isinstance(path, Path):
            path = Path(path)
        self._resources[alias if alias else path.stem] = fantas.AnimationHelper(
            path, hook
        )


animations = AnimationLoader()
