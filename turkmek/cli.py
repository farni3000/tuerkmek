"""Kommandozeile für den Zustand – ohne Bot, ohne Netz.

    python -m turkmek.cli status
    python -m turkmek.cli due
    python -m turkmek.cli send            # delegiert an turkmek.send
    python -m turkmek.cli pause 7
    python -m turkmek.cli resume
    python -m turkmek.cli reset kapi
"""

from __future__ import annotations

import argparse
from datetime import timedelta

from .bot import current_slots, is_paused, local_now
from .config import load_config
from .content import load_words
from .store import Store, ts


def _open():
    cfg = load_config()
    store = Store(cfg.db_path)
    words = {word["id"]: word for word in load_words()}
    store.sync_items(words.keys(), local_now(cfg))
    return cfg, store, words


def cmd_status(cfg, store, words):
    now = local_now(cfg)
    stats = store.stats(now)
    chat = store.get_setting("chat_id")
    pause = store.get_setting("pause_until")
    slots = current_slots(store, cfg)

    print(f"Wörter        {stats['total']}")
    print(f"Fällig        {stats['due']}")
    print(f"Serie         {stats['streak']} Tage")
    print(f"Beantwortet   {stats['answered']} "
          f"({stats['accuracy'] * 100:.0f} % richtig)")
    print(f"Slots         {', '.join(s.strftime('%H:%M') for s in slots)}")
    print(f"Chat          {chat or '– noch kein /start –'}")
    if is_paused(store, now):
        print(f"Pause         bis {pause}")


def cmd_due(cfg, store, words):
    now = local_now(cfg)
    rows = store.due_items(now) + store.new_items(now)
    if not rows:
        print("Nichts fällig.")
        return
    for row in rows:
        word = words.get(row["item_id"])
        label = word["tr"] if word else row["item_id"]
        print(f"{label:<14} fällig {row['due_at']}")


def cmd_pause(cfg, store, words, days):
    until = local_now(cfg) + timedelta(days=days)
    store.set_setting("pause_until", ts(until))
    print(f"Pause bis {until:%d.%m. %H:%M}")


def cmd_resume(cfg, store, words):
    store.set_setting("pause_until", "")
    print("Weiter.")


def cmd_reset(cfg, store, words, item_id):
    if item_id not in words:
        raise SystemExit(f"Unbekanntes Wort: {item_id}")
    store.reset(item_id)
    print(f"{item_id} zurück auf neu gesetzt.")


def _run_send(args):
    # Eine Implementierung für beide Einstiege: turkmek.send.
    from .send import main as send_main

    forwarded = ["--count", str(args.count)]
    if args.dry_run:
        forwarded.append("--dry-run")
    if args.force:
        forwarded.append("--force")
    send_main(forwarded)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Türkmek-Zustand ansehen")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Überblick")
    sub.add_parser("due", help="was gerade fällig ist")
    sub.add_parser("resume", help="Pause beenden")

    send = sub.add_parser("send", help="sofort eine Karte schicken")
    send.add_argument("-n", "--count", type=int, default=1)
    send.add_argument("--dry-run", action="store_true")
    send.add_argument("--force", action="store_true")

    pause = sub.add_parser("pause", help="Pause in Tagen")
    pause.add_argument("days", nargs="?", type=int, default=1)

    reset = sub.add_parser("reset", help="Wort vergessen lassen")
    reset.add_argument("item_id")

    args = parser.parse_args(argv)

    if args.command == "send":
        _run_send(args)
        return

    cfg, store, words = _open()
    try:
        if args.command == "status":
            cmd_status(cfg, store, words)
        elif args.command == "due":
            cmd_due(cfg, store, words)
        elif args.command == "pause":
            cmd_pause(cfg, store, words, args.days)
        elif args.command == "resume":
            cmd_resume(cfg, store, words)
        elif args.command == "reset":
            cmd_reset(cfg, store, words, args.item_id)
    finally:
        store.close()


if __name__ == "__main__":
    main()
