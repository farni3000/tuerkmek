"""Wort-Ruhestand: zweimal in Folge gewusst heißt nie wieder."""

import sqlite3
from datetime import datetime, timedelta

import pytest

from turkmek.store import Store, ts

NOW = datetime(2026, 11, 6, 8, 30)

OLD_SCHEMA = """
CREATE TABLE items (id TEXT PRIMARY KEY, added_at TEXT NOT NULL);
CREATE TABLE reviews (
    item_id      TEXT PRIMARY KEY REFERENCES items(id),
    due_at       TEXT NOT NULL,
    interval_days REAL NOT NULL DEFAULT 0,
    ease         REAL NOT NULL DEFAULT 2.5,
    lapses       INTEGER NOT NULL DEFAULT 0,
    reps         INTEGER NOT NULL DEFAULT 0,
    last_result  TEXT,
    last_seen_at TEXT
);
"""


@pytest.fixture
def store(tmp_path):
    instance = Store(tmp_path / "test.db")
    instance.sync_items(["a", "b", "c"], NOW)
    yield instance
    instance.close()


def send(store, item_id, now=NOW):
    delivery_id, _ = store.claim(
        item_id, f"slot-{now:%Y%m%d%H%M%S%f}", now.date(), "new", now
    )
    store.mark_sent(delivery_id, 1, now)
    return delivery_id


def answer(store, item_id, result, now):
    return store.answer(send(store, item_id, now), result, now)


def test_two_goods_retire_the_word(store):
    answer(store, "a", "y", NOW)
    later = NOW + timedelta(days=1)
    answer(store, "a", "y", later)

    row = store.review_of("a")
    assert row["reps"] == 2
    assert row["retired_at"] == ts(later)


def test_retired_word_is_never_selected_again(store):
    answer(store, "a", "y", NOW)
    later = NOW + timedelta(days=1)
    answer(store, "a", "y", later)

    horizon = later + timedelta(days=365)
    assert "a" not in {r["item_id"] for r in store.due_items(horizon)}
    assert "a" not in {r["item_id"] for r in store.new_items(horizon)}
    assert "a" not in {r["item_id"] for r in store.fallback_items()}

    # Die anderen Wörter bleiben im Umlauf.
    assert "b" in {r["item_id"] for r in store.new_items(horizon)}


def test_wrong_answer_prevents_retirement(store):
    answer(store, "a", "y", NOW)
    later = NOW + timedelta(days=1)
    answer(store, "a", "n", later)

    row = store.review_of("a")
    assert row["reps"] == 0
    assert row["retired_at"] is None
    assert "a" in {
        r["item_id"] for r in store.due_items(later + timedelta(days=1))
    }


def test_reset_brings_a_retired_word_back(store):
    answer(store, "a", "y", NOW)
    answer(store, "a", "y", NOW + timedelta(days=1))
    store.reset("a")

    row = store.review_of("a")
    assert row["retired_at"] is None
    assert row["reps"] == 0
    assert "a" in {r["item_id"] for r in store.new_items(datetime.now())}


def test_stats_separate_learned_words(store):
    answer(store, "a", "y", NOW)
    answer(store, "a", "y", NOW + timedelta(days=1))

    stats = store.stats(NOW + timedelta(days=1))
    assert stats["retired"] == 1
    assert stats["total"] == 2


def test_migration_adds_column_and_backfills(tmp_path):
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript(OLD_SCHEMA)
    conn.execute("INSERT INTO items VALUES('a', '2026-01-01T00:00')")
    conn.execute("INSERT INTO items VALUES('b', '2026-01-01T00:00')")
    conn.execute(
        "INSERT INTO reviews(item_id, due_at, reps, last_seen_at) "
        "VALUES('a', '2026-01-01T00:00', 2, '2026-01-01T00:00')"
    )
    conn.execute(
        "INSERT INTO reviews(item_id, due_at, reps, last_seen_at) "
        "VALUES('b', '2026-01-01T00:00', 1, '2026-01-01T00:00')"
    )
    conn.commit()
    conn.close()

    store = Store(path)
    try:
        assert store.review_of("a")["retired_at"] is not None
        assert store.review_of("b")["retired_at"] is None
    finally:
        store.close()
