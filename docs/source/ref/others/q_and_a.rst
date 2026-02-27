Q&A: 你想知道的一切
===============================

.. container:: question

   fantas 是什么？它和 pygame-ce 有什么关系？

.. container:: answer

    fantas 是一个基于 pygame-ce 的跨平台图形程序开发框架，旨在简化开发过程。
    它使用了 pygame-ce 作为底层图形库，并在此基础上进行了扩展和优化。

.. container:: question

   fantas 支持哪些平台？

.. container:: answer

    fantas 原生支持 Windows、macOS 和 Linux 等主流桌面平台。fantas 本身是一个纯 Python
    库，因此对其他平台的支持取决于 pygame-ce 的兼容性，理论上可以实验性支持 Android、
    iOS、Web 等平台，但可能需要额外的配置和适配工作。

.. container:: question

   pygame/pygame-ce 项目可以直接迁移到 fantas 吗？

.. container:: answer

    大部分 pygame 项目不可以直接迁移到 fantas，因为 pygame 本身是一个自由度极高的图形库，
    fantas 只是选择了一种可行的逻辑进行封装，一般情况下需要对项目进行一定程度的重构才能
    适配 fantas 的框架设计。
