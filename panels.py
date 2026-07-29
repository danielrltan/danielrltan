"""
panels.py - the section furniture, drawn as classic Mac OS window chrome.

The whole README is framed as a desktop: every section is a window title bar
(pinstripes, close box, zoom box), the stack is a row of chips carrying real
brand logos, and the contact links are chunky beveled buttons. Section labels
are plain words (About, Now, Stack, Contributions, Reach), each fronted by a
small icon, so the Mac styling carries the theme without cryptic names.
"""

import icons
import offbit

BAR_W, BAR_H = 880, 34


def _hex(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _shade(h, k):
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, int(c * k))) for c in _hex(h))


# ---------------------------------------------------------------- title bars
def titlebar(label, theme, icon=None, width=BAR_W):
    """A System-6 style window title bar: pinstripes, close box, zoom box."""
    t = theme
    h = BAR_H
    stripes = "".join(
        f'<rect x="10" y="{7 + i*3}" width="{width-20}" height="1.4" '
        f'fill="{t["accent"]}" opacity=".55"/>'
        for i in range(7)
    )
    # centre the icon + label as one group so the plate stays symmetric
    isize, gap = 17, 9
    text_w = offbit.measure(label, 15, "bold", 0.08)
    group_w = (isize + gap + text_w) if icon else text_w
    gx = (width - group_w) / 2
    plate_w = group_w + 34
    glyph = (icons.draw(icon, gx, h / 2 - isize / 2, isize, t["accent"])
             if icon else "")
    tx = gx + (isize + gap if icon else 0)
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
        # plate interrupts the stripes behind the icon + label
        f'<rect x="{(width-plate_w)/2:.0f}" y="0" width="{plate_w:.0f}" height="{h}" '
        f'fill="{t["panel"]}"/>'
        f'{glyph}'
        f'{offbit.text(label, tx, h/2 + 5.5, 15, t["text"], style="bold", tracking=0.08)}'
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
    """Tech stack as centred rows of chips, each carrying its real brand logo."""
    t = theme
    pad, chip_h, gap, row_gap = 22, 30, 9, 16
    isize, lpad, mid, rpad = 16, 12, 8, 13
    maxw = width - 2 * pad
    y = 26
    body = []
    for title, items in groups:
        # centred group heading
        body.append(offbit.text(title, width / 2, y, 12, t["accent"], style="dot",
                                tracking=0.12, anchor="middle"))
        y += 17
        # measure every chip, then greedily pack into rows
        chips = []
        for name, ikey in items:
            has_icon = icons.has(ikey)
            w = (lpad + (isize + mid if has_icon else 0)
                 + offbit.measure(name, 13, "bold", 0.02) + rpad)
            chips.append((name, ikey, has_icon, w))
        rows, row, roww = [], [], 0.0
        for c in chips:
            step = c[3] + (gap if row else 0)
            if row and roww + step > maxw:
                rows.append((row, roww))
                row, roww = [], 0.0
                step = c[3]
            row.append(c)
            roww += step
        if row:
            rows.append((row, roww))
        # place each row centred on the panel
        for row, roww in rows:
            x = (width - roww) / 2
            for name, ikey, has_icon, w in row:
                body.append(
                    f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{chip_h}" '
                    f'rx="5" fill="{t["chip"]}" stroke="{t["border"]}"/>'
                    f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="2.5" '
                    f'rx="1" fill="{t["accent"]}" opacity=".6"/>'
                )
                tx = x + lpad
                if has_icon:
                    body.append(icons.draw(ikey, x + lpad, y + (chip_h - isize) / 2,
                                           isize, t["text"]))
                    tx += isize + mid
                body.append(offbit.text(name, tx, y + chip_h / 2 + 4.5, 13,
                                        t["text"], style="bold", tracking=0.02))
                x += w + gap
            y += chip_h + gap
        y += row_gap - gap
    h = int(y + 4)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" '
        f'viewBox="0 0 {width} {h}" role="img" aria-label="Tech stack">'
        f'<rect width="{width}" height="{h}" rx="7" fill="{t["panel"]}" '
        f'stroke="{t["border"]}"/>{"".join(body)}</svg>\n'
    )


# ---------------------------------------------------------------- chooser
def button(label, icon, themes, width=196, height=62):
    """A chunky beveled Mac button. Individually linkable, so each is its own SVG.

    Unlike the bars/panels, this is ONE self-theming SVG carrying both palettes
    behind a prefers-color-scheme media query. GitHub wraps every <picture> in
    its themed-picture element, whose image renders block-level - four
    picture-based buttons can never share a row. A plain <img> stays inline,
    so the theme switch has to live inside the SVG instead.
    """
    def vars_css(t):
        return (f"--chip:{t['chip']};--border:{t['border']};"
                f"--accent:{t['accent']};--text:{t['text']};"
                f"--bevel:{_shade(t['chip'], 1.35)};"
                f"--shadow:{_shade(t['chip'], 0.55)}")
    # A faint breathing sheen. Anything stronger floods the whole face with
    # accent and the button stops reading as a button.
    css = (f":root{{{vars_css(themes['light'])}}}"
           f"@media (prefers-color-scheme:dark){{:root{{{vars_css(themes['dark'])}}}}}"
           "@keyframes pl{0%,100%{opacity:.03}50%{opacity:.16}}"
           ".g{animation:pl 3.4s ease-in-out infinite}"
           "@media (prefers-reduced-motion:reduce){.g{animation:none;opacity:.08}}")
    isize = 21
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{label}">'
        f'<style>{css}</style>'
        f'<rect x="3" y="4" width="{width-6}" height="{height-7}" rx="9" fill="var(--shadow)"/>'
        f'<rect x="3" y="2" width="{width-6}" height="{height-9}" rx="9" '
        f'fill="var(--chip)" stroke="var(--border)"/>'
        f'<rect x="7" y="5" width="{width-14}" height="2" rx="1" fill="var(--bevel)"/>'
        f'<rect class="g" x="3" y="2" width="{width-6}" height="{height-9}" rx="9" '
        f'fill="var(--accent)"/>'
        f'{icons.draw(icon, 18, (height-9)/2 + 2 - isize/2, isize, "var(--accent)")}'
        f'{offbit.text(label, 50, height/2 + 3, 15, "var(--text)", style="bold", tracking=0.05)}'
        f'</svg>\n'
    )
