# Türkmek

Nudging-App zum Türkischlernen. Statt einer Lernsession bekommst du über den
Tag verteilt kleine Karten: eine Vokabel, ein Beispielsatz, ein Bild. Die
Karten werden vorproduziert und später per Bot verschickt.

**Stand:** Wortliste und Karten-Pipeline stehen (50 A1-Wörter). Der
Telegram-Versand ist noch nicht gebaut.

Der Name ist ein Wortspiel: `türk` plus die türkische Infinitivendung `-mek`,
wie in `yürümek` (gehen) oder `gülmek` (lachen) – ein Verb, das es nicht gibt.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Kein Systempaket nötig: der Rasterizer ist selbst gebaut (Pillow plus
Supersampling), es gibt keine Abhängigkeit von cairo oder einem
SVG-Renderer.

## Kommandos

```bash
python -m turkmek.render              # alles rendern, was fehlt oder veraltet ist
python -m turkmek.render --all        # alles neu
python -m turkmek.render --only kapi  # nur ein Wort
python -m turkmek.render --sheet      # Kontaktabzug nach assets/sheet.png
python -m turkmek.render --jitter 0.03  # unordentlicher zeichnen
python -m turkmek.content             # Wortliste prüfen
pytest
```

Gerendert wird nur, was sich geändert hat (Hash-Manifest in
`assets/.manifest.json`). `--force` ignoriert das.

## Wie eine Karte entsteht

```
content/words.yaml     Vokabel + Beispielsatz
turkmek/icons.py       Zeichenrezept (Python, geometrische Primitive)
      │
      ├─ jitter_shapes   jede Form leicht verschieben/drehen, Seed = Wort-ID
      ├─ fit_shapes      auf 80×80 einpassen, damit alle Motive gleich wirken
      │
      ├─► assets/icons/svg/<id>.svg    Vektorquelle
      ├─► assets/icons/png/<id>.png    512 px, transparent
      └─► assets/cards/<id>.jpg        900 px, Papier + Körnung + Rahmen
```

Alle Koordinaten laufen von 0 bis 100, y zeigt nach unten, gezeichnet wird von
hinten nach vorn. Es gibt nur zwei Primitive – geschlossenes Polygon und offene
Linie –, deshalb sind SVG-Export und Rasterizer knapp und identisch.

**Warum gezeichnet und nicht generiert:** Ein Bildmodell liefert für 500 Wörter
500 verschiedene Strichstärken und Perspektiven. Hier kommt der Stil aus dem
Code: eine Palette, eine Kontur, eine Geometrie. Die Unvollkommenheit ist
dagegen Absicht und kommt aus `jitter_shapes` – geseedet, also bei jedem Build
identisch.

**Warum die Karte keinen Text trägt:** Die Vokabel steht in der Bildunterschrift.
So bleibt sie kopierbar, durchsuchbar und im gesperrten Bildschirm trotzdem
sichtbar.

## Ein Wort hinzufügen

1. Eintrag in `content/words.yaml` (ASCII-`id`, `tr`, `de`, `pos`, Beispielsatz).
2. Funktion in `turkmek/icons.py` schreiben und in `ICONS` eintragen.
3. `python -m turkmek.render --only <id> && python -m turkmek.render --sheet`

Die Prüfung in `turkmek/content.py` meckert, wenn ein Wort kein Icon hat, ein
Icon kein Wort, oder eine `id` doppelt bzw. nicht ASCII ist.

## Struktur

```
content/words.yaml      A1-Wortliste (50 Substantive)
turkmek/geometry.py     Punkte für Kreis, Rechteck, Stern, Bézier, Mondsichel
turkmek/scene.py        Formen, Jitter, Einpassen
turkmek/svg.py          Szene → SVG
turkmek/raster.py       Szene → PNG (Pillow, 4× Supersampling)
turkmek/card.py         Papierkarte mit Körnung und Rahmen
turkmek/icons.py        die 50 Zeichenrezepte
turkmek/content.py      Laden und Prüfen der Wortliste
turkmek/render.py       CLI
assets/                 generierte Icons und Karten (eingecheckt)
```

Icons und Karten liegen im Repo, weil sie Teil des Inhalts sind und nicht bei
jedem Lauf neu entstehen sollen. Eine Karte ist ~75 KB.

## Nächste Schritte

- Telegram-Bot: `/api`-freier Long-Polling-Bot, Versand aus `assets/cards/`.
- SRS (`due_at`, `interval`, `lapses`) und ein Tagesplan mit 2–3 Nudges.
- Weitere Wortarten: Verben und Adjektive brauchen statt Gegenständen Symbole.
