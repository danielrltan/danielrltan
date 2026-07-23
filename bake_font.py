"""
bake_font.py - LOCAL-ONLY build step.

Converts OffBit glyph outlines into SVG path data (glyphs.json).

An SVG referenced by <img> cannot load a webfont, and GitHub serves README
images that way, so text must ship as vector outlines. This extracts them once;
glyphs.json is the committed artifact and CI never needs fontTools or the TTF.

    python bake_font.py
"""

import json
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

FONT_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
STYLES = {
    "bold": "OffBit-Bold.ttf",
    "regular": "OffBit-Regular.ttf",
    "dot": "OffBit-DotBold.ttf",
}
CHARS = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
         "abcdefghijklmnopqrstuvwxyz"
         "0123456789"
         " .,:;/\\|()[]{}<>-_+=*&%#@!?'\"~^$")


def main():
    out = {}
    for style, fname in STYLES.items():
        path = os.path.join(FONT_DIR, fname)
        if not os.path.exists(path):
            print(f"  MISSING {path}")
            continue
        font = TTFont(path)
        upm = font["head"].unitsPerEm
        cmap = font.getBestCmap()
        gs = font.getGlyphSet()
        hmtx = font["hmtx"]
        glyphs = {}
        missing = []
        for ch in CHARS:
            gname = cmap.get(ord(ch))
            if gname is None:
                missing.append(ch)
                continue
            # Font units are integers at upm=1000; full float precision from the
            # pen just bloats the file.
            pen = SVGPathPen(gs, ntos=lambda v: str(int(round(v))))
            gs[gname].draw(pen)
            glyphs[ch] = {"d": pen.getCommands(), "w": hmtx[gname][0]}
        out[style] = {"upm": upm, "glyphs": glyphs,
                      "ascent": font["hhea"].ascent, "descent": font["hhea"].descent}
        print(f"{style:8} upm={upm} glyphs={len(glyphs)}"
              + (f" missing={''.join(missing)!r}" if missing else ""))

    with open("glyphs.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"wrote glyphs.json ({os.path.getsize('glyphs.json')/1024:.0f} KB)")


if __name__ == "__main__":
    main()
