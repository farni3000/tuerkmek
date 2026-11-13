"""Szene -> Raster (PNG) mit Pillow.

Kein cairo, kein Systemkram: 4x groß zeichnen und mit LANCZOS verkleinern
ergibt saubere Kanten. Alle Formen sind Polygone oder Polylinien, deshalb
reicht ImageDraw.
"""

from __future__ import annotations

from PIL import Image, ImageDraw


def render(shapes, size=512, supersample=4, background=None):
    """Rendert eine Szene. `background=None` ergibt Transparenz."""
    big = size * supersample
    scale = big / 100.0

    img = Image.new("RGBA", (big, big), background or (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for s in shapes:
        pts = [(x * scale, y * scale) for x, y in s.points]

        if s.fill and len(pts) >= 3:
            ox, oy = s.fill_offset
            fill_pts = [((x + ox) * scale, (y + oy) * scale)
                        for x, y in s.points]
            draw.polygon(fill_pts, fill=s.fill)

        if s.stroke and s.width:
            width = max(1, int(round(s.width * scale)))
            path = pts + [pts[0]] if s.closed else pts
            if len(path) >= 2:
                draw.line(path, fill=s.stroke, width=width, joint="curve")

            # Runde Ecken/Kappen: an jedem Knick einen Kreis setzen.
            caps = path if s.closed else [pts[0], pts[-1]]
            r = width / 2.0
            for px, py in caps:
                draw.ellipse([px - r, py - r, px + r, py + r], fill=s.stroke)

    return img.resize((size, size), Image.LANCZOS)
