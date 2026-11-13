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


# -------------------------------------------------------------- Verben ----

def gitmek():
    return compose(
        _figur("walk", x=38, y=50, shirt=BLUE),
        _arrow(62, 50, 86, 50),
    )


def gelmek():
    return compose(
        _arrow(88, 52, 64, 52),
        _figur("walk", x=54, y=52, shirt=GREEN),
        line((20, 72), (28, 72), width=1.6),
        line((24, 62), (24, 82), width=1.6),
    )


def yemek():
    parts = circle(44, 66, 24, fill=CREAM)
    parts += circle(44, 66, 15, fill=None, width=1.2)
    parts += line((74, 42), (74, 58), width=2.2)
    parts += line((79, 42), (79, 58), width=2.2)
    parts += line((84, 42), (84, 58), width=2.2)
    parts += rect(74, 56, 10, 5, 2, fill=GREY)
    parts += rect(76, 60, 5, 22, 2.5, fill=GREY)
    parts += poly([(16, 42), (22, 46), (18, 64), (14, 60)], fill=GREY)
    parts += rect(15, 63, 4, 19, 2, fill=BROWN)
    parts += polyline(geom.wave(34, 50, 28, 2.4, 1), stroke=GREY, width=1.5)
    parts += polyline(geom.wave(40, 56, 34, 2.4, 1), stroke=GREY, width=1.5)
    return parts


def icmek():
    return compose(
        poly([(38, 30), (62, 30), (58, 80), (42, 80)], fill=GLASS, stroke=None),
        poly([(40.5, 48), (59.5, 48), (56.5, 77), (43.5, 77)],
             fill=WATER, stroke=None),
        poly([(38, 30), (62, 30), (58, 80), (42, 80)], fill=None),
        line((54, 18), (47, 58), stroke=RED, width=3.0),
        ellipse(50, 80, 10, 2.5, fill=BLUE_L),
    )


def uyumak():
    return compose(
        rect(10, 54, 80, 9, 3, fill=WOOD),
        rect(14, 38, 7, 20, 2, fill=WOOD),
        rect(18, 44, 30, 12, 4, fill=CREAM),
        circle(34, 44, 7, fill=CREAM),
        line((31, 44), (36, 44), width=1.2),
        rect(28, 50, 56, 14, 3, fill=BLUE),
        _zzz(64, 34),
    )


def kosmak():
    return compose(
        _figur("run", x=52, y=52, shirt=RED),
        line((16, 36), (27, 36), width=1.4),
        line((10, 48), (24, 48), width=1.4),
        line((16, 60), (27, 60), width=1.4),
    )


def okumak():
    return compose(
        poly([(12, 32), (48, 38), (48, 78), (12, 72)], fill=CREAM),
        poly([(88, 32), (52, 38), (52, 78), (88, 72)], fill=CREAM),
        line((48, 38), (48, 78), width=1.6),
        line((20, 46), (42, 50), width=1.1),
        line((20, 54), (42, 58), width=1.1),
        line((20, 62), (36, 65), width=1.1),
        line((58, 50), (80, 46), width=1.1),
        line((58, 58), (80, 54), width=1.1),
        line((58, 66), (74, 63), width=1.1),
    )


def yazmak():
    return compose(
        rect(16, 20, 60, 62, 3, fill=CREAM),
        line((24, 32), (68, 32), width=1.0),
        line((24, 42), (60, 42), width=1.0),
        line((24, 52), (54, 52), width=1.0),
        polyline([(24, 68), (32, 62), (40, 70), (48, 62), (56, 70)],
                 stroke=BLUE, width=1.8),
        poly([(64, 70), (72, 78), (86, 44), (78, 38)], fill=YELLOW),
        poly([(64, 70), (72, 78), (58, 84)], fill=WOOD_L),
        circle(59, 84, 1.2, fill=INK, stroke=None),
    )


