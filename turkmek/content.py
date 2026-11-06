"""Wortliste laden und prüfen."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from .icons import ICONS

ROOT = Path(__file__).resolve().parent.parent
WORDS_FILE = ROOT / "content" / "words.yaml"

REQUIRED = ("id", "tr", "de", "pos", "example")


def load_words(path=None):
    path = Path(path) if path else WORDS_FILE
    with open(path, encoding="utf-8") as fh:
        words = yaml.safe_load(fh)

    problems = []
    seen = set()
    for w in words:
        missing = [k for k in REQUIRED if not w.get(k)]
        if missing:
            problems.append(f"{w.get('id', '?')}: fehlt {', '.join(missing)}")
        if w["id"] in seen:
            problems.append(f"{w['id']}: doppelte id")
        seen.add(w["id"])
        if not w["id"].isascii():
            problems.append(f"{w['id']}: id muss ASCII sein")
        if w["id"] not in ICONS:
            problems.append(f"{w['id']}: kein Icon in icons.py")
        ex = w.get("example") or {}
        if not ex.get("tr") or not ex.get("de"):
            problems.append(f"{w['id']}: Beispielsatz unvollständig")

    for icon_id in set(ICONS) - seen:
        problems.append(f"{icon_id}: Icon ohne Wort in words.yaml")

    if problems:
        raise ValueError("Wortliste fehlerhaft:\n  " + "\n  ".join(problems))

    return words


if __name__ == "__main__":
    try:
        words = load_words()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
    print(f"{len(words)} Wörter, {len(ICONS)} Icons – alles vollständig.")
