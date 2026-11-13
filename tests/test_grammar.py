"""Grammatik-Bits: Inhalt, Quiz und eigener Fortschritt."""

from datetime import datetime, timedelta

import pytest

from turkmek import grammar, planner, render, svg
from turkmek.bit_icons import BIT_ICONS
from turkmek.content import load_words
from turkmek.store import Store, ts

NOW = datetime(2026, 11, 6, 13, 0)
BITS = grammar.load_bits()


def test_bit_count():
    assert len(BITS) == 10


def test_bit_ids_unique_and_ascii():
    ids = [bit["id"] for bit in BITS]
    assert len(ids) == len(set(ids))
    assert all(i.isascii() for i in ids)


def test_bit_ids_do_not_collide_with_words():
    word_ids = {word["id"] for word in load_words()}
    assert not ({bit["id"] for bit in BITS} & word_ids)


def test_icons_are_known():
    for bit in BITS:
        assert bit["icon"] in BIT_ICONS


def test_options_and_answer_are_valid():
    for bit in BITS:
        assert 2 <= len(bit["options"]) <= 4
        assert 0 <= bit["answer"] < len(bit["options"])
        assert len(set(bit["options"])) == len(bit["options"])


def test_caption_stays_short_and_contains_the_parts():
    for bit in BITS:
        text = grammar.caption(bit)
        assert len(text) <= grammar.MAX_CAPTION
        assert bit["title"] in text
        assert bit["text"] in text
        assert bit["example"]["tr"] in text
        assert bit["example"]["de"] in text
        assert bit["question"]["tr"] in text
        assert bit["question"]["de"] in text


def test_keyboard_has_options_and_retire():
    bit = BITS[0]
    markup = grammar.keyboard(42, bit)
    rows = markup["inline_keyboard"]
    assert len(rows) == 2
    assert [button["text"] for button in rows[0]] == bit["options"]
    assert rows[1][0]["text"] == grammar.RETIRE_TEXT
    assert rows[1][0]["callback_data"] == "g:42:x"


def test_retire_keyboard_is_a_single_button():
    markup = grammar.retire_keyboard(42)
    assert len(markup["inline_keyboard"]) == 1
    assert markup["inline_keyboard"][0][0]["callback_data"] == "g:42:x"


def test_parse_callback_roundtrip():
    assert grammar.parse_callback("g:42:1") == (42, 1)
    assert grammar.parse_callback("g:42:x") == (42, "x")


def test_parse_callback_rejects_garbage():
    for data in (None, "", "a:1:y", "g:1", "g:abc:1", "g:1:-1", "g:1:y"):
        assert grammar.parse_callback(data) is None


def test_feedback_correct_and_wrong():
    bit = BITS[0]
    text, result = grammar.feedback(bit, bit["answer"])
    assert result == "y"
    assert text == grammar.CORRECT_TEXT

    wrong = (bit["answer"] + 1) % len(bit["options"])
    text, result = grammar.feedback(bit, wrong)
    assert result == "n"
    assert grammar.WRONG_TEXT in text
    assert bit["options"][bit["answer"]] in text


@pytest.mark.parametrize("icon_id", sorted(BIT_ICONS))
def test_bit_icons_stay_inside_canvas(icon_id):
    shapes = render.build_bit_scene(icon_id)
    assert shapes
    markup = svg.to_svg(shapes)
    assert "<polygon" in markup or "<polyline" in markup
    for shape in shapes:
        for x, y in shape.points:
            assert 0.0 <= x <= 100.0
            assert 0.0 <= y <= 100.0


@pytest.fixture
def store(tmp_path):
    instance = Store(tmp_path / "test.db")
    instance.sync_bits([bit["id"] for bit in BITS], NOW)
    instance.set_setting("chat_id", "1234")
    yield instance
    instance.close()


def force_due(store, bit_id, when):
    store.conn.execute(
        "UPDATE bit_reviews SET last_seen_at = ?, due_at = ? WHERE bit_id = ?",
        (ts(when - timedelta(days=2)), ts(when), bit_id),
    )
    store.conn.commit()


def test_sync_bits_is_idempotent(store):
    assert store.sync_bits([bit["id"] for bit in BITS], NOW) == 0