def gormek():
    upper = _bez((14, 50), (32, 24), (68, 24), (86, 50))
    lower = _bez((86, 50), (68, 76), (32, 76), (14, 50))
    return compose(
        poly(upper + lower, fill=CREAM),
        circle(50, 50, 14, fill=BLUE_L),
        circle(54, 52, 7, fill=INK, stroke=None),
        circle(50, 48, 2.4, fill=CREAM, stroke=None),
        line((28, 30), (22, 22), width=1.6),
        line((50, 25), (50, 16), width=1.6),
        line((72, 30), (78, 22), width=1.6),
    )


def duymak():
    ear = [(44, 84), (34, 76), (28, 56), (30, 38), (42, 22),
           (58, 20), (70, 32), (72, 48), (64, 60), (56, 66),
           (54, 76), (54, 84)]
    return compose(
        poly(ear, fill=CREAM),
        polyline(_bez((46, 54), (38, 42), (46, 32), (56, 34)),
                 stroke=GREY, width=1.6),
        polyline(_arc(76, 50, 7, 9, -55, 55, 20), stroke=BLUE, width=2.0),
        polyline(_arc(76, 50, 12, 15, -55, 55, 20), stroke=BLUE, width=1.8),
        polyline(_arc(76, 50, 17, 21, -55, 55, 20), stroke=BLUE, width=1.6),
    )


def sevmek():
    return compose(
        _herz(46, 54, 30),
        _sternchen(76, 26),
        _sternchen(20, 30),
        _sternchen(80, 68),
    )


def konusmak():
    return compose(
        _sprechblase(8, 18, 42, 28, fill=CREAM),
        line((16, 28), (40, 28), width=1.2),
        line((16, 36), (34, 36), width=1.2),
        _sprechblase(50, 52, 42, 28, fill=BLUE_L),
        line((58, 62), (82, 62), width=1.2),
        line((58, 70), (74, 70), width=1.2),
    )


def almak():
    return compose(
        _hand(46, 58),
        circle(76, 28, 9, fill=YELLOW),
        star(76, 28, 4.0, 1.8, fill=YELLOW),
        _arrow(74, 40, 60, 54),
    )


def vermek():
    return compose(
        _hand(38, 60, flip=True),
        circle(78, 42, 9, fill=YELLOW),
        _arrow(52, 54, 68, 46),
    )


def acmak():
    return compose(
        rect(22, 16, 50, 70, 2, fill=WOOD),
        poly([(32, 26), (60, 22), (60, 80), (32, 76)], fill=WOOD_L),
        circle(54, 54, 2.2, fill=INK, stroke=None),
        line((66, 50), (88, 50), width=2.4),
        line((88, 50), (82, 44), width=2.4),
        line((88, 50), (82, 56), width=2.4),
        line((24, 30), (14, 26), width=1.2),
        line((24, 50), (12, 50), width=1.2),
        line((24, 70), (14, 74), width=1.2),
    )


def kapatmak():
    return compose(
        rect(28, 14, 44, 72, 2, fill=WOOD),
        rect(34, 22, 32, 22, 1, fill=WOOD_L),
        rect(34, 52, 32, 26, 1, fill=WOOD_L),
        circle(64, 50, 2.4, fill=INK, stroke=None),
        rect(42, 64, 16, 14, 4, fill=GREY),
        polyline([(46, 64), (46, 59), (54, 59), (54, 64)], width=2.0),
        circle(50, 70, 1.6, fill=INK, stroke=None),
    )


def oturmak():
    return compose(
        rect(30, 24, 8, 34, 2, fill=WOOD),
        rect(30, 52, 34, 7, 2, fill=WOOD_L),
        rect(32, 59, 5, 24, 1, fill=WOOD),
        rect(58, 59, 5, 24, 1, fill=WOOD),
        _figur("sit", x=48, y=42, shirt=GREEN),
    )


def oynamak():
    return compose(
        circle(40, 60, 18, fill=RED),
        star(40, 60, 7, 3, fill=CREAM, stroke=None),
        _figur("run", x=74, y=54, s=0.85, shirt=BLUE),
        line((16, 44), (26, 44), width=1.4),
        line((12, 56), (24, 56), width=1.4),
    )


