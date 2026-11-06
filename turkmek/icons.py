"""Die Zeichenrezepte: ein Icon pro Wort.

Jedes Icon ist eine Funktion, die eine Szene (Liste von Formen) zurückgibt.
Koordinaten laufen von 0 bis 100, y zeigt nach unten. Gezeichnet wird von
hinten nach vorn, also erst Flächen, dann Details.

Die Unvollkommenheit kommt nicht von hier, sondern vom Jitter in
`scene.jitter_shapes` – dieselbe Zeichnung sieht dadurch handgemacht aus,
bleibt aber reproduzierbar.
"""

from __future__ import annotations

import math

from . import geometry as geom
from .palette import (
    BIRD, BIRD_D, BLUE, BLUE_L, BREAD, BROWN, CAT, CHEESE, CHEESE_D,
    CHEESE_L, COFFEE, CREAM, DOG, DOG_D, FISH, FISH_D, GLASS, GREEN,
    GREEN_D, GREY, GREY_L, HORSE, INK, MOON, ORANGE, PAPER, PINK, POTATO,
    RED, SNOW, TEA, WATER, WOOD, WOOD_L, YELLOW, YOLK,
)
from .scene import circle, compose, ellipse, line, poly, polyline, rect, star

# Wolkenumriss – von "bulut" und "yağmur" geteilt.
_CLOUD = [
    (22, 66), (21, 60), (24, 53), (30, 49), (33, 42), (40, 37),
    (48, 36), (55, 39), (60, 44), (67, 46), (72, 51), (73, 58),
    (70, 64), (66, 66),
]


# ---------------------------------------------------------------- Haushalt --

def kapi():
    return compose(
        rect(22, 10, 56, 80, 2, fill=WOOD),
        rect(30, 18, 40, 26, 1, fill=WOOD_L),
        rect(30, 54, 40, 26, 1, fill=WOOD_L),
        circle(68, 55, 2.6, fill=INK),
    )


def pencere():
    return compose(
        rect(20, 20, 60, 56, 1, fill=GLASS),
        line((50, 20), (50, 76)),
        line((20, 48), (80, 48)),
        rect(16, 78, 68, 6, 1, fill=WOOD),
    )


def masa():
    return compose(
        rect(10, 40, 80, 9, 1, fill=WOOD_L),
        rect(18, 49, 7, 37, 1, fill=WOOD),
        rect(75, 49, 7, 37, 1, fill=WOOD),
        line((25, 62), (75, 62), width=1.2),
    )


def sandalye():
    return compose(
        rect(24, 14, 9, 46, 1, fill=WOOD),
        rect(24, 58, 50, 9, 1, fill=WOOD_L),
        rect(28, 67, 6, 26, 1, fill=WOOD),
        rect(66, 67, 6, 26, 1, fill=WOOD),
        line((33, 30), (33, 52), width=1.2),
    )


def yatak():
    return compose(
        rect(10, 32, 10, 48, 2, fill=WOOD),
        rect(20, 52, 70, 18, 2, fill=CREAM),
        rect(22, 40, 20, 12, 2, fill=CREAM),
        rect(48, 46, 42, 24, 2, fill=RED),
        rect(16, 70, 5, 14, 1, fill=WOOD),
        rect(86, 70, 5, 14, 1, fill=WOOD),
    )


def kitap():
    return compose(
        rect(18, 24, 64, 52, 2, fill=BLUE),
        rect(62, 27, 7, 46, 0, fill=CREAM),
        rect(26, 34, 30, 4, 0, fill=CREAM),
        rect(26, 44, 36, 3, 0, fill=CREAM),
    )


def kalem():
    return compose(
        poly([(28, 72), (38, 82), (76, 38), (66, 28)], fill=YELLOW),
        poly([(28, 72), (38, 82), (20, 90)], fill=WOOD_L),
        circle(21, 89, 1.3, fill=INK),
        line((66, 28), (76, 38), width=1.2),
    )


def anahtar():
    return compose(
        circle(27, 30, 11, fill=None, width=3.4),
        line((35, 38), (74, 77), width=3.4),
        line((64, 67), (71, 60), width=3.0),
        line((72, 75), (79, 68), width=3.0),
    )


def saat():
    return compose(
        circle(50, 50, 32, fill=CREAM),
        line((50, 50), (50, 26), width=2.2),
        line((50, 50), (66, 58), width=2.2),
        circle(50, 50, 2.4, fill=INK),
        line((50, 21), (50, 25), width=1.0),
        line((50, 75), (50, 79), width=1.0),
        line((21, 50), (25, 50), width=1.0),
        line((75, 50), (79, 50), width=1.0),
    )


