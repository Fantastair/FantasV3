:mod:`fantas.fantas_typing`
===========================

.. automodule:: fantas.fantas_typing
    :no-members:

.. _rect-documentatioin:

Rect 矩形类
-----------

fantas 使用的矩形类，实际上是 pygame.Rect 和 pygame.FRect 的别名。

.. autoclass:: fantas.Rect

    整数精度矩形。

.. autoclass:: fantas.FRect

    浮点精度矩形。

    .. hint::
        
        使用浮点矩形可以在逻辑运算中获得更高的精度，但是注意，显示图像总是像素化的，
        这可能会导致意外的截断和舍入误差，表现为图像位置的微小偏移，
        这在动态变化的场景中可能会引起视觉上的抖动。

.. note::

    两种矩形在用法上完全相同，唯一的区别在于它们使用的数值类型不同。
    
    有关 :code:`fantas.Rect` 和 :code:`fantas.FRect` 的完整接口说明，
    请参阅 pygame 的文档 `pygame.Rect`_。

    如果想要快速了解 :code:`fantas.Rect` 的使用技巧，可以看看
    :doc:`../tutorials/rect` 。

.. _pygame.Rect: https://pyga.me/docs/ref/rect.html#pygame.Rect

.. _surface-documentation:

Surface 表面类
--------------

fantas 使用的表面类，实际上是 pygame.Surface 的别名。

.. autoclass:: fantas.Surface

.. autoclass:: fantas.PixelArray

Color 颜色类
------------

.. autoclass:: fantas.Color

    fantas 模块使用的颜色类，实际上是 pygame.Color 的别名。

    .. note::
        
        有关 :code:`fantas.Color` 的完整接口说明，请参阅 pygame 的文档 `pygame.Color`_。

        如果想要快速了解 :code:`fantas.Color` 的使用技巧，可以看看 :doc:`../tutorials/color` 。

.. _pygame.Color: https://pyga.me/docs/ref/color.html#pygame.Color

