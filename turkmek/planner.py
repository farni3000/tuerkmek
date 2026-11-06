"""Welche Karte kommt jetzt?

Reihenfolge: fällige Wiederholung → neues Wort (begrenzt) → irgendetwas, das
lange nicht dran war. Ein Slot bleibt dadurch nie leer.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_NEW_PER_DAY = 2


@dataclass
class Pick:
    item_id: str
    kind: str  # new | review | extra


def pick(store, now, day, max_new=MAX_NEW_PER_DAY, exclude=()):
    seen = store.seen_today(day) | set(exclude)

    for row in store.due_items(now):
        if row["item_id"] not in seen:
            return Pick(row["item_id"], "review")

    if store.new_today(day) < max_new:
        for row in store.new_items(now):
            if row["item_id"] not in seen:
                return Pick(row["item_id"], "new")

    for row in store.fallback_items():
        if row["item_id"] not in seen:
            return Pick(row["item_id"], "extra")

    return None