def bardak():
    return compose(
        poly([(34, 20), (66, 20), (61, 80), (39, 80)], fill=GLASS, stroke=None),
        poly([(36, 44), (64, 44), (60, 77), (40, 77)], fill=BLUE_L, stroke=None),
        poly([(34, 20), (66, 20), (61, 80), (39, 80)], fill=None),
    )


def tabak():
    return compose(
        circle(50, 52, 34, fill=CREAM),
        circle(50, 52, 23, fill=None, width=1.0),
    )


def kasik():
    return compose(
        ellipse(40, 28, 12, 16, fill=CREAM),
        rect(36, 42, 7, 46, 3.5, fill=CREAM),
    )


def catal():
    return compose(
        line((41, 10), (41, 26), width=3.0),
        line((50, 10), (50, 26), width=3.0),
        line((59, 10), (59, 26), width=3.0),
        rect(41, 23, 18, 8, 1, fill=CREAM),
        rect(47, 31, 6, 51, 3, fill=CREAM),
    )


def bicak():
    return compose(
        poly([(46, 64), (58, 64), (58, 24), (52, 10), (46, 24)], fill=GREY),
        rect(46, 63, 12, 25, 2, fill=BROWN),
        line((46, 64), (58, 64), width=1.4),
    )


# ------------------------------------------------------------------ Essen --

def ekmek():
    return compose(
        ellipse(50, 58, 32, 20, fill=BREAD),
        line((36, 52), (44, 44), width=1.4),
        line((48, 50), (56, 42), width=1.4),
        line((60, 52), (68, 44), width=1.4),
    )


def elma():
    return compose(
        circle(50, 58, 24, fill=RED),
        line((50, 35), (51, 21), width=2.4),
        ellipse(61, 26, 9, 4.5, rot=-25, fill=GREEN),
    )


def muz():
    pts = (
        [(26, 24)]
        + _bez((26, 24), (14, 56), (38, 86), (74, 72))
        + _bez((74, 72), (52, 72), (37, 52), (26, 24))[1:]
    )
    return compose(
        poly(pts, fill=YELLOW),
        rect(22, 18, 7, 8, 2, fill=BROWN),
    )


def portakal():
    return compose(
        circle(50, 58, 25, fill=ORANGE),
        circle(50, 33, 2.0, fill=INK),
        ellipse(61, 29, 8, 4, rot=-20, fill=GREEN),
    )


def domates():
    return compose(
        circle(50, 60, 23, fill=RED),
        star(50, 38, 12, 5.0, fill=GREEN),
        line((50, 39), (50, 30), width=2.2),
    )


def patates():
    return compose(
        ellipse(50, 58, 27, 20, rot=-12, fill=POTATO),
        circle(40, 54, 1.4, fill=BROWN),
        circle(58, 62, 1.4, fill=BROWN),
        circle(52, 50, 1.2, fill=BROWN),
    )


def peynir():
    return compose(
        poly([(18, 64), (82, 64), (82, 46), (18, 46)], fill=CHEESE),
        poly([(18, 46), (50, 33), (82, 46)], fill=CHEESE_L),
        circle(36, 55, 3.2, fill=CHEESE_D),
        circle(56, 57, 2.6, fill=CHEESE_D),
        circle(68, 53, 2.0, fill=CHEESE_D),
    )


def yumurta():
    return compose(
        ellipse(50, 56, 19, 26, fill=CREAM),
        circle(50, 62, 10, fill=YOLK),
    )


def sut():
    return compose(
        poly([(34, 32), (50, 18), (66, 32), (66, 82), (34, 82)], fill=CREAM),
        line((50, 18), (50, 32), width=1.2),
        rect(34, 44, 32, 10, 0, fill=BLUE),
    )


def su():
    pts = [(50, 14)] + _arc(50, 64, 21, 21, -30, 210, 60)
    return compose(poly(pts, fill=WATER))


def cay():
    return compose(
        poly([(37, 20), (63, 20), (58, 66), (42, 66)], fill=GLASS, stroke=None),
        poly([(38.5, 36), (61.5, 36), (57.2, 64), (42.8, 64)],
             fill=TEA, stroke=None),
        poly([(37, 20), (63, 20), (58, 66), (42, 66)], fill=None),
        ellipse(50, 72, 21, 4.5, fill=CREAM),
    )


def kahve():
    return compose(
        poly([(30, 44), (68, 44), (64, 68), (34, 68)], fill=CREAM),
        ellipse(49, 44, 19, 4.5, fill=COFFEE),
        _stroked_arc(68, 54, 8, 7, -80, 80),
        ellipse(49, 72, 24, 4.5, fill=CREAM),
        _stroked_bez((44, 34), (39, 27), (49, 23), (44, 15)),
        _stroked_bez((55, 34), (50, 27), (60, 23), (55, 15)),
    )


