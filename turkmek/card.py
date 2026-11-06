"""Karte: Papierhintergrund + Icon. Das ist das Bild, das verschickt wird.

Die Karte trägt bewusst keinen Text – die Vokabel steht in der Bildunterschrift
(Caption). So bleibt der Text kopierbar, durchsuchbar und im Lock-Screen
trotzdem sichtbar.
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


def make_card(icon, size=1024, seed="", icon_ratio=0.72, frame=True):
    """Setzt ein gerendertes Icon (RGBA) auf eine Papierkarte."""
    card = _grain(size, seed)

    target = int(size * icon_ratio)
    if icon.size != (target, target):
        icon = icon.resize((target, target), Image.LANCZOS)

    pos = ((size - target) // 2, (size - target) // 2 - int(size * 0.015))
    card.paste(icon, pos, icon)

    if frame:
        draw = ImageDraw.Draw(card)
        inset = max(8, int(size * 0.03))
        draw.rounded_rectangle(
            [inset, inset, size - inset, size - inset],
            radius=int(size * 0.02),
            outline=FRAME,
            width=max(1, int(size * 0.0025)),
        )

    return card
