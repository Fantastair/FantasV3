关于 fantas 使用的 pygame-ce
============================

pygame-ce 是 fantas 的核心依赖库，fantas 使用的 pygame-ce 版本是经过针对性修改的。它
fork 自 pygame-ce 2.5.7.dev1 的 main 分支，并保持与主仓库的同步更新，
也将自己的一些修改提交回主仓库。

- fork 仓库地址：https://github.com/Fantastair/pygame-ce
- 分支名称：:code:`fantas`

主要修改内容
------------

- 修复 :code:`pygame.draw.aacircle()` 无法绘制宽度为 2 的圆环的问题

  pygame-ce 为 :code:`pygame.draw` 模块新增了一系列绘制抗锯齿图形的 API，但是
  :code:`pygame.draw.aacircle()` 只能绘制宽度为 1, 3, 4, 5, ... 的圆环，具体信息可以查看
  `issue # 3682`_ 和 `PR # 3699`_。

.. _issue # 3682: https://github.com/pygame-community/pygame-ce/issues/3682

.. _PR # 3699: https://github.com/pygame-community/pygame-ce/pull/3699

- 新增 :code:`pygame.draw.aarect()` 函数，用于绘制抗锯齿矩形

  该函数的接口和 :code:`pygame.draw.rect()` 完全兼容，但可以绘制更平滑的圆角矩形，
  具体信息可以查看 `PR # 3701`_。

.. _PR # 3701: https://github.com/pygame-community/pygame-ce/pull/3701