def seker():
    return compose(
        rect(24, 54, 19, 19, 1, fill=CREAM),
        rect(45, 46, 19, 19, 1, fill=CREAM),
        rect(36, 62, 19, 19, 1, fill=CREAM),
    )


def tuz():
    return compose(
        poly([(36, 44), (64, 44), (60, 82), (40, 82)], fill=CREAM),
        rect(37, 32, 26, 10, 2, fill=GREY),
        circle(45, 37, 1.4, fill=INK, stroke=None),
        circle(50, 37, 1.4, fill=INK, stroke=None),
        circle(55, 37, 1.4, fill=INK, stroke=None),
    )


# ------------------------------------------------------------------ Tiere --

def kedi():
    return compose(
        poly([(31, 42), (32, 20), (46, 32)], fill=CAT),
        poly([(69, 42), (68, 20), (54, 32)], fill=CAT),
        circle(50, 54, 20, fill=CAT),
        ellipse(43, 52, 2.2, 3.4, fill=INK, stroke=None),
        ellipse(57, 52, 2.2, 3.4, fill=INK, stroke=None),
        poly([(47.5, 59), (52.5, 59), (50, 62)], fill=PINK),
        line((50, 62), (50, 65), width=1.0),
        line((44, 64), (35, 62), width=0.9),
        line((44, 66), (35, 67), width=0.9),
        line((56, 64), (65, 62), width=0.9),
        line((56, 66), (65, 67), width=0.9),
    )


def kopek():
    return compose(
        ellipse(32, 36, 5, 10, rot=-22, fill=DOG_D),
        ellipse(68, 36, 5, 10, rot=22, fill=DOG_D),
        circle(50, 52, 18, fill=DOG),
        ellipse(50, 63, 11, 8, fill=CREAM),
        circle(50, 57, 2.6, fill=INK, stroke=None),
        circle(43, 48, 2.0, fill=INK, stroke=None),
        circle(57, 48, 2.0, fill=INK, stroke=None),
    )


def kus():
    return compose(
        poly([(28, 52), (13, 43), (15, 61)], fill=BIRD_D),
        ellipse(46, 54, 18, 14, rot=-8, fill=BIRD),
        circle(64, 40, 10, fill=BIRD),
        poly([(73, 39), (83, 42), (73, 45)], fill=ORANGE),
        ellipse(43, 52, 10, 6, rot=-15, fill=BIRD_D),
        circle(66, 37, 1.8, fill=INK, stroke=None),
    )


def balik():
    return compose(
        poly([(24, 52), (9, 39), (11, 65)], fill=FISH_D),
        ellipse(48, 52, 24, 15, fill=FISH),
        poly([(44, 42), (52, 36), (50, 48)], fill=FISH_D),
        circle(62, 48, 2.0, fill=INK, stroke=None),
    )


def at():
    return compose(
        polyline([(24, 50), (16, 58), (19, 71)], width=3.2),
        rect(33, 60, 5, 22, 1, fill=HORSE),
        rect(43, 62, 5, 20, 1, fill=HORSE),
        rect(55, 60, 5, 22, 1, fill=HORSE),
        rect(64, 62, 5, 20, 1, fill=HORSE),
        ellipse(45, 52, 22, 13, rot=-4, fill=HORSE),
        poly([(56, 48), (59, 28), (68, 27), (69, 50)], fill=HORSE),
        poly([(66, 30), (80, 26), (84, 32), (68, 38)], fill=HORSE),
        poly([(66, 28), (66, 21), (71, 27)], fill=HORSE),
        line((59, 30), (56, 40), width=3.0),
        circle(74, 31, 1.6, fill=INK, stroke=None),
    )


def inek():
    return compose(
        rect(32, 64, 4, 18, 1, fill=CREAM),
        rect(40, 66, 4, 16, 1, fill=CREAM),
        rect(56, 64, 4, 18, 1, fill=CREAM),
        rect(64, 66, 4, 16, 1, fill=CREAM),
        ellipse(46, 54, 24, 14, fill=CREAM),
        circle(40, 50, 5, fill=INK),
        circle(53, 57, 4, fill=INK),
        ellipse(74, 44, 9, 10, fill=CREAM),
        circle(77, 41, 1.8, fill=INK, stroke=None),
        ellipse(79, 50, 4, 3, fill=PINK),
        poly([(70, 35), (67, 29), (73, 32)], fill=GREY),
    )


