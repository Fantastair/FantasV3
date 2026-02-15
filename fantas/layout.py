from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol, cast

import fantas

__all__ = (
    "Layout",
    "RelativeLayout",
    "RatioLayout",
    "DockLayout",
    "GridLayout",
)


class _HasRect(Protocol):
    rect: fantas.Rect | fantas.IntRect


@dataclass(slots=True)
class Layout(fantas.UI, ABC):
    """
    布局器基类。
    """

    def create_render_commands(
        self, offset: fantas.Point = (0, 0)
    ) -> Iterator[fantas.RenderCommand]:
        """
        创建渲染命令列表，由子类实现，本方法会遍历子节点并生成渲染命令
        Args:
            offset (fantas.Point): 当前元素的偏移位置，用于计算子元素的绝对位置。
        Yields:
            RenderCommand: 渲染命令对象。
        """
        self.auto_layout()
        yield from fantas.UI.create_render_commands(self, offset)

    @abstractmethod
    def auto_layout(self) -> None:
        """
        自动布局方法，由子类实现，负责根据布局规则调整子元素的位置和大小。
        """
        pass


@dataclass(slots=True)
class RelativeLayout(Layout):
    """
    相对布局器。
    """

    margin_dict: dict[fantas.UIID, list[int | None]] = field(
        default_factory=dict, init=False, repr=False
    )  # 元素ID到边距的映射，边距格式为 [left, top, right, bottom]
    default_margin: list[int | None] = field(
        default_factory=lambda: [None, None, None, None], init=False, repr=False
    )  # 默认边距

    def auto_layout(self) -> None:
        """
        自动相对布局。
        """
        father = cast(_HasRect, self.father)
        size = father.rect.size
        for child in self.children:
            rect_child = cast(_HasRect, child)
            left, top, right, bottom = self.margin_dict.get(
                child.ui_id, self.default_margin
            )
            # 水平布局
            if left is not None and right is not None:
                rect_child.rect.left = left
                rect_child.rect.width = size[0] - left - right
            elif left is not None:
                rect_child.rect.left = left
            elif right is not None:
                rect_child.rect.right = size[0] - right
            # 垂直布局
            if top is not None and bottom is not None:
                rect_child.rect.top = top
                rect_child.rect.height = size[1] - top - bottom
            elif top is not None:
                rect_child.rect.top = top
            elif bottom is not None:
                rect_child.rect.bottom = size[1] - bottom

    def set_margin(self, child: fantas.UI, margin: list[int | None]) -> None:
        """
        设置子元素的边距。
        Args:
            child (fantas.UI): 子元素对象。
            margin (list[int | None]): 边距值列表，格式为 [left, top, right, bottom]。
        """
        self.margin_dict[child.ui_id] = margin

    def set_margin_left(self, child: fantas.UI, left: int) -> None:
        """
        设置子元素的左边距。
        Args:
            child (fantas.UI): 子元素对象。
            left (int): 左边距值。
        """
        margin = self.margin_dict.setdefault(child.ui_id, [None, None, None, None])
        margin[0] = left

    def set_margin_top(self, child: fantas.UI, top: int) -> None:
        """
        设置子元素的上边距。
        Args:
            child (fantas.UI): 子元素对象。
            top (int): 上边距值。
        """
        margin = self.margin_dict.setdefault(child.ui_id, [None, None, None, None])
        margin[1] = top

    def set_margin_right(self, child: fantas.UI, right: int) -> None:
        """
        设置子元素的右边距。
        Args:
            child (fantas.UI): 子元素对象。
            right (int): 右边距值。
        """
        margin = self.margin_dict.setdefault(child.ui_id, [None, None, None, None])
        margin[2] = right

    def set_margin_bottom(self, child: fantas.UI, bottom: int) -> None:
        """
        设置子元素的下边距。
        Args:
            child (fantas.UI): 子元素对象。
            bottom (int): 下边距值。
        """
        margin = self.margin_dict.setdefault(child.ui_id, [None, None, None, None])
        margin[3] = bottom

    def _get_default_margin_left(self) -> int | None:
        """
        获取默认左边距。
        Returns:
            int | None: 默认左边距值，如果未设置则返回None。
        """
        return self.default_margin[0]

    def _set_default_margin_left(self, value: int | None) -> None:
        """
        设置默认左边距。
        Args:
            value (int | None): 默认左边距值，如果为None则表示不设置默认值。
        """
        self.default_margin[0] = value

    default_margin_left = property(_get_default_margin_left, _set_default_margin_left)

    def _get_default_margin_top(self) -> int | None:
        """
        获取默认上边距。
        Returns:
            int | None: 默认上边距值，如果未设置则返回None。
        """
        return self.default_margin[1]

    def _set_default_margin_top(self, value: int | None) -> None:
        """
        设置默认上边距。
        Args:
            value (int | None): 默认上边距值，如果为None则表示不设置默认值。
        """
        self.default_margin[1] = value

    default_margin_top = property(_get_default_margin_top, _set_default_margin_top)

    def _get_default_margin_right(self) -> int | None:
        """
        获取默认右边距。
        Returns:
            int | None: 默认右边距值，如果未设置则返回None。
        """
        return self.default_margin[2]

    def _set_default_margin_right(self, value: int | None) -> None:
        """
        设置默认右边距。
        Args:
            value (int | None): 默认右边距值，如果为None则表示不设置默认值。
        """
        self.default_margin[2] = value

    default_margin_right = property(
        _get_default_margin_right, _set_default_margin_right
    )

    def _get_default_margin_bottom(self) -> int | None:
        """
        获取默认下边距。
        Returns:
            int | None: 默认下边距值，如果未设置则返回None。
        """
        return self.default_margin[3]

    def _set_default_margin_bottom(self, value: int | None) -> None:
        """
        设置默认下边距。
        Args:
            value (int | None): 默认下边距值，如果为None则表示不设置默认值。
        """
        self.default_margin[3] = value

    default_margin_bottom = property(
        _get_default_margin_bottom, _set_default_margin_bottom
    )

    def append(
        self,
        node: fantas.UI,
        margin_left: int | None = None,
        margin_top: int | None = None,
        margin_right: int | None = None,
        margin_bottom: int | None = None,
    ) -> None:
        """
        添加子元素并设置边距。

        Args:
            node          (fantas.UI) : 子元素对象。
            margin_left   (int | None): 左边距值，如果为None则使用默认值。
            margin_top    (int | None): 上边距值，如果为None则使用默认值。
            margin_right  (int | None): 右边距值，如果为None则使用默认值。
            margin_bottom (int | None): 下边距值，如果为None则使用默认值。
        """
        fantas.UI.append(self, node)
        margin = [margin_left, margin_top, margin_right, margin_bottom]
        if any(margin):
            self.set_margin(node, margin)

    def insert(
        self,
        index: int,
        node: fantas.UI,
        margin_left: int | None = None,
        margin_top: int | None = None,
        margin_right: int | None = None,
        margin_bottom: int | None = None,
    ) -> None:
        """
        插入子元素并设置边距。

        Args:
            index         (int)       : 插入位置索引。
            node          (fantas.UI) : 子元素对象。
            margin_left   (int | None): 左边距值，如果为None则使用默认值。
            margin_top    (int | None): 上边距值，如果为None则使用默认值。
            margin_right  (int | None): 右边距值，如果为None则使用默认值。
            margin_bottom (int | None): 下边距值，如果为None则使用默认值。
        """
        fantas.UI.insert(self, index, node)
        margin = [margin_left, margin_top, margin_right, margin_bottom]
        if any(margin):
            self.set_margin(node, margin)

    def remove(self, node: fantas.UI) -> None:
        """
        从自己的子元素中移除 node。
        Args:
            node (fantas.UI): 子元素对象。
        Raises:
            ValueError: 要移除的子元素不是当前元素的子元素。
        """
        fantas.UI.remove(self, node)
        if node.ui_id in self.margin_dict:
            del self.margin_dict[node.ui_id]

    def pop(self, index: int) -> fantas.UI:
        """
        移除index位置的子元素。
        Args:
            index (int): 要移除子元素的位置索引。
        Returns:
            node (fantas.UI): 被移除的子元素对象。
        Raises:
            IndexError: 索引越界。
        """
        node = fantas.UI.pop(self, index)
        if node.ui_id in self.margin_dict:
            del self.margin_dict[node.ui_id]
        return node

    def clear(self) -> None:
        """
        清除所有子元素。
        """
        fantas.UI.clear(self)
        self.margin_dict.clear()

    def auto_clear(self) -> None:
        """
        清除不存在的子元素的边距数据。
        """
        for ui_id in set(self.margin_dict.keys()) - {
            child.ui_id for child in self.children
        }:
            del self.margin_dict[ui_id]


