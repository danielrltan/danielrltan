"""
bake_icons.py - LOCAL-ONLY build step.

Pulls the brand logos we actually use out of the `simple-icons` package and
writes their path data to icons-brand.json (a committed artifact, like
glyphs.json). CI never needs node/simple-icons; it just reads the json.

Run:
    npm i simple-icons            # once, anywhere on PATH's node_modules
    SIMPLE_ICONS_DIR=/path/to/node_modules/simple-icons/icons python bake_icons.py

If SIMPLE_ICONS_DIR is unset we look for ./node_modules/simple-icons/icons.
All simple-icons artwork is 24x24 and a single <path>.
"""

import json
import os
import re

# key we use  ->  simple-icons slug
BRANDS = {
    "typescript": "typescript",
    "javascript": "javascript",
    "python":     "python",
    "rust":       "rust",
    "css":        "css",
    "react":      "react",
    "threejs":    "threedotjs",
    "gsap":       "gsap",
    "vite":       "vite",
    "node":       "nodedotjs",
    "git":        "git",
    "figma":      "figma",
    "github":     "github",
    "docker":     "docker",
    "vercel":     "vercel",
    "notion":     "notion",
    "postman":    "postman",
}

_D = re.compile(r'\sd="([^"]+)"')


def main():
    root = os.environ.get(
        "SIMPLE_ICONS_DIR",
        os.path.join("node_modules", "simple-icons", "icons"))
    out = {}
    for key, slug in BRANDS.items():
        p = os.path.join(root, f"{slug}.svg")
        with open(p, encoding="utf-8") as fh:
            svg = fh.read()
        m = _D.search(svg)
        if not m:
            raise SystemExit(f"no path in {p}")
        out[key] = {"d": m.group(1), "vb": 24}
    with open("icons-brand.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, separators=(",", ":"), ensure_ascii=False)
    print(f"wrote icons-brand.json  ({len(out)} brands, "
          f"{os.path.getsize('icons-brand.json')/1024:.1f} KB)")


if __name__ == "__main__":
    main()
