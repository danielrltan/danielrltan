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
THEMES = {
    "dark": {
        "bg":  "#0d1117",
        PRI:   "#E58D7A",
        BRI:   "#f59e0b",
        TXT:   "#f5e6d3",
        GRN:   "#a3b86c",
        RED:   "#c4654b",
        DIM:   "#7a6a5e",
        "art": "#E58D7A",
    },
    "light": {
        "bg":  "#ffffff",
        PRI:   "#c2410c",
        BRI:   "#92400e",
        TXT:   "#3d2817",
        GRN:   "#65a30d",
        RED:   "#b91c1c",
        DIM:   "#a89283",
        "art": "#c2410c",
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
    "bg": "0d1117", "title": "E58D7A", "text": "f5e6d3", "icon": "f59e0b",
    "line": "f59e0b", "point": "f5e6d3", "color": "E58D7A", "label_bg": "0d1117",
}
LIGHT = {
    "bg": "ffffff", "title": "c2410c", "text": "3d2817", "icon": "92400e",
    "line": "92400e", "point": "3d2817", "color": "c2410c", "label_bg": "ffffff",
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

readme = f"""<p align="center">{neofetch}</p>

<p align="center">{activity}</p>

<p align="center">
  {visitors}
  &nbsp;
  {followers}
</p>
"""

with open("README.md", "w", encoding="utf-8", newline="\n") as f:
    f.write(readme)
print("wrote README.md")
