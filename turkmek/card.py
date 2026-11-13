"""Karte: Papierhintergrund + Icon. Das ist das Bild, das verschickt wird.

Die Karte trägt bewusst keinen Text – die Vokabel steht in der Bildunterschrift
(Caption). So bleibt der Text kopierbar, durchsuchbar und im Lock-Screen
trotzdem sichtbar.

Der Rahmen ist absichtlich schief und die Karte darf einen Kaffeefleck oder
Tesafilm haben: Perfektion langweilt, ein leicht verrupftes Bild bleibt besser
hängen.
"""

from __future__ import annotations

import random

from PIL import Image, ImageDraw, ImageFilter

from .palette import PAPER

FRAME = "#e2d8c6"


def _grain(size, seed, strength=0.055):
    """Sehr feine Papierkörnung, geseedet, also reproduzierbar."""
    rnd = random.Random(f"grain:{seed}")
    small = max(96, size // 4)
    noise = Image.new("L", (small, small))
    noise.putdata([rnd.randint(0, 255) for _ in range(small * small)])
    noise = noise.resize((size, size), Image.BILINEAR)
    noise = noise.filter(ImageFilter.GaussianBlur(0.6))

    base = Image.new("RGB", (size, size), PAPER)
    tint = Image.merge("RGB", (noise, noise, noise))
    return Image.blend(base, tint, strength)


def _frame(card, size, seed):
    """Handgezeichneter Rahmen: leicht zittrige Linie statt Rechteck."""
    rnd = random.Random(f"frame:{seed}")
    draw = ImageDraw.Draw(card)
    inset = max(8, int(size * 0.03))
    corners = [(inset, inset), (size - inset, inset),
               (size - inset, size - inset), (inset, size - inset)]

    pts = []
    steps = 22
    for i in range(4):
        ax, ay = corners[i]
        bx, by = corners[(i + 1) % 4]
        for k in range(steps):
            t = k / steps
            pts.append((ax + (bx - ax) * t + rnd.uniform(-1.4, 1.4),
                        ay + (by - ay) * t + rnd.uniform(-1.4, 1.4)))
    pts.append(pts[0])

    draw.line(pts, fill=FRAME, width=max(1, int(size * 0.0025)),
              joint="curve")


def _wear(card, size, seed):
    """Ab und zu ein Tesafilm-Streifen oder ein Kaffeering."""
    rnd = random.Random(f"wear:{seed}")

    if rnd.random() < 0.4:
        w, h = int(size * 0.18), int(size * 0.06)
        tape = Image.new("RGBA", (w, h), (255, 255, 255, 70))
        tape = tape.rotate(rnd.uniform(-10, 10), expand=True,
                           resample=Image.BICUBIC)
        card.paste(tape, (int(size * 0.02), int(size * 0.015)), tape)

    if rnd.random() < 0.25:
        r = int(size * 0.055)
        ring = Image.new("RGBA", (r * 2 + 4, r * 2 + 4), (0, 0, 0, 0))
        draw = ImageDraw.Draw(ring)
        draw.ellipse([2, 2, r * 2, r * 2], outline=(150, 110, 70, 45),
                     width=max(1, int(size * 0.003)))
        x = int(size * (0.70 + rnd.random() * 0.12))
        y = int(size * (0.74 + rnd.random() * 0.12))
        card.paste(ring, (x, y), ring)


def make_card(icon, size=1024, seed="", icon_ratio=0.72, frame=True):
    """Setzt ein gerendertes Icon (RGBA) auf eine Papierkarte."""
    card = _grain(size, seed)
    rnd = random.Random(f"tilt:{seed}")

    angle = rnd.uniform(-2.2, 2.2)
    if angle:
        icon = icon.rotate(angle, resample=Image.BICUBIC, expand=False)

    target = int(size * icon_ratio)
    if icon.size != (target, target):
        icon = icon.resize((target, target), Image.LANCZOS)

    pos = (
        (size - target) // 2 + int(size * rnd.uniform(-0.018, 0.018)),
        (size - target) // 2 - int(size * 0.015)
        + int(size * rnd.uniform(-0.015, 0.015)),
    )
    card.paste(icon, pos, icon)

    if frame:
        _frame(card, size, seed)
        _wear(card, size, seed)

    return card
