.. fantas documentation master file, created by
   sphinx-quickstart on Sun Feb 15 15:30:21 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

fantas V3
=========

|Docs| |License| |Python| |pygame| |Code style: black|

.. |Docs| image:: https://img.shields.io/badge/docs-online-green
   :target: #
.. |License| image:: https://img.shields.io/badge/License-MIT-lightgray
   :target: `MIT License`_
.. |Python| image:: https://img.shields.io/badge/python-3-blue?logo=python
   :target: https://www.python.org/
.. |pygame| image:: https://img.shields.io/badge/pygame_ce-2.5.7_for_fantas-blue
   :target: #
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

fantas 可以通过 pip 轻松安装：

.. code-block:: bash

    pip install fantas  # 最简单

    pip3 install fantas  # 兼容性更好

    python -m pip install fantas  # 兼容性最好

.. admonition:: 暂时未发布到 PyPI
    :class: warning

    目前 fantas 还没有发布到 PyPI 上，你可能需要从 GitHub 仓库下载并自行编译安装。

    别担心，fantas 提供了开发用的一键安装脚本 :code:`python dev.py install`，
    希望你不会碰到未知的错误。

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

想要更深入的探索可以看看 :ref:`tutorials-reference-label` 或者各个模块的接口文档，祝你好运！

.. _tutorials-reference-label:

教程
----

.. toctree::
    :maxdepth: 1
    :caption: 教程
    :hidden:


.. admonition:: 未完成

    TODO: 编写教程。

模块
----

.. toctree::
    :maxdepth: 1
    :caption: 模块
    :hidden:

    ref/modules/color
    ref/modules/constants
    ref/modules/curve
    ref/modules/debug
    ref/modules/fantas

.. hint:: 一般情况下，不需要手动导入任何 fantas 的子模块，直接导入 fantas 就可以了。

如果你想要知道某个东西如何使用，前往对应的模块文档，那里有详细的接口说明和使用示例。
如果你想要了解 fantas 的实现细节，或者想要参与开发，可以看看下面的介绍。

其他
----

.. toctree::
    :maxdepth: 2
    :caption: 其他
    :hidden:

    关于 fantas 使用的 pygame-ce <pygame-ce-for-fantas>
    致谢 <thanks>

`GitHub`_
    这是 fantas 的代码仓库，欢迎访问、使用和贡献。

`MIT License`_
    这是 fantas 的开源许可协议，允许你自由使用、修改和分发该软件，
    但必须保留原作者的版权声明和许可声明。

.. [1] pygame-ce_ 是 pygame_ 的一个社区维护版本，提供了更好的性能和更多的功能支持。
    fantas 使用的 pygame-ce 是从 pygame-ce 2.5.7 的 main 分支 fork 后进行了修改的版本。
    有关具体的修改内容，请参阅 :doc:`关于 fantas 使用的 pygame-ce <pygame-ce-for-fantas>` ，
    有关许可信息，请参阅 `DEPENDENCIES.md`_。

.. _GitHub: https://github.com/fantastair/FantasV3

.. _MIT License: LICENSE

.. _pygame: https://www.pygame.org/

.. _pygame-ce: https://pyga.me/

.. _DEPENDENCIES.md: https://github.com/fantastair/FantasV3#dependenciesmd
