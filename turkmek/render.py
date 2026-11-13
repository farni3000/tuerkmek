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
from . import bit_icons, gags, icons, mascot, raster, scene, svg
from .content import ROOT, load_words
from .grammar import load_bits

ASSETS = ROOT / "assets"
MANIFEST = ASSETS / ".manifest.json"
BIT_MANIFEST = ASSETS / "bits" / ".manifest.json"

ICON_SIZE = 512
CARD_SIZE = 900
BIT_SIZE = 320
JITTER = 0.012
ICON_FILL = 64.0
ICON_CENTER = (42.0, 44.0)
BIT_ICON_FILL = 72.0
# Bei Änderungen an Karte/Rahmen/Gebrauchsspuren hochzählen, damit der
# Manifest-Hash alte Karten als veraltet erkennt.
STYLE_VERSION = 3
BIT_STYLE_VERSION = 1


def build_scene(word, jitter=JITTER):
    icon = icons.ICONS[word["id"]]()
    icon = scene.jitter_shapes(icon, seed=word["id"], amount=jitter)
    icon = scene.fit_shapes(icon, size=ICON_FILL, center=ICON_CENTER)

    gag = gags.for_word(word)
    if gag is None:
        shapes = icon + mascot.paw_prints(seed=word["id"])
    else:
        x, y, s, target = gags.resolve(gag, scene.bounds(icon))
        cat = mascot.cat(gag.pose, x, y, s, flip=gag.flip, target=target,
                         accessory=gag.accessory, item=gag.item,
                         effect=gag.effect)
        shapes = cat + icon if gag.layer == "back" else icon + cat

    shapes = scene.wobble_shapes(shapes, seed=word["id"])
    return scene.misregister_shapes(shapes, seed=word["id"])


def build_bit_scene(icon_id, jitter=JITTER):
    """Kleines Grammatik-Motiv ohne Katze und ohne Kartenrahmen."""
    seed = f"bit:{icon_id}"
    shapes = bit_icons.BIT_ICONS[icon_id]()
    shapes = scene.jitter_shapes(shapes, seed=seed, amount=jitter)
    shapes = scene.fit_shapes(shapes, size=BIT_ICON_FILL, center=(50, 50))
    shapes = scene.wobble_shapes(shapes, seed=seed)
    return scene.misregister_shapes(shapes, seed=seed)


def _digest(shapes, jitter, extra=""):
    payload = svg.to_svg(shapes) + f"|{jitter}|{extra}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _bit_digest(shapes, jitter):
    return _digest(shapes, jitter, f"{BIT_SIZE}|v{BIT_STYLE_VERSION}")


def render_word(word, force=False, jitter=JITTER, quiet=False):
    shapes = build_scene(word, jitter)
    digest = _digest(shapes, jitter, f"{ICON_SIZE}|{CARD_SIZE}|v{STYLE_VERSION}")

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


def render_bit(icon_id, force=False, jitter=JITTER, quiet=False):
    shapes = build_bit_scene(icon_id, jitter)
    digest = _bit_digest(shapes, jitter)
    bit_path = ASSETS / "bits" / f"{icon_id}.jpg"

    manifest = _load_manifest(BIT_MANIFEST)
    if not force and manifest.get(icon_id) == digest and bit_path.exists():
        if not quiet:
            print(f"  {icon_id:<14} unverändert")
        return False

    bit_path.parent.mkdir(parents=True, exist_ok=True)
    icon = raster.render(shapes, size=ICON_SIZE)
    tile = card_mod.make_card(
        icon, size=BIT_SIZE, seed=f"bit:{icon_id}", icon_ratio=0.74,
        frame=False,
    )
    tile.save(bit_path, quality=90, optimize=True, subsampling=0)

    manifest[icon_id] = digest
    _save_manifest(manifest, BIT_MANIFEST)

    if not quiet:
        print(f"  {icon_id:<14} gerendert")
    return True


def render_bits(force=False, jitter=JITTER, quiet=False):
    changed = 0
    for icon_id in bit_icons.BIT_ICONS:
        changed += render_bit(icon_id, force=force, jitter=jitter, quiet=quiet)
    return changed


def _load_manifest(path=MANIFEST):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_manifest(data, path=MANIFEST):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True),
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
    parser.add_argument("--bits", action="store_true",
                        help="nur die Grammatik-Bit-Icons rendern")
    parser.add_argument("--sheet", action="store_true",
                        help="Kontaktabzug erzeugen")
    parser.add_argument("--force", action="store_true",
                        help="auch unveränderte neu rendern")
    parser.add_argument("--jitter", type=float, default=JITTER,
                        help="Unvollkommenheit (0 = exakt)")
    args = parser.parse_args(argv)

    if args.bits:
        load_bits()
        print(f"Rendere {len(bit_icons.BIT_ICONS)} Bit-Icons "
              f"(Jitter {args.jitter})")
        changed = render_bits(force=args.force, jitter=args.jitter)
        print(f"{changed} geändert, "
              f"{len(bit_icons.BIT_ICONS) - changed} unverändert")
        return

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
        if args.all:
            load_bits()
            print(f"Rendere {len(bit_icons.BIT_ICONS)} Bit-Icons")
            bit_changed = render_bits(force=args.force, jitter=args.jitter,
                                      quiet=True)
            print(f"{bit_changed} Bit-Icons geändert")
    else:
        # ohne Argument: alles, was fehlt oder veraltet ist
        for word in words:
            render_word(word, jitter=args.jitter, quiet=True)
        print(f"{len(words)} Icons geprüft")
        load_bits()
        render_bits(jitter=args.jitter, quiet=True)
        print(f"{len(bit_icons.BIT_ICONS)} Bit-Icons geprüft")

    if args.sheet or not (args.all or args.only):
        out = contact_sheet(load_words())
        print(f"Kontaktabzug: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
