import json
from datetime import date
from calendar import monthrange

with open("stats.json", encoding="utf-8") as f:
    s = json.load(f)

# --- age ---
born = date(2006, 11, 27)
today = date.today()
years = today.year - born.year
months = today.month - born.month
days = today.day - born.day
if days < 0:
    months -= 1
    prev = today.month - 1 or 12
    prev_y = today.year if today.month > 1 else today.year - 1
    days += monthrange(prev_y, prev)[1]
if months < 0:
    years -= 1
    months += 12
uptime = f"{years} years, {months} months, {days} days"

# --- languages ---
PROG   = {"TypeScript","JavaScript","Python","Go","Rust","Java","C","C++","C#","Ruby","Swift","Kotlin","PHP","Shell"}
MARKUP = {"HTML","CSS","SCSS","JSON","YAML","Markdown","Less"}
prog_langs   = [n for n,_ in s["languages_top"] if n in PROG]
markup_langs = [n for n,_ in s["languages_top"] if n in MARKUP]

# --- art (portrait ASCII; regenerate with `python img2ascii.py`) ---
with open("art.txt", encoding="utf-8") as f:
    art = f.read().split("\n")
art = [l.rstrip() for l in art]
while art and not art[-1]:
    art.pop()
ART_W = max(len(l) for l in art)
art = [l.ljust(ART_W) for l in art]

# --- semantic color keys ---
PRI, BRI, TXT, GRN, RED, DIM = "pri", "bri", "txt", "grn", "red", "dim"

def kv(label, value_segs, label_w=24):
    return [(f"{label:<{label_w}}", PRI), *value_segs]

info = []
info.append([("daniel", BRI), ("@", DIM), ("danielrltan", BRI)])
info.append([("─" * 50, PRI)])
info.append(kv("OS:",                    [("macOS, Windows, iOS", TXT)]))
info.append(kv("Uptime:",                [(uptime, TXT)]))
info.append(kv("Host:",                  [("Broadridge", TXT)]))
info.append(kv("Kernel:",                [("CS + Ivey Business student", TXT)]))
info.append(kv("IDE:",                   [("VS Code", TXT)]))
info.append([])
info.append(kv("Languages.Programming:", [(", ".join(prog_langs) or "—", TXT)]))
info.append(kv("Languages.Computer:",    [(", ".join(markup_langs) or "—", TXT)]))
info.append([])
info.append(kv("Hobbies.Physical:",      [("Taekwondo (2nd Dan), Kickboxing, Skiing", TXT)]))
info.append(kv("Hobbies.Creative:",      [("Piano, Design, Crocheting, Fashion", TXT)]))
info.append(kv("Hobbies.Tech:",          [("Workstation Setups, Speed Typing", TXT)]))
info.append(kv("Hobbies.Lifestyle:",     [("Cars & Driving, Travelling", TXT)]))
info.append([])
info.append([("─ Contact ", PRI), ("─" * 40, PRI)])
info.append(kv("Email.Personal:",        [("hello@danielrltan.com", TXT)]))
info.append(kv("Website:",               [("danielrltan.com", TXT)]))
info.append(kv("LinkedIn:",              [("danielrltan", TXT)]))
info.append(kv("Twitter:",               [("@danielrltan", TXT)]))
info.append(kv("GitHub:",                [("danielrltan", TXT)]))
info.append([])
info.append([("─ GitHub Stats ", PRI), ("─" * 35, PRI)])
info.append(kv("Repos:",                 [(f"{s['total_repos']} ({s['public_repos']} public)", TXT),
                                          ("  |  ", DIM),
                                          ("Stars: ", PRI),
                                          (f"{s['stars']}", TXT)]))
info.append(kv("Commits (this year):",   [(f"{s['commits_last_year'] + s['private_contribs_last_year']} ( ", TXT),
                                          (f"{s['commits_last_year']} public", GRN),
                                          (", ", TXT),
                                          (f"{s['private_contribs_last_year']} private", RED),
                                          (" )", TXT)]))
info.append(kv("Followers / Following:", [(f"{s['followers']} / {s['following']}", TXT)]))
info.append(kv("Code on GitHub:",        [(f"{s['languages_total_bytes']:,} bytes across {s['non_fork_repos']} repos", TXT)]))

# --- themes ---
# Palette is pulled from danielrltan.com (--accent-color #ff6b35 on near-black)
# so the profile and the site read as one system.
THEMES = {
    "dark": {
        "bg":  "#0d1117",
        PRI:   "#ff6b35",
        BRI:   "#ffb347",
        TXT:   "#f5e6d3",
        GRN:   "#a3b86c",
        RED:   "#ff2e63",
        DIM:   "#6e7681",
        "art": "#ff6b35",
    },
    "light": {
        "bg":  "#ffffff",
        PRI:   "#e2521a",
        BRI:   "#b45309",
        TXT:   "#3d2817",
        GRN:   "#4d7c0f",
        RED:   "#be123c",
        DIM:   "#8a8a8a",
        "art": "#e2521a",
    },
}

