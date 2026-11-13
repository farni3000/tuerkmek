"""Grammatik-Bits: eine kurze Regel, ein kleines Quiz, ein eigenes Tempo.

Die Bits sind bewusst kein zweiter Vokabelstapel. Sie kommen einmal am Tag,
werden nach demselben groben SRS wie Wörter wiederholt und lassen sich mit
einem ausdrücklichen Tap dauerhaft abschalten – eine richtige Quizantwort
allein heißt noch nicht „verstanden“.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .bit_icons import BIT_ICONS
from .content import ROOT

BITS_FILE = ROOT / "content" / "grammar.yaml"

REQUIRED = ("id", "icon", "title", "text", "example", "question",
            "options", "answer")

# Mehr passt nicht in eine Nudge. Die Grenze gilt für die komplette Caption
# inklusive Beispiel und Frage, nicht nur für den Regeltext.
MAX_CAPTION = 320

CORRECT_TEXT = "✅ Doğru! · Richtig"
WRONG_TEXT = "❌ Yanlış · Falsch"
RETIRE_TEXT = "✅ Anladım · nicht mehr zeigen"
RETIRED_TEXT = "✅ Anladım · wird nicht mehr gezeigt"
ALREADY_TEXT = "Zaten · schon erledigt"

__all__ = [
    "BITS_FILE", "MAX_CAPTION", "CORRECT_TEXT", "WRONG_TEXT", "RETIRE_TEXT",
    "RETIRED_TEXT", "ALREADY_TEXT", "load_bits", "caption",
    "keyboard", "retire_keyboard", "parse_callback", "feedback",
]


def load_bits(path=None):
    """Lädt und prüft content/grammar.yaml."""
    path = Path(path) if path else BITS_FILE
    with open(path, encoding="utf-8") as fh:
        bits = yaml.safe_load(fh) or []

    problems = []
    seen = set()
    for bit in bits:
        bit_id = bit.get("id", "?")
        missing = [key for key in REQUIRED
                   if key not in bit or bit[key] is None or bit[key] == ""]
        if missing:
            problems.append(f"{bit_id}: fehlt {', '.join(missing)}")
            continue

        if bit["id"] in seen:
            problems.append(f"{bit['id']}: doppelte id")
        seen.add(bit["id"])
        if not bit["id"].isascii():
            problems.append(f"{bit['id']}: id muss ASCII sein")
        if bit["icon"] not in BIT_ICONS:
            problems.append(f"{bit['id']}: unbekanntes Icon {bit['icon']}")

        example = bit["example"] or {}
        if not example.get("tr") or not example.get("de"):
            problems.append(f"{bit['id']}: Beispielsatz unvollständig")
        question = bit["question"] or {}
        if not question.get("tr") or not question.get("de"):
            problems.append(f"{bit['id']}: Frage unvollständig")

        options = bit["options"] or []
        if not isinstance(options, list) or not 2 <= len(options) <= 4:
            problems.append(f"{bit['id']}: 2 bis 4 Antworten erwartet")
        elif any(not str(option).strip() for option in options):
            problems.append(f"{bit['id']}: leere Antwort")
        elif len({str(option) for option in options}) != len(options):
            problems.append(f"{bit['id']}: doppelte Antwort")

        answer = bit["answer"]
        if not isinstance(answer, int) or isinstance(answer, bool):
            problems.append(f"{bit['id']}: answer muss eine Zahl sein")
        elif not 0 <= answer < len(options):
            problems.append(f"{bit['id']}: answer liegt außerhalb der Antworten")

        if not problems and len(caption(bit)) > MAX_CAPTION:
            problems.append(
                f"{bit['id']}: Caption zu lang "
                f"({len(caption(bit))} > {MAX_CAPTION} Zeichen)"
            )

    if not bits:
        problems.append("keine Grammatik-Bits gefunden")

    if problems:
        raise ValueError("Grammatik-Bits fehlerhaft:\n  "
                         + "\n  ".join(problems))

    return bits


def caption(bit, status=None):
    """Kurze Nachricht: Titel, Regel, Beispiel, Frage."""
    question = bit["question"]
    text = (
        f"{bit['title']}\n"
        f"{bit['text']}\n\n"
        f"{bit['example']['tr']}\n"
        f"{bit['example']['de']}\n\n"
        f"{question['tr']} · {question['de']}"
    )
    if status:
        text = f"{text}\n\n{status}"
    return text


def _rows(buttons, width=3):
    return [buttons[i:i + width] for i in range(0, len(buttons), width)]


def keyboard(delivery_id, bit):
    """Quiz-Optionen plus der ausdrückliche „nicht mehr zeigen“-Tap."""
    options = [
        {
            "text": str(option),
            "callback_data": f"g:{delivery_id}:{index}",
        }
        for index, option in enumerate(bit["options"])
    ]
    rows = _rows(options)
    rows.append([{
        "text": RETIRE_TEXT,
        "callback_data": f"g:{delivery_id}:x",
    }])
    return {"inline_keyboard": rows}


def retire_keyboard(delivery_id):
    """Nach dem Quiz bleibt nur noch der Abschalt-Tap stehen."""
    return {
        "inline_keyboard": [[{
            "text": RETIRE_TEXT,
            "callback_data": f"g:{delivery_id}:x",
        }]]
    }


def parse_callback(data):
    """'g:42:1' -> (42, 1), 'g:42:x' -> (42, 'x'). Sonst None."""
    if not data or not data.startswith("g:"):
        return None
    parts = data.split(":")
    if len(parts) != 3:
        return None
    try:
        delivery_id = int(parts[1])
    except ValueError:
        return None

    if parts[2] == "x":
        return delivery_id, "x"
    try:
        index = int(parts[2])
    except ValueError:
        return None
    if index < 0:
        return None
    return delivery_id, index


def feedback(bit, index):
    """Gibt (Feedbacktext, SRS-Ergebnis) für eine Quizantwort zurück."""
    if index == bit["answer"]:
        return CORRECT_TEXT, "y"

    correct = bit["options"][bit["answer"]]
    return f"{WRONG_TEXT}\nDoğru: {correct} · Richtig: {correct}", "n"
