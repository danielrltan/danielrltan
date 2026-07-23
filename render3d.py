"""
render3d.py - the animated hero banner.

The Macintosh itself is a z-buffered raster bake (bake_mac_png.py) embedded as a
data URI; everything around it - grid, sun, starfield, type - is vector, drawn
here. The machine FLOATS via SMIL transforms rather than a baked rotation
flipbook: a spin reads as a novelty, a slow hover reads as a product shot.

Run:  python render3d.py   ->  hero-dark.svg, hero-light.svg
"""

import base64
import math
import os
import random

import offbit

# ---------------------------------------------------------------- stage
W, H = 1200, 460
CX, CY = 640, 300            # grid vanishing point / horizon
FOCAL = 430.0
CAM_Z = 14.0
GRID_Y = -3.5
CELL = 3.0

MAC_X, MAC_Y, MAC_PX = 862, 210, 342      # centre + on-screen size of the machine
SUN_R = 190                               # must out-scale the machine, or the
                                          # sun survives only as an edge sliver
FRAMES = 48
DUR = 4.0
SLICE = 100.0 / FRAMES
FLOAT_DUR = 7.0

_HERE = os.path.dirname(os.path.abspath(__file__))


def project(p):
    x, y, z = p
    d = max(CAM_Z - z, 0.2)
    s = FOCAL / d
    return CX + x * s, CY - y * s, d


def f(v):
    return f"{v:.1f}"


def grid_frame(offset):
    segs, z = [], -66.0 + offset
    while z <= 9.0:
        xa, ya, _ = project((-46, GRID_Y, z))
        xb, yb, _ = project((46, GRID_Y, z))
        segs.append(f"M{f(xa)},{f(ya)}L{f(xb)},{f(yb)}")
        z += CELL
    return "".join(segs)


def grid_rails():
    segs, x = [], -46.0
    while x <= 46.0:
        xa, ya, _ = project((x, GRID_Y, 9.0))
        xb, yb, _ = project((x, GRID_Y, -66.0))
        segs.append(f"M{f(xa)},{f(ya)}L{f(xb)},{f(yb)}")
        x += CELL
    return "".join(segs)


def starfield(t):
    rnd = random.Random(7)
    out = []
    for _ in range(52):
        x, y = rnd.uniform(16, W - 16), rnd.uniform(14, CY - 24)
        if math.hypot(x - MAC_X, y - MAC_Y) < 210:      # keep clear of the machine
            continue
        r = rnd.choice([0.7, 0.9, 1.1, 1.4])
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{t["star"]}" '
                   f'class="tw" style="animation-delay:{rnd.uniform(0,3):.1f}s"/>')
    return "".join(out)


def mac_data_uri(name):
    with open(os.path.join(_HERE, f"mac-{name}.png"), "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")


THEMES = {
    "dark": {
        "bg": "#0d1117", "accent": "#ff6b35", "text": "#ffffff",
        "sun_a": "#ffb347", "sun_b": "#ff2e63", "grid": "#ff6b35",
        "dim": "#6e7681", "star": "#ffffff", "scan": "#ffffff", "scan_op": "0.05",
        "frame": "rgba(255,255,255,0.14)",
    },
    "light": {
        "bg": "#ffffff", "accent": "#e2521a", "text": "#141414",
        "sun_a": "#f59e0b", "sun_b": "#e11d48", "grid": "#e2521a",
        "dim": "#8a8a8a", "star": "#c96a3d", "scan": "#000000", "scan_op": "0.04",
        "frame": "rgba(0,0,0,0.16)",
    },
}


