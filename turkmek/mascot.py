"""Die Katze: das wiederkehrende Maskottchen auf fast jeder Karte.

Dieselbe beige Katze, aber in vielen Haltungen: sie sitzt, liegt, hängt,
reitet, läuft, schnuppert, winkt oder stemmt sich. Accessoires, Requisiten und
Effekte machen sie zum Teil der Szene statt zur Dekoration.

Koordinaten wie überall: 0 bis 100, y zeigt nach unten. `x`/`y` sind die Mitte
des Körpers, `s` skaliert die ganze Figur.
"""

from __future__ import annotations

import math
import random

from . import geometry as geom
from .icons import _frage, _herz
from .palette import (
    BLUE, BREAD, CAT, CHEESE, CHEESE_D, CREAM, FISH, FISH_D, GLASS, GREEN,
    GREY, GREY_L, INK, ORANGE, PINK, RED, WOOD_L, YELLOW,
)
from .scene import (
    bounds, circle, compose, ellipse, line, poly, polyline, rect, star,
)


def cat(pose="sit", x=84.0, y=80.0, s=0.7, flip=False, target=None,
        accessory=None, item=None, effect=None):
    """Baut eine Katze. `target` ist ein absoluter Punkt, zu dem sie langt."""
    builder = _POSES.get(pose, _sit)
    parts, head = builder(x, y, s)
    parts += _face(head, pose, effect, s)

    if accessory:
        parts += _ACCESSORIES.get(accessory, _none)(x, y, s, head)
    if item:
        parts += _ITEMS.get(item, _none)(x, y, s)
    if effect:
        parts += _EFFECTS.get(effect, _none)(x, y, s, head)

    if flip:
        from . import scene as scene_mod
        parts = scene_mod.mirror_shapes(parts, x)

    if target:
        parts += _reach(x, y, s, target)

    return _fit_canvas(parts)


def _fit_canvas(parts, margin=1.5):
    """Schiebt die fertige Katze in die Zeichenfläche, falls sie übersteht."""
    if not parts:
        return parts
    x0, y0, x1, y1 = bounds(parts)
    dx = dy = 0.0
    if x0 < margin:
        dx = margin - x0
    elif x1 > 100 - margin:
        dx = (100 - margin) - x1
    if y0 < margin:
        dy = margin - y0
    elif y1 > 100 - margin:
        dy = (100 - margin) - y1
    if dx or dy:
        for shape in parts:
            shape.points = [(px + dx, py + dy) for px, py in shape.points]
    return parts


def _none(*_args):
    return []


# ------------------------------------------------------------------ Posen --

def _kopf(hx, hy, r, s):
    parts = circle(hx, hy, r, fill=CAT)
    parts += poly([(hx - 6.5 * s, hy - 3.5 * s), (hx - 5 * s, hy - 13 * s),
                   (hx - 1 * s, hy - 5.5 * s)], fill=CAT)
    parts += poly([(hx + 6.5 * s, hy - 3.5 * s), (hx + 5 * s, hy - 13 * s),
                   (hx + 1 * s, hy - 5.5 * s)], fill=CAT)
    return parts


def _sit(x, y, s):
    hx, hy, r = x, y - 9 * s, 7 * s
    parts = ellipse(x, y + 3 * s, 8 * s, 10 * s, fill=CAT)
    parts += polyline([(x + 6 * s, y + 9 * s), (x + 13 * s, y + 6 * s),
                       (x + 15 * s, y - 2 * s)], width=2.4 * s)
    parts += ellipse(x - 4.5 * s, y + 12 * s, 2.6 * s, 1.5 * s, fill=CAT)
    parts += ellipse(x + 4.5 * s, y + 12 * s, 2.6 * s, 1.5 * s, fill=CAT)
    parts += _kopf(hx, hy, r, s)
    return parts, (hx, hy, r)


