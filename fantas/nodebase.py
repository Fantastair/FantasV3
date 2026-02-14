from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque

__all__ = ("NodeBase",)


@dataclass(slots=True)
class NodeBase:
    """树形节点基类，数据域由子类实现。"""

    father: NodeBase | None = field(default=None, init=False)  # 指向父节点
    children: list[NodeBase] = field(
        default_factory=list, init=False
    )  # 存储孩子节点，有序
    pass_path_cache: list[NodeBase] | None = field(
        default=None, init=False, repr=False
    )  # 传递路径缓存

    # === 结构操作方法 ===

    def append(self, node: NodeBase):
        """
        添加 node 节点至最后子节点。
        如果 node 已有父节点，则会先将 node 从其父节点中移除。
        Args:
            node (NodeBase): 要添加的节点。
        """
        if not node.is_root():
            node.leave()
        node.father = self
        self.children.append(node)

    def insert(self, index: int, node: NodeBase):
        """
        插入 node 至 index 位置。
        如果 node 已有父节点，则会先将 node 从其父节点中移除。
        Args:
            index (int): 插入位置索引。
            node (NodeBase): 要插入的节点。
        """
        if not node.is_root():
            node.leave()
        node.father = self
        self.children.insert(index, node)

    def remove(self, node: NodeBase):
        """
        从自己的子节点中移除 node。
        Args:
            node (NodeBase): 要移除的节点。
        Raises:
            ValueError: 要移除的节点不是当前节点的子节点。
        """
        try:
            self.children.remove(node)
            node.father = None
            node.clear_pass_path_cache()
        except ValueError:
            raise ValueError("要移除的节点不是当前节点的子节点。") from None

    def pop(self, index: int) -> NodeBase:
        """
        移除index位置的node。
        Args:
            index (int): 要移除节点的位置索引。
        Returns:
            node (NodeBase): 被移除的节点。
        Raises:
            IndexError: 索引越界。
        """
        try:
            node = self.children.pop(index)
            node.father = None
            node.clear_pass_path_cache()
            return node
        except IndexError:
            raise IndexError("索引越界。") from None

    def leave(self):
        """从父节点中移除自己。"""
        if self.father is not None:
            self.father.remove(self)

    def clear(self):
        """移除所有子节点。"""
        for child in self.children:
            child.father = None
            child.clear_pass_path_cache()
        self.children.clear()

    def build_pass_path_cache(self):
        """构建传递路径缓存，包括自己及所有子节点。"""
        build_queue = deque()
        build_queue.append(self)
        while build_queue:
            node = build_queue.popleft()
            # 构建当前节点的传递路径缓存
            node.get_pass_path()
            # 将子节点加入队列
            if not node.is_leaf():
                for child in node.children:
                    build_queue.append(child)

    def clear_pass_path_cache(self):
        """清除传递路径缓存，包括自己及所有子节点。"""
        clear_queue = deque()
        clear_queue.append(self)
        while clear_queue:
            node = clear_queue.popleft()
            # 清除当前节点的传递路径缓存
            node.pass_path_cache = None
            # 将子节点加入队列
            if not node.is_leaf():
                for child in node.children:
                    clear_queue.append(child)

    # === 信息查询方法 ===

    def is_root(self) -> bool:
        """是否为根节点。"""
        return self.father is None

    def is_leaf(self) -> bool:
        """是否为叶子节点。"""
        return not self.children

    def get_index(self) -> int:
        """查询自己在父节点中的位置。"""
        return self.father.children.index(self)

    def get_pass_path(self) -> list[NodeBase]:
        """
        获取传递路径。
        传递路径是从自己到根节点的节点列表。
        Returns:
            list[NodeBase]: 从自己到根节点的路径列表。
        """
        # 如果缓存命中，直接返回缓存
        if self.pass_path_cache is not None:
            return self.pass_path_cache
        # 如果是根节点，路径即为自己
        elif self.is_root():
            return [self]
        # 否则递归获取父节点的传递路径并添加自己
        self.pass_path_cache = [self] + self.father.get_pass_path()
        return self.pass_path_cache
