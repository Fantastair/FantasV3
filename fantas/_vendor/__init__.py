"""
无论是 fantas 内部还是外部，导入 fantas._vendor.pygame 都会得到顶级 pygame 模块。
这确保了无论用户如何导入 pygame，都不会重复加载 pygame。
"""
import sys
import pkgutil

__all__ = ("pygame",)

# 如果顶级 pygame 还没加载，加载它
if 'pygame' not in sys.modules:
    import pygame  # pylint: disable=import-error

# 欺骗导入系统：让 fantas._vendor.pygame 指向顶级 pygame
sys.modules[__name__ + '.pygame'] = sys.modules['pygame']
__path__ = pkgutil.extend_path(__path__, __name__)
