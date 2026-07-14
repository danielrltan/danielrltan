"""Convert a portrait photo into ASCII art for the neofetch card.

Output is written to art.txt, which build_readme.py reads. Re-run this only
when you want to change the portrait; the daily GitHub Action does NOT run it
(it just reuses the committed art.txt).

Usage:  python img2ascii.py
"""
from PIL import Image, ImageOps
import os, sys

SRC   = os.path.join(os.path.dirname(__file__), "portrait-src.png")
OUT   = os.path.join(os.path.dirname(__file__), "art.txt")

W           = 54            # width in characters (more = higher detail, wider card)
BLACK       = 22            # levels black point  (below this -> solid)
WHITE       = 124           # levels white point  (above this -> blank; kills the bg)
GAMMA       = 0.95          # <1 lifts midtones slightly
CHAR_ASPECT = 0.507         # monospace cell w/h (CHAR_W 7.6 / LINE_H 15 in build_readme)
RAMP        = " .,:;-=+ox*O8%#@"   # sparse -> dense; dark pixels map to dense (see INVERT)
INVERT      = True          # card bg is dark, so dark photo areas -> dense/bright glyphs


def levels(im, black, white):
    scale = 255.0 / max(1, (white - black))
    lut = [max(0, min(255, int((i - black) * scale))) for i in range(256)]
    return im.point(lut)


def trim_blank_border(lines):
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def convert():
    im = Image.open(SRC).convert("RGBA")
    # Flatten onto white so any transparency reads as background (blank).
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    im = Image.alpha_composite(bg, im).convert("L")

    w0, h0 = im.size
    h = int(W * (h0 / w0) * CHAR_ASPECT)
    im = im.resize((W, h), Image.LANCZOS)
    im = levels(im, BLACK, WHITE)
    if GAMMA != 1.0:
        im = im.point([min(255, int((i / 255) ** GAMMA * 255)) for i in range(256)])

    n = len(RAMP)
    px = list(im.getdata())
    lines = []
    for y in range(h):
        row = px[y * W:(y + 1) * W]
        s = "".join(
            RAMP[min(n - 1, int((255 - p if INVERT else p) / 255 * (n - 1)))]
            for p in row
        )
        lines.append(s.rstrip())
    return trim_blank_border(lines)


if __name__ == "__main__":
    art = convert()
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(art) + "\n")
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(art))
    print(f"\n--- wrote {OUT}  ({max(len(l) for l in art)} x {len(art)}) ---")
