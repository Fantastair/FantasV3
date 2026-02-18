import pytest
from fantas import (
    Quadrant,
    custom_event,
    event,
    get_event_category,
    MOUSECLICKED,
    DEBUGRECEIVED,
    EventCategory,
)

# 定义测试数据：(象限, 测试点, 预期结果)
# 需要注意的是，y 轴向下为正，所以点(1, 1) 实际上在第四象限，也就是BOTTOMRIGHT，
# 而不是 TOPRIGHT。
TEST_DATA = (
    # TOPRIGHT 象限的9个测试点
    (Quadrant.TOPRIGHT, (1, 1), False),
    (Quadrant.TOPRIGHT, (1, -1), True),
    (Quadrant.TOPRIGHT, (-1, 1), False),
    (Quadrant.BOTTOMRIGHT, (-1, 1), False),
    (Quadrant.BOTTOMRIGHT, (-1, -1), False),
    (Quadrant.BOTTOMRIGHT, (0, 0), True),
    (Quadrant.BOTTOMRIGHT, (0, 1), True),
    (Quadrant.BOTTOMRIGHT, (1, 0), True),
    (Quadrant.BOTTOMRIGHT, (0, -1), False),
    (Quadrant.BOTTOMRIGHT, (-1, 0), False),
    # TOPLEFT 象限的9个测试点
    (Quadrant.TOPLEFT, (1, 1), False),
    (Quadrant.TOPLEFT, (1, -1), False),
    (Quadrant.TOPLEFT, (-1, 1), False),
    (Quadrant.TOPLEFT, (-1, -1), True),
    (Quadrant.TOPLEFT, (0, 0), False),
    (Quadrant.TOPLEFT, (0, 1), False),
    (Quadrant.TOPLEFT, (1, 0), False),
    (Quadrant.TOPLEFT, (0, -1), False),
    (Quadrant.TOPLEFT, (-1, 0), False),
    # BOTTOMLEFT 象限的9个测试点
    (Quadrant.BOTTOMLEFT, (1, 1), False),
    (Quadrant.BOTTOMLEFT, (1, -1), False),
    (Quadrant.BOTTOMLEFT, (-1, 1), True),
    (Quadrant.BOTTOMLEFT, (-1, -1), False),
    (Quadrant.BOTTOMLEFT, (0, 0), False),
    (Quadrant.BOTTOMLEFT, (0, 1), False),
    (Quadrant.BOTTOMLEFT, (1, 0), False),
    (Quadrant.BOTTOMLEFT, (0, -1), False),
    (Quadrant.BOTTOMLEFT, (-1, 0), True),
)


@pytest.mark.parametrize("quadrant, point, expected", TEST_DATA)
def test_quadrant_has_point(quadrant, point, expected):
    assert quadrant.has_point(point) is expected


def test_get_event_category():
    assert get_event_category(MOUSECLICKED) == EventCategory.MOUSE
    assert get_event_category(DEBUGRECEIVED) == EventCategory.USER


def test_custom_event_unique():
    assert custom_event() != custom_event()


def test_custom_event_allowed():
    assert event.get_blocked(custom_event()) is False


def test_custom_event_category():
    assert get_event_category(custom_event()) == EventCategory.USER
    assert get_event_category(custom_event(EventCategory.MOUSE)) == EventCategory.MOUSE
    assert (
        get_event_category(custom_event(EventCategory.KEYBOARD))
        == EventCategory.KEYBOARD
    )
    assert get_event_category(custom_event(EventCategory.INPUT)) == EventCategory.INPUT
    assert (
        get_event_category(custom_event(EventCategory.WINDOW)) == EventCategory.WINDOW
    )