def _lie(x, y, s):
    hx, hy, r = x + 7 * s, y - 1 * s, 6 * s
    parts = ellipse(x, y + 4 * s, 11 * s, 5 * s, fill=CAT)
    parts += ellipse(x + 10 * s, y + 5 * s, 3 * s, 2 * s, fill=CAT)
    parts += polyline([(x - 8 * s, y + 4 * s), (x - 13 * s, y + 8 * s),
                       (x - 16 * s, y + 3 * s)], width=2.0 * s)
    parts += _kopf(hx, hy, r, s * 0.88)
    return parts, (hx, hy, r)


def _hang(x, y, s):
    hx, hy, r = x, y - 2 * s, 7 * s
    parts = ellipse(x, y + 8 * s, 4.5 * s, 5.5 * s, fill=CAT)
    parts += polyline([(x - 2.5 * s, y + 10 * s), (x - 4 * s, y + 14 * s)],
                      width=2.2 * s)
    parts += polyline([(x + 2.5 * s, y + 10 * s), (x + 4 * s, y + 14 * s)],
                      width=2.2 * s)
    parts += polyline([(x + 4 * s, y + 11 * s), (x + 10 * s, y + 13 * s),
                       (x + 12 * s, y + 8 * s)], width=2.0 * s)
    parts += ellipse(x - 5 * s, y + 2 * s, 2.4 * s, 1.6 * s, fill=CAT)
    parts += ellipse(x + 5 * s, y + 2 * s, 2.4 * s, 1.6 * s, fill=CAT)
    parts += _kopf(hx, hy, r, s)
    return parts, (hx, hy, r)


def _ride(x, y, s):
    hx, hy, r = x, y - 11 * s, 6.5 * s
    parts = ellipse(x, y, 7 * s, 8 * s, fill=CAT)
    parts += polyline([(x - 3 * s, y + 6 * s), (x - 4 * s, y + 13 * s)],
                      width=2.2 * s)
    parts += polyline([(x + 3 * s, y + 6 * s), (x + 4 * s, y + 13 * s)],
                      width=2.2 * s)
    parts += ellipse(x - 4 * s, y + 13.5 * s, 1.8 * s, 1.2 * s, fill=CAT)
    parts += ellipse(x + 4 * s, y + 13.5 * s, 1.8 * s, 1.2 * s, fill=CAT)
    parts += polyline([(x + 5 * s, y + 7 * s), (x + 11 * s, y + 6 * s),
                       (x + 13 * s, y + 1 * s)], width=2.0 * s)
    parts += _kopf(hx, hy, r, s)
    return parts, (hx, hy, r)


def _walk(x, y, s):
    hx, hy, r = x + 9 * s, y - 5 * s, 6 * s
    parts = ellipse(x, y, 10 * s, 5 * s, fill=CAT)
    for sx, ex in ((-7, -9), (-3, -2), (3, 2), (7, 9)):
        parts += line((x + sx * s, y + 4 * s), (x + ex * s, y + 11 * s),
                      width=2.2 * s)
    parts += polyline([(x - 10 * s, y), (x - 14 * s, y - 5 * s),
                       (x - 13 * s, y - 9 * s)], width=2.0 * s)
    parts += _kopf(hx, hy, r, s * 0.92)
    return parts, (hx, hy, r)


def _run(x, y, s):
    hx, hy, r = x + 10 * s, y - 6 * s, 6 * s
    parts = ellipse(x, y, 10 * s, 5 * s, fill=CAT)
    for sx, ex, ey in ((-7, -12, 9), (-3, -1, 11), (3, 7, 10), (7, 12, 8)):
        parts += line((x + sx * s, y + 4 * s), (x + ex * s, y + ey * s),
                      width=2.2 * s)
    parts += polyline([(x - 10 * s, y), (x - 15 * s, y - 4 * s),
                       (x - 14 * s, y - 8 * s)], width=2.0 * s)
    parts += line((x - 16 * s, y - 2 * s), (x - 22 * s, y - 2 * s), width=1.4)
    parts += line((x - 18 * s, y + 5 * s), (x - 24 * s, y + 5 * s), width=1.4)
    parts += _kopf(hx, hy, r, s * 0.92)
    return parts, (hx, hy, r)


