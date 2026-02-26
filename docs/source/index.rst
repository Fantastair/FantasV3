.. fantas documentation master file, created by
   sphinx-quickstart on Sun Feb 15 15:30:21 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

fantas V3
=========

.. toctree::
    :maxdepth: 2
    :caption: 教程
    :hidden:

    ref/tutorials/color
    ref/tutorials/rect
    ref/tutorials/animation

.. toctree::
    :maxdepth: 2
    :caption: 模块
    :hidden:

    ref/modules/color
    ref/modules/constants
    ref/modules/curve
    ref/modules/debug
    ref/modules/event_handler
    ref/modules/fantas_typing
    ref/modules/fantas

.. toctree::
    :maxdepth: 2
    :caption: 开发帮助
    :hidden:

.. toctree::
    :maxdepth: 2
    :caption: 其他
    :hidden:

    关于 fantas 使用的 pygame-ce <ref/others/pygame-ce-for-fantas>
    致谢💖💖💖 <ref/others/thanks>

|Docs| |License| |Python| |pygame| |Code style: black|

.. |Docs| image:: https://img.shields.io/badge/docs-online-green
   :target: https://fantas.fantastair.cn/docs/
.. |License| image:: https://img.shields.io/badge/License-MIT-lightgray
   :target: `MIT License`_
.. |Python| image:: https://img.shields.io/badge/python-3-blue?logo=python
   :target: https://www.python.org/
.. |pygame| image:: https://img.shields.io/badge/pygame_ce-2.5.7_for_fantas-blue
   :target: `pygame-ce for fantas`_
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-black
   :target: https://github.com/psf/black

快速开始
--------

欢迎了解 fantas！这是一个基于 pygame-ce [1]_ 的 2D 图形程序框架。
当你安装好 fantas 后，下一个问题就是怎样让程序运行起来。你可能知道，pygame-ce 
并不是一个开箱即用的库，它需要你完全掌控整个主循环，这对于初学者来说可能会有些困难。
幸运的是，fantas 帮你做好了一切。

安装 fantas
~~~~~~~~~~~

fantas 可以通过 :code:`pip` 轻松安装：

.. code-block:: bash

    pip install fantas


小试牛刀
~~~~~~~~

来看一个简单的例子吧：

.. literalinclude:: ref/code_examples/quick_start.py
    :language: python
    :linenos:

想要来点动画吗，那就试试这个：

.. literalinclude:: ref/code_examples/quick_start_animation.py
    :language: python
    :linenos:

想要更深入地探索可以看看 :ref:`tutorials-reference-label` 或者
:ref:`references-reference-label`，祝你好运！

.. _tutorials-reference-label:

教程
----

基础概念
~~~~~~~~

fantas 中有些类是直接复用的 pygame-ce 中的类，如 :class:`fantas.Rect` 和
:class:`fantas.color.Color` 等，
关于这些类的详细信息可以在 `pygame 文档`_ 中找到，本教程则会介绍一些常用的用法和技巧。

有些类是继承自 pygame-ce 中的类，如 :class:`~fantas.window.Window` 和
:class:`~fantas.font.Font` 等，在保留了原有接口的基础上，添加了一些新的功能和属性，
新增的部分可以在本文档中找到。

还有一些类是 fantas 独有的，如 :class:`~fantas.ui.UI` 和 :class:`~fantas.curve.Curve`
等，这些类决定了 fantas 的核心逻辑和设计理念，有关详细信息也可以在本文档中找到。

- :doc:`ref/tutorials/color`
- :doc:`ref/tutorials/rect`
- :doc:`ref/tutorials/animation`

.. _references-reference-label:

参考
----

.. important::

    所有模块的接口都是在 fantas 包的顶层导出的，你不需要使用任何子模块的名字来访问它们。

- :doc:`color <ref/modules/color>`
    .. automodule:: fantas.color
        :no-members:
        :no-index:
- :doc:`constants <ref/modules/constants>`: 
    .. automodule:: fantas.constants
        :no-members:
        :no-index:
- :doc:`curve <ref/modules/curve>`
    .. automodule:: fantas.curve
        :no-members:
        :no-index:
- :doc:`debug <ref/modules/debug>`
    .. automodule:: fantas.debug
        :no-members:
        :no-index:
- :doc:`event_handler <ref/modules/event_handler>`
    .. automodule:: fantas.event_handler
        :no-members:
        :no-index:
- :doc:`fantas_typing <ref/modules/fantas_typing>`
    .. automodule:: fantas.fantas_typing
        :no-members:
        :no-index:
- :doc:`fantas <ref/modules/fantas>`
    .. automodule:: fantas
        :no-members:
        :no-index:
- :ref:`rect-documentatioin` 

开发帮助
--------

.. admonition:: 未完成

    TODO: 编写开发帮助文档。

其他
----

`GitHub`_
    这是 fantas 的代码仓库，欢迎访问、使用和贡献。

    在此也一并提供 `pygame-ce for fantas`_ 的仓库链接。fantas 使用的是其 fantas
    分支编译的版本。

`MIT License`_
    这是 fantas 的开源许可协议，允许你自由使用、修改和分发该软件，
    但必须保留原作者的版权声明和许可声明。

.. [1] pygame-ce_ 是 pygame_ 的一个社区维护版本，提供了更好的性能和更多的功能支持。
    fantas 使用的 pygame-ce 是从 pygame-ce 2.5.7 的 main 分支 fork 后进行了修改的版本。
    有关具体的修改内容，请参阅
    :doc:`关于 fantas 使用的 pygame-ce <ref/others/pygame-ce-for-fantas>` 。

.. _GitHub: https://github.com/fantastair/FantasV3

.. _MIT License: LICENSE

.. _pygame: https://www.pygame.org/

.. _pygame-ce: https://pyga.me/

.. _pygame 文档: https://pyga.me/docs/

.. _pygame-ce for fantas: https://github.com/Fantastair/pygame-ce/tree/fantas
