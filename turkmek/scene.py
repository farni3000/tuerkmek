"""Szene: eine Liste von Formen, die aus den Geometrie-Helfern entsteht.

Ein Icon ist eine flache Liste von `Shape`-Objekten. Die Reihenfolge ist die
Zeichenreihenfolge (hinten nach vorn).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from . import geometry as g
from .palette import INK

# Standard-Konturbreite im 100x100-Raster.
STROKE = 1.6


@dataclass
class Shape:
    points: list
    closed: bool = True
    fill: Optional[str] = None
    stroke: Optional[str] = INK
    width: float = STROKE
    jitter: bool = True


def poly(points, fill=None, stroke=INK, width=STROKE, jitter=True):
    return [Shape(list(points), closed=True, fill=fill, stroke=stroke,
                  width=width, jitter=jitter)]


def line(p0, p1, stroke=INK, width=STROKE, jitter=True):
    return [Shape([p0, p1], closed=False, fill=None, stroke=stroke,
                  width=width, jitter=jitter)]


def polyline(points, stroke=INK, width=STROKE, jitter=True):
    return [Shape(list(points), closed=False, fill=None, stroke=stroke,
                  width=width, jitter=jitter)]


def rect(x, y, w, h, radius=0.0, fill=None, stroke=INK, width=STROKE,
         jitter=True):
    return poly(g.rect(x, y, w, h, radius), fill=fill, stroke=stroke,
                width=width, jitter=jitter)


def circle(cx, cy, r, fill=None, stroke=INK, width=STROKE, jitter=True):
    return poly(g.circle(cx, cy, r), fill=fill, stroke=stroke,
                width=width, jitter=jitter)


def ellipse(cx, cy, rx, ry, rot=0.0, fill=None, stroke=INK, width=STROKE,
            jitter=True):
    return poly(g.ellipse(cx, cy, rx, ry, rot), fill=fill, stroke=stroke,
                width=width, jitter=jitter)


def star(cx, cy, outer, inner, points=5, rot=-90, fill=None, stroke=INK,
         width=STROKE, jitter=True):
    return poly(g.star(cx, cy, outer, inner, points, rot), fill=fill,
                stroke=stroke, width=width, jitter=jitter)


def compose(*parts):
    """Mehrere Icon-Teile zu einer Szene verketten."""
    out = []
    for part in parts:
        out.extend(part)
    return out


def jitter_shapes(shapes, seed, amount=0.012):
    """Macht aus geraden Linien 'handgezeichnete'.

    Verschiebt und dreht jede Form leicht. Der Seed ist pro Wort fest, damit
    ein Rebuild exakt dasselbe Bild ergibt.
    """
    rnd = random.Random(seed)
    out = []
    for shape in shapes:
        if not shape.jitter or amount <= 0:
            out.append(shape)
            continue

        cx, cy = g.centroid(shape.points)
        dx = rnd.uniform(-amount, amount) * 100
        dy = rnd.uniform(-amount, amount) * 100
        angle = rnd.uniform(-amount, amount) * 60

        pts = g.translate(shape.points, dx, dy)
        if angle:
            pts = g.rotate(pts, angle, (cx + dx, cy + dy))

        out.append(Shape(pts, closed=shape.closed, fill=shape.fill,
                         stroke=shape.stroke, width=shape.width,
                         jitter=shape.jitter))
    return out


def fit_shapes(shapes, size=80.0, center=(50.0, 50.0)):
    """Skaliert eine Szene so, dass sie die Fläche gleichmäßig füllt.

    Ohne das wirken kleine Motive (Uhr) auf der Karte verloren, große
    (Flugzeug) zu dominant. Die Strichstärke skaliert mit.
    """
    if not shapes:
        return shapes

    pad = max((s.width for s in shapes if s.width), default=0.0) / 2.0
    xs = [p[0] for s in shapes for p in s.points]
    ys = [p[1] for s in shapes for p in s.points]
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad

    w = max(x1 - x0, 1e-6)
    h = max(y1 - y0, 1e-6)
    k = size / max(w, h)

    tx = center[0] - ((x0 + x1) / 2) * k
    ty = center[1] - ((y0 + y1) / 2) * k

    return [
        Shape([(x * k + tx, y * k + ty) for x, y in s.points],
              closed=s.closed, fill=s.fill, stroke=s.stroke,
              width=s.width * k, jitter=s.jitter)
        for s in shapes
    ]
