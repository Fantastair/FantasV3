import os
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