def calismak():
    return compose(
        _figur("sit", x=38, y=40, s=0.9, shirt=BLUE),
        rect(14, 58, 72, 8, 2, fill=WOOD_L),
        rect(18, 66, 6, 20, 1, fill=WOOD),
        rect(76, 66, 6, 20, 1, fill=WOOD),
        rect(56, 34, 28, 20, 2, fill=INK),
        rect(59, 37, 22, 14, 1, fill=GLASS),
        polyline([(46, 48), (56, 50)], width=2.0),
    )


def beklemek():
    return compose(
        _figur("stand", x=38, y=50, shirt=GREY),
        circle(76, 36, 15, fill=CREAM),
        line((76, 36), (76, 26), width=2.0),
        line((76, 36), (84, 40), width=2.0),
        circle(76, 36, 2.0, fill=INK, stroke=None),
        circle(60, 78, 2.0, fill=GREY, stroke=None),
        circle(66, 78, 2.0, fill=GREY, stroke=None),
        circle(72, 78, 2.0, fill=GREY, stroke=None),
    )


# ----------------------------------------------------------- Adjektive ----

def buyuk():
    return compose(
        circle(34, 56, 29, fill=RED),
        ellipse(30, 50, 8, 5, rot=-25, fill=CREAM, stroke=None),
        _figur("stand", x=82, y=64, s=0.5, shirt=BLUE),
    )


def kucuk():
    return compose(
        circle(24, 74, 5.5, fill=RED),
        _figur("stand", x=58, y=50, shirt=BLUE),
    )


def guzel():
    return compose(
        _gesicht(46, 52, 27, "happy"),
        _sternchen(76, 26),
        _sternchen(20, 70),
        _sternchen(78, 72),
    )


def cirkin():
    return compose(
        _gesicht(46, 52, 27, "sick"),
        circle(34, 40, 2.0, fill=GREEN_D, stroke=None),
        circle(60, 36, 1.6, fill=GREEN_D, stroke=None),
        polyline(geom.wave(12, 38, 16, 3, 1), stroke=GREY, width=1.4),
        polyline(geom.wave(58, 86, 14, 3, 1), stroke=GREY, width=1.4),
        _fliege(76, 62),
        _fliege(18, 60),
    )


def sicak():
    parts = _thermometer(28, 0.9, RED)
    parts += circle(70, 34, 11, fill=YELLOW)
    for a in range(0, 360, 60):
        rad = math.radians(a)
        parts += line((70 + 15 * math.cos(rad), 34 + 15 * math.sin(rad)),
                      (70 + 21 * math.cos(rad), 34 + 21 * math.sin(rad)),
                      width=2.0)
    parts += polyline([(84, 64), (80, 74)], stroke=BLUE, width=1.8)
    parts += polyline([(90, 58), (87, 66)], stroke=BLUE, width=1.8)
    return parts


def soguk():
    return compose(
        _thermometer(30, 0.9, BLUE),
        _schneeflocke(70, 40, 15),
        line((20, 82), (30, 80), width=1.6),
        line((34, 86), (44, 84), width=1.6),
    )


def yeni():
    return compose(
        rect(28, 16, 44, 68, 4, fill=BLUE),
        rect(33, 24, 34, 46, 2, fill=GLASS),
        circle(50, 78, 2.4, fill=CREAM, stroke=None),
        _sternchen(18, 28),
        _sternchen(82, 24),
        _sternchen(78, 76),
    )


def eski():
    return compose(
        poly([(30, 20), (70, 16), (74, 80), (32, 82)], fill=GREY_L),
        polyline([(42, 24), (46, 36), (40, 46), (44, 56)],
                 stroke=INK, width=1.6),
        polyline([(60, 62), (64, 70), (58, 76)], stroke=INK, width=1.6),
        rect(54, 36, 12, 10, 1, fill=WOOD_L),
        circle(38, 70, 1.6, fill=BROWN, stroke=None),
        circle(66, 28, 1.4, fill=BROWN, stroke=None),
        polyline([(66, 72), (74, 78), (82, 72)], stroke=GREY, width=1.2),
    )