@dataclass(slots=True)
class RatioLayout(Layout):
    """
    比例布局器。
    """

    ratio_dict: dict[fantas.UIID, list[float | None]] = field(
        default_factory=dict, init=False, repr=False
    )  # 元素ID到比例的映射，比例格式为 [left_ratio, top_ratio, width_ratio, height_ratio]
    default_ratio: list[float | None] = field(
        default_factory=lambda: [None, None, None, None], init=False, repr=False
    )  # 默认比例

    def auto_layout(self) -> None:
        """
        自动比例布局。
        """
        father = cast(_HasRect, self.father)
        size = father.rect.size
        for child in self.children:
            rect_child = cast(_HasRect, child)
            left_ratio, top_ratio, width_ratio, height_ratio = self.ratio_dict.get(
                child.ui_id, self.default_ratio
            )
            if left_ratio is not None:
                rect_child.rect.left = round(size[0] * left_ratio)
            if top_ratio is not None:
                rect_child.rect.top = round(size[1] * top_ratio)
            if width_ratio is not None:
                rect_child.rect.width = round(size[0] * width_ratio)
            if height_ratio is not None:
                rect_child.rect.height = round(size[1] * height_ratio)

    def set_ratio(self, child: fantas.UI, ratio: list[float | None]) -> None:
        """
        设置子元素的比例。
        Args:
            child (fantas.UI): 子元素对象。
            ratio (list[float, float, float, float]): 比例值列表，格式为 [left_ratio, top_ratio, width_ratio, height_ratio]。
        """
        self.ratio_dict[child.ui_id] = ratio

    def set_ratio_left(self, child: fantas.UI, left_ratio: float) -> None:
        """
        设置子元素的左边距比例。
        Args:
            child (fantas.UI): 子元素对象。
            left_ratio (float): 左边距比例值。
        """
        rect_ratio = self.ratio_dict.setdefault(child.ui_id, [None, None, None, None])
        rect_ratio[0] = left_ratio

    def set_ratio_top(self, child: fantas.UI, top_ratio: float) -> None:
        """
        设置子元素的上边距比例。
        Args:
            child (fantas.UI): 子元素对象。
            top_ratio (float): 上边距比例值。
        """
        rect_ratio = self.ratio_dict.setdefault(child.ui_id, [None, None, None, None])
        rect_ratio[1] = top_ratio

    def set_ratio_width(self, child: fantas.UI, width_ratio: float) -> None:
        """
        设置子元素的宽度比例。
        Args:
            child (fantas.UI): 子元素对象。
            width_ratio (float): 宽度比例值。
        """
        rect_ratio = self.ratio_dict.setdefault(child.ui_id, [None, None, None, None])
        rect_ratio[2] = width_ratio

    def set_ratio_height(self, child: fantas.UI, height_ratio: float) -> None:
        """
        设置子元素的高度比例。
        Args:
            child (fantas.UI): 子元素对象。
            height_ratio (float): 高度比例值。
        """
        rect_ratio = self.ratio_dict.setdefault(child.ui_id, [None, None, None, None])
        rect_ratio[3] = height_ratio

    def _get_default_ratio_left(self) -> float | None:
        """
        获取默认左边距比例。
        Returns:
            float | None: 默认左边距比例值，如果未设置则返回None。
        """
        return self.default_ratio[0]

    def _set_default_ratio_left(self, value: float | None) -> None:
        """
        设置默认左边距比例。
        Args:
            value (float | None): 默认左边距比例值，如果为None则表示不设置默认值。
        """
        self.default_ratio[0] = value

    default_ratio_left = property(_get_default_ratio_left, _set_default_ratio_left)

    def _get_default_ratio_top(self) -> float | None:
        """
        获取默认上边距比例。
        Returns:
            float | None: 默认上边距比例值，如果未设置则返回None。
        """
        return self.default_ratio[1]

    def _set_default_ratio_top(self, value: float | None) -> None:
        """
        设置默认上边距比例。
        Args:
            value (float | None): 默认上边距比例值，如果为None则表示不设置默认值。
        """
        self.default_ratio[1] = value

    default_ratio_top = property(_get_default_ratio_top, _set_default_ratio_top)

    def _get_default_ratio_width(self) -> float | None:
        """
        获取默认宽度比例。
        Returns:
            float | None: 默认宽度比例值，如果未设置则返回None。
        """
        return self.default_ratio[2]

    def _set_default_ratio_width(self, value: float | None) -> None:
        """
        设置默认宽度比例。
        Args:
            value (float | None): 默认宽度比例值，如果为None则表示不设置默认值。
        """
        self.default_ratio[2] = value

    default_ratio_width = property(_get_default_ratio_width, _set_default_ratio_width)

    def _get_default_ratio_height(self) -> float | None:
        """
        获取默认高度比例。
        Returns:
            float | None: 默认高度比例值，如果未设置则返回None。
        """
        return self.default_ratio[3]

    def _set_default_ratio_height(self, value: float | None) -> None:
        """
        设置默认高度比例。
        Args:
            value (float | None): 默认高度比例值，如果为None则表示不设置默认值。
        """
        self.default_ratio[3] = value

    default_ratio_height = property(
        _get_default_ratio_height, _set_default_ratio_height
    )

    def append(
        self,
        node: fantas.UI,
        left_ratio: float | None = None,
        top_ratio: float | None = None,
        width_ratio: float | None = None,
        height_ratio: float | None = None,
    ) -> None:
        """
        添加子元素并设置比例。

        Args:
            node         (fantas.UI)   : 子元素对象。
            left_ratio   (float | None): 左边距比例值，如果为None则使用默认值。
            top_ratio    (float | None): 上边距比例值，如果为None则使用默认值。
            width_ratio  (float | None): 宽度比例值，如果为None则使用默认值。
            height_ratio (float | None): 高度比例值，如果为None则使用默认值。
        """
        fantas.UI.append(self, node)
        ratio = [left_ratio, top_ratio, width_ratio, height_ratio]
        if any(ratio):
            self.set_ratio(node, ratio)

    def insert(
        self,
        index: int,
        node: fantas.UI,
        left_ratio: float | None = None,
        top_ratio: float | None = None,
        width_ratio: float | None = None,
        height_ratio: float | None = None,
    ) -> None:
        """
        插入子元素并设置比例。

        Args:
            index        (int)         : 插入位置索引。
            node         (fantas.UI)   : 子元素对象。
            left_ratio   (float | None): 左边距比例值，如果为None则使用默认值。
            top_ratio    (float | None): 上边距比例值，如果为None则使用默认值。
            width_ratio  (float | None): 宽度比例值，如果为None则使用默认值。
            height_ratio (float | None): 高度比例值，如果为None则使用默认值。
        """
        fantas.UI.insert(self, index, node)
        ratio = [left_ratio, top_ratio, width_ratio, height_ratio]
        if any(ratio):
            self.set_ratio(node, ratio)

    def remove(self, node: fantas.UI) -> None:
        """
        从自己的子元素中移除 node。
        Args:
            node (fantas.UI): 子元素对象。
        Raises:
            ValueError: 要移除的子元素不是当前元素的子元素。
        """
        fantas.UI.remove(self, node)
        if node.ui_id in self.ratio_dict:
            del self.ratio_dict[node.ui_id]

    def pop(self, index: int) -> fantas.UI:
        """
        移除index位置的子元素。
        Args:
            index (int): 要移除子元素的位置索引。
        Returns:
            node (fantas.UI): 被移除的子元素对象。
        Raises:
            IndexError: 索引越界。
        """
        node = fantas.UI.pop(self, index)
        if node.ui_id in self.ratio_dict:
            del self.ratio_dict[node.ui_id]
        return node

    def clear(self) -> None:
        """
        清除所有子元素。
        """
        fantas.UI.clear(self)
        self.ratio_dict.clear()

    def auto_clear(self) -> None:
        """
        清除不存在的子元素的比例数据。
        """
        for ui_id in set(self.ratio_dict.keys()) - {
            child.ui_id for child in self.children
        }:
            del self.ratio_dict[ui_id]


