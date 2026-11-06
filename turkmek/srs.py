"""Spaced Repetition, bewusst grob.

Warum tagesgranular und nicht wie Anki mit Minutenstufen: bei drei Nudges am
Tag wäre eine 10-Minuten-Wiederholung schlicht nicht zustellbar. Die kleinste
sinnvolle Einheit ist ein Tag.
"""

from __future__ import annotations

EASE_START = 2.5
EASE_MIN = 1.3
EASE_MAX = 3.0
MAX_INTERVAL = 180.0

GOOD = "y"
AGAIN = "n"


def apply(result, reps, interval, ease, lapses):
    """Nächster Zustand nach einer Antwort.

    `result` ist "y" (gewusst) oder "n" (nochmal). Gibt ein dict zurück.
    """
    if result == AGAIN:
        return {
            "reps": 0,
            "interval": 1.0,
            "ease": max(EASE_MIN, ease - 0.2),
            "lapses": lapses + 1,
        }

    reps += 1
    if reps == 1:
        new_interval = 1.0
    elif reps == 2:
        new_interval = 3.0
    else:
        new_interval = min(MAX_INTERVAL, max(interval, 1.0) * ease)

    return {
        "reps": reps,
        "interval": new_interval,
        "ease": min(EASE_MAX, ease + 0.05),
        "lapses": lapses,
    }


def is_mature(interval):
    return interval >= 21.0
