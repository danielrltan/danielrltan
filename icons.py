"""
icons.py - draw small icons into the SVGs.

Two sources, both on a 24x24 grid:
  * BRAND  - real logos baked from simple-icons (icons-brand.json), filled.
  * LINE   - hand-drawn line icons for the generic stuff simple-icons doesn't
             carry (globe, envelope, LinkedIn, an editor mark, and the five
             section-header glyphs). Stroked, so they sit lightly next to the
             thin Mac chrome.

draw(name, x, y, size, color) scales the 24-unit art into a size x size box with
its top-left at (x, y).
"""

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "icons-brand.json"), encoding="utf-8") as _f:
    BRAND = json.load(_f)

# name -> (path, stroke-width in 24-units)
LINE = {
    # generic / contact
    "website":  ("M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M3.5 9h17M3.5 15h17"
                 "M12 3c-2.6 2.4-2.6 15.6 0 18M12 3c2.6 2.4 2.6 15.6 0 18", 1.7),
    "email":    ("M4 6h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7"
                 "a1 1 0 0 1 1-1M3.4 7.3l8.6 5.6 8.6-5.6", 1.7),
    "linkedin": ("M5 4.5h14A1.5 1.5 0 0 1 20.5 6v12a1.5 1.5 0 0 1-1.5 1.5H5"
                 "A1.5 1.5 0 0 1 3.5 18V6A1.5 1.5 0 0 1 5 4.5"
                 "M7.9 8.1v.02M7.9 11v5.5M11.3 16.5v-5.5"
                 "M11.3 12.7c.6-1.5 4.2-2 4.2 1.1v2.7", 1.7),
    "vscode":   ("M8.5 8 4.5 12l4 4M15.5 8l4 4-4 4M13.6 6.4l-3.2 11.2", 1.9),
    # section headers
    "about":    ("M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M12 7.6v.02M12 10.6v6", 1.8),
    "now":      ("M2.5 12h4l2.4-6.6 4 13 2.4-6.4H21.5", 1.9),
    "stack":    ("M12 3 3 8l9 5 9-5-9-5M3 12l9 5 9-5M3 16l9 5 9-5", 1.6),
    "contrib":  ("M6 20v-6.5M12 20V6M18 20v-9.5", 2.6),
    "reach":    ("M21.5 3.5 2.6 11.6l7 2.7 2.7 7 9.2-17.8M9.6 14.3 21.5 3.5", 1.7),
}


def draw(name, x, y, size, color, opacity=None):
    k = size / 24.0
    op = f' opacity="{opacity}"' if opacity is not None else ""
    g = f'transform="translate({x:.2f},{y:.2f}) scale({k:.4f})"'
    if name in BRAND:
        return f'<g {g} fill="{color}"{op}><path d="{BRAND[name]["d"]}"/></g>'
    d, sw = LINE[name]
    return (f'<g {g} fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"{op}>'
            f'<path d="{d}"/></g>')


def has(name):
    return name in BRAND or name in LINE
