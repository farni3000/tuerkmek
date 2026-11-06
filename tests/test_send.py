"""Soft-Versand: eine Karte pro Aufruf, ohne den Slot zu verbrauchen."""

import asyncio
from datetime import datetime, time
from types import SimpleNamespace

import pytest

from turkmek.config import CARDS_DIR
from turkmek.content import load_words
from turkmek.send import send_cards
from turkmek.store import Store

NOW = datetime(2026, 11, 6, 8, 30)


class FakeTelegram:
    def __init__(self):
        self.sent = []

    async def send_photo(self, chat_id, path, caption, reply_markup=None):
        self.sent.append(path.name)
        return {"message_id": 700 + len(self.sent)}


@pytest.fixture
def env(tmp_path):
    store = Store(tmp_path / "test.db")
    words = {word["id"]: word for word in load_words()}
    store.sync_items(words.keys(), NOW)
    store.set_setting("chat_id", "1234")

    cfg = SimpleNamespace(
        tz="Europe/Berlin",
        slots=[time(8, 30)],
        weekend_off=False,
        slot_window=15,
        cards_dir=CARDS_DIR,
        token="test",
    )
    yield store, cfg, words
    store.close()


def test_dry_run_lists_distinct_cards(env):
    store, cfg, words = env
    results = asyncio.run(
        send_cards(None, store, cfg, words, 1234, count=3, dry_run=True)
    )

    assert len(results) == 3
    ids = [item_id for item_id, _, _ in results]
    assert len(set(ids)) == 3


def test_dry_run_changes_nothing(env):
    store, cfg, words = env
    asyncio.run(send_cards(None, store, cfg, words, 1234, count=2,
                           dry_run=True))

    assert store.seen_today(datetime.now().date()) == set()
    assert store.new_today(datetime.now().date()) == 0


def test_send_sends_one_card(env):
    store, cfg, words = env
    telegram = FakeTelegram()

    results = asyncio.run(
        send_cards(telegram, store, cfg, words, 1234, count=1)
    )

    assert len(results) == 1
    assert results[0][2] is True
    assert len(telegram.sent) == 1


def test_soft_send_does_not_consume_the_slot(env):
    store, cfg, words = env
    telegram = FakeTelegram()

    asyncio.run(send_cards(telegram, store, cfg, words, 1234, count=1))

    # Der 08:30-Slot bleibt frei, der Scheduler darf später noch senden.
    assert store.delivery("08:30", datetime.now().date()) is None


def test_soft_send_does_not_repeat_today(env):
    store, cfg, words = env
    telegram = FakeTelegram()

    first = asyncio.run(send_cards(telegram, store, cfg, words, 1234, count=1))
    second = asyncio.run(send_cards(telegram, store, cfg, words, 1234, count=1))

    assert first[0][0] != second[0][0]


def test_soft_send_ignores_the_new_word_budget(env):
    store, cfg, words = env
    telegram = FakeTelegram()

    results = asyncio.run(
        send_cards(telegram, store, cfg, words, 1234, count=5)
    )

    assert [kind for _, kind, _ in results] == ["new"] * 5
