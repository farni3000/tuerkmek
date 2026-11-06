import pytest

from turkmek import srs


def test_first_good_is_one_day():
    state = srs.apply("y", 0, 0.0, srs.EASE_START, 0)
    assert state["interval"] == 1.0
    assert state["reps"] == 1


def test_second_good_is_three_days():
    state = srs.apply("y", 1, 1.0, srs.EASE_START, 0)
    assert state["interval"] == 3.0


def test_third_good_multiplies_by_ease():
    state = srs.apply("y", 2, 3.0, 2.5, 0)
    assert state["interval"] == pytest.approx(7.5)


def test_again_resets_the_ladder():
    state = srs.apply("n", 5, 40.0, 2.6, 1)
    assert state["interval"] == 1.0
    assert state["reps"] == 0
    assert state["lapses"] == 2
    assert state["ease"] < 2.6


def test_ease_never_drops_below_minimum():
    ease = srs.EASE_START
    for _ in range(20):
        ease = srs.apply("n", 0, 1.0, ease, 0)["ease"]
    assert ease == pytest.approx(srs.EASE_MIN)


def test_ease_never_rises_above_maximum():
    ease = srs.EASE_START
    for _ in range(20):
        ease = srs.apply("y", 3, 20.0, ease, 0)["ease"]
    assert ease == pytest.approx(srs.EASE_MAX)


def test_interval_is_capped():
    state = srs.apply("y", 10, 175.0, 3.0, 0)
    assert state["interval"] <= srs.MAX_INTERVAL


def test_good_does_not_touch_lapses():
    assert srs.apply("y", 2, 3.0, 2.5, 4)["lapses"] == 4
