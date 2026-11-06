# Türkmek

Nudging-App zum Türkischlernen. Dreimal am Tag kommt eine Karte per Telegram:
Bild, Wort, Beispielsatz. Zwei Buttons, ein Tap – daraus lernt ein
Spaced-Repetition-Algorithmus, was morgen wieder dran ist.

Der Name ist ein Wortspiel: `türk` plus die türkische Infinitivendung `-mek`,
wie in `yürümek` (gehen) oder `gülmek` (lachen) – ein Verb, das es nicht gibt.

**Stand:** 50 A1-Wörter, Karten-Pipeline und Telegram-Bot laufen.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env      # Token von @BotFather eintragen
python -m turkmek.bot
```

Danach im Chat einmal `/start` schicken. Der erste Nutzer wird automatisch
freigeschaltet, alle weiteren ignoriert der Bot.

Läuft, solange der Prozess läuft. Für Dauerbetrieb braucht es später einen
Rechner, der an bleibt (VPS, Pi) oder `python -m turkmek.bot --once` per cron.

## Kommandos im Chat

| Kommando | Wirkung |
|---|---|
| `/next` | sofort eine Karte |
| `/heute` | was heute noch kommt, wie viel fällig ist |
| `/stats` | Serie, Trefferquote, fällige Karten |
| `/pause 7` | sieben Tage Ruhe (ohne Zahl: ein Tag) |
| `/resume` | weiter |
| `/zeit 08:30 13:00 20:00` | Sendezeiten ändern |

## Kommandozeile

```bash
python -m turkmek.cli status     # Überblick
python -m turkmek.cli due        # was gerade fällig ist
python -m turkmek.cli send       # sofort eine Karte (delegiert an turkmek.send)
python -m turkmek.cli pause 7
python -m turkmek.cli resume
python -m turkmek.cli reset kapi # Wort zurück auf neu
```

## Karte auf Abruf (soft)

Eine Karte pro Aufruf, ohne auf einen Slot zu warten:

```bash
python -m turkmek.send                 # eine Karte
python -m turkmek.send --count 3       # drei Karten
python -m turkmek.send --dry-run       # nur zeigen, was käme
python -m turkmek.send --force         # auch während einer Pause
```

Der Soft-Versand ignoriert das Tagesbudget für neue Wörter – wer fragt,
bekommt. Wiederholt wird trotzdem nichts, was heute schon raus ist. Und er
verbraucht **keinen** Slot: der 13:00-Versand findet danach trotzdem statt.
Gedacht für cron, launchd oder einfach von Hand: ein Aufruf, eine Karte,
Prozess beendet.

```cron
30 9 * * * cd ~/Documents/projects/tuerkmek && .venv/bin/python -m turkmek.send
```

## Wie der Bot entscheidet

Reihenfolge pro Slot: fällige Wiederholung → neues Wort (höchstens zwei pro
Tag) → irgendetwas, das lange nicht dran war. Ein Slot bleibt dadurch nie leer.

Ein Slot wird genau einmal bedient. Das erzwingt die Datenbank über
`UNIQUE(slot, local_date)`, damit ein doppelt laufender Tick nicht zweimal
anpingt. Verpasste Slots werden nicht nachgeholt – eine Nudge, die drei Stunden
zu spät kommt, ist keine Nudge mehr.

Die Wiederholung ist **tagesgranular** (1 → 3 → ×2,5 → …), nicht wie Anki mit
Minutenstufen: bei drei Nudges am Tag wäre „in 10 Minuten nochmal“ schlicht
nicht zustellbar.

## Zweisprachigkeit

Türkisch führt, Deutsch steht dahinter:

```
[ ✅ Biliyorum · Gewusst ]  [ 🔁 Tekrar · Nochmal ]
```

Nach dem Tap: `Doğru!` oder `Yarın tekrar · morgen nochmal`. Die Bedienvokabeln
wiederholen sich täglich – `biliyorum`, `tekrar`, `doğru`, `yarın` sitzen nach
zwei Wochen von selbst.

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

## Rendern

```bash
python -m turkmek.render              # alles, was fehlt oder veraltet ist
python -m turkmek.render --all        # alles neu
python -m turkmek.render --only kapi  # nur ein Wort
python -m turkmek.render --sheet      # Kontaktabzug nach assets/sheet.png
python -m turkmek.render --jitter 0.03  # unordentlicher zeichnen
```

Gerendert wird nur, was sich geändert hat (Hash-Manifest in
`assets/.manifest.json`).

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
turkmek/render.py       Render-CLI
turkmek/config.py       .env, Zeitzone, Slots, Pfade
turkmek/store.py        SQLite: Reviews, Sendungen, Antworten
turkmek/srs.py          Spaced Repetition
turkmek/planner.py      Kartenauswahl
turkmek/cards.py        Caption und Inline-Buttons
turkmek/telegram.py     API-Client (Long Polling)
turkmek/bot.py          Polling, Scheduler, Kommandos
turkmek/send.py         Einzelversand pro Aufruf (soft)
turkmek/cli.py          Zustand von der Kommandozeile
assets/                 generierte Icons und Karten (eingecheckt)
data/                   SQLite und Log (nicht eingecheckt)
```

Icons und Karten liegen im Repo, weil sie Teil des Inhalts sind. Eine Karte ist
~75 KB.

## Tests

```bash
pytest
```

Abgedeckt: SRS-Intervalle, Kartenauswahl, Idempotenz des Versands (der Tick darf
nie zweimal dieselbe Karte schicken), Caption- und Button-Format.

## Nächste Schritte

- Multiple Choice statt Selbstbewertung – dafür braucht `words.yaml` ein
  `topic`-Feld, damit die Distraktoren aus derselben Kategorie kommen.
- Verben und Adjektive: brauchen Symbole statt Gegenständen.
- Mehrere Karten pro Nudge, sobald die Wortliste über ~200 wächst.
