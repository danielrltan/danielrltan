"""
render3d.py — a tiny software 3D renderer that emits an animated SVG.

GitHub READMEs cannot execute JavaScript, so Three.js can't run there. Instead we
do the same job offline: build geometry, rotate it with real matrices, project it
through a perspective camera, depth-sort it, and bake the result into a vector
flipbook driven by CSS keyframes. GitHub renders declarative animation inside
<img>-referenced SVGs, so the scene animates, stays crisp at any zoom, and costs
a fraction of a GIF.

Scene: a wireframe Macintosh rotating over a synthwave grid — a nod to the
macintosh.glb in danielrltan.com's R3F scene.

Run:  python render3d.py   ->  hero-dark.svg, hero-light.svg
"""

import math
import random

# ---------------------------------------------------------------- camera / stage
W, H = 1200, 440
CX, CY = 600, 250            # vanishing point; also the horizon line
FOCAL = 420.0
CAM_Z = 14.0                 # camera sits at +z looking down -z, at eye height y=0
GRID_Y = -3.5                # ground plane
CELL = 3.0                   # grid cell size in world units

FRAMES = 72
DUR = 4.8                    # seconds per loop -> 15fps
SLICE = 100.0 / FRAMES       # % of the cycle each frame owns

FONT_SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"
FONT_MONO = "'Cascadia Code','JetBrains Mono','SF Mono','Consolas',monospace"


def project(p):
    """Perspective-project a world point. Returns (screen_x, screen_y, depth)."""
    x, y, z = p
    d = CAM_Z - z
    if d < 0.2:
        d = 0.2
    s = FOCAL / d
    return CX + x * s, CY - y * s, d


def rot_y(p, a):
    x, y, z = p
    ca, sa = math.cos(a), math.sin(a)
    return (x * ca + z * sa, y, -x * sa + z * ca)


def f(v):
    """Compact coordinate formatting — keeps the SVG small and git-stable."""
    return f"{v:.1f}"


# ---------------------------------------------------------------- geometry
def box(x0, x1, y0, y1, z0, z1, taper=0.0, ytaper=0.0):
    """An axis-aligned box. `taper`/`ytaper` shrink the BACK face for a CRT profile."""
    t, yt = taper, ytaper
    v = [
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),          # front
        (x0 + t, y0 + yt, z0), (x1 - t, y0 + yt, z0),
        (x1 - t, y1 - yt, z0), (x0 + t, y1 - yt, z0),                     # back
    ]
    e = [(0, 1), (1, 2), (2, 3), (3, 0),
         (4, 5), (5, 6), (6, 7), (7, 4),
         (0, 4), (1, 5), (2, 6), (3, 7)]
    return v, e


def rect_z(x0, x1, y0, y1, z):
    """A flat rectangle outline on a constant-z plane (front-panel detailing)."""
    v = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    return v, [(0, 1), (1, 2), (2, 3), (3, 0)]


MAC_SCALE = 0.78       # keeps the machine subordinate to the sun behind it


def macintosh():
    """A wireframe Macintosh 128K, assembled from primitives.

    Proportions follow the real thing (9.7"W x 13.5"H x 11"D ~= 0.72 : 1 : 0.81);
    an under-wide, under-deep box reads as a PC tower instead.
    """
    verts, edges = [], []

    def add(vs, es):
        o = len(verts)
        verts.extend(vs)
        edges.extend((a + o, b + o) for a, b in es)

    FZ = 2.80          # front plane
    D = 2.81           # detail plane, a hair proud of the front

    # main shell — tapers toward the back like the real CRT housing
    add(*box(-2.5, 2.5, -3.5, 3.5, -2.8, FZ, taper=0.34, ytaper=0.25))
    # screen bezel + inner CRT opening
    add(*rect_z(-1.75, 1.75, 0.80, 3.05, D))
    add(*rect_z(-1.52, 1.52, 1.00, 2.85, D))
    # brand plate, then the floppy slot low on the front panel
    add(*rect_z(-1.40, -0.50, 0.10, 0.35, D))
    add(*rect_z(-1.15, 1.15, -1.70, -1.45, D))
    # front feet
    add([(-1.95, -3.5, FZ), (-1.95, -3.12, FZ)], [(0, 1)])
    add([(1.95, -3.5, FZ), (1.95, -3.12, FZ)], [(0, 1)])

    screen = [(-1.52, 1.00, D - 0.02), (1.52, 1.00, D - 0.02),
              (1.52, 2.85, D - 0.02), (-1.52, 2.85, D - 0.02)]

    # Scale down, then re-seat the machine so its base rests on the grid plane.
    s = MAC_SCALE
    verts = [(x * s, y * s, z * s) for x, y, z in verts]
    screen = [(x * s, y * s, z * s) for x, y, z in screen]
    dy = GRID_Y - min(y for _, y, _ in verts)
    verts = [(x, y + dy, z) for x, y, z in verts]
    screen = [(x, y + dy, z) for x, y, z in screen]
    return verts, edges, screen