@dataclass(slots=True)
class DockLayout(Layout):
    """
    停靠布局器。
    """

    dock_mode_dict: dict[fantas.UIID, fantas.DockMode] = field(
        default_factory=dict, init=False, repr=False
    )  # 元素ID到停靠模式的映射

    def auto_layout(self) -> None:
        """
        自动停靠布局。
        """
        father = cast(_HasRect, self.father)
        free_rect = father.rect.copy()  # 剩余空间矩形，初始为父元素矩形
        free_rect.topleft = (0, 0)  # 初始偏移为 (0, 0)
        for child in self.children:
            rect_child = cast(_HasRect, child)
            if free_rect.width <= 0 or free_rect.height <= 0:
                break
            dock_mode = self.dock_mode_dict.get(child.ui_id, fantas.DockMode.NONE)
            if dock_mode == fantas.DockMode.LEFT:
                rect_child.rect.topleft = free_rect.topleft
                rect_child.rect.height = free_rect.height
                free_rect.left += rect_child.rect.width
                free_rect.width -= rect_child.rect.width
            elif dock_mode == fantas.DockMode.TOP:
                rect_child.rect.topleft = free_rect.topleft
                rect_child.rect.width = free_rect.width
                free_rect.top += rect_child.rect.height
                free_rect.height -= rect_child.rect.height
            elif dock_mode == fantas.DockMode.RIGHT:
                rect_child.rect.topright = free_rect.topright
                rect_child.rect.height = free_rect.height
                free_rect.width -= rect_child.rect.width
            elif dock_mode == fantas.DockMode.BOTTOM:
                rect_child.rect.bottomleft = free_rect.bottomleft
                rect_child.rect.width = free_rect.width
                free_rect.height -= rect_child.rect.height
            elif dock_mode == fantas.DockMode.FILL:
                rect_child.rect.update(free_rect)
                free_rect.width = 0
                free_rect.height = 0

    def set_dock_mode(self, child: fantas.UI, dock_mode: fantas.DockMode) -> None:
        """
        设置子元素的停靠模式。
        Args:
            child (fantas.UI): 子元素对象。
            dock_mode (fantas.DockMode): 停靠模式值。
        """
        self.dock_mode_dict[child.ui_id] = dock_mode

    def append(
        self, node: fantas.UI, dock_mode: fantas.DockMode = fantas.DockMode.NONE
    ) -> None:
        """
        添加子元素并设置停靠模式。

        Args:
            node (fantas.UI): 子元素对象。
            dock_mode (fantas.DockMode): 停靠模式值，默认为 fantas.DockMode.NONE。
        """
        fantas.UI.append(self, node)
        if dock_mode != fantas.DockMode.NONE:
            self.set_dock_mode(node, dock_mode)

    def insert(
        self,
        index: int,
        node: fantas.UI,
        dock_mode: fantas.DockMode = fantas.DockMode.NONE,
    ) -> None:
        """
        插入子元素并设置停靠模式。

        Args:
            index (int): 插入位置索引。
            node (fantas.UI): 子元素对象。
            dock_mode (fantas.DockMode): 停靠模式值，默认为 fantas.DockMode.NONE。
        """
        fantas.UI.insert(self, index, node)
        if dock_mode != fantas.DockMode.NONE:
            self.set_dock_mode(node, dock_mode)

    def remove(self, node: fantas.UI) -> None:
        """
        从自己的子元素中移除 node。
        Args:
            node (fantas.UI): 子元素对象。
        Raises:
            ValueError: 要移除的子元素不是当前元素的子元素。
        """
        fantas.UI.remove(self, node)
        if node.ui_id in self.dock_mode_dict:
            del self.dock_mode_dict[node.ui_id]

    def pop(self, index: int) -> fantas.UI:
        """
        移除index位置的子元素。
        Args:
            index (int): 要移除子元素的位置索引。
        Returns:
            node (fantas.UI): 被移除的子元素对象。
        Raises:
            IndexError: 索引越界。
        """
        node = fantas.UI.pop(self, index)
        if node.ui_id in self.dock_mode_dict:
            del self.dock_mode_dict[node.ui_id]
        return node

    def clear(self) -> None:
        """
        清除所有子元素。
        """
        fantas.UI.clear(self)
        self.dock_mode_dict.clear()

    def auto_clear(self) -> None:
        """
        清除不存在的子元素的停靠模式数据。
        """
        for ui_id in set(self.dock_mode_dict.keys()) - {
            child.ui_id for child in self.children
        }:
            del self.dock_mode_dict[ui_id]


