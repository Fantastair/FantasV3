# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath('../../fantas'))

extensions = [
    'sphinx.ext.autodoc',      # 核心：提供 automodule/autofunction 等指令
    'sphinx.ext.napoleon',     # 可选：支持 Google/NumPy 风格的 docstring
    # 'sphinx.ext.viewcode',     # 可选：显示代码链接
    # 'sphinx.ext.todo',         # 可选：支持 todo 标记
]

autodoc_member_order = 'bysource'

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "fantas"
copyright = "2026, Fantastair"
author = "Fantastair"
release = "3.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ["_templates"]
exclude_patterns = []

language = "zh_CN"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = "fantas 文档"
html_static_path = ["_static"]
html_extra_path = [
    '../../LICENSE',
]
