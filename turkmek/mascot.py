"""Die Katze: das wiederkehrende Maskottchen auf jeder Karte.

Sie sitzt neben dem Motiv, schläft daneben, hebt die Pfote oder hält etwas
fest. Accessoires und Gegenstände sind bewusst albern – das Bild soll im Kopf
bleiben, nicht schön sein.
"""

from __future__ import annotations

from .icons import _frage, _herz
from .palette import (
    BLUE, CAT, CREAM, FISH, FISH_D, GLASS, INK, PINK, YELLOW,
)
from .scene import circle, compose, ellipse, line, poly, polyline, rect


def cat(pose="sit", x=84.0, y=80.0, s=0.7, accessory=None, item=None,
        effect=None):
    builder = _POSES.get(pose, _sit)
    parts, head = builder(x, y, s)
    parts += _face(head, pose, effect, s)
    if accessory:
        parts += _ACCESSORIES.get(accessory, lambda *a: [])(x, y, s, head)
    if item:
        parts += _ITEMS.get(item, lambda *a: [])(x, y, s)
    if effect:
        parts += _EFFECTS.get(effect, lambda *a: [])(x, y, s, head)
    return parts


# ------------------------------------------------------------------ Posen --

def _sit(x, y, s):
    hx, hy, r = x, y - 9 * s, 7 * s
    parts = ellipse(x, y + 3 * s, 8 * s, 10 * s, fill=CAT)
    parts += polyline([(x + 6 * s, y + 9 * s), (x + 13 * s, y + 6 * s),
                       (x + 15 * s, y - 2 * s)], width=2.4 * s)
    parts += ellipse(x - 4.5 * s, y + 12 * s, 2.6 * s, 1.5 * s, fill=CAT)
    parts += ellipse(x + 4.5 * s, y + 12 * s, 2.6 * s, 1.5 * s, fill=CAT)
    parts += _kopf(hx, hy, r, s)
    return parts, (hx, hy, r)


def _peek(x, y, s):
    hx, hy, r = x, y - 4 * s, 8 * s
    parts = _kopf(hx, hy, r, s)
    parts += ellipse(x - 5 * s, y + 5 * s, 2.4 * s, 1.5 * s, fill=CAT)
    parts += ellipse(x + 5 * s, y + 5 * s, 2.4 * s, 1.5 * s, fill=CAT)
    return parts, (hx, hy, r)


def _sleep(x, y, s):
    hx, hy, r = x + 8 * s, y + 1 * s, 6 * s
    parts = ellipse(x, y + 6 * s, 11 * s, 5.5 * s, fill=CAT)
    parts += polyline([(x - 10 * s, y + 8 * s), (x - 15 * s, y + 4 * s),
                       (x - 13 * s, y - 1 * s)], width=2.0 * s)
    parts += _kopf(hx, hy, r, s * 0.86)
    return parts, (hx, hy, r)


def _point(x, y, s):
    parts, head = _sit(x, y, s)
    parts += line((x + 5 * s, y + 2 * s), (x + 11 * s, y - 9 * s),
                  width=2.4 * s)
    parts += circle(x + 12 * s, y - 10 * s, 1.8 * s, fill=CAT)
    return parts, head


def _hold(x, y, s):
    parts, head = _sit(x, y, s)
    parts += line((x + 5 * s, y + 2 * s), (x + 9 * s, y + 5 * s),
                  width=2.4 * s)
    return parts, head


_POSES = {
    "sit": _sit,
    "judge": _sit,  # gleiche Haltung, anderer Blick
    "peek": _peek,
    "sleep": _sleep,
    "point": _point,
    "hold": _hold,
}


# ------------------------------------------------------------- Kopf & Gesicht

def _kopf(hx, hy, r, s):
    parts = circle(hx, hy, r, fill=CAT)
    parts += poly([(hx - 6.5 * s, hy - 3.5 * s), (hx - 5 * s, hy - 13 * s),
                   (hx - 1 * s, hy - 5.5 * s)], fill=CAT)
    parts += poly([(hx + 6.5 * s, hy - 3.5 * s), (hx + 5 * s, hy - 13 * s),
                   (hx + 1 * s, hy - 5.5 * s)], fill=CAT)
    return parts


def _face(head, pose, effect, s):
    hx, hy, r = head
    parts = []

    if pose == "sleep":
        parts += line((hx - 3.5 * s, hy), (hx - 1.2 * s, hy), width=1.4 * s)
        parts += line((hx + 1.2 * s, hy), (hx + 3.5 * s, hy), width=1.4 * s)
    elif pose == "judge":
        parts += line((hx - 4 * s, hy - 0.6 * s), (hx - 1.5 * s, hy),
                      width=1.5 * s)
        parts += line((hx + 1.5 * s, hy), (hx + 4 * s, hy - 0.6 * s),
                      width=1.5 * s)
    else:
        er = 1.5 * s if effect == "surprise" else 1.25 * s
        parts += circle(hx - 2.6 * s, hy - 0.5 * s, er,
                        fill=INK, stroke=None)
        parts += circle(hx + 2.6 * s, hy - 0.5 * s, er,
                        fill=INK, stroke=None)
        parts += circle(hx - 2.9 * s, hy - 0.9 * s, er * 0.32,
                        fill=CREAM, stroke=None)
        parts += circle(hx + 2.3 * s, hy - 0.9 * s, er * 0.32,
                        fill=CREAM, stroke=None)

    parts += poly([(hx - 0.9 * s, hy + 1.1 * s), (hx + 0.9 * s, hy + 1.1 * s),
                   (hx, hy + 2.1 * s)], fill=PINK)
    parts += line((hx, hy + 2.1 * s), (hx, hy + 3 * s), width=0.9 * s)
    parts += line((hx - 1.4 * s, hy + 2.7 * s),
                  (hx - 4.8 * s, hy + 2.2 * s), width=0.8 * s)
    parts += line((hx + 1.4 * s, hy + 2.7 * s),
                  (hx + 4.8 * s, hy + 2.2 * s), width=0.8 * s)
    return parts