CHAR_W   = 7.6
LINE_H   = 15
PAD_X    = 18
PAD_Y    = 18
GAP_CHARS = 2
INFO_START_COL = ART_W + GAP_CHARS
FONT  = '"Cascadia Code","JetBrains Mono","Fira Code","SF Mono","Menlo","Consolas",monospace'

max_lines = max(len(art), len(info))
art_diff = max_lines - len(art)
art_top = art_diff // 2
art_bot = art_diff - art_top
art_padded  = [" " * ART_W] * art_top + list(art) + [" " * ART_W] * art_bot
info_padded = list(info) + [[]] * (max_lines - len(info))

def xml_escape(t):
    return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def build_svg(theme):
    def tspan(t, key):
        return f'<tspan xml:space="preserve" fill="{theme[key]}">{xml_escape(t)}</tspan>'

    rows = []
    for i in range(max_lines):
        y = PAD_Y + LINE_H * (i + 1)
        art_line = art_padded[i]
        art_len_px = len(art_line) * CHAR_W
        rows.append(
            f'<text x="{PAD_X}" y="{y}" textLength="{art_len_px:.2f}" '
            f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
            f'{tspan(art_line, "art")}</text>'
        )
        if info_padded[i]:
            info_xml = "".join(tspan(t, c) for t, c in info_padded[i])
            info_chars = sum(len(t) for t, _ in info_padded[i])
            info_len_px = info_chars * CHAR_W
            info_x = PAD_X + INFO_START_COL * CHAR_W
            rows.append(
                f'<text x="{info_x:.1f}" y="{y}" textLength="{info_len_px:.2f}" '
                f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
                f'{info_xml}</text>'
            )

    info_widths = [sum(len(t) for t, _ in row) for row in info_padded]
    max_info_chars = max(info_widths) if info_widths else 0
    total_cols = INFO_START_COL + max_info_chars
    width  = int(PAD_X * 2 + total_cols * CHAR_W)
    height = int(PAD_Y * 2 + LINE_H * max_lines)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family=\'{FONT}\' font-size="13" font-weight="500">\n'
        f'<rect width="100%" height="100%" rx="8" ry="8" fill="{theme["bg"]}"/>\n'
        + "\n".join(rows) +
        "\n</svg>\n"
    )

for name, theme in THEMES.items():
    with open(f"profile-{name}.svg", "w", encoding="utf-8", newline="\n") as f:
        f.write(build_svg(theme))
    print(f"wrote profile-{name}.svg")

# --- README.md with picture tags + widgets ---
USER = "danielrltan"

# Match GitHub's actual page background so widgets blend seamlessly
DARK = {
    "bg": "0d1117", "title": "ff6b35", "text": "f5e6d3", "icon": "ffb347",
    "line": "ff6b35", "point": "f5e6d3", "color": "ff6b35", "label_bg": "0d1117",
}
LIGHT = {
    "bg": "ffffff", "title": "e2521a", "text": "3d2817", "icon": "b45309",
    "line": "e2521a", "point": "3d2817", "color": "e2521a", "label_bg": "ffffff",
}

def picture(dark_url, light_url, alt):
    return (
        f'<picture>\n'
        f'  <source media="(prefers-color-scheme: dark)" srcset="{dark_url}">\n'
        f'  <img alt="{alt}" src="{light_url}">\n'
        f'</picture>'
    )

neofetch = picture("./profile-dark.svg", "./profile-light.svg", "daniel@danielrltan")

def visitors_url(t):
    return (f"https://komarev.com/ghpvc/?username={USER}"
            f"&color={t['color']}&style=for-the-badge&label=Profile+Visitors")
visitors = picture(visitors_url(DARK), visitors_url(LIGHT), "Profile visitors")

def followers_url(t):
    return (f"https://img.shields.io/github/followers/{USER}"
            f"?style=for-the-badge&color={t['color']}&labelColor={t['label_bg']}&logo=github")
followers = (
    f'<a href="https://github.com/{USER}?tab=followers">'
    + picture(followers_url(DARK), followers_url(LIGHT), "Followers")
    + '</a>'
)

def activity_url(t):
    return (f"https://github-readme-activity-graph.vercel.app/graph?username={USER}"
            f"&bg_color={t['bg']}&color={t['title']}&line={t['line']}&point={t['point']}"
            f"&area=true&hide_border=true&radius=8&custom_title=Contribution%20Graph")
