"""
repocards.py — self-hosted repo cards.

The usual choice here is github-readme-stats.vercel.app, but the public instance
is heavily rate-limited and returns 503 often enough that the section renders as
broken images. We draw the cards ourselves from data in stats.json instead: no
external dependency, no rate limit, and the palette matches the rest of the
profile exactly.

Exposes build_cards(featured, theme) -> SVG string.
"""

CARD_W, CARD_H, GAP, PAD = 406, 132, 14, 18
COLS = 2
FONT_MONO = "'Cascadia Code','JetBrains Mono','SF Mono','Consolas',monospace"

# GitHub's own language colours, for the languages actually in play.
LANG_COLORS = {
    "Rust": "#dea584", "TypeScript": "#3178c6", "Python": "#3572A5",
    "JavaScript": "#f1e05a", "CSS": "#563d7c", "HTML": "#e34c26",
    "Go": "#00ADD8", "C++": "#f34b7d", "Shell": "#89e051", "Swift": "#F05138",
}


def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(text, width, lines=2):
    """Greedy word wrap, ellipsised at `lines`."""
    words, out, cur = (text or "").split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if len(trial) <= width:
            cur = trial
        else:
            out.append(cur)
            cur = w
            if len(out) == lines:
                break
    if cur and len(out) < lines:
        out.append(cur)
    if len(out) == lines and (len(" ".join(out)) < len(text or "")):
        out[-1] = out[-1][: width - 1].rstrip() + "…"
    return out[:lines]


def card(r, theme, x, y):
    t = theme
    inner = CARD_W - PAD * 2
    body = []

    # panel + hairline border
    body.append(
        f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{CARD_H}" rx="8" '
        f'fill="{t["card"]}" stroke="{t["border"]}" stroke-width="1"/>'
    )
    # corner brackets, echoing the hero's HUD chrome
    b = 9
    for dx, dy, sx, sy in ((PAD - 8, PAD - 8, 1, 1), (CARD_W - PAD + 8, PAD - 8, -1, 1)):
        px, py = x + dx, y + dy
        body.append(
            f'<path d="M{px},{py+sy*b}L{px},{py}L{px+sx*b},{py}" fill="none" '
            f'stroke="{t["accent"]}" stroke-width="1.2" opacity=".55"/>'
        )

    # repo name
    body.append(
        f'<text x="{x+PAD}" y="{y+34}" font-family={FONT_MONO!r} font-size="14.5" '
        f'font-weight="700" fill="{t["accent"]}">{esc(r["name"])}</text>'
    )

    # description
    for i, line in enumerate(wrap(r.get("description") or "—", 50, 2)):
        body.append(
            f'<text x="{x+PAD}" y="{y+58+i*17}" font-family={FONT_MONO!r} '
            f'font-size="11.5" fill="{t["text"]}" opacity=".85">{esc(line)}</text>'
        )

    # footer: language dot + name, then stars
    fy = y + CARD_H - PAD - 2
    lang = r.get("language")
    cx = x + PAD
    if lang:
        body.append(f'<circle cx="{cx+4}" cy="{fy-4}" r="4.5" '
                    f'fill="{LANG_COLORS.get(lang, t["accent"])}"/>')
        body.append(
            f'<text x="{cx+16}" y="{fy}" font-family={FONT_MONO!r} font-size="11" '
            f'fill="{t["dim"]}">{esc(lang)}</text>'
        )
        cx += 16 + len(lang) * 6.7 + 18
    body.append(
        f'<text x="{cx}" y="{fy}" font-family={FONT_MONO!r} font-size="11" '
        f'fill="{t["dim"]}">★ {r.get("stars", 0)}</text>'
    )
    return "".join(body)


def build_cards(featured, theme):
    """Render `featured` into a grid. Pass a single-item list to get one card —
    that's how the README keeps each card independently clickable."""
    cols = max(1, min(COLS, len(featured)))
    rows = (len(featured) + cols - 1) // cols
    W = CARD_W * cols + GAP * (cols - 1)
    H = CARD_H * rows + GAP * (rows - 1)
    cards = "".join(
        card(r, theme,
             (i % cols) * (CARD_W + GAP),
             (i // cols) * (CARD_H + GAP))
        for i, r in enumerate(featured)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="Featured repositories">'
        f'<rect width="{W}" height="{H}" fill="{theme["bg"]}"/>{cards}</svg>\n'
    )