def hizli():
    return compose(
        ellipse(44, 54, 20, 13, fill=CREAM),
        circle(64, 40, 10, fill=CREAM),
        ellipse(70, 24, 4, 12, rot=22, fill=CREAM),
        ellipse(60, 23, 4, 11, rot=-8, fill=CREAM),
        line((30, 62), (22, 70), width=2.0),
        line((46, 66), (40, 74), width=2.0),
        circle(68, 38, 1.6, fill=INK, stroke=None),
        line((16, 44), (28, 44), width=1.4),
        line((10, 54), (25, 54), width=1.4),
        line((16, 64), (28, 64), width=1.4),
    )


def yavas():
    return compose(
        polyline([(14, 78), (30, 74), (48, 78), (66, 74), (86, 78)],
                 stroke=BLUE_L, width=2.0),
        ellipse(48, 64, 26, 11, rot=-6, fill=CREAM),
        circle(58, 56, 16, fill=CHEESE),
        polyline(_arc(58, 56, 11, 11, 0, 300, 24), stroke=BROWN, width=1.6),
        polyline(_arc(58, 56, 6, 6, 60, 340, 18), stroke=BROWN, width=1.4),
        line((38, 58), (32, 42), width=2.0),
        line((46, 57), (44, 40), width=2.0),
        circle(32, 40, 3.0, fill=CREAM),
        circle(44, 38, 3.0, fill=CREAM),
        circle(33, 40, 1.2, fill=INK, stroke=None),
        circle(45, 38, 1.2, fill=INK, stroke=None),
    )


def iyi():
    return compose(
        _gesicht(44, 52, 28, "happy"),
        polyline([(70, 24), (76, 32), (88, 16)], stroke=GREEN, width=4.0),
    )


def kotu():
    return compose(
        poly(geom.translate(_CLOUD, -1, -32), fill=GREY_L),
        line((38, 40), (34, 52), stroke=BLUE, width=2.2),
        line((50, 40), (46, 52), stroke=BLUE, width=2.2),
        line((62, 40), (58, 52), stroke=BLUE, width=2.2),
        _gesicht(48, 70, 15, "sad"),
        polyline([(74, 62), (82, 70)], stroke=RED, width=3.0),
        polyline([(82, 62), (74, 70)], stroke=RED, width=3.0),
    )


# -------------------------------------------------------------- Farben ----

def kirmizi():
    return _farbe(RED)


def mavi():
    return _farbe(BLUE)


def yesil():
    return _farbe(GREEN)


def sari():
    return _farbe(YELLOW)


def siyah():
    return _farbe(INK, outline=INK)


def beyaz():
    return _farbe(CREAM, outline=GREY)


# --------------------------------------------------------------- Alltag ---

def merhaba():
    return compose(
        _sprechblase(10, 14, 52, 30, fill=CREAM),
        line((20, 24), (52, 24), width=1.4),
        line((20, 32), (44, 32), width=1.4),
        _winkhand(74, 62, s=0.9),
    )


def tesekkurler():
    return compose(
        _sprechblase(14, 14, 58, 40, fill=CREAM),
        _herz(43, 36, 17),
        _sternchen(76, 24, 5),
    )


def lutfen():
    return compose(
        _hand(36, 64, s=0.9),
        _hand(64, 64, s=0.9, flip=True),
        _herz(50, 28, 11),
    )


def evet():
    return compose(
        _sprechblase(12, 18, 56, 40, fill=CREAM),
        polyline([(30, 40), (42, 50), (60, 26)], stroke=GREEN, width=4.0),
    )


def hayir():
    return compose(
        _sprechblase(12, 18, 56, 40, fill=CREAM),
        polyline([(32, 28), (52, 48)], stroke=RED, width=4.0),
        polyline([(52, 28), (32, 48)], stroke=RED, width=4.0),
    )


def bugun():
    parts = _kalender(16, 22, 68, 62)
    parts += circle(50, 58, 12, fill=YELLOW)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        parts += line((50 + 16 * math.cos(rad), 58 + 16 * math.sin(rad)),
                      (50 + 21 * math.cos(rad), 58 + 21 * math.sin(rad)),
                      width=1.8)
    return parts


def yarin():
    return compose(
        _kalender(10, 24, 56, 56),
        _arrow(72, 54, 90, 54),
        circle(82, 26, 8, fill=YELLOW),
    )


