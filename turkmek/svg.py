"""Szene -> SVG. Das ist die Vektorquelle, die im Repo liegt."""

from __future__ import annotations


def _fmt(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _points(pts):
    return " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in pts)


def _shape_tag(s, points, fill, stroke):
    attrs = [f'points="{_points(points)}"', f'fill="{fill}"']
    if stroke and s.width:
        attrs.append(f'stroke="{s.stroke}"')
        attrs.append(f'stroke-width="{_fmt(s.width)}"')
        attrs.append('stroke-linejoin="round"')
        attrs.append('stroke-linecap="round"')
    elif fill != "none":
        attrs.append('stroke="none"')
    tag = "polygon" if s.closed else "polyline"
    return f"  <{tag} {' '.join(attrs)}/>"


def to_svg(shapes, size=100):
    body = []
    for s in shapes:
        ox, oy = s.fill_offset

        if s.fill and len(s.points) >= 3:
            # Füllung und Kontur getrennt, damit der Versatz sichtbar wird.
            fill_pts = [(x + ox, y + oy) for x, y in s.points]
            body.append(_shape_tag(s, fill_pts, s.fill, None))
            if s.stroke and s.width:
                body.append(_shape_tag(s, s.points, "none", s.stroke))
        else:
            body.append(_shape_tag(s, s.points, "none", s.stroke))

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {size} {size}" width="{size}" height="{size}">\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )
