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

from . import cards, planner
from .config import load_config, parse_slots
from .content import load_words
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


async def tick(tg, store, cfg, words, now=None):
    """Prüft, ob gerade ein Slot dran ist, und schickt höchstens eine Karte."""
    now = now or local_now(cfg)

    if is_paused(store, now):
        return False

    day = now.date()
    if cfg.weekend_off and day.weekday() >= 5:
        return False

    chat_id = store.get_setting("chat_id")
    if not chat_id:
        return False

    for slot in current_slots(store, cfg):
        start = datetime.combine(day, slot)
        if not (start <= now < start + timedelta(minutes=cfg.slot_window)):
            continue
        return await send_slot(
            tg, store, cfg, words, slot.strftime("%H:%M"), day, now, int(chat_id)
        )

    return False


# ------------------------------------------------------------------ Loops --

async def tick_loop(tg, store, cfg, words):
    while True:
        try:
            await tick(tg, store, cfg, words)
        except Exception:
            log.exception("Tick fehlgeschlagen")
        await asyncio.sleep(TICK_SECONDS)


async def poll_loop(tg, store, cfg, words):
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
                await handle_update(tg, store, cfg, words, update)
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


async def handle_update(tg, store, cfg, words, update):
    if "callback_query" in update:
        await handle_callback(tg, store, cfg, update["callback_query"])
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


async def handle_callback(tg, store, cfg, query):
    user_id = (query.get("from") or {}).get("id")
    if not user_id or not ensure_allowed(store, user_id):
        await tg.answer_callback(query["id"])
        return

    parsed = cards.parse_callback(query.get("data"))
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
        await tg.answer_callback(
            query["id"], "Zaten cevaplandı · schon beantwortet"
        )
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
    store = Store(cfg.db_path)
    added = store.sync_items(words.keys(), local_now(cfg))
    for user_id in cfg.seed_ids:
        store.add_allowed(user_id)
    if added:
        log.info("%d neue Wörter aufgenommen", added)

    telegram = Telegram(cfg.token)
    log.info(
        "Türkmek läuft · %s · Slots %s",
        cfg.tz,
        " · ".join(cfg.slot_labels),
    )

    try:
        if once:
            await tick(telegram, store, cfg, words)
            return
        await asyncio.gather(
            poll_loop(telegram, store, cfg, words),
            tick_loop(telegram, store, cfg, words),
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