# -------------------------------------------------------------- Natur ----

def agac():
    return compose(
        rect(46, 58, 8, 28, 2, fill=BROWN),
        circle(42, 44, 17, fill=GREEN),
        circle(58, 40, 15, fill=GREEN),
        circle(50, 31, 14, fill=GREEN),
    )


def cicek():
    parts = []
    for a in (0, 72, 144, 216, 288):
        rad = math.radians(a)
        parts += circle(50 + 13 * math.cos(rad), 44 + 13 * math.sin(rad),
                        9, fill=RED)
    parts += circle(50, 44, 7, fill=YELLOW)
    parts += line((50, 51), (50, 86), stroke=GREEN_D, width=2.6)
    parts += ellipse(59, 72, 9, 4.5, rot=-25, fill=GREEN)
    return parts


def gunes():
    parts = []
    parts += circle(50, 50, 19, fill=YELLOW)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        parts += line((50 + 25 * math.cos(rad), 50 + 25 * math.sin(rad)),
                      (50 + 35 * math.cos(rad), 50 + 35 * math.sin(rad)),
                      width=3.0)
    return parts


def ay():
    return compose(
        poly(geom.crescent((48, 50), 27, (60, 42), 24), fill=MOON),
    )


def yildiz():
    return compose(
        star(50, 52, 30, 13, fill=YELLOW),
    )


def yagmur():
    return compose(
        poly(geom.translate(_CLOUD, 0, -6), fill=GREY_L),
        line((38, 64), (34, 77), stroke=BLUE, width=2.6),
        line((50, 64), (46, 77), stroke=BLUE, width=2.6),
        line((62, 64), (58, 77), stroke=BLUE, width=2.6),
    )


def kar():
    parts = []
    arm = 29
    for a in (0, 60, 120):
        rad = math.radians(a)
        dx, dy = math.cos(rad), math.sin(rad)
        parts += line((50 - dx * arm, 50 - dy * arm),
                      (50 + dx * arm, 50 + dy * arm),
                      stroke=BLUE, width=2.4)
        for sign in (1, -1):
            base = a if sign > 0 else a + 180
            tx, ty = 50 + dx * arm * 0.72 * sign, 50 + dy * arm * 0.72 * sign
            for offset in (-40, 40):
                bang = math.radians(base + offset)
                parts += line((tx, ty),
                              (tx + math.cos(bang) * 9.5,
                               ty + math.sin(bang) * 9.5),
                              stroke=BLUE, width=2.0)
    parts += circle(50, 50, 2.0, fill=BLUE, stroke=None)
    return parts


def bulut():
    return compose(poly(_CLOUD, fill=CREAM))


# ------------------------------------------------------------ Gebäude ----

def ev():
    return compose(
        poly([(12, 47), (50, 17), (88, 47)], fill=RED),
        rect(22, 46, 56, 38, 1, fill=CREAM),
        rect(44, 62, 13, 22, 1, fill=WOOD),
        rect(30, 54, 11, 11, 1, fill=GLASS),
        line((35.5, 54), (35.5, 65), width=1.0),
        line((30, 59.5), (41, 59.5), width=1.0),
    )


def okul():
    return compose(
        poly([(9, 43), (50, 22), (91, 43)], fill=GREY),
        rect(16, 42, 68, 42, 1, fill=CREAM),
        rect(44, 64, 14, 20, 1, fill=WOOD),
        rect(24, 50, 12, 10, 1, fill=GLASS),
        rect(64, 50, 12, 10, 1, fill=GLASS),
        rect(24, 68, 12, 8, 1, fill=GLASS),
        rect(64, 68, 12, 8, 1, fill=GLASS),
    )


# ----------------------------------------------------------- Fahrzeuge ----

def araba():
    return compose(
        poly([(15, 58), (22, 46), (36, 46), (46, 36), (70, 36),
              (78, 46), (86, 48), (86, 60), (15, 60)], fill=RED),
        poly([(38, 45), (46, 38), (57, 38), (57, 45)], fill=GLASS),
        poly([(60, 38), (69, 38), (75, 45), (60, 45)], fill=GLASS),
        circle(32, 64, 7.5, fill=INK),
        circle(32, 64, 3.0, fill=CREAM, stroke=None),
        circle(70, 64, 7.5, fill=INK),
        circle(70, 64, 3.0, fill=CREAM, stroke=None),
    )


