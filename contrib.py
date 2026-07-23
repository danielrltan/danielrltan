"""
contrib.py - the activity panel: an isometric landscape of commits.

Each day is an extruded bar on a shallow isometric grid, height scaled by
contribution count. A highlight wave sweeps left-to-right across the weeks via
per-column CSS animation delays, so the data itself is the motion - no mascot,
no game, nothing competing with the numbers.
"""

import math

import offbit

WK = 14.0          # px per week, along +x
DX, DY = -5.0, 8.0  # per weekday, down-and-left
CW, CD = 11.0, 6.6  # bar footprint (inset from the cell for a visible gap)
MAXH = 66.0        # tallest bar
PAD_L, PAD_T = 40, 30
WAVE = 5.0         # seconds for one sweep


def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _hex(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _css(rgb, k=1.0):
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, int(c * k))) for c in rgb)


def build(calendar, total, theme):
    weeks = len(calendar)
    flat = [v for w in calendar for v in w]
    peak = max(flat) or 1

    W = int(PAD_L * 2 + weeks * WK + abs(DX) * 7)
    H = int(PAD_T + MAXH + 7 * DY + 58)

    lo = _hex(theme["empty"])
    hi = _hex(theme["accent"])
    ox, oy = PAD_L + abs(DX) * 7, PAD_T + MAXH

    cols = {}
    for wi, week in enumerate(calendar):
        for di, v in enumerate(week):
            # Log, not sqrt: this calendar is sparse (most days zero) with one
            # huge outlier, and sqrt still crushed ordinary days into the floor.
            t = math.log1p(v) / math.log1p(peak) if v else 0.0
            h = MAXH * t
            ax = ox + wi * WK + di * DX
            ay = oy + di * DY
            bx, by = ax + CW, ay
            cx, cy = bx + DX * (CD / DY), by + CD
            ex, ey = ax + DX * (CD / DY), ay + CD

            base = _lerp(lo, hi, 0.42 + 0.58 * t) if v else lo
            top = _css(base, 1.12 if v else 0.82)  # dim the empty tiles back
            right = _css(base, 0.74)
            front = _css(base, 0.5)
            u = h

            seg = []
            if h > 0.4:
                seg.append(f'<path d="M{bx:.1f},{by:.1f}L{cx:.1f},{cy:.1f}'
                           f'L{cx:.1f},{cy-u:.1f}L{bx:.1f},{by-u:.1f}Z" fill="{right}"/>')
                seg.append(f'<path d="M{ex:.1f},{ey:.1f}L{cx:.1f},{cy:.1f}'
                           f'L{cx:.1f},{cy-u:.1f}L{ex:.1f},{ey-u:.1f}Z" fill="{front}"/>')
            seg.append(f'<path d="M{ax:.1f},{ay-u:.1f}L{bx:.1f},{by-u:.1f}'
                       f'L{cx:.1f},{cy-u:.1f}L{ex:.1f},{ey-u:.1f}Z" fill="{top}"/>')
            cols.setdefault(wi, []).append((di, "".join(seg)))

    # Draw far rows first so nearer bars overlap correctly.
    body = []
    for wi in sorted(cols):
        parts = [s for _, s in sorted(cols[wi], key=lambda p: p[0])]
        delay = (wi / max(weeks - 1, 1)) * WAVE
        body.append(f'<g class="c" style="animation-delay:{delay:.2f}s">'
                    f'{"".join(parts)}</g>')

    # month ticks along the base
    ticks = []
    for wi in range(0, weeks, 9):
        tx = ox + wi * WK
        ticks.append(f'<rect x="{tx:.0f}" y="{H-30}" width="1" height="5" '
                     f'fill="{theme["dim"]}" opacity=".5"/>')

    legend = offbit.text(f"{total} CONTRIBUTIONS  /  PEAK {peak} IN A DAY",
                         PAD_L, H - 14, 12.5, theme["dim"], style="dot", tracking=0.06)
    scale = offbit.text("52 WEEKS", W - PAD_L, H - 14, 12.5, theme["dim"],
                        style="dot", tracking=0.06, anchor="end")

    css = f"""
    .c{{animation:wv {WAVE}s linear infinite}}
    @keyframes wv{{0%,100%{{opacity:.72}}6%{{opacity:1}}14%{{opacity:.72}}}}
    @media (prefers-reduced-motion:reduce){{.c{{animation:none;opacity:.9}}}}
    """
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Contribution activity: {total} contributions over 52 weeks">'
        f'<style>{css}</style>'
        f'<rect width="{W}" height="{H}" fill="{theme["bg"]}"/>'
        f'{"".join(ticks)}{"".join(body)}{legend}{scale}</svg>\n'
    )