def dun():
    return compose(
        _kalender(32, 24, 56, 56),
        _arrow(24, 54, 6, 54),
        poly(geom.crescent((18, 24), 9, (23, 19), 8), fill=MOON),
    )


def simdi():
    return compose(
        circle(46, 52, 30, fill=CREAM),
        line((46, 52), (46, 30), width=3.0),
        line((46, 52), (64, 58), width=2.4),
        circle(46, 52, 2.6, fill=RED, stroke=None),
        line((22, 76), (16, 84), width=2.0),
        line((46, 82), (46, 92), width=2.0),
        line((70, 76), (76, 84), width=2.0),
        line((78, 52), (88, 52), width=2.0),
    )


def belki():
    parts = poly(geom.translate(_CLOUD, 2, -8), fill=CREAM)
    parts += _frage(48, 44, 0.8)
    parts += circle(26, 72, 4.5, fill=CREAM)
    parts += circle(20, 82, 2.6, fill=CREAM)
    return parts


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


# --------------------------------------------------- Figuren und Requisiten --

_POSES = {
    "stand": {
        "arms": [[(0, -9), (-9, 3)], [(0, -9), (9, 3)]],
        "legs": [[(0, 4), (-6, 21)], [(0, 4), (6, 21)]],
    },
    "walk": {
        "arms": [[(0, -9), (-9, -2)], [(0, -9), (9, 5)]],
        "legs": [[(0, 4), (-9, 22)], [(0, 4), (8, 20)]],
    },
    "run": {
        "arms": [[(0, -9), (-11, -14)], [(0, -9), (11, -1)]],
        "legs": [[(0, 4), (-12, 16)], [(0, 4), (13, 9)]],
    },
    "sit": {
        "arms": [[(0, -9), (-9, -2)], [(0, -9), (9, -2)]],
        "legs": [[(0, 4), (-11, 13), (-11, 24)],
                 [(0, 4), (11, 13), (11, 24)]],
    },
}


def _figur(pose="stand", x=50, y=52, s=1.0, shirt=BLUE):
    """Strichmännchen für die Verben. Kopf, Rumpf, Arme, Beine."""
    spec = _POSES[pose]
    parts = circle(x, y - 20 * s, 7 * s, fill=CREAM)
    parts += line((x, y - 13 * s), (x, y + 4 * s),
                  stroke=shirt, width=3.4 * s)
    for seg in spec["arms"] + spec["legs"]:
        pts = [(x + dx * s, y + dy * s) for dx, dy in seg]
        parts += polyline(pts, width=2.4 * s)
    return parts


def _zzz(x, y, s=1.0):
    parts = []
    for i, size in enumerate((6, 9, 12)):
        bx, by = x + i * 4 * s, y - i * 9 * s
        parts += polyline([(bx, by), (bx + size * s, by),
                           (bx, by + size * s), (bx + size * s, by + size * s)],
                          stroke=GREY, width=1.8)
    return parts


def _arrow(x0, y0, x1, y1, stroke=INK, width=2.6, head=7.0):
    a = math.atan2(y1 - y0, x1 - x0)
    parts = line((x0, y0), (x1, y1), stroke=stroke, width=width)
    for sign in (1, -1):
        ang = a + math.pi + sign * 0.5
        parts += line((x1, y1), (x1 + head * math.cos(ang),
                                y1 + head * math.sin(ang)),
                      stroke=stroke, width=width)
    return parts


def _sternchen(cx, cy, r=6.0, fill=YELLOW):
    return star(cx, cy, r, r * 0.34, 4, fill=fill, stroke=None)


def _herz(cx, cy, s=24.0, fill=RED):
    left = _arc(cx - 0.42 * s, cy - 0.28 * s, 0.42 * s, 0.42 * s,
                180, 360, 18)
    right = _arc(cx + 0.42 * s, cy - 0.28 * s, 0.42 * s, 0.42 * s,
                 180, 360, 18)
    return poly(left + right + [(cx, cy + 0.82 * s)], fill=fill)


