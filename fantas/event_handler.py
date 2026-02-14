from __future__ import annotations
from dataclasses import dataclass, field

import fantas

__all__ = ("EventHandler",)


@dataclass(slots=True)
class EventHandler:
    """
    事件处理器，负责预处理并分发事件。
    Args:
        window: 关联的窗口对象。
    """

    window: fantas.Window

    active_ui: fantas.UI = field(init=False)  # 当前激活的 UI 元素
    hover_ui: fantas.UI = field(init=False)  # 当前鼠标悬停的 UI 元素
    last_hover_ui: fantas.UI = field(init=False)  # 上一次鼠标悬停的 UI 元素
    last_pressed_ui: fantas.UI | None = field(
        default=None, init=False
    )  # 上一次按下的 UI 元素
    listener_dict: fantas.ListenerDict = field(
        default_factory=dict, init=False
    )  # 事件监听注册表

    def __post_init__(self):
        self.active_ui = self.hover_ui = self.last_hover_ui = self.window.root_ui

        pre_handle_event = (
            (fantas.WINDOWCLOSE, self.handle_windowclose_event),
            (fantas.WINDOWLEAVE, self.handle_windowleave_event),
            (fantas.WINDOWRESIZED, self.handle_windowresized_event),
            (fantas.MOUSEMOTION, self.handle_mousemotion_event),
            (fantas.MOUSEBUTTONDOWN, self.handle_mousebuttondown_event),
            (fantas.MOUSEBUTTONUP, self.handle_mousebuttonup_event),
        )

        # 注册事件的预处理器
        for event_type, handler in pre_handle_event:
            self.add_event_listener(event_type, self.window.root_ui, True, handler)

    def handle_event(self, event: fantas.Event, focused_ui: fantas.UI | None = None):
        """
        处理单个事件。
        Args:
            event      (fantas.Event)    : 要处理的事件对象。
            focused_ui (fantas.UI | None): 事件传递的焦点 UI 元素，为 None 会自动确认焦点。
        """
        # 获取焦点 UI 元素
        if focused_ui is None:
            # 鼠标事件的焦点为当前悬停的 UI 元素，其他事件的焦点为当前激活的 UI 元素
            focused_ui = (
                self.hover_ui
                if fantas.get_event_category(event.type) == fantas.EventCategory.MOUSE
                else self.active_ui
            )
        # 构建传递路径
        event_pass_path = focused_ui.get_pass_path()
        # 事件传递 [根节点 -> ... -> 焦点节点（捕获阶段）, 焦点节点 -> ... -> 根节点（冒泡阶段）]
        for ui in reversed(event_pass_path):
            # 捕获阶段
            # 依次调用回调函数
            for callback in self.listener_dict.get((event.type, ui.ui_id, True), []):
                # 如果回调函数返回 True，停止事件传递
                if callback(event):
                    return
        for ui in event_pass_path:
            # 冒泡阶段
            # 依次调用回调函数
            for callback in self.listener_dict.get((event.type, ui.ui_id, False), []):
                # 如果回调函数返回 True，停止事件传递
                if callback(event):
                    return

    def add_event_listener(
        self,
        event_type: fantas.EventType,
        ui: fantas.UI,
        use_capture: bool,
        listener: fantas.ListenerFunc,
    ):
        """
        为指定事件类型和 UI 元素添加事件监听器。
        Args:
            event_type  (fantas.EventType)   : 事件类型。
            ui          (fantas.UI)          : 关联的 UI 元素。
            use_capture (bool)               : 是否在捕获阶段调用回调函数。
            listener    (fantas.ListenerFunc): 要添加的事件监听函数。
        """
        # 获取或创建该监听器键的监听函数列表
        listener_list = self.listener_dict.setdefault(
            (event_type, ui.ui_id, use_capture), []
        )
        # 添加回调函数到列表
        listener_list.append(listener)

    def remove_event_listener(
        self,
        event_type: fantas.EventType,
        ui: fantas.UI,
        use_capture: bool,
        listener: fantas.ListenerFunc,
    ):
        """
        移除指定事件类型和 UI 元素的事件监听器。
        Args:
            event_type  (fantas.EventType)   : 事件类型。
            ui          (fantas.UI)          : 关联的 UI 元素。
            use_capture (bool)               : 是否在捕获阶段调用回调函数。
            listener    (fantas.ListenerFunc): 要移除的事件监听函数。
        Raises:
            ValueError: 如果指定的监听器不存在则引发此异常。
        """
        # 获取该监听器键的回调函数列表
        listener_list = self.listener_dict.get((event_type, ui.ui_id, use_capture), [])
        # 尝试移除回调函数
        try:
            listener_list.remove(listener)
        except ValueError:
            raise ValueError("监听器不存在。") from None

    def set_hover_ui(self, ui: fantas.UI):
        """
        设置当前悬停的 UI 元素。
        Args:
            ui (fantas.UI): 要设置为悬停的 UI 元素。
        """
        # 更新悬停的 UI 元素
        self.last_hover_ui = self.hover_ui
        self.hover_ui = ui
        # 获取悬停传递路径
        this_hover_pass_path = self.hover_ui.get_pass_path()
        last_hover_pass_path = self.last_hover_ui.get_pass_path()
        # 查找最近公共祖先节点索引
        lca_index = 0  # 最近公共祖先节点索引
        for i, (last_ui, this_ui) in enumerate(
            zip(reversed(last_hover_pass_path), reversed(this_hover_pass_path))
        ):
            if last_ui is this_ui:
                lca_index = i
            else:
                break
        # 触发事件
        if lca_index < len(last_hover_pass_path) - 1:  # 有节点移出
            self.handle_event(
                fantas.Event(fantas.MOUSELEAVED, ui=last_hover_pass_path[0]),
                focused_ui=last_hover_pass_path[0],
            )
        if lca_index < len(this_hover_pass_path) - 1:  # 有节点移入
            self.handle_event(
                fantas.Event(fantas.MOUSEENTERED, ui=this_hover_pass_path[0]),
                focused_ui=this_hover_pass_path[0],
            )

    def set_active_ui(self, ui: fantas.UI):
        """
        设置当前激活的 UI 元素。
        Args:
            ui (fantas.UI): 要设置为激活的 UI 元素。
        """
        self.active_ui = ui

    def handle_windowclose_event(self, event: fantas.Event):
        """
        处理窗口关闭事件。
        Args:
            event (fantas.Event): 关闭事件对象。
        """
        if event.window is self.window:
            self.window.running = False

    def handle_windowleave_event(self, event: fantas.Event):
        """
        处理窗口离开事件，设置悬停 UI 元素为根节点。
        Args:
            event (fantas.Event): 窗口离开事件对象。
        """
        if event.window is self.window:
            self.set_hover_ui(self.window.root_ui)
            self.set_active_ui(self.window.root_ui)

    def handle_windowresized_event(self, event: fantas.Event):
        """
        处理窗口调整大小事件，更新根 UI 元素的矩形。
        Args:
            event (fantas.Event): 窗口调整大小事件对象。
        """
        if event.window is self.window:
            self.window.root_ui.update_rect()

    def handle_mousemotion_event(self, event: fantas.Event):
        """
        处理鼠标移动事件，更新悬停的 UI 元素。
        Args:
            event (fantas.Event): 鼠标移动事件对象。
        """
        # 更新悬停的 UI 元素
        self.set_hover_ui(self.window.renderer.coordinate_hit_test(event.pos))

    def handle_mousebuttondown_event(self, event: fantas.Event):
        """
        处理鼠标按下事件，更新激活的 UI 元素。
        Args:
            event (fantas.Event): 鼠标按下事件对象。
        """
        if event.button != fantas.BUTTON_LEFT:
            return
        # 更新激活的 UI 元素
        self.set_active_ui(self.hover_ui)
        # 更新上一次按下的 UI 元素
        self.last_pressed_ui = self.hover_ui

    def handle_mousebuttonup_event(self, event: fantas.Event):
        """
        处理鼠标释放事件。
        Args:
            event (fantas.Event): 鼠标释放事件对象。
        """
        # 判断有效单击
        if self.last_pressed_ui is self.hover_ui:
            self.handle_event(
                fantas.Event(fantas.MOUSECLICKED, ui=self.hover_ui),
                focused_ui=self.hover_ui,
            )
        # 清除上一次按下的 UI 元素
        self.last_pressed_ui = None
