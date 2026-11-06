"""Eine Karte pro Aufruf – ohne auf einen Slot zu warten.

Für cron, LaunchAgent oder einfach von Hand:

    python -m turkmek.send                 # eine Karte
    python -m turkmek.send --count 3       # drei Karten
    python -m turkmek.send --dry-run       # nur zeigen, was käme
    python -m turkmek.send --force         # auch wenn pausiert

Anders als der Scheduler ignoriert der Soft-Versand das Tagesbudget für neue
Wörter: wer ausdrücklich fragt, bekommt. Bereits heute verschickte Karten
werden trotzdem nicht wiederholt.
"""

from __future__ import annotations

import argparse
import asyncio

from . import planner
from .bot import deliver, is_paused, local_now
from .config import load_config
from .content import load_words
from .store import Store
from .telegram import Telegram


async def send_cards(telegram, store, cfg, words, chat_id, count=1,
                     dry_run=False):
    """Schickt bis zu `count` Karten. Gibt [(item_id, kind, gesendet)] zurück."""
    now = local_now(cfg)
    day = now.date()
    exclude = set()
    results = []

    for index in range(count):
        picked = planner.pick(store, now, day, max_new=99, exclude=exclude)
        if picked is None:
            break

        if dry_run:
            exclude.add(picked.item_id)
            results.append((picked.item_id, picked.kind, False))
            continue

        sent = await deliver(
            telegram, store, cfg, words, chat_id, picked,
            f"soft-{now:%H%M%S}-{index}", day, now,
        )
        results.append((picked.item_id, picked.kind, sent))

    return results


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Eine Karte sofort schicken, ohne auf den Slot zu warten"
    )
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="Anzahl Karten (Standard: 1)")
    parser.add_argument("--dry-run", action="store_true",
                        help="nur zeigen, was gesendet würde")
    parser.add_argument("--force", action="store_true",
                        help="auch während einer Pause senden")
    args = parser.parse_args(argv)

    cfg = load_config()
    if not cfg.token:
        raise SystemExit("TELEGRAM_BOT_TOKEN fehlt (siehe .env.example).")

    store = Store(cfg.db_path)
    try:
        words = {word["id"]: word for word in load_words()}
        now = local_now(cfg)
        store.sync_items(words.keys(), now)

        chat_id = store.get_setting("chat_id")
        if not chat_id and not args.dry_run:
            raise SystemExit(
                "Noch kein Chat bekannt – schreib dem Bot einmal /start."
            )

        if is_paused(store, now) and not args.force:
            until = store.get_setting("pause_until")
            raise SystemExit(f"Pausiert bis {until} (--force ignoriert das).")

        if args.dry_run:
            results = asyncio.run(
                send_cards(None, store, cfg, words, int(chat_id or 0),
                           count=args.count, dry_run=True)
            )
        else:
            async def run():
                telegram = Telegram(cfg.token)
                try:
                    return await send_cards(
                        telegram, store, cfg, words, int(chat_id),
                        count=args.count,
                    )
                finally:
                    await telegram.close()

            results = asyncio.run(run())

        if not results:
            raise SystemExit("Nichts mehr übrig – heute ist alles durch.")

        for item_id, kind, sent in results:
            if args.dry_run:
                print(f"{item_id:<12} ({kind}) würde gesendet")
            else:
                print(f"{item_id:<12} ({kind}) "
                      f"{'gesendet' if sent else 'fehlgeschlagen'}")

        if not args.dry_run and not any(sent for _, _, sent in results):
            raise SystemExit(1)
    finally:
        store.close()


if __name__ == "__main__":
    main()
