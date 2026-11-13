"""Kleine Motive für die Grammatik-Bits.

Bewusst abstrakt und ohne Katze: Auf der Bit-Kachel ist das Icon nur ein
Tupfer, der die Regel markiert. Die Motive werden von mehreren Bits geteilt –
so bleibt die Sammlung klein und beim Erweitern konsistent.
"""

from __future__ import annotations

from .icons import _frage, _herz
from .palette import (
    BLUE, BLUE_L, CREAM, GREEN, INK, RED, YELLOW,
)
from .scene import circle, compose, line, poly, polyline, rect


def akkusativ():
    """Zielscheibe mit Pfeil: das Objekt bekommt eine Markierung."""
    return compose(
        circle(43, 48, 25, fill=None, width=2.2),
        circle(43, 48, 13, fill=None, width=1.8),
        circle(43, 48, 4, fill=RED, stroke=None),
        polyline([(64, 28), (84, 28)], width=2.4),
        poly([(76, 21), (86, 28), (76, 35)], fill=INK, stroke=None),
    )


def plural():
    """Drei Karten nebeneinander: eins wird viele."""
    return compose(
        rect(16, 32, 20, 26, 3, fill=BLUE_L),
        rect(40, 26, 20, 30, 3, fill=GREEN),
        rect(64, 32, 20, 26, 3, fill=YELLOW),
        circle(26, 45, 2.8, fill=INK, stroke=None),
        circle(50, 41, 2.8, fill=CREAM, stroke=None),
        circle(74, 45, 2.8, fill=INK, stroke=None),
    )


def lokativ():
    """Ortsmarke: wo etwas ist."""
    return compose(
        circle(50, 40, 18, fill=RED),
        poly([(34, 47), (66, 47), (50, 78)], fill=RED),
        circle(50, 40, 6, fill=CREAM, stroke=None),
    )


def vokal():
    """Zwei Laute, die sich angleichen."""
    return compose(
        circle(35, 50, 17, fill=BLUE_L),
        circle(65, 50, 17, fill=YELLOW),
        circle(35, 50, 5, fill=INK, stroke=None),
        circle(65, 50, 5, fill=INK, stroke=None),
    )


def frage():
    """Fragezeichen auf Papier."""
    return compose(
        circle(50, 50, 30, fill=CREAM),
        _frage(50, 48, 1.7),
    )


def besitz():
    """Ein Anhänger mit Herz: das gehört mir."""
    return compose(
        poly([(24, 22), (62, 22), (78, 38), (78, 58), (62, 74), (24, 74)],
             fill=BLUE_L, width=2.0),
        circle(35, 34, 3, fill=CREAM, stroke=INK, width=1.1),
        _herz(55, 50, 18),
    )


def gegenwart():
    """Uhr: jetzt, im Moment."""
    return compose(
        circle(50, 50, 30, fill=CREAM),
        circle(50, 50, 2.6, fill=INK, stroke=None),
        line((50, 50), (50, 28), width=2.6),
        line((50, 50), (67, 58), width=2.2),
        line((50, 80), (50, 84), width=2.4),
        line((50, 20), (50, 16), width=2.4),
    )


def vergangenheit():
    """Kalender mit Pfeil nach links: das ist vorbei."""
    return compose(
        rect(24, 24, 52, 48, 4, fill=CREAM),
        rect(24, 24, 52, 12, 4, fill=BLUE),
        line((38, 17), (38, 29), width=2.2),
        line((62, 17), (62, 29), width=2.2),
        polyline([(68, 52), (38, 52)], width=2.4),
        poly([(45, 45), (36, 52), (45, 59)], fill=INK, stroke=None),
    )


def instrumental():
    """Zwei verbundene Ringe: mit etwas zusammen."""
    return compose(
        circle(39, 50, 18, fill=None, width=2.6),
        circle(61, 50, 18, fill=None, width=2.6),
        line((48, 39), (55, 39), width=2.0),
        line((48, 61), (55, 61), width=2.0),
    )


def var_yok():
    """Haken und Kreuz: gibt es, gibt es nicht."""
    return compose(
        circle(31, 50, 18, fill=GREEN),
        polyline([(22, 50), (29, 58), (41, 42)], stroke=CREAM, width=3.0),
        circle(69, 50, 18, fill=RED),
        line((61, 42), (77, 58), stroke=CREAM, width=3.0),
        line((77, 42), (61, 58), stroke=CREAM, width=3.0),
    )


BIT_ICONS = {
    "akkusativ": akkusativ,
    "plural": plural,
    "lokativ": lokativ,
    "vokal": vokal,
    "frage": frage,
    "besitz": besitz,
    "gegenwart": gegenwart,
    "vergangenheit": vergangenheit,
    "instrumental": instrumental,
    "var_yok": var_yok,
}
