from fantas import get_distinct_blackorwhite, Color


def test_get_distinct_blackorwhite():
    assert get_distinct_blackorwhite(Color("#000000")) == Color("#FFFFFF")
    assert get_distinct_blackorwhite(Color("#FFFFFF")) == Color("#000000")
    assert get_distinct_blackorwhite(Color("#FF0000")) == Color("#000000")
    assert get_distinct_blackorwhite(Color("#00FF00")) == Color("#000000")
    assert get_distinct_blackorwhite(Color("#0000FF")) == Color("#000000")
    assert get_distinct_blackorwhite(Color("#808080")) == Color("#000000")
    assert get_distinct_blackorwhite(Color("#7F7F7F")) == Color("#FFFFFF")
    assert get_distinct_blackorwhite(Color("#C0C0C0")) == Color("#000000")
    assert get_distinct_blackorwhite(Color("#800000")) == Color("#FFFFFF")
    assert get_distinct_blackorwhite(Color("#008000")) == Color("#FFFFFF")
    assert get_distinct_blackorwhite(Color("#000080")) == Color("#FFFFFF")
