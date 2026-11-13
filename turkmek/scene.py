"""Szene: eine Liste von Formen, die aus den Geometrie-Helfern entsteht.

Ein Icon ist eine flache Liste von `Shape`-Objekten. Die Reihenfolge ist die
Zeichenreihenfolge (hinten nach vorn).
"""

from __future__ import annotations

import math
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
    # Versatz der Füllung gegenüber der Kontur – sieht aus wie schlecht
    # gedruckt. Wird von Raster- und SVG-Renderer gleich behandelt.
    fill_offset: tuple = (0.0, 0.0)


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


def wobble_shapes(shapes, seed, amount=0.3, segments=4):
    """Verbiegt jede Kante leicht – Handzittern statt Lineal.

    Anders als `jitter_shapes`, das ganze Formen verschiebt, wandert hier
    jeder Zwischenpunkt ein Stück nach links oder rechts. Offene Linien
    schießen am Ende ein bisschen über, wie beim schnellen Zeichnen.
    Dicke Konturen zittern weniger als dünne – sonst wirkt die Linie pelzig.
    """
    rnd = random.Random(f"wobble:{seed}")
    out = []
    for shape in shapes:
        pts = list(shape.points)
        if not shape.jitter or len(pts) < 2 or amount <= 0:
            out.append(shape)
            continue

        local = amount * min(1.0, 1.8 / max(shape.width, 0.8))
        n = len(pts)
        edges = n if shape.closed else n - 1
        new = []
        for i in range(edges):
            p0 = pts[i]
            p1 = pts[(i + 1) % n]
            new.append(p0)
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            length = math.hypot(dx, dy)
            if length < 1e-6:
                continue
            nx, ny = -dy / length, dx / length
            for k in range(1, segments):
                t = k / segments
                off = rnd.uniform(-local, local)
                new.append((p0[0] + dx * t + nx * off,
                            p0[1] + dy * t + ny * off))

        if not shape.closed:
            new.append(pts[-1])
            new[0] = _overshoot(new[1], new[0], rnd.uniform(0.3, 1.1))
            new[-1] = _overshoot(new[-2], new[-1], rnd.uniform(0.3, 1.1))

        out.append(Shape(new, closed=shape.closed, fill=shape.fill,
                         stroke=shape.stroke, width=shape.width,
                         jitter=shape.jitter))
    return out


def bounds(shapes):
    """Bounding-Box einer Szene als (x0, y0, x1, y1)."""
    xs = [p[0] for s in shapes for p in s.points]
    ys = [p[1] for s in shapes for p in s.points]
    return min(xs), min(ys), max(xs), max(ys)


def mirror_shapes(shapes, cx):
    """Spiegelt eine Szene horizontal um `cx`."""
    out = []
    for s in shapes:
        pts = [(2 * cx - x, y) for x, y in s.points]
        out.append(Shape(pts, closed=s.closed, fill=s.fill,
                         stroke=s.stroke, width=s.width, jitter=s.jitter,
                         fill_offset=(-s.fill_offset[0], s.fill_offset[1])))
    return out


def _overshoot(inside, end, distance):
    dx, dy = end[0] - inside[0], end[1] - inside[1]
    length = math.hypot(dx, dy) or 1.0
    return (end[0] + dx / length * distance,
            end[1] + dy / length * distance)


def misregister_shapes(shapes, seed, amount=0.7):
    """Setzt Füllungen leicht neben die Kontur, wie ein schlechter Druck."""
    rnd = random.Random(f"print:{seed}")
    out = []
    for shape in shapes:
        if not shape.fill or not shape.closed or amount <= 0:
            out.append(shape)
            continue
        dx = rnd.uniform(-amount, amount)
        dy = rnd.uniform(-amount, amount)
        out.append(Shape(shape.points, closed=shape.closed, fill=shape.fill,
                         stroke=shape.stroke, width=shape.width,
                         jitter=shape.jitter, fill_offset=(dx, dy)))
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
              width=s.width * k, jitter=s.jitter,
              fill_offset=(s.fill_offset[0] * k, s.fill_offset[1] * k))
        for s in shapes
    ]