def _sniff(x, y, s):
    hx, hy, r = x + 9 * s, y + 1 * s, 5.5 * s
    parts = ellipse(x, y, 9 * s, 4.5 * s, fill=CAT)
    for sx in (-6, -2, 2, 6):
        parts += line((x + sx * s, y + 3.5 * s),
                      (x + sx * s, y + 10 * s), width=2.0 * s)
    parts += polyline([(x - 9 * s, y), (x - 13 * s, y - 4 * s),
                       (x - 12 * s, y - 8 * s)], width=2.0 * s)
    parts += _kopf(hx, hy, r, s * 0.92)
    # Schnurrhaare nach vorn
    parts += line((hx + 3 * s, hy + 1 * s), (hx + 7 * s, hy - 1 * s),
                  width=0.8 * s)
    parts += line((hx + 3 * s, hy + 2 * s), (hx + 7 * s, hy + 3 * s),
                  width=0.8 * s)
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


def _wave(x, y, s):
    parts, head = _sit(x, y, s)
    parts += line((x + 5 * s, y + 2 * s), (x + 10 * s, y - 12 * s),
                  width=2.4 * s)
    parts += circle(x + 11 * s, y - 13 * s, 1.8 * s, fill=CAT)
    parts += polyline(_arc(x + 15 * s, y - 12 * s, 3 * s, 4 * s, 120, 240, 10),
                      stroke=BLUE, width=1.2)
    return parts, head


def _push(x, y, s):
    hx, hy, r = x + 4 * s, y - 9 * s, 6.5 * s
    parts = ellipse(x, y, 6 * s, 9 * s, fill=CAT)
    parts += line((x + 4 * s, y - 4 * s), (x + 11 * s, y - 2 * s),
                  width=2.2 * s)
    parts += line((x + 4 * s, y), (x + 10 * s, y + 3 * s), width=2.2 * s)
    parts += line((x - 2 * s, y + 7 * s), (x - 10 * s, y + 12 * s),
                  width=2.2 * s)
    parts += line((x + 2 * s, y + 7 * s), (x - 6 * s, y + 13 * s),
                  width=2.2 * s)
    parts += polyline([(x - 5 * s, y + 4 * s), (x - 12 * s, y + 1 * s),
                       (x - 15 * s, y - 3 * s)], width=2.0 * s)
    parts += _kopf(hx, hy, r, s)
    return parts, (hx, hy, r)


_POSES = {
    "sit": _sit,
    "judge": _sit,  # gleiche Haltung, anderer Blick
    "reach": _sit,  # Arm kommt aus `target` dazu
    "lie": _lie,
    "hang": _hang,
    "ride": _ride,
    "walk": _walk,
    "run": _run,
    "sniff": _sniff,
    "peek": _peek,
    "sleep": _sleep,
    "point": _point,
    "hold": _hold,
    "wave": _wave,
    "push": _push,
}


# ------------------------------------------------------------- Kopf & Gesicht

def _face(head, pose, effect, s):
    hx, hy, _ = head
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
        er = 1.5 * s if effect == "surprise" else 1.2 * s
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

    if effect == "hearts":
        parts += polyline(_arc(hx, hy + 2.2 * s, 2.2 * s, 1.4 * s,
                               25, 155, 12), width=1.0 * s)
    return parts


# ---------------------------------------------------------- Accessoires ----