def build(theme, name):
    t = theme
    cut = SLICE * 0.985
    css = f"""
    .f{{opacity:0;animation:fl {DUR}s linear infinite}}
    @keyframes fl{{0%{{opacity:1}}{cut:.3f}%{{opacity:1}}{SLICE:.3f}%{{opacity:0}}100%{{opacity:0}}}}
    .tw{{animation:tw 3.2s ease-in-out infinite}}
    @keyframes tw{{0%,100%{{opacity:.25}}50%{{opacity:.9}}}}
    @media (prefers-reduced-motion:reduce){{
      .f{{animation:none}}.f0{{opacity:1}}.tw{{animation:none;opacity:.6}}
      .hover,.shad{{animation:none}}
    }}
    .hover{{animation:hov {FLOAT_DUR}s ease-in-out infinite}}
    @keyframes hov{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-17px)}}}}
    .tilt{{animation:tlt {FLOAT_DUR}s ease-in-out infinite;transform-origin:{MAC_X}px {MAC_Y}px}}
    @keyframes tlt{{0%,100%{{transform:rotate(-1.1deg)}}50%{{transform:rotate(1.1deg)}}}}
    .shad{{animation:shd {FLOAT_DUR}s ease-in-out infinite}}
    @keyframes shd{{0%,100%{{opacity:.42;transform:scale(1)}}
                   50%{{opacity:.24;transform:scale(.86)}}}}
    """

    defs = f"""<defs><style>{css}</style>
<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%" stop-color="{t['sun_a']}"/><stop offset="100%" stop-color="{t['sun_b']}"/>
</linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%" stop-color="{t['bg']}" stop-opacity="1"/>
  <stop offset="58%" stop-color="{t['bg']}" stop-opacity="0"/>
</linearGradient>
<radialGradient id="halo"><stop offset="0%" stop-color="{t['sun_b']}" stop-opacity=".34"/>
  <stop offset="100%" stop-color="{t['sun_b']}" stop-opacity="0"/></radialGradient>
<radialGradient id="shadow"><stop offset="0%" stop-color="{t['accent']}" stop-opacity=".85"/>
  <stop offset="100%" stop-color="{t['accent']}" stop-opacity="0"/></radialGradient>
<mask id="slits"><rect width="{W}" height="{H}" fill="#fff"/>
  {"".join(f'<rect x="{MAC_X-260}" y="{CY-124+i*24}" width="520" height="{4+i*2.0:.1f}" fill="#000"/>' for i in range(6))}
</mask>
<clipPath id="above"><rect x="0" y="0" width="{W}" height="{CY}"/></clipPath>
<clipPath id="below"><rect x="0" y="{CY}" width="{W}" height="{H-CY}"/></clipPath>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
  <rect width="4" height="1.4" fill="{t['scan']}" opacity="{t['scan_op']}"/></pattern>
</defs>"""

    grid = [f'<g clip-path="url(#below)">',
            f'<path d="{grid_rails()}" fill="none" stroke="{t["grid"]}" '
            f'stroke-width="1" opacity=".42"/>']
    for i in range(FRAMES):
        cls = "f f0" if i == 0 else "f"
        grid.append(f'<g class="{cls}" style="animation-delay:{i*DUR/FRAMES:.3f}s">'
                    f'<path d="{grid_frame(CELL*i/FRAMES)}" fill="none" '
                    f'stroke="{t["grid"]}" stroke-width="1.15" opacity=".68"/></g>')
    grid.append("</g>")
    grid.append(f'<rect x="0" y="{CY}" width="{W}" height="{H-CY}" fill="url(#fade)"/>')

    half = MAC_PX / 2
    machine = (
        f'<g class="hover"><g class="tilt">'
        f'<image href="{mac_data_uri(name)}" x="{MAC_X-half:.0f}" y="{MAC_Y-half:.0f}" '
        f'width="{MAC_PX}" height="{MAC_PX}"/></g></g>'
    )
    shadow = (f'<ellipse class="shad" cx="{MAC_X}" cy="{CY+92}" rx="126" ry="20" '
              f'fill="url(#shadow)"/>')

    title = (
        offbit.text("DANIEL TAN", 74, 178, 60, t["accent"], style="bold", opacity=".42")
        + offbit.text("DANIEL TAN", 68, 172, 60, t["text"], style="bold")
        + offbit.text("DESIGNER  x  SOFTWARE ENGINEER", 70, 208, 15,
                      t["dim"], style="regular", tracking=0.06)
    )
    meta = "".join(
        offbit.text(s, 70, 268 + i * 21, 12.5, t["dim"], style="dot", tracking=0.05)
        for i, s in enumerate(("MACINTOSH 128K / SOFTWARE 3D",
                               "TORONTO - ONTARIO"))
    )

    B, M = 26, 22
    corners = "".join(
        f'<path d="{d}" fill="none" stroke="{t["frame"]}" stroke-width="1.5"/>'
        for d in (f"M{M},{M+B}L{M},{M}L{M+B},{M}", f"M{W-M-B},{M}L{W-M},{M}L{W-M},{M+B}",
                  f"M{M},{H-M-B}L{M},{H-M}L{M+B},{H-M}",
                  f"M{W-M-B},{H-M}L{W-M},{H-M}L{W-M},{H-M-B}")
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Daniel Tan - a Macintosh floating over a neon grid">
{defs}
<rect width="{W}" height="{H}" rx="10" fill="{t['bg']}"/>
<g clip-path="url(#above)">
  {starfield(t)}
  <ellipse cx="{MAC_X}" cy="{CY}" rx="380" ry="200" fill="url(#halo)"/>
  <circle cx="{MAC_X}" cy="{CY}" r="{SUN_R}" fill="url(#sun)" mask="url(#slits)" opacity=".9"/>
</g>
{"".join(grid)}
<rect x="{MAC_X-330}" y="{CY-0.7}" width="660" height="1.4" fill="{t['accent']}" opacity=".34"/>
{shadow}
{machine}
{title}
{meta}
<rect width="{W}" height="{H}" rx="10" fill="url(#scan)"/>
{corners}
</svg>
"""


def main():
    for name, theme in THEMES.items():
        path = f"hero-{name}.svg"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(build(theme, name))
        print(f"wrote {path}  ({os.path.getsize(path)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
