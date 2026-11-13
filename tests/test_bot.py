"""Versand-Flow ohne Netz: der Tick darf nie zweimal dieselbe Karte schicken."""

import asyncio
from datetime import datetime, time, timedelta
from types import SimpleNamespace

import pytest

from turkmek import grammar
from turkmek.bot import handle_callback, local_now, tick
from turkmek.config import BITS_DIR, CARDS_DIR
from turkmek.content import load_words
from turkmek.grammar import load_bits
from turkmek.store import Store

NOW = datetime(2026, 11, 6, 8, 30)  # Freitag
NOON = datetime(2026, 11, 6, 13, 0)
BITS = {bit["id"]: bit for bit in load_bits()}


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
    store.sync_bits(BITS.keys(), NOW)
    store.set_setting("chat_id", "1234")

    cfg = SimpleNamespace(
        tz="Europe/Berlin",
        slots=[time(8, 30), time(13, 0)],
        weekend_off=False,
        slot_window=15,
        cards_dir=CARDS_DIR,
        bits_dir=BITS_DIR,
        token="test",
    )
    yield store, cfg, words
    store.close()


def run(coro):
    return asyncio.run(coro)


def test_tick_sends_once(env):
    store, cfg, words = env
    telegram = FakeTelegram()

    assert run(tick(telegram, store, cfg, words, BITS, now=NOW)) is True
    assert len(telegram.sent) == 1

    assert run(tick(telegram, store, cfg, words, BITS, now=NOW)) is False
    assert len(telegram.sent) == 1


def test_tick_outside_the_window_does_nothing(env):
    store, cfg, words = env
    telegram = FakeTelegram()

    late = NOW + timedelta(minutes=40)
    assert run(tick(telegram, store, cfg, words, BITS, now=late)) is False
    assert telegram.sent == []


def test_tick_respects_pause(env):
    store, cfg, words = env
    telegram = FakeTelegram()
    store.set_setting("pause_until", "2026-11-20T00:00")

    assert run(tick(telegram, store, cfg, words, BITS, now=NOW)) is False
    assert telegram.sent == []


def test_tick_without_chat_does_nothing(env):
    store, cfg, words = env
    telegram = FakeTelegram()
    store.set_setting("chat_id", "")

    assert run(tick(telegram, store, cfg, words, BITS, now=NOW)) is False
    assert telegram.sent == []


def test_delivery_is_recorded_and_answerable(env):
    store, cfg, words = env
    telegram = FakeTelegram()
    run(tick(telegram, store, cfg, words, BITS, now=NOW))

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
        run(tick(BrokenTelegram(), store, cfg, words, BITS, now=NOW))

    row = store.delivery("08:30", NOW.date())
    assert row["status"] == "failed"
    assert row["attempts"] <= 3


class CallbackTelegram:
    def __init__(self):
        self.answers = []
        self.captions = []

    async def answer_callback(self, callback_id, text=None):
        self.answers.append(text)

    async def edit_caption(self, chat_id, message_id, caption,
                           reply_markup=None):
        self.captions.append(caption)


def callback_query(delivery_id, result):
    return {
        "id": "cb-1",
        "from": {"id": 1234},
        "data": f"a:{delivery_id}:{result}",
        "message": {
            "message_id": 1,
            "chat": {"id": 1234},
            "caption": "kapi — Tür",
        },
    }


def test_second_tap_is_a_duplicate(env):
    store, cfg, words = env
    now = local_now(cfg)
    delivery_id, _ = store.claim("kapi", "08:30", now.date(), "review", now)
    store.mark_sent(delivery_id, 1, now)
    telegram = CallbackTelegram()
    query = callback_query(delivery_id, "y")

    run(handle_callback(telegram, store, cfg, BITS, query))
    run(handle_callback(telegram, store, cfg, BITS, query))

    assert telegram.answers == ["✅ Doğru! · Gewusst",
                                "Zaten cevaplandı · schon beantwortet"]
    assert store.review_of("kapi")["reps"] == 1


def test_stale_tap_is_rejected_with_hint(env):
    store, cfg, words = env
    old = local_now(cfg) - timedelta(days=3)
    delivery_id, _ = store.claim("kapi", "08:30", old.date(), "review", old)
    store.mark_sent(delivery_id, 1, old)
    telegram = CallbackTelegram()

    run(handle_callback(telegram, store, cfg, BITS,
                        callback_query(delivery_id, "y")))

    assert telegram.answers == ["⌛ Çok geç · zu alt"]
    assert store.review_of("kapi")["reps"] == 0


def bit_query(delivery_id, action, caption="Belirtme · Akkusativ"):
    return {
        "id": "cb-bit",
        "from": {"id": 1234},
        "data": f"g:{delivery_id}:{action}",
        "message": {
            "message_id": 9,
            "chat": {"id": 1234},
            "caption": caption,
        },
    }


def send_bit_for_test(store, cfg, words):
    telegram = FakeTelegram()
    run(tick(telegram, store, cfg, words, BITS, now=NOON))
    row = store.delivery("bit", NOON.date())
    assert row is not None
    return telegram, row


def claim_bit_for_test(store, cfg, bit_id="akkusativ"):
    """Legt eine frische Bit-Lieferung relativ zur echten Uhrzeit an."""
    now = local_now(cfg)
    delivery_id, _ = store.claim(bit_id, "bit", now.date(), "bit", now)
    store.mark_sent(delivery_id, 1, now)
    return store.delivery_by_id(delivery_id)