def _shades(x, y, s, head):
    hx, hy, _ = head
    ey = hy - 0.5 * s
    return compose(
        rect(hx - 5.2 * s, ey - 1.8 * s, 4.4 * s, 3.4 * s, 1.2 * s, fill=GLASS),
        rect(hx + 0.8 * s, ey - 1.8 * s, 4.4 * s, 3.4 * s, 1.2 * s, fill=GLASS),
        line((hx - 0.8 * s, ey), (hx + 0.8 * s, ey), width=1.2 * s),
        line((hx - 5.2 * s, ey), (hx - 7 * s, ey - 1 * s), width=1.0 * s),
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


def _scarf(x, y, s, head):
    hx, hy, _ = head
    return compose(
        rect(hx - 5 * s, hy + 4.6 * s, 10 * s, 2.2 * s, 1 * s, fill=RED),
        poly([(hx + 2 * s, hy + 6 * s), (hx + 5 * s, hy + 6 * s),
              (hx + 4 * s, hy + 10 * s), (hx + 1 * s, hy + 10 * s)],
             fill=RED),
    )


_ACCESSORIES = {
    "shades": _shades,
    "goggles": _goggles,
    "hat": _hat,
    "crown": _crown,
    "scarf": _scarf,
}


# --------------------------------------------------------------- Requisiten -

def _item_fish(x, y, s):
    return compose(
        ellipse(x + 11 * s, y + 4 * s, 4.5 * s, 2.8 * s, fill=FISH),
        poly([(x + 15 * s, y + 4 * s), (x + 18.5 * s, y + 1.5 * s),
              (x + 18.5 * s, y + 6.5 * s)], fill=FISH_D),
        circle(x + 13 * s, y + 3.2 * s, 0.5 * s, fill=INK, stroke=None),
    )


def _item_bread(x, y, s):
    return compose(
        ellipse(x + 11 * s, y + 3 * s, 5 * s, 3.4 * s, fill=BREAD),
        line((x + 8 * s, y + 1 * s), (x + 10 * s, y + 3 * s),
             width=0.9 * s),
        line((x + 11 * s, y + 1 * s), (x + 13 * s, y + 3 * s),
             width=0.9 * s),
    )


def _item_apple(x, y, s):
    return compose(
        circle(x + 11 * s, y + 3 * s, 3.8 * s, fill=RED),
        line((x + 11 * s, y - 1 * s), (x + 11 * s, y + 1 * s),
             width=1.2 * s),
        ellipse(x + 13 * s, y - 1 * s, 2 * s, 1 * s, rot=-25, fill=GREEN),
    )


def _item_orange(x, y, s):
    return compose(
        circle(x + 11 * s, y + 3 * s, 3.8 * s, fill=ORANGE),
        ellipse(x + 13 * s, y - 1 * s, 2 * s, 1 * s, rot=-25, fill=GREEN),
    )


def _item_cheese(x, y, s):
    return compose(
        poly([(x + 7 * s, y + 5 * s), (x + 15 * s, y + 5 * s),
              (x + 11 * s, y - 1 * s)], fill=CHEESE),
        circle(x + 10 * s, y + 3 * s, 0.8 * s, fill=CHEESE_D, stroke=None),
        circle(x + 12.5 * s, y + 2 * s, 0.6 * s, fill=CHEESE_D, stroke=None),
    )


def _item_ball(x, y, s):
    return compose(
        circle(x + 11 * s, y + 3 * s, 4 * s, fill=RED),
        star(x + 11 * s, y + 3 * s, 1.8 * s, 0.8 * s, fill=CREAM,
             stroke=None),
    )


def _item_key(x, y, s):
    return compose(
        circle(x + 8 * s, y + 1 * s, 2.2 * s, fill=None, width=1.4 * s),
        line((x + 9.5 * s, y + 2.5 * s), (x + 16 * s, y + 6 * s),
             width=1.4 * s),
        line((x + 13 * s, y + 4 * s), (x + 15 * s, y + 2 * s),
             width=1.2 * s),
    )


def _item_spoon(x, y, s):
    return compose(
        ellipse(x + 13 * s, y + 1 * s, 2.4 * s, 3.2 * s, fill=GREY_L),
        rect(x + 12 * s, y + 4 * s, 2 * s, 8 * s, 1 * s, fill=GREY_L),
    )


def _item_pencil(x, y, s):
    return compose(
        poly([(x + 6 * s, y + 7 * s), (x + 9 * s, y + 9 * s),
              (x + 16 * s, y - 4 * s), (x + 13 * s, y - 6 * s)],
             fill=YELLOW),
        poly([(x + 6 * s, y + 7 * s), (x + 9 * s, y + 9 * s),
              (x + 5 * s, y + 11 * s)], fill=WOOD_L),
    )


def _item_phone(x, y, s):
    return compose(
        rect(x + 8 * s, y - 3 * s, 6 * s, 11 * s, 1.5 * s, fill=BLUE),
        rect(x + 9.2 * s, y - 1.5 * s, 3.6 * s, 7 * s, 1 * s, fill=GLASS),
    )


def _item_mug(x, y, s):
    return compose(
        rect(x + 8 * s, y, 6 * s, 7 * s, 1.5 * s, fill=CREAM),
        polyline([(x + 14 * s, y + 2 * s), (x + 16 * s, y + 3 * s),
                  (x + 14 * s, y + 5 * s)], width=1.2 * s),
        polyline([(x + 10 * s, y - 2 * s), (x + 9 * s, y - 5 * s)],
                 stroke=GREY, width=1.0 * s),
        polyline([(x + 12 * s, y - 2 * s), (x + 11 * s, y - 5 * s)],
                 stroke=GREY, width=1.0 * s),
    )


def _item_heart(x, y, s):
    return _herz(x + 11 * s, y + 2 * s, 4.5 * s)


def _item_question(x, y, s):
    return _frage(x + 12 * s, y + 4 * s, 0.45 * s)


def _item_milk(x, y, s):
    return compose(
        poly([(x + 8 * s, y - 1 * s), (x + 12 * s, y - 4 * s),
              (x + 16 * s, y - 1 * s), (x + 16 * s, y + 7 * s),
              (x + 8 * s, y + 7 * s)], fill=CREAM),
        rect(x + 8 * s, y + 2 * s, 8 * s, 2 * s, 0, fill=BLUE),
    )


_ITEMS = {
    "fish": _item_fish,
    "bread": _item_bread,
    "apple": _item_apple,
    "orange": _item_orange,
    "cheese": _item_cheese,
    "ball": _item_ball,
    "key": _item_key,
    "spoon": _item_spoon,
    "pencil": _item_pencil,
    "phone": _item_phone,
    "mug": _item_mug,
    "heart": _item_heart,
    "question": _item_question,
    "milk": _item_milk,
}


# ---------------------------------------------------------------- Effekte --

def _arc(cx, cy, rx, ry, a0, a1, n=20):
    return geom.arc(cx, cy, rx, ry, a0, a1, n)


def _eff_zzz(x, y, s, head):
    hx, hy, r = head
    parts = []
    for i, size in enumerate((4, 6, 8)):
        bx = hx + (2 + i * 2.4) * s
        by = hy - (r + 3 + i * 4) * s * 0.7
        parts += polyline([(bx, by), (bx + size * s, by),
                           (bx, by + size * s),
                           (bx + size * s, by + size * s)],
                          stroke=GREY, width=1.4)
    return parts


def _eff_hearts(x, y, s, head):
    hx, hy, r = head
    return compose(
        _herz(hx + 7 * s, hy - r - 5 * s, 3.2 * s),
        _herz(hx + 13 * s, hy - r - 2 * s, 2.2 * s),
        _herz(hx + 3 * s, hy - r - 9 * s, 1.8 * s),
    )


def _eff_stink(x, y, s, head):
    hx, hy, _ = head
    parts = []
    for i in range(3):
        by = hy + (5 + i * 3) * s
        parts += polyline([(hx + 7 * s, by), (hx + 10 * s, by - 2 * s),
                           (hx + 13 * s, by)], stroke=GREEN, width=1.3)
    return parts


def _eff_sweat(x, y, s, head):
    hx, hy, _ = head
    return compose(
        polyline([(hx + 7 * s, hy - 4 * s), (hx + 8 * s, hy - 1 * s)],
                 stroke=BLUE, width=1.6),
        polyline([(hx + 9 * s, hy - 4 * s), (hx + 10 * s, hy - 1 * s)],
                 stroke=BLUE, width=1.4),
    )


def _eff_cold(x, y, s, head):
    hx, hy, _ = head
    return compose(
        polyline([(hx - 9 * s, hy - 6 * s), (hx - 12 * s, hy - 2 * s)],
                 stroke=BLUE, width=1.3),
        polyline([(hx - 11 * s, hy - 1 * s), (hx - 14 * s, hy + 3 * s)],
                 stroke=BLUE, width=1.3),
        polyline([(hx + 9 * s, hy - 6 * s), (hx + 12 * s, hy - 2 * s)],
                 stroke=BLUE, width=1.3),
    )


def _eff_milk(x, y, s, head):
    hx, hy, _ = head
    return compose(
        ellipse(hx, hy + 3.4 * s, 3.2 * s, 1.6 * s, fill=CREAM,
                stroke=None),
        circle(hx - 3 * s, hy + 4.6 * s, 0.8 * s, fill=CREAM, stroke=None),
        circle(hx + 3 * s, hy + 4.6 * s, 0.8 * s, fill=CREAM, stroke=None),
    )


def _eff_paint(color):
    def effect(x, y, s, head):
        hx, hy, _ = head
        return compose(
            ellipse(hx - 4 * s, hy - 5 * s, 3.2 * s, 2.4 * s, rot=-20,
                    fill=color, stroke=None),
            ellipse(x + 9 * s, y + 4 * s, 2.6 * s, 2.0 * s, rot=-15,
                    fill=color, stroke=None),
        )
    return effect


def _eff_surprise(x, y, s, head):
    hx, hy, _ = head
    return compose(
        line((hx - 10 * s, hy - 8 * s), (hx - 14 * s, hy - 13 * s),
             width=1.3),
        line((hx + 10 * s, hy - 8 * s), (hx + 14 * s, hy - 13 * s),
             width=1.3),
    )


def _eff_question(x, y, s, head):
    hx, hy, r = head
    return _frage(hx, hy - r - 6 * s, 0.42 * s)


def _eff_exclaim(x, y, s, head):
    hx, hy, r = head
    return compose(
        line((hx, hy - r - 10 * s), (hx, hy - r - 2 * s), width=2.4 * s),
        circle(hx, hy - r + 0.5 * s, 1.2 * s, fill=INK, stroke=None),
    )


_EFFECTS = {
    "zzz": _eff_zzz,
    "hearts": _eff_hearts,
    "stink": _eff_stink,
    "sweat": _eff_sweat,
    "cold": _eff_cold,
    "milk": _eff_milk,
    "paint_yellow": _eff_paint(YELLOW),
    "paint_blue": _eff_paint(BLUE),
    "paint_green": _eff_paint(GREEN),
    "surprise": _eff_surprise,
    "question": _eff_question,
    "exclaim": _eff_exclaim,
}


# -------------------------------------------------------------- Reichweite --

def _reach(x, y, s, target):
    """Pfote vom Körper zum Zielpunkt."""
    tx, ty = target
    side = 1 if tx >= x else -1
    start = (x + 4 * s * side, y + 2 * s)
    dx, dy = tx - start[0], ty - start[1]
    length = math.hypot(dx, dy)
    if length > 3:
        end = (start[0] + dx * (1 - 2 / length),
               start[1] + dy * (1 - 2 / length))
    else:
        end = (tx, ty)
    return (line(start, end, width=2.2 * s)
            + circle(end[0], end[1], 1.5 * s, fill=CAT))


# ------------------------------------------------------- Abwesenheitsspur --

def paw_prints(seed, x=84.0, y=82.0, s=0.9):
    """Drei Pfotenabdrücke, wenn die Katze gerade nicht da ist."""
    rnd = random.Random(f"paw:{seed}")
    parts = []
    for i in range(3):
        cx = x + i * 5 * s * rnd.uniform(0.8, 1.2)
        cy = y + i * 5 * s
        angle = rnd.uniform(-18, 18)
        step = ellipse(cx, cy, 3.2 * s, 2.6 * s, fill=GREY, stroke=None)
        step += circle(cx - 2.4 * s, cy - 3.0 * s, 1.1 * s,
                       fill=GREY, stroke=None)
        step += circle(cx, cy - 3.8 * s, 1.1 * s, fill=GREY, stroke=None)
        step += circle(cx + 2.4 * s, cy - 3.0 * s, 1.1 * s,
                       fill=GREY, stroke=None)
        for shape in step:
            shape.points = geom.rotate(shape.points, angle, (cx, cy))
        parts += step
    return parts
