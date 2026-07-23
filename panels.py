"""
panels.py - the section furniture, drawn as classic Mac OS window chrome.

The whole README is framed as a desktop: every section is a window title bar
(pinstripes, close box, zoom box), the stack is a row of disk icons, and the
contact links are chunky beveled buttons. Section names borrow the System 6/7
vocabulary - GET INFO, NOW RUNNING, EXTENSIONS, DISK ACTIVITY, CHOOSER - which
keeps the whole page inside one metaphor instead of generic labels.
"""

import offbit

BAR_W, BAR_H = 880, 34


def _hex(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _shade(h, k):
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, int(c * k))) for c in _hex(h))


# ---------------------------------------------------------------- title bars
def titlebar(label, theme, width=BAR_W):
    """A System-6 style window title bar: pinstripes, close box, zoom box."""
    t = theme
    h = BAR_H
    stripes = "".join(
        f'<rect x="10" y="{7 + i*3}" width="{width-20}" height="1.4" '
        f'fill="{t["accent"]}" opacity=".55"/>'
        for i in range(7)
    )
    tw = offbit.measure(label, 15, "bold", 0.08) + 30
    plate_x = (width - tw) / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" '
        f'viewBox="0 0 {width} {h}" role="img" aria-label="{label}">'
        f'<rect width="{width}" height="{h}" rx="7" fill="{t["panel"]}" '
        f'stroke="{t["border"]}"/>'
        f'{stripes}'
        # close box (left) and zoom box (right)
        f'<rect x="12" y="{h/2-6.5}" width="13" height="13" rx="2" '
        f'fill="{t["panel"]}" stroke="{t["border"]}"/>'
        f'<rect x="{width-25}" y="{h/2-6.5}" width="13" height="13" rx="2" '
        f'fill="{t["panel"]}" stroke="{t["border"]}"/>'
        f'<rect x="{width-22}" y="{h/2-3.5}" width="7" height="7" '
        f'fill="none" stroke="{t["border"]}"/>'
        # title plate interrupts the stripes
        f'<rect x="{plate_x:.0f}" y="0" width="{tw:.0f}" height="{h}" '
        f'fill="{t["panel"]}"/>'
        f'{offbit.text(label, width/2, h/2 + 5.5, 15, t["text"], style="bold", tracking=0.08, anchor="middle")}'
        f'</svg>\n'
    )


# ---------------------------------------------------------------- now running
def now_running(lines, theme, width=BAR_W):
    """A note-window listing what's currently in progress."""
    t = theme
    row = 30
    h = 26 + len(lines) * row
    body = []
    for i, (head, sub) in enumerate(lines):
        y = 34 + i * row
        body.append(f'<rect x="22" y="{y-9}" width="7" height="7" '
                    f'fill="{t["accent"]}"/>')
        body.append(offbit.text(head, 42, y, 14.5, t["text"], style="bold"))
        body.append(offbit.text(sub, 42 + offbit.measure(head, 14.5, "bold") + 14, y,
                                12.5, t["dim"], style="regular", tracking=0.03))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" '
        f'viewBox="0 0 {width} {h}" role="img" aria-label="Currently working on">'
        f'<rect width="{width}" height="{h}" rx="7" fill="{t["panel"]}" '
        f'stroke="{t["border"]}"/>{"".join(body)}</svg>\n'
    )


# ---------------------------------------------------------------- stack
def stack(groups, theme, width=BAR_W):
    """Tech stack as rows of labelled chips, grouped by role."""
    t = theme
    pad, chip_h, gap, row_gap = 22, 26, 8, 16
    y = 26
    body = []
    for title, items in groups:
        body.append(offbit.text(title, pad, y, 12, t["accent"], style="dot",
                                tracking=0.12))
        y += 14
        x = pad
        for name in items:
            w = offbit.measure(name, 13, "bold", 0.02) + 22
            if x + w > width - pad:
                x = pad
                y += chip_h + gap
            body.append(
                f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{chip_h}" '
                f'rx="4" fill="{t["chip"]}" stroke="{t["border"]}"/>'
                f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="2.5" '
                f'rx="1" fill="{t["accent"]}" opacity=".6"/>'
            )
            body.append(offbit.text(name, x + w / 2, y + 18, 13, t["text"],
                                    style="bold", tracking=0.02, anchor="middle"))
            x += w + gap
        y += chip_h + row_gap
    h = int(y + 6)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" '
        f'viewBox="0 0 {width} {h}" role="img" aria-label="Tech stack">'
        f'<rect width="{width}" height="{h}" rx="7" fill="{t["panel"]}" '
        f'stroke="{t["border"]}"/>{"".join(body)}</svg>\n'
    )


# ---------------------------------------------------------------- chooser
def button(label, glyph, theme, width=196, height=62):
    """A chunky beveled Mac button. Individually linkable, so each is its own SVG."""
    t = theme
    bevel = _shade(t["chip"], 1.35)
    shadow = _shade(t["chip"], 0.55)
    # A faint breathing sheen. Anything stronger floods the whole face with
    # accent and the button stops reading as a button.
    css = ("@keyframes pl{0%,100%{opacity:.03}50%{opacity:.16}}"
           ".g{animation:pl 3.4s ease-in-out infinite}"
           "@media (prefers-reduced-motion:reduce){.g{animation:none;opacity:.08}}")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{label}">'
        f'<style>{css}</style>'
        f'<rect x="3" y="4" width="{width-6}" height="{height-7}" rx="9" fill="{shadow}"/>'
        f'<rect x="3" y="2" width="{width-6}" height="{height-9}" rx="9" '
        f'fill="{t["chip"]}" stroke="{t["border"]}"/>'
        f'<rect x="7" y="5" width="{width-14}" height="2" rx="1" fill="{bevel}"/>'
        f'<rect class="g" x="3" y="2" width="{width-6}" height="{height-9}" rx="9" '
        f'fill="{t["accent"]}"/>'
        f'{offbit.text(glyph, 22, height/2 + 3, 19, t["accent"], style="bold")}'
        f'{offbit.text(label, 54, height/2 + 3, 15, t["text"], style="bold", tracking=0.05)}'
        f'</svg>\n'
    )