@dataclass(slots=True)
class GridLayout(Layout):
    """
    网格布局器。
    """

    rows: list[int | float] = field(
        default_factory=list, init=False, repr=False
    )  # 行高列表，0 表示自适应高度，大于0表示固定高度，介于0和1之间表示比例高度
    columns: list[int | float] = field(
        default_factory=list, init=False, repr=False
    )  # 列宽列表，0 表示自适应宽度，大于0表示固定宽度，介于0和1之间表示比例宽度
    cell_dict: dict[fantas.UIID, tuple[int, int]] = field(
        default_factory=dict, init=False, repr=False
    )  # 元素ID到单元格位置的映射，单元格位置格式为 (row_index, column_index)

    def auto_layout(self) -> None:
        """
        自动网格布局。
        """
        # 获取父元素的宽高
        father = cast(_HasRect, self.father)
        total_width = father.rect.width
        total_height = father.rect.height
        # 计算行列坐标
        rt = self.rows.copy()  # 行顶端坐标列表
        cl = self.columns.copy()  # 列左端坐标列表
        # 将比例尺寸转换为绝对尺寸
        for i in range(len(rt)):
            if 0 < rt[i] < 1:
                rt[i] = total_height * rt[i]
        for i in range(len(cl)):
            if 0 < cl[i] < 1:
                cl[i] = total_width * cl[i]
        # 计算自适应尺寸
        auto_width = (
            (total_width - sum(width for width in cl if width > 0)) / cl.count(0)
            if cl.count(0) > 0
            else 0
        )
        auto_height = (
            (total_height - sum(height for height in rt if height > 0)) / rt.count(0)
            if rt.count(0) > 0
            else 0
        )
        for i in range(len(rt)):
            if rt[i] == 0:
                rt[i] = auto_height
        for i in range(len(cl)):
            if cl[i] == 0:
                cl[i] = auto_width
        # 计算累积坐标
        rt.insert(0, 0)
        cl.insert(0, 0)
        for i in range(1, len(rt)):
            rt[i] = round(rt[i] + rt[i - 1])
        for i in range(1, len(cl)):
            cl[i] = round(cl[i] + cl[i - 1])
        # 最后强行设置为总宽高，防止计算误差
        if len(rt) > 0:
            rt[-1] = total_height
        if len(cl) > 0:
            cl[-1] = total_width
        # 设置子元素位置和大小
        for child in self.children:
            rect_child = cast(_HasRect, child)
            row_index, column_index = self.cell_dict.get(child.ui_id, (0, 0))
            rect_child.rect.left = cl[column_index]
            rect_child.rect.top = rt[row_index]
            rect_child.rect.width = cl[column_index + 1] - cl[column_index]
            rect_child.rect.height = rt[row_index + 1] - rt[row_index]

    def set_cell(self, child: fantas.UI, row_index: int, column_index: int) -> None:
        """
        设置子元素的单元格位置。
        Args:
            child (fantas.UI): 子元素对象。
            row_index (int): 行索引。
            column_index (int): 列索引。
        """
        self.cell_dict[child.ui_id] = (row_index, column_index)

    def set_size(self, row: int, column: int) -> None:
        """
        设置网格的行列数及默认单元格大小。
        Args:
            row (int): 行数。
            column (int): 列数。
        """
        self.rows = [0] * row
        self.columns = [0] * column

    def set_row_height(self, row_index: int, height: int | float) -> None:
        """
        设置指定行的高度。
        Args:
            row_index (int): 行索引。
            height (int | float): 行高度，可以是固定高度或比例高度或自适应高度。
        """
        self.rows[row_index] = height

    def set_column_width(self, column_index: int, width: int | float) -> None:
        """
        设置指定列的宽度。
        Args:
            column_index (int): 列索引。
            width (int | float): 列宽度，可以是固定宽度或比例宽度或自适应宽度。
        """
        self.columns[column_index] = width

    def append(
        self, node: fantas.UI, row_index: int = 0, column_index: int = 0
    ) -> None:
        """
        添加子元素并设置单元格位置。
        Args:
            node (fantas.UI): 子元素对象。
            row_index (int): 行索引，默认为0。
            column_index (int): 列索引，默认为0。
        """
        fantas.UI.append(self, node)
        if (row_index, column_index) != (0, 0):
            self.set_cell(node, row_index, column_index)

    def insert(
        self, index: int, node: fantas.UI, row_index: int = 0, column_index: int = 0
    ) -> None:
        """
        插入子元素并设置单元格位置。
        Args:
            index (int): 插入位置索引。
            node (fantas.UI): 子元素对象。
            row_index (int): 行索引，默认为0。
            column_index (int): 列索引，默认为0。
        """
        fantas.UI.insert(self, index, node)
        if (row_index, column_index) != (0, 0):
            self.set_cell(node, row_index, column_index)

    def remove(self, node: fantas.UI) -> None:
        """
        从自己的子元素中移除 node。
        Args:
            node (fantas.UI): 子元素对象。
        Raises:
            ValueError: 要移除的子元素不是当前元素的子元素。
        """
        fantas.UI.remove(self, node)
        if node.ui_id in self.cell_dict:
            del self.cell_dict[node.ui_id]

    def pop(self, index: int) -> fantas.UI:
        """
        移除index位置的子元素。
        Args:
            index (int): 要移除子元素的位置索引。
        Returns:
            node (fantas.UI): 被移除的子元素对象。
        Raises:
            IndexError: 索引越界。
        """
        node = fantas.UI.pop(self, index)
        if node.ui_id in self.cell_dict:
            del self.cell_dict[node.ui_id]
        return node

    def clear(self) -> None:
        """
        清除所有子元素。
        """
        fantas.UI.clear(self)
        self.cell_dict.clear()

    def auto_clear(self) -> None:
        """
        清除不存在的子元素的单元格数据。
        """
        for ui_id in set(self.cell_dict.keys()) - {
            child.ui_id for child in self.children
        }:
            del self.cell_dict[ui_id]
