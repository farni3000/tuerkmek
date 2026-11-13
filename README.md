# Türkmek

Nudging-App zum Türkischlernen. Dreimal am Tag kommt eine Karte per Telegram:
Bild, Wort, Beispielsatz. Zwei Buttons, ein Tap – daraus lernt ein
Spaced-Repetition-Algorithmus, was morgen wieder dran ist.

Der Name ist ein Wortspiel: `türk` plus die türkische Infinitivendung `-mek`,
wie in `yürümek` (gehen) oder `gülmek` (lachen) – ein Verb, das es nicht gibt.

**Stand:** 98 A1-Wörter (50 Nomen, 20 Verben, 12 Adjektive, 6 Farben,
10 Alltagswörter), Karten-Pipeline und Telegram-Bot laufen.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env      # Token von @BotFather eintragen
python -m turkmek.bot
```

Alternativ startet `./start.sh` den Bot und legt die venv bei Bedarf an.

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
turkmek/gags.py        welcher Katzen-Auftritt zu welchem Wort gehört
      │
      ├─ jitter_shapes   jede Form leicht verschieben/drehen, Seed = Wort-ID
      ├─ fit_shapes      auf 64×64 einpassen, damit alle Motive gleich wirken
      ├─ mascot.cat      die Katze in Szene setzen (Pose, Accessoire, Requisite)
      ├─ wobble_shapes   Kanten verbiegen, Linien überschießen lassen
      ├─ misregister     Füllungen leicht neben die Kontur setzen
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
Code: eine Palette, eine Kontur, eine Geometrie.

**Warum die Bilder absichtlich schief sind:** Eine perfekte Vektorgrafik ist
hübsch, aber austauschbar. Damit das Wort hängen bleibt, darf das Bild ruhig
etwas falsch aussehen: `jitter_shapes` verschiebt ganze Formen,
`wobble_shapes` verbiegt jede Kante wie eine zittrige Hand, `misregister_shapes`
setzt Füllungen neben die Kontur, und der Kartenrahmen ist von Hand gezogen.
Der Witz ist der Anker – alles bleibt geseedet (Seed = Wort-ID) und damit bei
jedem Build identisch.

## Die Katze

Dieselbe beige Katze taucht auf fast jeder Karte auf, aber nie einfach nur
daneben: `gags.py` gibt jedem Wort einen eigenen Auftritt. Sie liegt auf dem
Bett, hängt am Baum, reitet auf dem Pferd, guckt aus dem Busfenster, hält den
Fisch oder schläft auf der Schnecke. Die Position wird relativ zur
Bounding-Box des Icons aufgelöst, nicht in festen Koordinaten:

| Anker | Bedeutung |
|---|---|
| `beside_left` / `beside_right` | steht neben dem Motiv |
| `on_top` | sitzt oder liegt auf der Oberkante (Tisch, Buch, Dach) |
| `inside` | Kopf in einer Öffnung (Fenster, Tür, Fahrzeug) |
| `behind_left` / `behind_right` | lugt hervor, teilweise verdeckt |
| `under` | darunter |
| `edge` | nur Kopf und Pfoten am Bildrand |

Dazu kommen Pose (`sit`, `lie`, `hang`, `ride`, `walk`, `run`, `sniff`,
`peek`, `sleep`, `point`, `hold`, `wave`, `push`, `reach`), Blickrichtung,
Größe, Schicht (vor/hinter dem Motiv) und optional ein Accessoire, eine
Requisite oder ein Effekt.

Zehn Karten bleiben bewusst katzenfrei: `gunes`, `ay`, `yildiz`, `yagmur`,
`kar`, `bulut`, `su`, `tuz`, `seker`, `beyaz`. Dort liegt nur ein
Pfotenabdruck – die Abwesenheit ist selbst ein kleiner Gag.

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
   `pos` ist eine von `noun`, `verb`, `adj`, `color`, `phrase`.
2. Funktion in `turkmek/icons.py` schreiben und in `ICONS` eintragen.
3. Auftritt in `turkmek/gags.py` unter `SCENES` eintragen (Pose, Anker,
   Accessoire, Requisite, Effekt) – oder bewusst in `NO_CAT` aufnehmen.
4. `python -m turkmek.render --only <id> && python -m turkmek.render --sheet`

Die Prüfung in `turkmek/content.py` meckert, wenn ein Wort kein Icon hat, ein
Icon kein Wort, oder eine `id` doppelt bzw. nicht ASCII ist. Die Tests prüfen
zusätzlich, dass jede Karte auf die 100×100-Fläche passt, dass jedes Wort
entweder eine Szene oder einen bewussten Katzenverzicht hat, und dass in
`gags.py` nur bekannte Posen, Accessoires und Requisiten referenziert werden.

## Struktur

```
content/words.yaml      A1-Wortliste (98 Wörter, fünf Wortarten)
turkmek/geometry.py     Punkte für Kreis, Rechteck, Stern, Bézier, Mondsichel
turkmek/scene.py        Formen, Jitter, Wobble, Füllungsversatz, Einpassen
turkmek/svg.py          Szene → SVG
turkmek/raster.py       Szene → PNG (Pillow, 4× Supersampling)
turkmek/card.py         Papierkarte mit Körnung, schiefem Rahmen, Gebrauchsspuren
turkmek/icons.py        die 98 Zeichenrezepte
turkmek/mascot.py       die Katze in vielen Posen plus Accessoires und Requisiten
turkmek/gags.py         Wort → Katzen-Auftritt (Anker, Pose, Requisit)
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
nie zweimal dieselbe Karte schicken), Caption- und Button-Format, Wortliste und
Icons, Determinismus von Jitter und Wobble, ob jede Karte auf die Zeichenfläche
passt, ob jedes Wort entweder eine Szene oder einen bewussten Katzenverzicht
hat, und ob `gags.py` nur bekannte Posen, Accessoires und Requisiten
referenziert.

## Nächste Schritte

- Multiple Choice statt Selbstbewertung – dafür braucht `words.yaml` ein
  `topic`-Feld, damit die Distraktoren aus derselben Kategorie kommen.
- Mehr Wörter: Familie (`anne`, `baba`, `çocuk`), Körper (`göz`, `el`, `ayak`)
  und Zahlen. Für Pronomen und Konjunktionen braucht es neue Symbolideen.
- Mehrere Karten pro Nudge, sobald die Wortliste über ~200 wächst.
