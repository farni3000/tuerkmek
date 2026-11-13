from datetime import datetime, timedelta

import pytest

from turkmek.planner import pick
from turkmek.store import Store, ts

NOW = datetime(2026, 11, 6, 8, 30)


@pytest.fixture
def store(tmp_path):
    instance = Store(tmp_path / "test.db")
    instance.sync_items(["a", "b", "c", "d"], NOW)
    yield instance
    instance.close()


def send(store, item_id, slot, now=NOW):
    delivery_id, _ = store.claim(item_id, slot, now.date(), "new", now)
    store.mark_sent(delivery_id, 1, now)
    return delivery_id


def force_due(store, item_id, when):
    store.conn.execute(
        "UPDATE reviews SET due_at = ?, last_seen_at = ? WHERE item_id = ?",
        (ts(when), ts(when - timedelta(days=1)), item_id),
    )
    store.conn.commit()


def test_new_words_first(store):
    picked = pick(store, NOW, NOW.date())
    assert picked is not None
    assert picked.kind == "new"


def test_sent_word_is_not_picked_again_today(store):
    first = pick(store, NOW, NOW.date())
    send(store, first.item_id, "08:30")

    assert first.item_id in store.seen_today(NOW.date())
    second = pick(store, NOW, NOW.date())
    assert second.item_id != first.item_id


def test_new_word_budget(store):
    for slot in ("08:30", "13:00"):
        picked = pick(store, NOW, NOW.date())
        send(store, picked.item_id, slot)

    assert store.new_today(NOW.date()) == 2
    third = pick(store, NOW, NOW.date())
    assert third.kind == "extra"


def test_due_review_beats_new_word(store):
    force_due(store, "d", NOW - timedelta(hours=2))

    picked = pick(store, NOW, NOW.date())
    assert picked.item_id == "d"
    assert picked.kind == "review"


def test_nothing_left_returns_none(store):
    for index, item_id in enumerate(["a", "b", "c", "d"]):
        send(store, item_id, f"slot-{index}")

    assert pick(store, NOW, NOW.date()) is None


def test_claim_is_idempotent(store):
    first_id, fresh = store.claim("a", "08:30", NOW.date(), "new", NOW)
    assert fresh is True

    second_id, fresh = store.claim("a", "08:30", NOW.date(), "new", NOW)
    assert second_id == first_id
    assert fresh is False


def test_answer_updates_schedule(store):
    delivery_id = send(store, "a", "08:30")
    item_id, status = store.answer(delivery_id, "y", NOW)

    assert status == "ok"
    assert item_id == "a"

    review = store.review_of("a")
    assert review["reps"] == 1
    assert review["interval_days"] == 1
    assert ts(NOW + timedelta(days=1)) == review["due_at"]


def test_answer_twice_is_rejected(store):
    delivery_id = send(store, "a", "08:30")
    store.answer(delivery_id, "y", NOW)

    _, status = store.answer(delivery_id, "n", NOW)
    assert status == "duplicate"
    assert store.review_of("a")["reps"] == 1


def test_answer_after_a_day_is_stale(store):
    delivery_id = send(store, "a", "08:30")

    _, status = store.answer(delivery_id, "y", NOW + timedelta(hours=25))

    assert status == "stale"
    review = store.review_of("a")
    assert review["reps"] == 0
    assert review["last_result"] is None


def test_stale_guard_can_be_disabled(store):
    delivery_id = send(store, "a", "08:30")

    _, status = store.answer(
        delivery_id, "y", NOW + timedelta(days=30), max_age=None
    )

    assert status == "ok"