activity = picture(activity_url(DARK), activity_url(LIGHT), "Contribution graph")

# --- animated 3D hero (see render3d.py) ---
import render3d
render3d.main()
hero = picture("./hero-dark.svg", "./hero-light.svg", "Daniel Tan")

# --- section furniture: Mac window chrome, stack, buttons, activity ---
import panels
import contrib

PANEL_THEMES = {
    "dark":  {"bg": "#0d1117", "panel": "#11161d", "chip": "#1b222c",
              "border": "#2b323d", "accent": "#ff6b35", "text": "#f5e6d3",
              "dim": "#8b949e", "empty": "#1c222b"},
    "light": {"bg": "#ffffff", "panel": "#fbfaf9", "chip": "#f1eeea",
              "border": "#d8d4d0", "accent": "#e2521a", "text": "#3d2817",
              "dim": "#6a6a6a", "empty": "#eae6e0"},
}

# ---- EDIT ME: what you're actually working on right now ----
NOW = [
    ("BROADRIDGE",   "software engineering"),
    ("WESTERN + IVEY", "computer science & business"),
    ("REPOHUNT",     "grounded GitHub discovery, as an MCP server"),
    ("INFINITE-AUTOCLICKER", "cross-platform clicker & macro recorder, in Rust"),
]

# ---- EDIT ME: the stack (label, icon key -> icons.py) ----
STACK = [
    ("LANGUAGES", [("TypeScript", "typescript"), ("JavaScript", "javascript"),
                   ("Python", "python"), ("Rust", "rust"), ("CSS", "css")]),
    ("BUILDING WITH", [("React", "react"), ("Three.js", "threejs"),
                       ("GSAP", "gsap"), ("Vite", "vite"), ("Node", "node")]),
    ("TOOLS", [("Git", "git"), ("VS Code", "vscode"), ("Figma", "figma")]),
]

CHOOSER = [
    ("WEBSITE",  "https://danielrltan.com",             "website"),
    ("EMAIL",    "mailto:hello@danielrltan.com",        "email"),
    ("LINKEDIN", "https://linkedin.com/in/danielrltan", "linkedin"),
    ("GITHUB",   f"https://github.com/{USER}",          "github"),
]

# (label, header icon key). Plain words, not System-6 jargon.
SECTIONS = [
    ("ABOUT",         "about"),
    ("NOW",           "now"),
    ("STACK",         "stack"),
    ("CONTRIBUTIONS", "contrib"),
    ("REACH",         "reach"),
]


def slug(name):
    return name.lower().replace(" ", "-")


def emit(basename, fn):
    """Write dark+light variants and return the <picture> markup."""
    for theme_name, th in PANEL_THEMES.items():
        with open(f"{basename}-{theme_name}.svg", "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(fn(th))
    return picture(f"./{basename}-dark.svg", f"./{basename}-light.svg", basename)


bars = {label: emit(f"bar-{slug(label)}",
                    lambda th, l=label, ic=icon: panels.titlebar(l, th, ic))
        for label, icon in SECTIONS}

now_panel = emit("panel-now", lambda th: panels.now_running(NOW, th))
stack_panel = emit("panel-stack", lambda th: panels.stack(STACK, th))
activity_panel = emit(
    "panel-activity",
    lambda th: contrib.build(s.get("calendar", []), s.get("calendar_total", 0), th))

buttons = []
for label, url, icon in CHOOSER:
    mk = emit(f"btn-{label.lower()}",
              lambda th, l=label, ic=icon: panels.button(l, ic, th))
    # No whitespace between the anchors: a newline here renders as a linked
    # gap on GitHub (the stray blue tick between buttons).
    buttons.append(f'<a href="{url}">{mk}</a>')
chooser = "".join(buttons)
print(f"wrote {(len(SECTIONS) + 3 + len(CHOOSER)) * 2} panel SVGs")

# Each title bar rides directly above its own panel inside one centered block,
# so the page reads as coupled sections instead of floating strips.
readme = f"""<p align="center">{hero}</p>

<p align="center">{bars['ABOUT']}<br />{neofetch}</p>

<p align="center">{bars['NOW']}<br />{now_panel}</p>

<p align="center">{bars['STACK']}<br />{stack_panel}</p>

<p align="center">{bars['CONTRIBUTIONS']}<br />{activity_panel}</p>

<p align="center">{bars['REACH']}<br />{chooser}</p>
"""

with open("README.md", "w", encoding="utf-8", newline="\n") as f:
    f.write(readme)
print("wrote README.md")
