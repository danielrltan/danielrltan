"""
bake_mac_png.py - LOCAL-ONLY build step.

Rasterises the Macintosh mesh with a real z-buffer and writes mac-<theme>.png
(transparent background, 2x supersampled).

Why not SVG polygons: this mesh has interpenetrating and coincident surfaces
(CRT glass sitting inside the bezel, case interior behind it). A painter's
algorithm over per-triangle depth cannot order those correctly - it produced
jagged shapes across the screen and stray slivers. A z-buffer resolves
visibility per pixel, which is simply the correct tool.

The pose is fixed, so this runs by hand and the PNG is the committed artifact;
CI never needs numpy, Pillow, or the mesh.

    python bake_mac_png.py
"""

import json
import math
import os

import numpy as np
from PIL import Image

SS = 2                      # supersample factor
W = H = 620                 # final size (so the buffer is 1240px)
YAW, PITCH, ROLL = -28.0, 12.0, -14.0
FOCAL, CAM_Z = 900.0, 9.0
MODEL_PX = 430              # on-screen height of the model, pre-supersample
LIGHT = (-0.45, 0.72, 0.62)

THEMES = {
    "dark":  {"body": "#e8e4d9", "accent": "#ff6b35", "crt": "#120c06",
              "glow": "#ff9d3c"},
    "light": {"body": "#f2efe7", "accent": "#e2521a", "crt": "#1a1208",
              "glow": "#e2761a"},
}


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float64)


def rot(p, yaw, pitch, roll):
    x, y, z = p[:, 0].copy(), p[:, 1].copy(), p[:, 2].copy()
    cy, sy = math.cos(yaw), math.sin(yaw)
    x, z = x * cy + z * sy, -x * sy + z * cy
    cx, sx = math.cos(pitch), math.sin(pitch)
    y, z = y * cx - z * sx, y * sx + z * cx
    cz, sz = math.cos(roll), math.sin(roll)
    x, y = x * cz - y * sz, x * sz + y * cz
    return np.stack([x, y, z], axis=1)


def main():
    mesh = json.load(open("mac-mesh.json", encoding="utf-8"))
    verts = np.array(mesh["verts"], dtype=np.float64)
    tris = np.array(mesh["tris"], dtype=np.int32)
    luma = np.array(mesh["tri_luma"], dtype=np.float64)
    is_scr = np.array(mesh["tri_screen"], dtype=bool)

    bw, bh = W * SS, H * SS
    world = (MODEL_PX * SS) / (FOCAL * SS / CAM_Z)
    P = rot(verts * world, math.radians(YAW), math.radians(PITCH), math.radians(ROLL))

    depth = CAM_Z - P[:, 2]
    depth = np.maximum(depth, 0.15)
    s = (FOCAL * SS) / depth
    sx = bw / 2 + P[:, 0] * s
    sy = bh / 2 - P[:, 1] * s

    # per-face normals + shading
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    L = np.array(LIGHT, dtype=np.float64)
    L /= np.linalg.norm(L)

    for name, th in THEMES.items():
        body, acc, crt = hexrgb(th["body"]), hexrgb(th["accent"]), hexrgb(th["crt"])
        glow = hexrgb(th["glow"])

        lam = np.maximum(0.0, n @ L)
        shade = (0.34 + 0.66 * lam)[:, None]
        rim = ((1.0 - np.minimum(1.0, np.abs(n[:, 2]))) ** 3 * 0.55)[:, None]
        k = (0.62 + 0.38 * (luma / 255.0))[:, None]
        col = np.clip(body[None, :] * k * shade + acc[None, :] * rim, 0, 255)
        # CRT is emissive: flat dark glass with a warm centre bloom added later
        col[is_scr] = crt[None, :]

        zbuf = np.full((bh, bw), np.inf)
        rgb = np.zeros((bh, bw, 3), dtype=np.float64)
        alpha = np.zeros((bh, bw), dtype=bool)
        scr_mask = np.zeros((bh, bw), dtype=bool)

        # screen-space winding cull
        ax, ay = sx[tris[:, 0]], sy[tris[:, 0]]
        bx, by = sx[tris[:, 1]], sy[tris[:, 1]]
        cx_, cy_ = sx[tris[:, 2]], sy[tris[:, 2]]
        area2 = (bx - ax) * (cy_ - ay) - (by - ay) * (cx_ - ax)
        front = area2 < 0

        zd = depth
        for i in np.nonzero(front)[0]:
            i0, i1, i2 = tris[i]
            x0, y0, z0 = sx[i0], sy[i0], zd[i0]
            x1, y1, z1 = sx[i1], sy[i1], zd[i1]
            x2, y2, z2 = sx[i2], sy[i2], zd[i2]
            xmin = max(int(math.floor(min(x0, x1, x2))), 0)
            xmax = min(int(math.ceil(max(x0, x1, x2))), bw - 1)
            ymin = max(int(math.floor(min(y0, y1, y2))), 0)
            ymax = min(int(math.ceil(max(y0, y1, y2))), bh - 1)
            if xmax < xmin or ymax < ymin:
                continue
            xs = np.arange(xmin, xmax + 1)
            ys = np.arange(ymin, ymax + 1)
            gx, gy = np.meshgrid(xs + 0.5, ys + 0.5)
            d = area2[i]
            w0 = ((x1 - x0) * (gy - y0) - (y1 - y0) * (gx - x0)) / d
            w1 = ((x2 - x1) * (gy - y1) - (y2 - y1) * (gx - x1)) / d
            w2 = ((x0 - x2) * (gy - y2) - (y0 - y2) * (gx - x2)) / d
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any():
                continue
            # barycentric order: w1->v0, w2->v1, w0->v2
            z = w1 * z0 + w2 * z1 + w0 * z2
            sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            win = inside & (z < sub)
            if not win.any():
                continue
            sub[win] = z[win]
            reg = rgb[ymin:ymax + 1, xmin:xmax + 1]
            reg[win] = col[i]
            alpha[ymin:ymax + 1, xmin:xmax + 1][win] = True
            if is_scr[i]:
                scr_mask[ymin:ymax + 1, xmin:xmax + 1][win] = True

        # CRT bloom: radial warm glow confined to the screen pixels
        if scr_mask.any():
            ys_, xs_ = np.nonzero(scr_mask)
            cyv, cxv = ys_.mean(), xs_.mean()
            ry = (ys_ - cyv) / max(ys_.ptp(), 1) * 2
            rx = (xs_ - cxv) / max(xs_.ptp(), 1) * 2
            r = np.sqrt(rx ** 2 + ry ** 2)
            g = np.clip(1.0 - r, 0, 1) ** 1.6
            rgb[ys_, xs_] = (rgb[ys_, xs_] * (1 - g[:, None] * 0.92)
                             + glow[None, :] * g[:, None] * 0.92)

        img = np.zeros((bh, bw, 4), dtype=np.uint8)
        img[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        img[..., 3] = np.where(alpha, 255, 0).astype(np.uint8)
        out = Image.fromarray(img, "RGBA").resize((W, H), Image.LANCZOS)
        path = f"mac-{name}.png"
        out.save(path, optimize=True)
        print(f"wrote {path}  {W}x{H}  {os.path.getsize(path)/1024:.0f} KB  "
              f"({int(front.sum()):,} front faces)")


if __name__ == "__main__":
    main()