MAC_V, MAC_E, SCREEN_QUAD = macintosh()


def convex_hull(pts):
    """Monotone-chain hull — gives us the machine's silhouette in screen space."""
    p = sorted(set(pts))
    if len(p) < 3:
        return p

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for q in p:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(p):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]


# ---------------------------------------------------------------- frame builders
def mac_frame(angle, bob):
    """Return (silhouette, far_path, near_path, screen) for one rotation step."""
    def xf(v):
        x, y, z = rot_y(v, angle)
        return project((x, y + bob, z))

    pts = [xf(v) for v in MAC_V]

    near, far = [], []
    for a, b in MAC_E:
        xa, ya, da = pts[a]
        xb, yb, db = pts[b]
        seg = f"M{f(xa)},{f(ya)}L{f(xb)},{f(yb)}"
        (near if (da + db) * 0.5 < CAM_Z else far).append(seg)

    # Fill the silhouette so the machine occludes the sun behind it. Without
    # this the sun bleeds through the wireframe and the CRT never reads.
    hull = convex_hull([(round(x, 1), round(y, 1)) for x, y, _ in pts])
    sil = " ".join(f"{f(x)},{f(y)}" for x, y in hull)

    # The CRT only glows while its face is turned toward the camera.
    facing = math.cos(angle)
    screen = None
    if facing > 0.12:
        q = [xf(v) for v in SCREEN_QUAD]
        pl = " ".join(f"{f(x)},{f(y)}" for x, y, _ in q)
        screen = (pl, round(facing * 0.9, 2))

    return sil, "".join(far), "".join(near), screen


def grid_frame(offset):
    """Horizontal (receding) grid lines, scrolled toward the viewer by `offset`."""
    segs = []
    z = -66.0 + offset
    while z <= 9.0:
        xa, ya, _ = project((-42, GRID_Y, z))
        xb, yb, _ = project((42, GRID_Y, z))
        segs.append(f"M{f(xa)},{f(ya)}L{f(xb)},{f(yb)}")
        z += CELL
    return "".join(segs)


def grid_rails():
    """Converging grid lines — fixed in screen space, so emitted once."""
    segs = []
    x = -42.0
    while x <= 42.0:
        xa, ya, _ = project((x, GRID_Y, 9.0))
        xb, yb, _ = project((x, GRID_Y, -66.0))
        segs.append(f"M{f(xa)},{f(ya)}L{f(xb)},{f(yb)}")
        x += CELL
    return "".join(segs)


def starfield(theme):
    rnd = random.Random(7)          # seeded: identical output every rebuild
    out = []
    for i in range(46):
        x = rnd.uniform(20, W - 20)
        y = rnd.uniform(18, CY - 30)
        if abs(x - CX) < 130 and y > CY - 170:   # keep the sun disc clean
            continue
        r = rnd.choice([0.7, 0.9, 1.1, 1.4])
        out.append(
            f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{theme["star"]}" '
            f'class="tw" style="animation-delay:{rnd.uniform(0, 3):.1f}s"/>'
        )
    return "".join(out)


