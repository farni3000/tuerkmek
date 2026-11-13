"""Welche Katze auf welcher Karte auftaucht.

Jedes Wort hat einen eigenen Auftritt. Die Position wird relativ zur
Bounding-Box des Icons aufgelöst, damit die Katze auf dem Tisch sitzt und
nicht irgendwo im Papier.

Zehn Karten bleiben bewusst katzenfrei – dort bleibt nur ein Pfotenabdruck.
So ist die Abwesenheit selbst ein kleiner Gag.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Scene:
    pose: str
    anchor: str
    tx: float = 0.5          # relative Position in der Icon-Box (0..1)
    ty: float = 0.5
    s: float = 0.55
    flip: bool = False
    layer: str = "front"     # "front" oder "back"
    accessory: Optional[str] = None
    item: Optional[str] = None
    effect: Optional[str] = None
    target: Optional[tuple] = None   # relative Zielkoordinate für "reach"


def _s(pose, anchor, tx=0.5, ty=0.5, s=0.55, **kw):
    return Scene(pose, anchor, tx, ty, s, **kw)


# Haushalt -----------------------------------------------------------------
SCENES = {
    "kapi": _s("sit", "beside_right", ty=0.72),
    "pencere": _s("peek", "inside", ty=0.45, s=0.5),
    "masa": _s("lie", "on_top", tx=0.42, ty=0.02, s=0.5),
    "sandalye": _s("lie", "on_top", tx=0.52, ty=0.55, s=0.48),
    "yatak": _s("sleep", "on_top", tx=0.45, ty=0.42, s=0.52),
    "kitap": _s("lie", "on_top", tx=0.45, ty=0.03, s=0.5),
    "kalem": _s("reach", "beside_right", ty=0.55, target=(0.55, 0.5)),
    "anahtar": _s("hold", "beside_right", ty=0.62, item="key"),
    "saat": _s("reach", "beside_right", ty=0.55, target=(0.5, 0.5)),
    "bardak": _s("reach", "beside_right", ty=0.55, target=(0.5, 0.55)),
    "tabak": _s("reach", "beside_left", ty=0.55, target=(0.5, 0.55)),
    "kasik": _s("hold", "beside_left", ty=0.6, item="spoon"),
    "catal": _s("judge", "beside_right", ty=0.7),
    "bicak": _s("peek", "behind_left", ty=0.7, s=0.5, layer="back"),

    # Essen -----------------------------------------------------------------
    "ekmek": _s("hold", "beside_right", ty=0.6, item="bread"),
    "elma": _s("hold", "beside_right", item="apple"),
    "muz": _s("reach", "beside_right", ty=0.55, target=(0.5, 0.35)),
    "portakal": _s("hold", "beside_left", item="orange"),
    "domates": _s("sniff", "beside_right", ty=0.75),
    "patates": _s("lie", "on_top", ty=0.05, s=0.45),
    "peynir": _s("hold", "beside_right", item="cheese"),
    "yumurta": _s("lie", "on_top", ty=0.05, s=0.45),
    "sut": _s("hold", "beside_right", ty=0.6, item="milk", effect="milk"),
    "cay": _s("sniff", "beside_left", ty=0.6),
    "kahve": _s("sit", "beside_right", effect="surprise"),

    # Tiere -----------------------------------------------------------------
    "kedi": _s("judge", "beside_right", ty=0.55),
    "kopek": _s("peek", "behind_left", ty=0.65, s=0.5, layer="back"),
    "kus": _s("lie", "beside_left", ty=0.75, s=0.5),
    "balik": _s("hold", "beside_right", item="fish"),
    "at": _s("ride", "on_top", tx=0.45, ty=0.35, s=0.48),
    "inek": _s("sit", "beside_right", accessory="shades"),

    # Natur -----------------------------------------------------------------
    "agac": _s("hang", "beside_left", ty=0.55, s=0.5),
    "cicek": _s("sniff", "beside_left", ty=0.7),

    # Gebäude ---------------------------------------------------------------
    "ev": _s("sit", "on_top", tx=0.55, ty=0.02, s=0.48),
    "okul": _s("peek", "inside", tx=0.35, ty=0.45, s=0.48),

    # Fahrzeuge -------------------------------------------------------------
    "araba": _s("peek", "inside", tx=0.5, ty=0.3, s=0.45),
    "bisiklet": _s("ride", "on_top", ty=0.48, s=0.42),
    "otobus": _s("peek", "inside", tx=0.34, ty=0.3, s=0.45),
    "ucak": _s("sit", "on_top", tx=0.5, ty=0.05, s=0.4,
               accessory="goggles"),
    "tren": _s("peek", "inside", tx=0.3, ty=0.48, s=0.45),
    "gemi": _s("sit", "on_top", tx=0.6, ty=0.58, s=0.48, accessory="hat"),

    # Verben ----------------------------------------------------------------
    "gitmek": _s("walk", "beside_right", ty=0.7, s=0.5),
    "gelmek": _s("walk", "beside_left", ty=0.7, s=0.5),
    "yemek": _s("reach", "beside_left", ty=0.6, target=(0.5, 0.6)),
    "icmek": _s("reach", "beside_right", target=(0.5, 0.5), effect="milk"),
    "uyumak": _s("sleep", "on_top", ty=0.42, s=0.5),
    "kosmak": _s("run", "beside_left", ty=0.7, s=0.5),
    "okumak": _s("lie", "on_top", ty=0.03, s=0.48),
    "yazmak": _s("sit", "on_top", tx=0.78, ty=0.05, s=0.45),
    "gormek": _s("peek", "beside_right", effect="surprise"),
    "duymak": _s("sit", "beside_right"),
    "sevmek": _s("hold", "beside_right", item="heart"),
    "konusmak": _s("peek", "inside", tx=0.78, ty=0.7, s=0.4),
    "almak": _s("reach", "beside_right", target=(0.7, 0.25)),
    "vermek": _s("wave", "beside_left", ty=0.6),
    "acmak": _s("peek", "inside", tx=0.45, ty=0.5, s=0.48),
    "kapatmak": _s("sit", "beside_right", ty=0.7),
    "oturmak": _s("sit", "beside_left", ty=0.82, s=0.4),
    "oynamak": _s("run", "beside_left", ty=0.7, s=0.5),
    "calismak": _s("lie", "on_top", tx=0.75, ty=0.72, s=0.42),
    "beklemek": _s("sit", "beside_right", ty=0.7),

    # Adjektive -------------------------------------------------------------
    "buyuk": _s("sit", "beside_right", ty=0.7, s=0.32),
    "kucuk": _s("sit", "beside_right", s=1.0),
    "guzel": _s("sit", "beside_right", effect="hearts"),
    "cirkin": _s("sit", "beside_right", effect="stink"),
    "sicak": _s("sit", "beside_right", effect="sweat"),
    "soguk": _s("sit", "beside_right", effect="cold"),
    "yeni": _s("peek", "beside_right", effect="surprise"),
    "eski": _s("judge", "beside_right"),
    "hizli": _s("run", "beside_left", ty=0.7),
    "yavas": _s("sleep", "on_top", ty=0.35, s=0.42),
    "iyi": _s("sit", "beside_right"),
    "kotu": _s("peek", "beside_left", effect="cold"),

    # Farben ----------------------------------------------------------------
    "kirmizi": _s("sit", "on_top", tx=0.4, ty=0.05, s=0.42),
    "mavi": _s("reach", "beside_right", target=(0.45, 0.4),
               effect="paint_blue"),
    "yesil": _s("peek", "behind_left", s=0.48, layer="back"),
    "sari": _s("sit", "beside_right", effect="paint_yellow"),
    "siyah": _s("peek", "inside", tx=0.42, ty=0.45, s=0.42),

    # Alltag ----------------------------------------------------------------
    "merhaba": _s("wave", "beside_right"),
    "tesekkurler": _s("hold", "beside_right", item="heart"),
    "lutfen": _s("peek", "beside_left", effect="surprise"),
    "evet": _s("point", "beside_right"),
    "hayir": _s("sit", "beside_right", flip=True),
    "bugun": _s("sit", "beside_left", ty=0.7),
    "yarin": _s("walk", "beside_right", ty=0.7),
    "dun": _s("walk", "beside_left", ty=0.7, flip=True),
    "simdi": _s("reach", "beside_right", target=(0.5, 0.5)),
    "belki": _s("sit", "beside_right", effect="question"),
}

# Diese Karten bleiben ohne Katze – dort liegt nur eine Spur.
NO_CAT = {
    "gunes", "ay", "yildiz", "yagmur", "kar", "bulut",
    "su", "tuz", "seker", "beyaz",
}


def for_word(word):
    """Scene für ein Wort oder None, wenn die Karte katzenfrei bleibt."""
    if word["id"] in NO_CAT:
        return None
    return SCENES[word["id"]]


def resolve(scene, bbox):
    """Rechnet Anker + relative Position in absolute Katzenkoordinaten um."""
    x0, y0, x1, y1 = bbox
    w = max(x1 - x0, 1e-6)
    h = max(y1 - y0, 1e-6)
    s = scene.s

    if scene.anchor == "beside_right":
        x = x1 + 9 * s
        y = y0 + h * scene.ty
    elif scene.anchor == "beside_left":
        x = x0 - 9 * s
        y = y0 + h * scene.ty
    elif scene.anchor == "on_top":
        x = x0 + w * scene.tx
        y = y0 + h * scene.ty - 13 * s
    elif scene.anchor == "inside":
        x = x0 + w * scene.tx
        y = y0 + h * scene.ty
    elif scene.anchor == "behind_left":
        x = x0 - 3 * s
        y = y0 + h * scene.ty
    elif scene.anchor == "behind_right":
        x = x1 + 3 * s
        y = y0 + h * scene.ty
    elif scene.anchor == "under":
        x = x0 + w * scene.tx
        y = y1 + 6 * s
    elif scene.anchor == "edge":
        x, y = 86.0, 88.0
    else:
        x = x0 + w * scene.tx
        y = y0 + h * scene.ty

    target = None
    if scene.target:
        target = (x0 + w * scene.target[0], y0 + h * scene.target[1])
    return x, y, s, target
