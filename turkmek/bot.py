"""Long-Polling-Bot mit eingebautem Scheduler.

    python -m turkmek.bot           # Polling + Scheduler
    python -m turkmek.bot --once    # ein Tick, z.B. für cron

Zwei asyncio-Tasks: einer holt Updates, einer prüft alle 20 Sekunden, ob ein
Slot fällig ist. Kein offener Port, kein HTTPS nötig.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import cards, grammar, planner
from .config import load_config, parse_slots
from .content import load_words
from .grammar import load_bits
from .store import Store, ts
from .telegram import Telegram, TelegramError

log = logging.getLogger("turkmek.bot")

TICK_SECONDS = 20
MAX_ATTEMPTS = 3

HELP_TEXT = (
    "Kommandos · Komutlar\n\n"
    "/next – sofort eine Karte · hemen bir kart\n"
    "/heute – was heute noch kommt · bugün\n"
    "/stats – Serie, Quote, Fällige · istatistik\n"
    "/pause 7 – Pause in Tagen (ohne Zahl: 1)\n"
    "/resume – weiter · devam\n"
    "/zeit 08:30 13:00 20:00 – Zeiten ändern\n"
    "/hilfe – diese Liste · yardım"
)


# ------------------------------------------------------------------ Zeit --

def local_now(cfg):
    return datetime.now(ZoneInfo(cfg.tz)).replace(tzinfo=None)


def current_slots(store, cfg):
    raw = store.get_setting("slots")
    parsed = parse_slots(raw) if raw else []
    return parsed or cfg.slots


def is_paused(store, now):
    until = store.get_setting("pause_until")
    return bool(until) and until > ts(now)


# --------------------------------------------------------------- Versand --

async def deliver(tg, store, cfg, words, chat_id, picked, slot, day, now):
    word = words.get(picked.item_id)
    if word is None:
        log.warning("Wort %s fehlt in words.yaml", picked.item_id)
        return False

    card_path = cfg.cards_dir / f"{picked.item_id}.jpg"
    if not card_path.exists():
        log.error("Karte fehlt: %s", card_path)
        return False

    delivery_id, fresh = store.claim(picked.item_id, slot, day, picked.kind, now)
    if delivery_id is None:
        return False

    row = store.delivery_by_id(delivery_id)
    if not fresh and row["status"] == "sent":
        return False
    if row["attempts"] >= MAX_ATTEMPTS:
        log.warning("Slot %s gibt nach %d Versuchen auf", slot, MAX_ATTEMPTS)
        return False

    try:
        message = await tg.send_photo(
            chat_id,
            card_path,
            cards.caption(word),
            cards.keyboard(delivery_id, picked.kind),
        )
    except TelegramError as exc:
        log.error("Versand %s fehlgeschlagen: %s", picked.item_id, exc)
        store.mark_failed(delivery_id)
        return False

    store.mark_sent(delivery_id, message["message_id"], now)
    log.info("Karte %s (%s) um %s", picked.item_id, picked.kind, slot)
    return True


async def send_slot(tg, store, cfg, words, label, day, now, chat_id):
    row = store.delivery(label, day)
    if row:
        if row["status"] == "sent" or row["attempts"] >= MAX_ATTEMPTS:
            return False
        picked = planner.Pick(row["item_id"], row["kind"])
    else:
        picked = planner.pick(store, now, day)
        if picked is None:
            log.warning("Slot %s: nichts mehr übrig", label)
            return False

    return await deliver(tg, store, cfg, words, chat_id, picked, label, day, now)


async def send_bit(tg, store, cfg, bits, chat_id, day, now):
    """Verschickt höchstens ein Grammatik-Bit pro Tag."""
    row = store.delivery("bit", day)
    if row:
        if row["status"] == "sent" or row["attempts"] >= MAX_ATTEMPTS:
            return False
        bit_id = row["item_id"]
    else:
        bit_id = planner.pick_bit(store, now)
        if bit_id is None:
            return False

    bit = bits.get(bit_id)
    if bit is None:
        log.warning("Bit %s fehlt in grammar.yaml", bit_id)
        return False

    bit_path = cfg.bits_dir / f"{bit['icon']}.jpg"
    if not bit_path.exists():
        log.error("Bit-Icon fehlt: %s", bit_path)
        return False

    delivery_id, fresh = store.claim(bit_id, "bit", day, "bit", now)
    if delivery_id is None:
        return False

    row = store.delivery_by_id(delivery_id)
    if not fresh and row["status"] == "sent":
        return False
    if row["attempts"] >= MAX_ATTEMPTS:
        log.warning("Bit %s gibt nach %d Versuchen auf", bit_id, MAX_ATTEMPTS)
        return False

    try:
        message = await tg.send_photo(
            chat_id,
            bit_path,
            grammar.caption(bit),
            grammar.keyboard(delivery_id, bit),
        )
    except TelegramError as exc:
        log.error("Bit-Versand %s fehlgeschlagen: %s", bit_id, exc)
        store.mark_failed(delivery_id)
        return False

    store.mark_sent(delivery_id, message["message_id"], now)
    log.info("Bit %s um %s", bit_id, now.strftime("%H:%M"))
    return True


async def tick(tg, store, cfg, words, bits, now=None):
    """Prüft, ob gerade ein Slot dran ist, und schickt höchstens eine Karte
    plus das Bit des Tages."""
    now = now or local_now(cfg)

    if is_paused(store, now):
        return False

    day = now.date()
    if cfg.weekend_off and day.weekday() >= 5:
        return False

    chat_id = store.get_setting("chat_id")
    if not chat_id:
        return False

    slots = current_slots(store, cfg)
    if not slots:
        return False
    sent = False

    for slot in slots:
        start = datetime.combine(day, slot)
        if not (start <= now < start + timedelta(minutes=cfg.slot_window)):
            continue
        sent = await send_slot(
            tg, store, cfg, words, slot.strftime("%H:%M"), day, now, int(chat_id)
        )
        break

    # Das Bit hängt am zweiten Slot des Tages. Es wird auch dann geschickt,
    # wenn die Karte dort schon raus ist oder gerade nicht mehr übrig war.
    bit_slot = slots[1] if len(slots) > 1 else slots[0]
    start = datetime.combine(day, bit_slot)
    if start <= now < start + timedelta(minutes=cfg.slot_window):
        sent = await send_bit(
            tg, store, cfg, bits, int(chat_id), day, now
        ) or sent

    return sent


# ------------------------------------------------------------------ Loops --

async def tick_loop(tg, store, cfg, words, bits):
    while True:
        try:
            await tick(tg, store, cfg, words, bits)
        except Exception:
            log.exception("Tick fehlgeschlagen")
        await asyncio.sleep(TICK_SECONDS)


async def poll_loop(tg, store, cfg, words, bits):
    offset = 0
    while True:
        try:
            updates = await tg.get_updates(offset)
        except TelegramError as exc:
            log.warning("Polling: %s", exc)
            await asyncio.sleep(5)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            try:
                await handle_update(tg, store, cfg, words, bits, update)
            except Exception:
                log.exception("Update %s fehlgeschlagen", update["update_id"])


# --------------------------------------------------------------- Routing ---

def ensure_allowed(store, user_id):
    """Der erste Nutzer wird automatisch Eigentümer, alle anderen fliegen raus."""
    ids = store.allowed_ids()
    if not ids:
        store.add_allowed(user_id)
        log.info("Erster Nutzer registriert: %s", user_id)
        return True
    return user_id in ids


async def handle_update(tg, store, cfg, words, bits, update):
    if "callback_query" in update:
        await handle_callback(tg, store, cfg, bits, update["callback_query"])
    elif "message" in update:
        await handle_message(tg, store, cfg, words, update["message"])


async def handle_message(tg, store, cfg, words, message):
    user = message.get("from") or {}
    user_id = user.get("id")
    chat_id = (message.get("chat") or {}).get("id")
    if not user_id or not chat_id or not ensure_allowed(store, user_id):
        return

    store.set_setting("chat_id", str(chat_id))

    text = (message.get("text") or "").strip()
    if not text.startswith("/"):
        return

    command = text.split()[0][1:].split("@")[0].lower()
    args = text.split()[1:]
    now = local_now(cfg)

    if command == "start":
        slots = " · ".join(s.strftime("%H:%M") for s in current_slots(store, cfg))
        await tg.send_message(
            chat_id,
            "Merhaba! 👋\n"
            f"Dreimal am Tag kommt eine Karte: {slots}.\n"
            "Einmal am Tag kommt ein Grammatik-Bit.\n"
            "Hazır mısın? · Bist du bereit?\n\n" + HELP_TEXT,
        )

    elif command in {"hilfe", "help"}:
        await tg.send_message(chat_id, HELP_TEXT)

    elif command == "heute":
        slots = current_slots(store, cfg)
        remaining = [s.strftime("%H:%M") for s in slots
                     if datetime.combine(now.date(), s) > now]
        stats = store.stats(now)
        kommt = ", ".join(remaining) if remaining else "nichts mehr · bugün bitti"
        await tg.send_message(
            chat_id,
            f"Bugün · Heute noch: {kommt}\n"
            f"Fällig: {stats['due']} · Serie: {stats['streak']} Tage",
        )

    elif command == "stats":
        stats = store.stats(now)
        await tg.send_message(
            chat_id,
            f"🔥 Seri · Serie: {stats['streak']} Tage\n"
            f"📚 Fällig: {stats['due']} von {stats['total']}\n"
            f"✅ Doğru: {stats['accuracy'] * 100:.0f} % "
            f"({stats['answered']} Antworten)",
        )

    elif command == "next":
        picked = planner.pick(store, now, now.date())
        if picked is None:
            await tg.send_message(chat_id, "Nichts mehr übrig · bugün bitti")
            return
        await deliver(tg, store, cfg, words, chat_id, picked,
                      f"manuell-{now:%H%M%S}", now.date(), now)

    elif command == "pause":
        days = int(args[0]) if args and args[0].isdigit() else 1
        until = now + timedelta(days=days)
        store.set_setting("pause_until", ts(until))
        await tg.send_message(
            chat_id, f"Mola · Pause bis {until:%d.%m. %H:%M}"
        )

    elif command == "resume":
        store.set_setting("pause_until", "")
        await tg.send_message(chat_id, "Devam · weiter geht's")

    elif command == "zeit":
        slots = parse_slots(" ".join(args).replace(" ", ","))
        if not slots:
            await tg.send_message(
                chat_id, "Format: /zeit 08:30 13:00 20:00"
            )
            return
        store.set_setting("slots", ",".join(s.strftime("%H:%M") for s in slots))
        await tg.send_message(
            chat_id,
            "Yeni saatler · neue Zeiten: "
            + " · ".join(s.strftime("%H:%M") for s in slots),
        )

    else:
        await tg.send_message(chat_id, "Anlamadım · verstehe ich nicht.\n\n"
                                       + HELP_TEXT)


async def handle_callback(tg, store, cfg, bits, query):
    user_id = (query.get("from") or {}).get("id")
    if not user_id or not ensure_allowed(store, user_id):
        await tg.answer_callback(query["id"])
        return

    data = query.get("data")
    if data and data.startswith("g:"):
        await handle_bit_callback(tg, store, cfg, bits, query)
        return

    parsed = cards.parse_callback(data)
    if not parsed:
        await tg.answer_callback(query["id"])
        return

    delivery_id, result = parsed
    item_id, status = store.answer(delivery_id, result, local_now(cfg))

    if status == "ok":
        await tg.answer_callback(query["id"], cards.STATUS[result])
        message = query.get("message") or {}
        chat_id = (message.get("chat") or {}).get("id")
        if chat_id and message.get("message_id"):
            caption = message.get("caption") or ""
            if cards.STATUS[result] not in caption:
                await tg.edit_caption(
                    chat_id, message["message_id"],
                    f"{caption}\n\n{cards.STATUS[result]}",
                )
    elif status == "duplicate":
        log.info("Doppeltap auf Lieferung %s (%s) ignoriert",
                 delivery_id, result)
        await tg.answer_callback(
            query["id"], "Zaten cevaplandı · schon beantwortet"
        )
    elif status == "stale":
        log.info("Alte Lieferung %s (%s) abgelehnt", delivery_id, result)
        await tg.answer_callback(query["id"], cards.STALE_TEXT)
    else:
        await tg.answer_callback(query["id"])


def _bit_id(store, delivery_id):
    row = store.delivery_by_id(delivery_id)
    if row is None or row["kind"] != "bit":
        return None
    return row["item_id"]


async def _announce_retired(tg, bits, chat_id, message, bit_id):
    """Entfernt die Buttons und hängt die Bestätigung an die Caption."""
    if not chat_id or not message.get("message_id"):
        return
    bit = bits.get(bit_id)
    caption = message.get("caption") or ""
    if not caption and bit:
        caption = grammar.caption(bit)
    if grammar.RETIRED_TEXT in caption:
        return
    caption = (f"{caption}\n\n{grammar.RETIRED_TEXT}"
               if caption else grammar.RETIRED_TEXT)
    await tg.edit_caption(chat_id, message["message_id"], caption)


async def handle_bit_callback(tg, store, cfg, bits, query):
    parsed = grammar.parse_callback(query.get("data"))
    if not parsed:
        await tg.answer_callback(query["id"])
        return

    delivery_id, action = parsed
    now = local_now(cfg)
    message = query.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    bit_id = _bit_id(store, delivery_id)

    if action == "x":
        retired_id, status = store.retire_bit(delivery_id, now)
        if status == "ok":
            await tg.answer_callback(query["id"], grammar.RETIRED_TEXT)
            await _announce_retired(
                tg, bits, chat_id, message, retired_id or bit_id
            )
        elif status == "duplicate":
            await tg.answer_callback(query["id"], grammar.ALREADY_TEXT)
            await _announce_retired(tg, bits, chat_id, message, bit_id)
        else:
            await tg.answer_callback(query["id"])
        return

    bit = bits.get(bit_id)
    if bit is None or action >= len(bit["options"]):
        await tg.answer_callback(query["id"])
        return

    feedback_text, result = grammar.feedback(bit, action)
    _, status = store.answer_bit(delivery_id, result, now)

    if status == "ok":
        await tg.answer_callback(query["id"], feedback_text.splitlines()[0])
        if chat_id and message.get("message_id"):
            await tg.edit_caption(
                chat_id,
                message["message_id"],
                grammar.caption(bit, feedback_text),
                grammar.retire_keyboard(delivery_id),
            )
    elif status == "duplicate":
        await tg.answer_callback(query["id"], grammar.ALREADY_TEXT)
    elif status == "stale":
        await tg.answer_callback(query["id"], cards.STALE_TEXT)
    else:
        await tg.answer_callback(query["id"])


# ------------------------------------------------------------------ Start --

def setup_logging(cfg):
    cfg.log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(cfg.log_path),
        ],
    )
    # httpx loggt sonst jede Request-URL – inklusive Bot-Token.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def run(once=False):
    cfg = load_config()
    if not cfg.token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN fehlt.\n"
            "  cp .env.example .env\n"
            "und den Token von @BotFather eintragen."
        )

    setup_logging(cfg)

    words = {word["id"]: word for word in load_words()}
    bits = {bit["id"]: bit for bit in load_bits()}
    store = Store(cfg.db_path)
    now = local_now(cfg)
    added = store.sync_items(words.keys(), now)
    added_bits = store.sync_bits(bits.keys(), now)
    for user_id in cfg.seed_ids:
        store.add_allowed(user_id)
    if added:
        log.info("%d neue Wörter aufgenommen", added)
    if added_bits:
        log.info("%d neue Grammatik-Bits aufgenommen", added_bits)

    telegram = Telegram(cfg.token)
    log.info(
        "Türkmek läuft · %s · Slots %s",
        cfg.tz,
        " · ".join(cfg.slot_labels),
    )

    try:
        if once:
            await tick(telegram, store, cfg, words, bits)
            return
        await asyncio.gather(
            poll_loop(telegram, store, cfg, words, bits),
            tick_loop(telegram, store, cfg, words, bits),
        )
    finally:
        await telegram.close()
        store.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Türkmek Telegram-Bot")
    parser.add_argument("--once", action="store_true",
                        help="nur einen Versand-Tick ausführen")
    args = parser.parse_args(argv)

    try:
        asyncio.run(run(once=args.once))
    except KeyboardInterrupt:
        print("\nGörüşürüz · bis später")


if __name__ == "__main__":
    main()
