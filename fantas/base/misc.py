"""
base 模块的杂项工具。
"""

from itertools import count
from time import perf_counter_ns as get_time_ns

__all__ = (
    "get_time_ns",
    "generate_unique_id",
)


# 全局唯一 ID 生成器
id_counter = count()


def generate_unique_id() -> int:
    """
    生成一个全局唯一的整数 ID。
    Returns:
        int: 唯一整数 ID。
    """
    return next(id_counter)
