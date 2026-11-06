"""Szene -> SVG. Das ist die Vektorquelle, die im Repo liegt."""

from __future__ import annotations


def _fmt(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _points(pts):
    return " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in pts)


def to_svg(shapes, size=100):
    body = []
    for s in shapes:
        attrs = [f'points="{_points(s.points)}"']
        if s.fill and len(s.points) >= 3:
            attrs.append(f'fill="{s.fill}"')
        else:
            attrs.append('fill="none"')

        if s.stroke and s.width:
            attrs.append(f'stroke="{s.stroke}"')
            attrs.append(f'stroke-width="{_fmt(s.width)}"')
            attrs.append('stroke-linejoin="round"')
            attrs.append('stroke-linecap="round"')

        tag = "polygon" if s.closed else "polyline"
        body.append(f"  <{tag} {' '.join(attrs)}/>")

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {size} {size}" width="{size}" height="{size}">\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )
