"""Baut Icons, Karten und Kontaktabzüge.

    python -m turkmek.render --all
    python -m turkmek.render --only kapi pencere
    python -m turkmek.render --sheet
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import card as card_mod
from . import icons, raster, scene, svg
from .content import ROOT, load_words

ASSETS = ROOT / "assets"
MANIFEST = ASSETS / ".manifest.json"

ICON_SIZE = 512
CARD_SIZE = 900
JITTER = 0.012


def build_scene(word, jitter=JITTER):
    shapes = icons.ICONS[word["id"]]()
    shapes = scene.jitter_shapes(shapes, seed=word["id"], amount=jitter)
    return scene.fit_shapes(shapes, size=80.0)


def _digest(shapes, jitter):
    payload = svg.to_svg(shapes) + f"|{jitter}|{ICON_SIZE}|{CARD_SIZE}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def render_word(word, force=False, jitter=JITTER, quiet=False):
    shapes = build_scene(word, jitter)
    digest = _digest(shapes, jitter)

    svg_path = ASSETS / "icons" / "svg" / f"{word['id']}.svg"
    png_path = ASSETS / "icons" / "png" / f"{word['id']}.png"
    card_path = ASSETS / "cards" / f"{word['id']}.jpg"

    manifest = _load_manifest()
    if not force and manifest.get(word["id"]) == digest:
        if svg_path.exists() and png_path.exists() and card_path.exists():
            if not quiet:
                print(f"  {word['id']:<10} unverändert")
            return False

    for path in (svg_path, png_path, card_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    svg_path.write_text(svg.to_svg(shapes), encoding="utf-8")

    icon = raster.render(shapes, size=ICON_SIZE)
    icon.save(png_path)

    card = card_mod.make_card(icon, size=CARD_SIZE, seed=word["id"])
    card.save(card_path, quality=88, optimize=True, subsampling=0)

    manifest[word["id"]] = digest
    _save_manifest(manifest)

    if not quiet:
        print(f"  {word['id']:<10} gerendert")
    return True


def _load_manifest():
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_manifest(data):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(data, indent=2, sort_keys=True),
                        encoding="utf-8")


def _font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def contact_sheet(words, out=None, cols=8, cell=240):
    """Ein Blatt mit allen Karten plus Beschriftung – zum Drüberschauen."""
    rows = (len(words) + cols - 1) // cols
    pad = 10
    label_h = 26
    width = cols * (cell + pad) + pad
    height = rows * (cell + pad + label_h) + pad

    sheet = Image.new("RGB", (width, height), "#dcd3c4")
    draw = ImageDraw.Draw(sheet)
    font = _font(17)

    for i, word in enumerate(words):
        r, c = divmod(i, cols)
        x = pad + c * (cell + pad)
        y = pad + r * (cell + pad + label_h)

        path = ASSETS / "cards" / f"{word['id']}.jpg"
        if path.exists():
            img = Image.open(path).convert("RGB").resize((cell, cell),
                                                         Image.LANCZOS)
            sheet.paste(img, (x, y))

        label = f"{word['tr']} · {word['de']}"
        draw.text((x + 2, y + cell + 4), label, fill="#2b2724", font=font)

    out = out or ASSETS / "sheet.png"
    sheet.save(out)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Icons und Karten rendern")
    parser.add_argument("--all", action="store_true", help="alles neu rendern")
    parser.add_argument("--only", nargs="+", metavar="ID", help="nur diese IDs")
    parser.add_argument("--sheet", action="store_true",
                        help="Kontaktabzug erzeugen")
    parser.add_argument("--force", action="store_true",
                        help="auch unveränderte neu rendern")
    parser.add_argument("--jitter", type=float, default=JITTER,
                        help="Unvollkommenheit (0 = exakt)")
    args = parser.parse_args(argv)

    words = load_words()

    if args.only:
        wanted = set(args.only)
        unknown = wanted - {w["id"] for w in words}
        if unknown:
            raise SystemExit(f"Unbekannte IDs: {', '.join(sorted(unknown))}")
        words = [w for w in words if w["id"] in wanted]

    if args.all or args.only:
        print(f"Rendere {len(words)} Icons (Jitter {args.jitter})")
        changed = 0
        for word in words:
            changed += render_word(word, force=args.force, jitter=args.jitter)
        print(f"{changed} geändert, {len(words) - changed} unverändert")
    else:
        # ohne Argument: alles, was fehlt oder veraltet ist
        for word in words:
            render_word(word, jitter=args.jitter, quiet=True)
        print(f"{len(words)} Icons geprüft")

    if args.sheet or not (args.all or args.only):
        out = contact_sheet(load_words())
        print(f"Kontaktabzug: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
