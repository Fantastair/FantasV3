使用 :code:`dev.py` 脚本
========================

这个脚本集成了所有开发过程中可能需要用到的命令，执行命令 :code:`python dev.py --help`
可以查看所有可用的命令和选项。

.. hint::

    大多数情况下，:code:`dev.py` 内部使用绝对路径，
    但是执行脚本时最好确保工作目录为项目根目录，避免出现未知的错误。

关于 Python 环境
----------------

你不需要手动安装任何库，:code:`dev.py` 在运行时会自动检测依赖并安装它们（确保你有网络连接），
你也不需要手动创建虚拟环境，:code:`dev.py` 会为当前项目自动创建一个虚拟环境并提示你切换
（当然，如果你已经手动创建了虚拟环境，:code:`dev.py` 会直接使用它）

运行命令
--------

.. important::

    使用 :code:`dev.py` 前，请确保 git 仓库处于干净状态（没有未提交的更改），
    否则命令将中止，可以传递 :code:`--ignore-git` 或 :code:`-i` 选项来跳过检查。

使用 :code:`dev.py` 的基本格式如下：

.. code-block:: bash

    python dev.py COMMAND [ARGS]...

其中 :code:`COMMAND` 是子命令，:code:`ARGS` 是传递给子命令的参数，你可以执行
:code:`python dev.py COMMAND --help` 来查看子命令的帮助信息。

所有可用的子命令如下：

prep-all
~~~~~~~~

.. code-block:: bash

    python dev.py prep-all [--ignore-git / -i]

执行所有准备工作。

该命令适合克隆仓库后第一次执行，事实上其他所有命令在开始前都会执行一遍 :code:`prep-all`
的工作确保环境准备就绪，所以你也可以直接执行其他命令来完成准备工作。

format
~~~~~~

.. code-block:: bash

    python dev.py format [--ignore-git / -i]

格式化代码。

.. hint::

    如果执行 format 以后 git 检测到有更改，会自动帮你生成一次 commit（需要你手动确认），
    如果你传递了 :code:`--ignore-git` 或 :code:`-i` 选项来跳过检查，那么这个自动 commit
    的功能也会被跳过。

.. important::

    提交 PR 或 push 到主分支时，CI 会自动执行该命令来格式化代码，如果产生了更改，CI 会失败，
    因此请务必在提交 PR 或 push 之前先执行该命令来格式化代码。

stubs
~~~~~

.. code-block:: bash

    python dev.py stubs [--ignore-git / -i]

静态类型检查。


.. important::

    提交 PR 或 push 到主分支时，CI 会自动执行该命令来检查代码静态类型，如果检查不通过，
    CI 会失败，因此请务必在提交 PR 或 push 之前先执行该命令来检查代码。

lint
~~~~

.. code-block:: bash

    python dev.py lint [--ignore-git / -i]

代码质量检查。

.. important::

    提交 PR 或 push 到主分支时，CI 会自动执行该命令来检查代码质量，如果评分低于 9.5，CI 会失败，
    因此请务必在提交 PR 或 push 之前先执行该命令来检查代码质量。

docs
~~~~

.. code-block:: bash

    python dev.py docs [--full / -f] [--quiet / --no-quiet] [--ignore-git / -i]

生成文档。

- :code:`--full / -f`

  重新生成完整文档，忽略之前的构建缓存。适用于某些文档内容没有更新但是索引更新了的情况。

- :code:`--quiet / --no-quiet`

  是否在生成文档时显示输出。

  .. warning::

    该选项默认为 :code:`--quiet`，只在生成文档失败时显示错误信息，
    这会被判断为生成文档失败。而如果你传递了 :code:`--no-quiet`
    选项来显示生成文档的输出，脚本无法通过是否有输出来判断文档是否生成成功，
    需要你手动检查输出信息来判断文档是否生成成功。

test
~~~~

.. code-block:: bash

    python dev.py test [--ignore-git / -i] [mod]...

运行测试。

- :code:`mod`

  可选参数，指定要测试的模块，如果不指定则测试所有模块。可以指定多个模块。

  .. code-block:: bash

      e.g.
      python dev.py test test/test_color.py test/test_curve.py

.. important::

    提交 PR 或 push 到主分支时，CI 会自动执行该命令来运行测试，如果测试失败，CI 会失败，
    因此请务必在提交 PR 或 push 之前先执行该命令来确认测试能够成功。

build
~~~~~

.. code-block:: bash

    python dev.py build [--ignore-git / -i] [--install / --no-install] [target]

构建项目。

- :code:`--install / --no-install`

  是否在构建完成后安装项目（常规安装 [1]_）。默认为 :code:`--no-install`，即不安装项目。

- :code:`target`

  指定构建产物（即 whl 文件）的输出目录，默认为项目根目录下的 dist 目录。

.. note::

    :code:`build` 命令只会构建当前系统和架构的 whl 文件，fantas 支持单机器构建全平台，
    参见 :ref:`command-reference-build-all` 命令。

install
~~~~~~~

.. code-block:: bash

    python dev.py install [--ignore-git / -i]

安装项目（可编辑安装 [2]_）。

此命令不需要提前构建项目，速度比 :code:`build` 命令快很多，
且安装后对源代码的修改会实时生效，适合开发过程中使用。

.. _command-reference-build-all:

build-all
~~~~~~~~~

.. code-block:: bash

    python dev.py build-all [--ignore-git / -i] [--yes / -y] [target]

构建所有支持的平台和架构的 whl 文件。

- :code:`--yes / -y`

  跳过确认提示。

  .. warning::

    该命令适合在 CI 中使用，因为如果命令中途失败，可能会污染开发环境，
    所以本地运行前会要求输入确认信息来继续。

pre-pr
~~~~~~

.. code-block:: bash

    python dev.py pre-pr [--ignore-git / -i]

本地检查是否可以提交 PR。

这是一条简化命令，如果你不想单独输入前面的某些命令，
可以直接执行该命令来完成所有检查工作，以确保你的代码符合提交 PR 的要求。
推荐在提交 PR 或 push 之前先执行该命令来检查代码，以避免 CI 检查失败。

release
~~~~~~~

.. code-block:: bash

    python dev.py release [--ignore-git / -i] [--yes / -y]

创建 release/* 分支。

- :code:`--yes / -y`

  跳过确认提示。

fantas 的发布是自动化的，通过推送一个 release/* 分支到远程仓库来触发 GitHub Actions
工作流来完成发布工作，该命令用于快捷创建并推送 release/* 分支。

.. [1] 一般的 pip 安装就是常规安装，会将代码安装到解释器的 site-packages 目录下。

.. [2] 与常规安装对应的是可编辑安装（editable），
       这会在 site-packages 目录下创建一个链接指向源代码，只要修改源代码就会实时生效，
       适合开发过程中使用，避免了每次修改后都需要重新安装的麻烦。
