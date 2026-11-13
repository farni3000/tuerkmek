"""Prüft Wortliste und Zeichenrezepte.

Der Fokus liegt auf dem, was beim Erweitern der Liste schiefgehen kann:
fehlende Icons, doppelte IDs, kaputte Beispielsätze.
"""

import pytest

from turkmek import gags, mascot, render, scene, svg
from turkmek.content import load_words
from turkmek.icons import ICONS

WORDS = load_words()


def test_word_count():
    assert len(WORDS) == 98


def test_all_parts_of_speech():
    assert {w["pos"] for w in WORDS} == {
        "noun", "verb", "adj", "color", "phrase",
    }


def test_word_and_icon_sets_match():
    assert {w["id"] for w in WORDS} == set(ICONS)


def test_ids_unique_and_ascii():
    ids = [w["id"] for w in WORDS]
    assert len(ids) == len(set(ids))
    assert all(i.isascii() for i in ids)


def test_examples_complete():
    for word in WORDS:
        assert word["example"]["tr"].strip()
        assert word["example"]["de"].strip()


@pytest.mark.parametrize("word", WORDS, ids=[w["id"] for w in WORDS])
def test_icon_stays_inside_canvas(word):
    shapes = scene.fit_shapes(
        scene.jitter_shapes(ICONS[word["id"]](), seed=word["id"])
    )
    assert shapes
    markup = svg.to_svg(shapes)
    assert "<polygon" in markup or "<polyline" in markup

    for shape in shapes:
        for x, y in shape.points:
            assert 0.0 <= x <= 100.0
            assert 0.0 <= y <= 100.0


def test_jitter_is_deterministic():
    first = svg.to_svg(scene.jitter_shapes(ICONS["kapi"](), seed="kapi"))
    second = svg.to_svg(scene.jitter_shapes(ICONS["kapi"](), seed="kapi"))
    assert first == second


def test_wobble_is_deterministic():
    shapes = scene.fit_shapes(ICONS["kapi"]())
    first = svg.to_svg(scene.wobble_shapes(shapes, seed="kapi"))
    second = svg.to_svg(scene.wobble_shapes(shapes, seed="kapi"))
    assert first == second
    assert first != svg.to_svg(shapes)


@pytest.mark.parametrize("word", WORDS, ids=[w["id"] for w in WORDS])
def test_full_card_fits_on_canvas(word):
    shapes = render.build_scene(word)
    assert shapes
    for shape in shapes:
        for x, y in shape.points:
            assert 0.0 <= x <= 100.0
            assert 0.0 <= y <= 100.0


def test_gags_reference_known_parts():
    for word in WORDS:
        gag = gags.for_word(word)
        assert gag.pose in mascot._POSES
        if gag.accessory:
            assert gag.accessory in mascot._ACCESSORIES
        if gag.item:
            assert gag.item in mascot._ITEMS
        if gag.effect:
            assert gag.effect in mascot._EFFECTS