def test_pick_bit_prefers_due_over_new(store):
    force_due(store, "lokativ", NOW - timedelta(hours=1))
    assert planner.pick_bit(store, NOW) == "lokativ"


def test_pick_bit_returns_new_when_nothing_is_due(store):
    assert planner.pick_bit(store, NOW) in {bit["id"] for bit in BITS}


def test_pick_bit_falls_back_to_oldest(store):
    for index, bit in enumerate(BITS):
        seen = NOW - timedelta(days=30 - index)
        store.conn.execute(
            "UPDATE bit_reviews SET last_seen_at = ?, due_at = ? "
            "WHERE bit_id = ?",
            (ts(seen), ts(NOW + timedelta(days=10)), bit["id"]),
        )
    store.conn.commit()

    assert planner.pick_bit(store, NOW) == BITS[0]["id"]


def test_pick_bit_skips_retired(store):
    store.retire_bit(
        store.claim("lokativ", "bit", NOW.date(), "bit", NOW)[0], NOW
    )
    active = [r["bit_id"] for r in store.fallback_bits()]
    assert "lokativ" not in active


def test_all_bits_retired_returns_none(store):
    for bit in BITS:
        delivery_id, _ = store.claim(
            bit["id"], f"bit-{bit['id']}", NOW.date(), "bit", NOW
        )
        store.retire_bit(delivery_id, NOW)

    assert planner.pick_bit(store, NOW) is None
    assert store.fallback_bits() == []


def test_claim_is_once_per_day(store):
    first, fresh = store.claim("akkusativ", "bit", NOW.date(), "bit", NOW)
    assert fresh is True

    second, fresh = store.claim("plural", "bit", NOW.date(), "bit", NOW)
    assert second == first
    assert fresh is False


def send_bit(store, bit_id, now=NOW):
    delivery_id, _ = store.claim(bit_id, "bit", now.date(), "bit", now)
    store.mark_sent(delivery_id, 1, now)
    return delivery_id


def test_answer_updates_bit_schedule(store):
    delivery_id = send_bit(store, "akkusativ")
    bit_id, status = store.answer_bit(delivery_id, "y", NOW)

    assert status == "ok"
    assert bit_id == "akkusativ"

    review = store.bit_review_of("akkusativ")
    assert review["reps"] == 1
    assert review["interval_days"] == 1
    assert review["due_at"] == ts(NOW + timedelta(days=1))
    assert review["retired_at"] is None


def test_answer_twice_is_rejected(store):
    delivery_id = send_bit(store, "akkusativ")
    store.answer_bit(delivery_id, "y", NOW)

    _, status = store.answer_bit(delivery_id, "n", NOW)
    assert status == "duplicate"
    assert store.bit_review_of("akkusativ")["reps"] == 1


def test_answer_after_a_day_is_stale(store):
    delivery_id = send_bit(store, "akkusativ")

    _, status = store.answer_bit(delivery_id, "y", NOW + timedelta(hours=25))
    assert status == "stale"
    assert store.bit_review_of("akkusativ")["reps"] == 0
    assert store.bit_review_of("akkusativ")["last_result"] is None


def test_retire_is_permanent_and_idempotent(store):
    delivery_id = send_bit(store, "akkusativ")

    bit_id, status = store.retire_bit(delivery_id, NOW)
    assert status == "ok"
    assert bit_id == "akkusativ"
    assert store.bit_review_of("akkusativ")["retired_at"] == ts(NOW)

    _, status = store.retire_bit(delivery_id, NOW)
    assert status == "duplicate"


def test_retire_ignores_the_answer_window(store):
    old = NOW - timedelta(days=3)
    delivery_id = send_bit(store, "akkusativ", old)

    _, status = store.retire_bit(delivery_id, NOW)
    assert status == "ok"
    assert store.bit_review_of("akkusativ")["retired_at"] == ts(NOW)


def test_answer_bit_rejects_word_deliveries(store):
    store.sync_items(["kapi"], NOW)
    delivery_id, _ = store.claim("kapi", "08:30", NOW.date(), "review", NOW)
    store.mark_sent(delivery_id, 1, NOW)

    _, status = store.answer_bit(delivery_id, "y", NOW)
    assert status == "unknown"
