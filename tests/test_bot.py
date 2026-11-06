"""Versand-Flow ohne Netz: der Tick darf nie zweimal dieselbe Karte schicken."""

import asyncio
from datetime import datetime, time, timedelta
from types import SimpleNamespace

import pytest

from turkmek.bot import tick
from turkmek.config import CARDS_DIR
from turkmek.content import load_words
from turkmek.store import Store

NOW = datetime(2026, 11, 6, 8, 30)  # Freitag


class FakeTelegram:
    def __init__(self):
        self.sent = []

    async def send_photo(self, chat_id, path, caption, reply_markup=None):
        self.sent.append(
            {"chat": chat_id, "path": path, "caption": caption,
             "markup": reply_markup}
        )
        return {"message_id": 500 + len(self.sent)}


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


def run(coro):
    return asyncio.run(coro)


def test_tick_sends_once(env):
    store, cfg, words = env
    telegram = FakeTelegram()

    assert run(tick(telegram, store, cfg, words, now=NOW)) is True
    assert len(telegram.sent) == 1

    assert run(tick(telegram, store, cfg, words, now=NOW)) is False
    assert len(telegram.sent) == 1


def test_tick_outside_the_window_does_nothing(env):
    store, cfg, words = env
    telegram = FakeTelegram()

    late = NOW + timedelta(minutes=40)
    assert run(tick(telegram, store, cfg, words, now=late)) is False
    assert telegram.sent == []


def test_tick_respects_pause(env):
    store, cfg, words = env
    telegram = FakeTelegram()
    store.set_setting("pause_until", "2026-11-20T00:00")

    assert run(tick(telegram, store, cfg, words, now=NOW)) is False
    assert telegram.sent == []


def test_tick_without_chat_does_nothing(env):
    store, cfg, words = env
    telegram = FakeTelegram()
    store.set_setting("chat_id", "")

    assert run(tick(telegram, store, cfg, words, now=NOW)) is False
    assert telegram.sent == []


def test_delivery_is_recorded_and_answerable(env):
    store, cfg, words = env
    telegram = FakeTelegram()
    run(tick(telegram, store, cfg, words, now=NOW))

    row = store.delivery("08:30", NOW.date())
    assert row is not None
    assert row["status"] == "sent"
    assert row["message_id"] == 501

    item_id, status = store.answer(row["id"], "y", NOW)
    assert status == "ok"
    assert item_id == row["item_id"]


def test_send_failure_is_retried_and_then_given_up(env):
    store, cfg, words = env

    from turkmek.telegram import TelegramError

    class BrokenTelegram:
        async def send_photo(self, *args, **kwargs):
            raise TelegramError("kaputt")

    for _ in range(5):
        run(tick(BrokenTelegram(), store, cfg, words, now=NOW))

    row = store.delivery("08:30", NOW.date())
    assert row["status"] == "failed"
    assert row["attempts"] <= 3