# ---------------------------------------------------------- Accessoires ----

def _shades(x, y, s, head):
    hx, hy, _ = head
    ey = hy - 0.5 * s
    return compose(
        rect(hx - 5 * s, ey - 1.6 * s, 4.2 * s, 3.2 * s, 1.2 * s, fill=INK),
        rect(hx + 0.8 * s, ey - 1.6 * s, 4.2 * s, 3.2 * s, 1.2 * s, fill=INK),
        line((hx - 0.8 * s, ey), (hx + 0.8 * s, ey), width=1.2 * s),
    )


def _goggles(x, y, s, head):
    hx, hy, _ = head
    return compose(
        circle(hx - 2.6 * s, hy - 0.5 * s, 2.2 * s, fill=GLASS),
        circle(hx + 2.6 * s, hy - 0.5 * s, 2.2 * s, fill=GLASS),
        line((hx - 5 * s, hy - 1 * s), (hx + 5 * s, hy - 1 * s),
             width=1.0 * s),
        line((hx - 6.5 * s, hy - 1 * s), (hx - 7 * s, hy - 3 * s),
             width=1.0 * s),
    )


def _hat(x, y, s, head):
    hx, hy, _ = head
    return compose(
        rect(hx - 5 * s, hy - 9 * s, 10 * s, 3.4 * s, 1 * s, fill=BLUE),
        rect(hx - 6.5 * s, hy - 6 * s, 13 * s, 2 * s, 1 * s, fill=INK),
        circle(hx, hy - 7.3 * s, 1.0 * s, fill=YELLOW),
    )


def _crown(x, y, s, head):
    hx, hy, _ = head
    return poly([(hx - 5 * s, hy - 5 * s), (hx - 5 * s, hy - 10 * s),
                 (hx - 2 * s, hy - 7 * s), (hx, hy - 11.5 * s),
                 (hx + 2 * s, hy - 7 * s), (hx + 5 * s, hy - 10 * s),
                 (hx + 5 * s, hy - 5 * s)], fill=YELLOW)


_ACCESSORIES = {
    "shades": _shades,
    "goggles": _goggles,
    "hat": _hat,
    "crown": _crown,
}


# --------------------------------------------------------------- Requisiten -

def _fish(x, y, s):
    return compose(
        ellipse(x + 11 * s, y + 4 * s, 4.5 * s, 2.8 * s, fill=FISH),
        poly([(x + 15 * s, y + 4 * s), (x + 18.5 * s, y + 1.5 * s),
              (x + 18.5 * s, y + 6.5 * s)], fill=FISH_D),
        circle(x + 13 * s, y + 3.2 * s, 0.5 * s, fill=INK, stroke=None),
    )


def _bread(x, y, s):
    return compose(
        ellipse(x + 11 * s, y + 3 * s, 5 * s, 3.4 * s, fill="#c99a5e"),
        line((x + 8 * s, y + 1 * s), (x + 10 * s, y + 3 * s),
             width=0.9 * s),
        line((x + 11 * s, y + 1 * s), (x + 13 * s, y + 3 * s),
             width=0.9 * s),
    )


def _heart(x, y, s):
    return _herz(x + 11 * s, y + 2 * s, 4.5 * s)


def _question(x, y, s):
    return _frage(x + 12 * s, y + 4 * s, 0.45 * s)


_ITEMS = {
    "fish": _fish,
    "bread": _bread,
    "heart": _heart,
    "question": _question,
}


# ---------------------------------------------------------------- Effekte --

def _zzz(x, y, s, head):
    hx, hy, r = head
    parts = []
    for i, size in enumerate((4, 6, 8)):
        bx = hx + (2 + i * 2.4) * s
        by = hy - (r + 3 + i * 4) * s * 0.7
        parts += polyline([(bx, by), (bx + size * s, by),
                           (bx, by + size * s),
                           (bx + size * s, by + size * s)],
                          stroke="#9b9d9a", width=1.4)
    return parts


def _sweat(x, y, s, head):
    hx, hy, r = head
    return compose(
        polyline([(hx + 7 * s, hy - 4 * s), (hx + 8 * s, hy - 1 * s)],
                 stroke=BLUE, width=1.6),
        polyline([(hx + 9 * s, hy - 4 * s), (hx + 10 * s, hy - 1 * s)],
                 stroke=BLUE, width=1.4),
    )


def _surprise(x, y, s, head):
    hx, hy, _ = head
    return compose(
        line((hx - 10 * s, hy - 8 * s), (hx - 14 * s, hy - 13 * s),
             width=1.3),
        line((hx + 10 * s, hy - 8 * s), (hx + 14 * s, hy - 13 * s),
             width=1.3),
    )


def _question_effect(x, y, s, head):
    hx, hy, r = head
    return _frage(hx - 12 * s, hy - 6 * s, 0.4 * s)


_EFFECTS = {
    "zzz": _zzz,
    "sweat": _sweat,
    "surprise": _surprise,
    "question": _question_effect,
}