def test_tick_sends_bit_after_card(env):
    store, cfg, words = env
    telegram, row = send_bit_for_test(store, cfg, words)

    assert len(telegram.sent) == 2
    assert row["kind"] == "bit"
    assert row["item_id"] in BITS
    bit_message = telegram.sent[1]
    assert bit_message["path"].parent == BITS_DIR
    assert bit_message["markup"]["inline_keyboard"][-1][0]["text"] == \
        grammar.RETIRE_TEXT

    # Ein zweiter Tick im selben Fenster schickt weder Karte noch Bit erneut.
    assert run(tick(telegram, store, cfg, words, BITS, now=NOON)) is False
    assert len(telegram.sent) == 2


def test_bit_is_not_sent_outside_window(env):
    store, cfg, words = env
    telegram = FakeTelegram()

    assert run(tick(telegram, store, cfg, words, BITS,
                    now=NOON + timedelta(minutes=40))) is False
    assert telegram.sent == []
    assert store.delivery("bit", NOON.date()) is None


def test_bit_respects_pause(env):
    store, cfg, words = env
    store.set_setting("pause_until", "2026-11-20T00:00")
    telegram = FakeTelegram()

    assert run(tick(telegram, store, cfg, words, BITS, now=NOON)) is False
    assert telegram.sent == []


def test_bit_respects_weekend(env):
    store, cfg, words = env
    cfg.weekend_off = True
    telegram = FakeTelegram()
    saturday = datetime(2026, 11, 7, 13, 0)

    assert run(tick(telegram, store, cfg, words, BITS, now=saturday)) is False
    assert telegram.sent == []


def test_correct_quiz_answer_does_not_retire(env):
    store, cfg, words = env
    row = claim_bit_for_test(store, cfg)
    bit = BITS[row["item_id"]]
    telegram = CallbackTelegram()

    run(handle_callback(
        telegram, store, cfg, BITS,
        bit_query(row["id"], bit["answer"]),
    ))

    review = store.bit_review_of(row["item_id"])
    assert review["retired_at"] is None
    assert review["reps"] == 1
    assert review["last_result"] == "y"
    assert telegram.answers == [grammar.CORRECT_TEXT]
    assert grammar.CORRECT_TEXT in telegram.captions[0]


def test_wrong_quiz_answer_is_still_scheduled(env):
    store, cfg, words = env
    row = claim_bit_for_test(store, cfg)
    bit = BITS[row["item_id"]]
    wrong = (bit["answer"] + 1) % len(bit["options"])
    telegram = CallbackTelegram()

    run(handle_callback(
        telegram, store, cfg, BITS,
        bit_query(row["id"], wrong),
    ))

    review = store.bit_review_of(row["item_id"])
    assert review["retired_at"] is None
    assert review["reps"] == 0
    assert review["last_result"] == "n"
    assert "Doğru:" in telegram.captions[0]


def test_retire_removes_bit_permanently(env):
    store, cfg, words = env
    row = claim_bit_for_test(store, cfg)
    telegram = CallbackTelegram()

    run(handle_callback(
        telegram, store, cfg, BITS, bit_query(row["id"], "x")
    ))

    review = store.bit_review_of(row["item_id"])
    assert review["retired_at"] is not None
    assert grammar.RETIRED_TEXT in telegram.captions[0]

    # Nach dem Abschalten taucht genau dieses Bit nicht mehr auf.
    active = [r["bit_id"] for r in store.due_bits(NOON)]
    active += [r["bit_id"] for r in store.new_bits(NOON)]
    active += [r["bit_id"] for r in store.fallback_bits()]
    assert row["item_id"] not in active


def test_retire_still_works_after_quiz_answer(env):
    store, cfg, words = env
    row = claim_bit_for_test(store, cfg)
    bit = BITS[row["item_id"]]
    telegram = CallbackTelegram()

    run(handle_callback(
        telegram, store, cfg, BITS, bit_query(row["id"], bit["answer"])
    ))
    run(handle_callback(
        telegram, store, cfg, BITS, bit_query(row["id"], "x")
    ))

    assert store.bit_review_of(row["item_id"])["retired_at"] is not None


def test_retire_is_idempotent(env):
    store, cfg, words = env
    row = claim_bit_for_test(store, cfg)
    telegram = CallbackTelegram()

    run(handle_callback(
        telegram, store, cfg, BITS, bit_query(row["id"], "x")
    ))
    run(handle_callback(
        telegram, store, cfg, BITS, bit_query(row["id"], "x")
    ))

    assert telegram.answers[0] == grammar.RETIRED_TEXT
    assert telegram.answers[1] == grammar.ALREADY_TEXT


def test_retire_works_on_an_old_delivery(env):
    store, cfg, words = env
    old = NOON - timedelta(days=3)
    delivery_id, _ = store.claim("akkusativ", "bit", old.date(), "bit", old)
    store.mark_sent(delivery_id, 1, old)
    telegram = CallbackTelegram()

    run(handle_callback(
        telegram, store, cfg, BITS, bit_query(delivery_id, "x")
    ))

    assert store.bit_review_of("akkusativ")["retired_at"] is not None


def test_bit_answers_do_not_change_word_stats(env):
    store, cfg, words = env
    now = local_now(cfg)

    word_delivery, _ = store.claim("kapi", "08:30", now.date(), "review", now)
    store.mark_sent(word_delivery, 1, now)
    store.answer(word_delivery, "y", now)

    _, row = send_bit_for_test(store, cfg, words)
    store.answer_bit(row["id"], "y", NOON)

    stats = store.stats(NOON)
    assert stats["answered"] == 1
    assert stats["good"] == 1
    assert stats["accuracy"] == 1.0
