"""
fantas 顶级包
"""

__all__ = (
    "time",
    "draw",
    "math",
    "event",
    "mouse",
    "image",
    "display",
    "transform",
)

__version__ = "3.0.1.dev1"

# 设置 Pygame 环境变量以优化性能和兼容性
import os

os.environ.update(
    {
        "PYGAME_BLEND_ALPHA_SDL2": "1",  # 启用 SDL2 Alpha 混合支持
        "PYGAME_FREETYPE": "1",  # 启用 Pygame FreeType 字体支持
        "PYGAME_HIDE_SUPPORT_PROMPT": "1",  # 隐藏 Pygame 支持提示
        "SDL_VIDEO_ALLOW_SCREENSAVER": "1",  # 允许屏幕保护程序
        "SDL_IME_SHOW_UI": "1",  # 显示输入法编辑器 (IME) 界面
        "SDL_WINDOWS_DPI_AWARENESS": "permonitorv2",  # 启用每个监视器（V2）的 DPI 感知
        "SDL_TIMER_RESOLUTION": "1",  # 提高定时器分辨率
        "SDL_RENDER_VSYNC": "0",  # 禁用渲染垂直同步
        "SDL_KMSDRM_ATOMIC": "1",  # 启用 KMSDRM 原子模式
        "SDL_JOYSTICK_HIDAPI": "1",  # 启用 HIDAPI 支持的操纵杆
        "SDL_JOYSTICK_RAWINPUT": "1",  # 启用 RawInput 支持的操纵杆
        "SDL_WINDOWS_RAW_KEYBOARD": "1",  # 启用 Windows 原始键盘输入
        "SDL_AUDIO_ALSA_DEFAULT_DEVICE": "hw:0,0",  # 设置 ALSA 默认音频设备
        "SDL_VIDEO_WAYLAND_SCALE_TO_DISPLAY": "0",  # 禁用 Wayland 显示缩放
        "SDL_VIDEO_X11_SCALING_FACTOR": "0",  # 禁用 X11 显示缩放
        "SDL_MOUSE_DPI_SCALE_CURSORS": "1",  # 启用鼠标 DPI 缩放光标
        "SDL_VIDEO_METAL_AUTO_RESIZE_DRAWABLE": "1",  # 启用 Metal 自动调整可绘制区域
        "SDL_RENDER_LINE_METHOD": "1",  # 使用更高质量的线条渲染方法
        "SDL_VIDEO_WAYLAND_ALLOW_LIBDECOR": "0",  # 禁用 Wayland Libdecor 支持
        "SDL_WINDOWS_ENABLE_MESSAGELOOP": "1",  # 启用 Windows 消息循环
        "SDL_QUIT_ON_LAST_WINDOW_CLOSE": "1",  # 在最后一个窗口关闭时退出应用程序
    }
)

import sys

VENDOR_DIR = os.path.join(os.path.dirname(__file__), "_vendor")
sys.path.insert(0, VENDOR_DIR)

# 初始化 Pygame
from fantas._vendor import pygame

if not getattr(pygame, "IS_FANTAS", False):
    raise RuntimeError(
        "使用的 Pygame 版本不兼容 Fantas，请确保安装了 pygame-ce for fantas 分支版本。"
    )

from fantas._vendor.pygame import freetype

pygame.init()
freetype.init(cache_size=1024)

# 导入 Pygame 的子模块以简化调用链
from fantas._vendor.pygame import (
    time,
    draw,
    math,
    event,
    mouse,
    image,
    display,
    transform,
)

# 导入 fantas 包的各个子模块
from fantas.base.fantas_typing import *  # 类型定义
from fantas.base.constants import *  # 常量定义
from fantas.utils.misc import *  # 杂项工具
from fantas.base.nodebase import *  # 节点基类
from fantas.utils.curve import *  # 曲线支持
from fantas.utils.color import *  # 颜色支持
from fantas.ext.font import *  # 字体支持
from fantas.base.style import *  # 样式支持
from fantas.utils.resource import *  # 资源管理
from fantas.base.window import *  # 窗口管理
from fantas.base.renderer import *  # 渲染支持
from fantas.base.event_handler import *  # 事件处理
from fantas.base.framefunc import *  # 帧函数支持
from fantas.base.ui import *  # UI 基类
from fantas.ext.layout import *  # 布局支持

from fantas.utils.udp import *  # UDP 通信
from fantas.utils.debug import *  # 调试功能

# 先禁用所有事件，然后再根据需要启用特定事件
event.set_blocked(None)
# 启用所有已分类事件
event.set_allowed(list(event_category_dict.keys()))

del os
