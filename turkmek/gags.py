"""Welche Katze auf welcher Karte auftaucht.

Standard ist nach Wortart sortiert, damit die Katze nicht bei jedem alten
Nomen dasselbe tut. Ein paar Wörter haben einen eigenen Auftritt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Gag:
    pose: str = "sit"
    x: float = 84.0
    y: float = 80.0
    s: float = 0.7
    accessory: Optional[str] = None
    item: Optional[str] = None
    effect: Optional[str] = None


DEFAULTS = {
    "noun": Gag("peek", 86, 88, 0.8),
    "verb": Gag("point", 84, 80, 0.72),
    "adj": Gag("judge", 84, 80, 0.72),
    "color": Gag("sit", 84, 80, 0.7),
    "phrase": Gag("sit", 84, 80, 0.7),
}

# Eigene Auftritte: Pose, Accessoire, Requisite oder Effekt.
SPECIAL = {
    "saat": Gag("sleep", 78, 86, 0.75, effect="zzz"),
    "inek": Gag("judge", 84, 80, 0.72, accessory="shades"),
    "balik": Gag("hold", 82, 80, 0.72, item="fish"),
    "ucak": Gag("sit", 84, 80, 0.72, accessory="goggles"),
    "gemi": Gag("sit", 84, 80, 0.72, accessory="hat"),
    "gormek": Gag("peek", 86, 88, 0.82, effect="surprise"),
    "sicak": Gag("sit", 84, 80, 0.72, effect="sweat"),
    "ekmek": Gag("hold", 82, 80, 0.72, item="bread"),
    "kedi": Gag("sit", 84, 80, 0.75, accessory="crown"),
    "sevmek": Gag("hold", 82, 80, 0.72, item="heart"),
    "belki": Gag("judge", 84, 80, 0.72),
    "yavas": Gag("sleep", 80, 86, 0.72, effect="zzz"),
    "kotu": Gag("judge", 84, 80, 0.72),
}


def for_word(word):
    """Gibt den Auftritt für ein Wort zurück (nie None)."""
    return SPECIAL.get(word["id"], DEFAULTS.get(word.get("pos"),
                                               DEFAULTS["noun"]))