def _gesicht(cx, cy, r, mood="happy"):
    parts = circle(cx, cy, r, fill=CREAM)
    parts += circle(cx - r * 0.35, cy - r * 0.22, r * 0.1,
                    fill=INK, stroke=None)
    parts += circle(cx + r * 0.35, cy - r * 0.22, r * 0.1,
                    fill=INK, stroke=None)
    if mood == "happy":
        parts += polyline(_arc(cx, cy + r * 0.08, r * 0.5, r * 0.38,
                               25, 155, 20), width=2.2)
        parts += circle(cx - r * 0.58, cy + r * 0.16, r * 0.09,
                        fill=PINK, stroke=None)
        parts += circle(cx + r * 0.58, cy + r * 0.16, r * 0.09,
                        fill=PINK, stroke=None)
    elif mood == "sad":
        parts += polyline(_arc(cx, cy + r * 0.6, r * 0.5, r * 0.38,
                               205, 335, 20), width=2.2)
    else:  # sick
        parts += polyline([(cx - r * 0.32, cy + r * 0.42),
                           (cx + r * 0.32, cy + r * 0.42)], width=2.2)
        parts += ellipse(cx + r * 0.12, cy + r * 0.52, r * 0.16, r * 0.22,
                         fill=PINK, stroke=None)
        parts += line((cx - r * 0.5, cy - r * 0.48),
                      (cx - r * 0.2, cy - r * 0.36), width=2.0)
        parts += line((cx + r * 0.2, cy - r * 0.36),
                      (cx + r * 0.5, cy - r * 0.48), width=2.0)
    return parts


def _fliege(x, y, s=1.0):
    return compose(
        ellipse(x, y, 3.0 * s, 2.0 * s, fill=INK, stroke=None),
        polyline([(x - 1, y - 1), (x - 5 * s, y - 6 * s)], width=1.2),
        polyline([(x + 1, y - 1), (x + 5 * s, y - 6 * s)], width=1.2),
    )


def _hand(x, y, s=1.0, flip=False, fill=CREAM):
    k = -1.0 if flip else 1.0
    parts = []
    for i in range(4):
        fx = x + (-6.5 + i * 4.3) * s
        parts += rect(fx, y - 14 * s, 3.2 * s, 12 * s, 1.6 * s, fill=fill)
    thumb_x = x + k * 8 * s - (6 * s if flip else 0)
    parts += rect(thumb_x, y - 1 * s, 6 * s, 3.6 * s, 1.8 * s, fill=fill)
    parts += rect(x - 9 * s, y - 4 * s, 18 * s, 16 * s, 5 * s, fill=fill)
    return parts


def _winkhand(x, y, s=1.0):
    parts = _hand(x, y, s=s)
    parts += polyline(_arc(x - 14 * s, y - 6 * s, 8 * s, 10 * s, 120, 240, 12),
                      stroke=BLUE, width=1.8)
    parts += polyline(_arc(x - 20 * s, y - 6 * s, 8 * s, 10 * s, 120, 240, 12),
                      stroke=BLUE, width=1.6)
    return parts


def _farbe(color, outline=INK):
    return compose(
        ellipse(40, 42, 26, 21, rot=-14, fill=color, stroke=outline),
        ellipse(60, 66, 6, 4.0, rot=-20, fill=color, stroke=outline),
        ellipse(66, 72, 3.2, 2.2, rot=-20, fill=color, stroke=outline),
        poly([(64, 30), (74, 24), (86, 58), (76, 62)], fill=WOOD_L),
        poly([(76, 62), (86, 58), (90, 68), (79, 72)],
             fill=color, stroke=outline),
    )


def _sprechblase(x, y, w, h, fill=CREAM):
    tail = poly([(x + w * 0.2, y + h - 2), (x + w * 0.08, y + h + 9),
                 (x + w * 0.42, y + h - 2)], fill=fill)
    return tail + rect(x, y, w, h, 5, fill=fill)