def bisiklet():
    return compose(
        circle(30, 66, 14, fill=None, width=2.6),
        circle(70, 66, 14, fill=None, width=2.6),
        line((48, 64), (44, 38), width=2.4),
        line((48, 64), (66, 38), width=2.4),
        line((44, 38), (66, 38), width=2.4),
        line((48, 64), (30, 66), width=2.4),
        line((44, 38), (30, 66), width=2.4),
        line((66, 38), (70, 66), width=2.4),
        rect(38, 34, 12, 3.5, 1, fill=INK, stroke=None),
        line((63, 34), (73, 34), width=2.4),
    )


def otobus():
    return compose(
        rect(14, 34, 72, 38, 3, fill=YELLOW),
        rect(20, 40, 17, 12, 1, fill=GLASS),
        rect(41, 40, 17, 12, 1, fill=GLASS),
        rect(62, 40, 17, 12, 1, fill=GLASS),
        line((50, 56), (50, 72), width=1.2),
        circle(30, 74, 6.5, fill=INK),
        circle(70, 74, 6.5, fill=INK),
    )


def ucak():
    return compose(
        poly([(44, 42), (12, 57), (12, 63), (44, 52)], fill=BLUE_L),
        poly([(56, 42), (88, 57), (88, 63), (56, 52)], fill=BLUE_L),
        poly([(44, 74), (32, 85), (68, 85), (56, 74)], fill=BLUE_L),
        ellipse(50, 48, 7, 30, fill=CREAM),
        circle(50, 22, 1.6, fill=INK, stroke=None),
    )


def tren():
    return compose(
        rect(24, 22, 8, 14, 1, fill=INK),
        rect(16, 36, 44, 30, 2, fill=BLUE),
        rect(58, 28, 26, 38, 2, fill=BLUE),
        rect(22, 42, 11, 11, 1, fill=GLASS),
        rect(62, 34, 17, 12, 1, fill=GLASS),
        circle(30, 70, 6.0, fill=INK),
        circle(46, 70, 6.0, fill=INK),
        circle(68, 70, 6.0, fill=INK),
        line((10, 80), (90, 80), width=1.6),
    )


def gemi():
    return compose(
        poly([(12, 62), (88, 62), (76, 80), (24, 80)], fill=RED),
        rect(30, 54, 40, 8, 1, fill=CREAM),
        rect(40, 40, 16, 14, 1, fill=CREAM),
        line((48, 40), (48, 15), width=2.0),
        poly([(48, 15), (67, 21), (48, 27)], fill=YELLOW),
        polyline([(16, 86), (30, 84), (44, 88)], stroke=BLUE, width=2.0),
        polyline([(56, 88), (70, 84), (84, 86)], stroke=BLUE, width=2.0),
    )


# ------------------------------------------------------------- Helfer ----

def _bez(p0, p1, p2, p3, n=26):
    from . import geometry as g
    return g.bezier(p0, p1, p2, p3, n)


def _arc(cx, cy, rx, ry, a0, a1, n=60):
    from . import geometry as g
    return g.arc(cx, cy, rx, ry, a0, a1, n)


def _stroked_arc(cx, cy, rx, ry, a0, a1):
    return polyline(_arc(cx, cy, rx, ry, a0, a1, 24), width=2.4)


def _stroked_bez(p0, p1, p2, p3):
    return polyline(_bez(p0, p1, p2, p3), width=1.6)


ICONS = {
    # Haushalt
    "kapi": kapi,
    "pencere": pencere,
    "masa": masa,
    "sandalye": sandalye,
    "yatak": yatak,
    "kitap": kitap,
    "kalem": kalem,
    "anahtar": anahtar,
    "saat": saat,
    "bardak": bardak,
    "tabak": tabak,
    "kasik": kasik,
    "catal": catal,
    "bicak": bicak,
    # Essen
    "ekmek": ekmek,
    "elma": elma,
    "muz": muz,
    "portakal": portakal,
    "domates": domates,
    "patates": patates,
    "peynir": peynir,
    "yumurta": yumurta,
    "sut": sut,
    "su": su,
    "cay": cay,
    "kahve": kahve,
    "seker": seker,
    "tuz": tuz,
    # Tiere
    "kedi": kedi,
    "kopek": kopek,
    "kus": kus,
    "balik": balik,
    "at": at,
    "inek": inek,
    # Natur
    "agac": agac,
    "cicek": cicek,
    "gunes": gunes,
    "ay": ay,
    "yildiz": yildiz,
    "yagmur": yagmur,
    "kar": kar,
    "bulut": bulut,
    # Gebäude
    "ev": ev,
    "okul": okul,
    # Fahrzeuge
    "araba": araba,
    "bisiklet": bisiklet,
    "otobus": otobus,
    "ucak": ucak,
    "tren": tren,
    "gemi": gemi,
}
