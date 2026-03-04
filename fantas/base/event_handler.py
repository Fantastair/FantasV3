"""
提供事件处理器类。
"""

from __future__ import annotations
from dataclasses import dataclass, field

import fantas

__all__ = ("EventHandler",)


@dataclass(slots=True)
class EventHandler:
    """
    事件处理器，负责预处理并分发事件。
    """

    window: fantas.Window
    """ 关联的窗口对象 """

    active_ui: fantas.UI = field(init=False)
    """ 当前激活的 UI 元素 """
    hover_ui: fantas.UI = field(init=False)
    """ 当前鼠标悬停的 UI 元素 """
    last_hover_ui: fantas.UI = field(init=False)
    """ 上一次鼠标悬停的 UI 元素 """
    last_pressed_ui: fantas.UI | None = field(default=None, init=False)
    """ 上一次按下的 UI 元素 """
    listener_dict: fantas.ListenerDict = field(default_factory=dict, init=False)
    """ 事件监听注册表 """

    def __post_init__(self) -> None:
        self.active_ui = self.hover_ui = self.last_hover_ui = self.window.root_ui

        pre_handle_event = (
            (fantas.WINDOWCLOSE, self._handle_windowclose_event),
            (fantas.WINDOWLEAVE, self._handle_windowleave_event),
            (fantas.WINDOWRESIZED, self._handle_windowresized_event),
            (fantas.MOUSEMOTION, self._handle_mousemotion_event),
            (fantas.MOUSEBUTTONDOWN, self._handle_mousebuttondown_event),
            (fantas.MOUSEBUTTONUP, self._handle_mousebuttonup_event),
        )

        # 注册事件的预处理器
        for event_type, handler in pre_handle_event:
            self.add_event_listener(event_type, self.window.root_ui, True, handler)

    def handle_event(
        self, event: fantas.Event, focused_ui: fantas.UI | None = None
    ) -> None:
        """
        处理单个事件。

        :param event: 要处理的事件对象。
        :type event: fantas.Event
        :param focused_ui: 事件传递的焦点 UI 元素，为 None 会自动确认焦点。
        :type focused_ui: fantas.UI | None
        """
        # 获取焦点 UI 元素
        if focused_ui is None:
            focused_ui = (
                self.hover_ui
                if fantas.get_event_category(event.type) == fantas.EventCategory.MOUSE
                else self.active_ui
            )
        event_pass_path = focused_ui.get_pass_path()
        for ui in reversed(event_pass_path):
            # 捕获阶段
            for callback in self.listener_dict.get((event.type, ui.ui_id, True), []):
                if callback(event):
                    return
        for ui in event_pass_path:
            # 冒泡阶段
            for callback in self.listener_dict.get((event.type, ui.ui_id, False), []):
                if callback(event):
                    return

    def add_event_listener(
        self,
        event_type: fantas.EventType,
        ui: fantas.UI,
        use_capture: bool,
        listener: fantas.ListenerFunc,
    ) -> None:
        """
        为指定事件类型和 UI 元素添加事件监听器。

        :param event_type: 要监听的事件类型。
        :type event_type: fantas.EventType
        :param ui: 要关联的 UI 元素。
        :type ui: fantas.UI
        :param use_capture: 是否在捕获阶段调用回调函数。
        :type use_capture: bool
        :param listener: 要添加的事件监听函数。
        :type listener: fantas.ListenerFunc
        """
        listener_list = self.listener_dict.setdefault(
            (event_type, ui.ui_id, use_capture), []
        )
        listener_list.append(listener)

    def remove_event_listener(
        self,
        event_type: fantas.EventType,
        ui: fantas.UI,
        use_capture: bool,
        listener: fantas.ListenerFunc,
    ) -> None:
        """
        移除指定事件类型和 UI 元素的事件监听器。

        :param event_type: 要移除监听器的事件类型。
        :type event_type: fantas.EventType
        :param ui: 要移除监听器的 UI 元素。
        :type ui: fantas.UI
        :param use_capture: 是否在捕获阶段调用回调函数。
        :type use_capture: bool
        :param listener: 要移除的事件监听函数。
        :type listener: fantas.ListenerFunc
        """
        listener_list = self.listener_dict.get((event_type, ui.ui_id, use_capture), [])
        try:
            listener_list.remove(listener)
        except ValueError:
            raise ValueError("监听器不存在。") from None

    def set_hover_ui(self, ui: fantas.UI) -> None:
        """
        set_hover_ui 的 Docstring
        设置当前悬停的 UI 元素。

        :param ui: 要设置为悬停的 UI 元素。
        :type ui: fantas.UI
        """
        self.last_hover_ui = self.hover_ui
        self.hover_ui = ui
        this_hover_pass_path = self.hover_ui.get_pass_path()
        last_hover_pass_path = self.last_hover_ui.get_pass_path()
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

    def set_active_ui(self, ui: fantas.UI) -> None:
        """
        设置当前激活的 UI 元素。

        :param ui: 要设置为激活的 UI 元素。
        :type ui: fantas.UI
        """
        self.active_ui = ui

    def _handle_windowclose_event(self, event: fantas.Event) -> None:
        """
        处理窗口关闭事件。

        :param event: 要处理的窗口关闭事件对象。
        :type event: fantas.Event
        """
        if event.window is self.window:
            self.window.running = False

    def _handle_windowleave_event(self, event: fantas.Event) -> None:
        """
        处理窗口离开事件，设置悬停 UI 元素为根节点。

        :param event: 要处理的窗口离开事件对象。
        :type event: fantas.Event
        """
        if event.window is self.window:
            self.set_hover_ui(self.window.root_ui)
            self.set_active_ui(self.window.root_ui)

    def _handle_windowresized_event(self, event: fantas.Event) -> None:
        """
        处理窗口调整大小事件，更新根 UI 元素的矩形。

        :param event: 要处理的窗口调整大小事件对象。
        :type event: fantas.Event
        """
        if event.window is self.window:
            self.window.root_ui.update_rect()

    def _handle_mousemotion_event(self, event: fantas.Event) -> None:
        """
        处理鼠标移动事件，更新悬停的 UI 元素。

        :param event: 要处理的鼠标移动事件对象。
        :type event: fantas.Event
        """
        self.set_hover_ui(self.window.renderer.coordinate_hit_test(event.pos))

    def _handle_mousebuttondown_event(self, event: fantas.Event) -> None:
        """
        处理鼠标按下事件，更新激活的 UI 元素。

        :param event: 要处理的鼠标按下事件对象。
        :type event: fantas.Event
        """
        if event.button != fantas.BUTTON_LEFT:
            return
        self.set_active_ui(self.hover_ui)
        self.last_pressed_ui = self.hover_ui

    def _handle_mousebuttonup_event(self, _: fantas.Event) -> None:
        """
        处理鼠标释放事件。

        :param _: 要处理的鼠标释放事件对象。
        :type _: fantas.Event
        """
        if self.last_pressed_ui is self.hover_ui:
            self.handle_event(
                fantas.Event(fantas.MOUSECLICKED, ui=self.hover_ui),
                focused_ui=self.hover_ui,
            )
        self.last_pressed_ui = None