def _kalender(x, y, w, h):
    parts = rect(x, y, w, h, 4, fill=CREAM)
    parts += rect(x, y, w, h * 0.2, 4, fill=RED)
    parts += rect(x + w * 0.2, y - 6, 4, 12, 2, fill=GREY)
    parts += rect(x + w * 0.7, y - 6, 4, 12, 2, fill=GREY)
    for row in range(2):
        for col in range(3):
            gy = y + h * (0.44 + row * 0.24)
            parts += line((x + w * (0.2 + col * 0.25), gy),
                          (x + w * (0.3 + col * 0.25), gy), width=1.0)
    return parts


def _thermometer(x, s=1.0, color=RED):
    return compose(
        rect(x - 5 * s, 16 * s, 10 * s, 46 * s, 5 * s, fill=CREAM),
        circle(x, 66 * s, 10 * s, fill=color),
        rect(x - 2 * s, 34 * s, 4 * s, 33 * s, 2 * s,
             fill=color, stroke=None),
        line((x - 7 * s, 28 * s), (x - 11 * s, 28 * s), width=1.0),
        line((x - 7 * s, 38 * s), (x - 11 * s, 38 * s), width=1.0),
        line((x - 7 * s, 48 * s), (x - 11 * s, 48 * s), width=1.0),
    )


def _schneeflocke(cx, cy, r=16):
    parts = []
    for a in (0, 60, 120):
        rad = math.radians(a)
        dx, dy = math.cos(rad), math.sin(rad)
        parts += line((cx - dx * r, cy - dy * r),
                      (cx + dx * r, cy + dy * r),
                      stroke=BLUE, width=2.2)
        for sign in (1, -1):
            tx = cx + dx * r * 0.62 * sign
            ty = cy + dy * r * 0.62 * sign
            for off in (-40, 40):
                base = a if sign > 0 else a + 180
                b = math.radians(base + off)
                parts += line((tx, ty),
                              (tx + math.cos(b) * r * 0.36,
                               ty + math.sin(b) * r * 0.36),
                              stroke=BLUE, width=1.6)
    parts += circle(cx, cy, r * 0.07, fill=BLUE, stroke=None)
    return parts


def _frage(cx, cy, s=1.0, stroke=INK):
    hook = _bez((cx - 7 * s, cy - 4 * s),
                (cx - 15 * s, cy - 18 * s),
                (cx + 15 * s, cy - 17 * s),
                (cx + 4 * s, cy - 1 * s), 22)
    parts = polyline(hook, stroke=stroke, width=2.8 * s)
    parts += line((cx + 4 * s, cy - 1 * s), (cx + 1 * s, cy + 6 * s),
                  stroke=stroke, width=2.8 * s)
    parts += circle(cx + 1 * s, cy + 12 * s, 1.7 * s,
                    fill=stroke, stroke=None)
    return parts


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
    # Verben
    "gitmek": gitmek,
    "gelmek": gelmek,
    "yemek": yemek,
    "icmek": icmek,
    "uyumak": uyumak,
    "kosmak": kosmak,
    "okumak": okumak,
    "yazmak": yazmak,
    "gormek": gormek,
    "duymak": duymak,
    "sevmek": sevmek,
    "konusmak": konusmak,
    "almak": almak,
    "vermek": vermek,
    "acmak": acmak,
    "kapatmak": kapatmak,
    "oturmak": oturmak,
    "oynamak": oynamak,
    "calismak": calismak,
    "beklemek": beklemek,
    # Adjektive
    "buyuk": buyuk,
    "kucuk": kucuk,
    "guzel": guzel,
    "cirkin": cirkin,
    "sicak": sicak,
    "soguk": soguk,
    "yeni": yeni,
    "eski": eski,
    "hizli": hizli,
    "yavas": yavas,
    "iyi": iyi,
    "kotu": kotu,
    # Farben
    "kirmizi": kirmizi,
    "mavi": mavi,
    "yesil": yesil,
    "sari": sari,
    "siyah": siyah,
    "beyaz": beyaz,
    # Alltag
    "merhaba": merhaba,
    "tesekkurler": tesekkurler,
    "lutfen": lutfen,
    "evet": evet,
    "hayir": hayir,
    "bugun": bugun,
    "yarin": yarin,
    "dun": dun,
    "simdi": simdi,
    "belki": belki,
}
