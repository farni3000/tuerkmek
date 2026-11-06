"""Geometrie im 100x100-Raster, y zeigt nach unten.

Alle Zeichenbefehle geben Punktlisten zurück. Dadurch gibt es nur zwei
Primitive (geschlossenes Polygon, offene Linie) und damit genau zwei
Renderer: SVG für die Vektordatei, Pillow für das Raster.
"""

from __future__ import annotations

import math

Point = tuple

TAU = 2 * math.pi


def arc(cx: float, cy: float, rx: float, ry: float,
        a0: float, a1: float, n: int = 48) -> list:
    """Punkte auf einem Ellipsenbogen. Winkel in Grad."""
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def ellipse(cx: float, cy: float, rx: float, ry: float,
            rot: float = 0.0, n: int = 48) -> list:
    pts = arc(cx, cy, rx, ry, 0, 360, n)[:-1]
    if rot:
        pts = rotate(pts, rot, (cx, cy))
    return pts


def circle(cx: float, cy: float, r: float, n: int = 48) -> list:
    return ellipse(cx, cy, r, r, 0, n)


def rect(x: float, y: float, w: float, h: float,
         radius: float = 0.0, n: int = 6) -> list:
    """Rechteck, optional mit abgerundeten Ecken."""
    if radius <= 0:
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

    r = min(radius, w / 2, h / 2)
    pts = []
    pts += arc(x + w - r, y + r, r, r, -90, 0, n)
    pts += arc(x + w - r, y + h - r, r, r, 0, 90, n)
    pts += arc(x + r, y + h - r, r, r, 90, 180, n)
    pts += arc(x + r, y + r, r, r, 180, 270, n)
    return pts


def star(cx: float, cy: float, outer: float, inner: float,
         points: int = 5, rot: float = -90) -> list:
    pts = []
    step = 180.0 / points
    for i in range(points * 2):
        rr = outer if i % 2 == 0 else inner
        a = math.radians(rot + i * step)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def bezier(p0: Point, p1: Point, p2: Point, p3: Point, n: int = 28) -> list:
    """Kubische Bézierkurve, als Punktliste abgetastet."""
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def wave(x0: float, x1: float, y: float, amp: float, humps: int = 3,
         n: int = 40) -> list:
    """Sanfte Wellenlinie, z.B. für Wasser."""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + (x1 - x0) * t,
                    y + amp * math.sin(t * humps * TAU)))
    return pts


def _contiguous(pts: list, keep, n: int = None) -> list:
    """Der zusammenhängende Lauf von Punkten, der `keep` erfüllt.

    Die Punktliste ist ringförmig (Kreis), der Lauf darf also über den
    Anfang hinauslaufen.
    """
    n = n or len(pts)
    start = next((i for i in range(n) if keep(pts[i])), None)
    if start is None:
        return []

    while keep(pts[(start - 1) % n]):
        start = (start - 1) % n

    out = []
    i = start
    while keep(pts[i]) and len(out) < n:
        out.append(pts[i])
        i = (i + 1) % n
    return out


def crescent(c1: Point, r1: float, c2: Point, r2: float, n: int = 160) -> list:
    """Mondsichel: Kreis 1 minus Kreis 2, als geschlossene Punktliste."""
    (x1, y1), (x2, y2) = c1, c2
    d = math.hypot(x2 - x1, y2 - y1)

    if d >= r1 + r2 or d + min(r1, r2) <= max(r1, r2):
        return circle(x1, y1, r1, n)

    def outside(p):
        return math.hypot(p[0] - x2, p[1] - y2) > r2

    def inside(p):
        return math.hypot(p[0] - x1, p[1] - y1) < r1

    outer = _contiguous(circle(x1, y1, r1, n), outside)
    inner = _contiguous(circle(x2, y2, r2, n), inside)
    return outer + inner[::-1]


def rotate(pts: list, angle: float, origin: Point = (50.0, 50.0)) -> list:
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    ox, oy = origin
    return [(ox + (x - ox) * ca - (y - oy) * sa,
             oy + (x - ox) * sa + (y - oy) * ca) for x, y in pts]


def translate(pts: list, dx: float, dy: float) -> list:
    return [(x + dx, y + dy) for x, y in pts]


def centroid(pts: list) -> Point:
    if not pts:
        return (50.0, 50.0)
    return (sum(p[0] for p in pts) / len(pts),
            sum(p[1] for p in pts) / len(pts))
