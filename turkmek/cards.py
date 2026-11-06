"""Caption und Buttons einer Karte.

Regel für die Zweisprachigkeit: türkisch führt, deutsch steht dahinter. Die
Bedienvokabeln (biliyorum, tekrar, doğru, yarın) wiederholen sich täglich und
sitzen dadurch irgendwann von selbst.
"""

from __future__ import annotations

GOOD_TEXT = "✅ Biliyorum · Gewusst"
AGAIN_TEXT = "🔁 Tekrar · Nochmal"

STATUS = {
    "y": "✅ Doğru! · Gewusst",
    "n": "🔁 Yarın tekrar · morgen nochmal",
}


def caption(word, status=None):
    """Bildunterschrift: Wort, Übersetzung, Beispielsatz."""
    text = (
        f"{word['tr']} — {word['de']}\n\n"
        f"{word['example']['tr']}\n"
        f"{word['example']['de']}"
    )
    if status:
        text = f"{text}\n\n{status}"
    return text


def keyboard(delivery_id, kind):
    """Neue Wörter werden nur gezeigt, Wiederholungen abgefragt."""
    if kind == "new":
        return None

    return {
        "inline_keyboard": [[
            {"text": GOOD_TEXT, "callback_data": f"a:{delivery_id}:y"},
            {"text": AGAIN_TEXT, "callback_data": f"a:{delivery_id}:n"},
        ]]
    }


def parse_callback(data):
    """'a:42:y' -> (42, 'y'). Gibt None bei fremdem Format."""
    if not data or not data.startswith("a:"):
        return None
    parts = data.split(":")
    if len(parts) != 3:
        return None
    try:
        delivery_id = int(parts[1])
    except ValueError:
        return None
    if parts[2] not in STATUS:
        return None
    return delivery_id, parts[2]