# ---------------------------------------------------------------- themes
# Backgrounds match GitHub's own page colour so the banner floats on the README
# instead of reading as a pasted-in panel. The accent is the site's #ff6b35.
THEMES = {
    "dark": {
        "bg": "#0d1117", "accent": "#ff6b35", "text": "#ffffff",
        "sun_a": "#ffb347", "sun_b": "#ff2e63",
        "grid": "#ff6b35", "mac": "#ffffff", "dim": "#6e7681",
        "star": "#ffffff", "scan": "#ffffff", "scan_op": "0.05",
        "frame": "rgba(255,255,255,0.14)",
    },
    "light": {
        "bg": "#ffffff", "accent": "#e2521a", "text": "#141414",
        "sun_a": "#f59e0b", "sun_b": "#e11d48",
        "grid": "#e2521a", "mac": "#141414", "dim": "#8a8a8a",
        "star": "#c96a3d", "scan": "#000000", "scan_op": "0.04",
        "frame": "rgba(0,0,0,0.16)",
    },
}


def build(theme):
    t = theme
    cut = SLICE * 0.985

    # --- CSS flipbook: one shared keyframe, per-frame delay picks the slice ---
    css = f"""
    .f{{opacity:0;animation:fl {DUR}s linear infinite}}
    @keyframes fl{{0%{{opacity:1}}{cut:.3f}%{{opacity:1}}{SLICE:.3f}%{{opacity:0}}100%{{opacity:0}}}}
    .tw{{animation:tw 3.2s ease-in-out infinite}}
    @keyframes tw{{0%,100%{{opacity:.25}}50%{{opacity:.9}}}}
    @media (prefers-reduced-motion:reduce){{
      .f{{animation:none}}.f0{{opacity:1}}.tw{{animation:none;opacity:.6}}
    }}
    """

    defs = f"""<defs><style>{css}</style>
<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%" stop-color="{t['sun_a']}"/><stop offset="100%" stop-color="{t['sun_b']}"/>
</linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%" stop-color="{t['bg']}" stop-opacity="1"/>
  <stop offset="55%" stop-color="{t['bg']}" stop-opacity="0"/>
</linearGradient>
<radialGradient id="halo" cx="50%" cy="50%" r="50%">
  <stop offset="0%" stop-color="{t['sun_b']}" stop-opacity=".35"/>
  <stop offset="100%" stop-color="{t['sun_b']}" stop-opacity="0"/>
</radialGradient>
<radialGradient id="crt" cx="50%" cy="45%" r="70%">
  <stop offset="0%" stop-color="{t['sun_a']}" stop-opacity=".9"/>
  <stop offset="100%" stop-color="{t['accent']}" stop-opacity=".25"/>
</radialGradient>
<mask id="slits">
  <rect width="{W}" height="{H}" fill="#fff"/>
  {"".join(f'<rect x="{CX-190}" y="{CY-88+i*17}" width="380" height="{3.5+i*1.4:.1f}" fill="#000"/>' for i in range(6))}
</mask>
<clipPath id="above"><rect x="0" y="0" width="{W}" height="{CY}"/></clipPath>
<clipPath id="below"><rect x="0" y="{CY}" width="{W}" height="{H-CY}"/></clipPath>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
  <rect width="4" height="1.4" fill="{t['scan']}" opacity="{t['scan_op']}"/>
</pattern>
</defs>"""

    # --- grid ---
    grid = [f'<g clip-path="url(#below)">',
            f'<path d="{grid_rails()}" fill="none" stroke="{t["grid"]}" '
            f'stroke-width="1" opacity=".45"/>']
    for i in range(FRAMES):
        d = grid_frame(CELL * i / FRAMES)
        cls = "f f0" if i == 0 else "f"
        grid.append(
            f'<g class="{cls}" style="animation-delay:{i*DUR/FRAMES:.3f}s">'
            f'<path d="{d}" fill="none" stroke="{t["grid"]}" stroke-width="1.15" opacity=".7"/></g>'
        )
    grid.append("</g>")
    grid.append(f'<rect x="0" y="{CY}" width="{W}" height="{H-CY}" fill="url(#fade)"/>')

    # --- macintosh flipbook ---
    # The machine sweeps back and forth rather than spinning a full turn: a 360
    # loop spends half its time showing a featureless back panel with the CRT
    # dark. Oscillating keeps the screen lit and still reads unmistakably 3D.
    mac = []
    for i in range(FRAMES):
        phase = 2 * math.pi * i / FRAMES
        a = math.radians(42) * math.sin(phase)
        bob = math.cos(phase) * 0.10
        sil, far, near, screen = mac_frame(a, bob)
        cls = "f f0" if i == 0 else "f"
        parts = [f'<g class="{cls}" style="animation-delay:{i*DUR/FRAMES:.3f}s">']
        parts.append(f'<polygon points="{sil}" fill="{t["bg"]}" opacity=".82"/>')
        parts.append(f'<path d="{far}" fill="none" stroke="{t["mac"]}" stroke-width="1" '
                     f'opacity=".30" stroke-linecap="round"/>')
        if screen:
            pl, op = screen
            parts.append(f'<polygon points="{pl}" fill="url(#crt)" opacity="{op}"/>')
        parts.append(f'<path d="{near}" fill="none" stroke="{t["mac"]}" stroke-width="1.7" '
                     f'opacity=".95" stroke-linecap="round"/>')
        parts.append("</g>")
        mac.append("".join(parts))

    # --- retro-futurist chrome: corner brackets + HUD telemetry ---
    B, M = 26, 22
    corners = "".join(
        f'<path d="{d}" fill="none" stroke="{t["frame"]}" stroke-width="1.5"/>'
        for d in (
            f"M{M},{M+B}L{M},{M}L{M+B},{M}",
            f"M{W-M-B},{M}L{W-M},{M}L{W-M},{M+B}",
            f"M{M},{H-M-B}L{M},{H-M}L{M+B},{H-M}",
            f"M{W-M-B},{H-M}L{W-M},{H-M}L{W-M},{H-M-B}",
        )
    )

    hud = "".join(
        f'<text x="{W-58}" y="{y}" text-anchor="end" font-family={FONT_MONO!r} '
        f'font-size="10.5" fill="{t["dim"]}" letter-spacing="1.6">{s}</text>'
        for y, s in ((66, "SYS / MACINTOSH 128K"), (84, "RENDER / SOFTWARE 3D"),
                     (102, "LOC / TORONTO — ON"))
    )

    title = (
        f'<text x="72" y="112" font-family={FONT_SANS!r} font-size="62" font-weight="700" '
        f'letter-spacing="-1.2" fill="{t["accent"]}" opacity=".45" '
        f'textLength="392" lengthAdjust="spacingAndGlyphs">DANIEL TAN</text>'
        f'<text x="66" y="106" font-family={FONT_SANS!r} font-size="62" font-weight="700" '
        f'letter-spacing="-1.2" fill="{t["text"]}" '
        f'textLength="392" lengthAdjust="spacingAndGlyphs">DANIEL TAN</text>'
        f'<text x="68" y="140" font-family={FONT_MONO!r} font-size="11.5" '
        f'fill="{t["dim"]}" letter-spacing="3.4">DESIGNER × SOFTWARE ENGINEER</text>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Daniel Tan — wireframe Macintosh rotating over a synthwave grid">
{defs}
<rect width="{W}" height="{H}" rx="10" fill="{t['bg']}"/>
<g clip-path="url(#above)">
  {starfield(t)}
  <ellipse cx="{CX}" cy="{CY}" rx="360" ry="180" fill="url(#halo)"/>
  <circle cx="{CX}" cy="{CY}" r="132" fill="url(#sun)" mask="url(#slits)" opacity=".92"/>
</g>
{"".join(grid)}
<rect x="{CX-330}" y="{CY-0.7}" width="660" height="1.4" fill="{t['accent']}" opacity=".38"/>
{"".join(mac)}
{title}
{hud}
<rect width="{W}" height="{H}" rx="10" fill="url(#scan)"/>
{corners}
</svg>
"""


def main():
    import os
    for name, theme in THEMES.items():
        path = f"hero-{name}.svg"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(build(theme))
        print(f"wrote {path}  ({os.path.getsize(path)/1024:.1f} KB, {FRAMES} frames)")


if __name__ == "__main__":
    main()
