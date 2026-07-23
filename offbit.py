"""
offbit.py - set text in OffBit as SVG outlines.

glyphs.json (baked by bake_font.py) holds each glyph's path in font units with
Y pointing up. We emit one <g> per string that flips Y and scales to the
requested pixel size, with each glyph translated along the pen position.
"""

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "glyphs.json"), encoding="utf-8") as _f:
    FONTS = json.load(_f)


def measure(s, size, style="bold", tracking=0.0):
    """Advance width in px, including letter tracking (em fraction)."""
    f = FONTS[style]
    upm = f["upm"]
    total = 0
    for ch in s:
        g = f["glyphs"].get(ch)
        total += (g["w"] if g else upm // 2) + tracking * upm
    return total * size / upm


def text(s, x, y, size, fill, style="bold", tracking=0.0, anchor="start",
         opacity=None, extra=""):
    """Render `s` with its baseline at (x, y). Returns SVG markup."""
    f = FONTS[style]
    upm = f["upm"]
    k = size / upm
    w = measure(s, size, style, tracking)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w

    parts, pen = [], 0
    for ch in s:
        g = f["glyphs"].get(ch)
        if g is None:
            pen += upm // 2 + tracking * upm
            continue
        if g["d"]:
            parts.append(f'<path d="{g["d"]}" transform="translate({pen:.0f},0)"/>')
        pen += g["w"] + tracking * upm

    op = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.5f},-{k:.5f})" '
            f'fill="{fill}"{op}{extra}>{"".join(parts)}</g>')
