"""
bake_mesh.py - LOCAL-ONLY build step.

Reads the Macintosh model from danielrltan.com and bakes it into a compact
mac-mesh.json that the profile renderer can use without shipping a 3 MB .glb
or a glTF parser into CI. Run this by hand when the model changes; the JSON
is the committed artifact.

    python bake_mesh.py [path/to/macintosh.glb]

Needs Pillow (for sampling the baked-in texture). Not needed at README build time.
"""

import json
import math
import os
import struct
import sys
from collections import Counter

GLB = sys.argv[1] if len(sys.argv) > 1 else (
    r"E:\Documents\PROJECTS\danielrltan.com\danielrltan.com\public\models\macintosh.glb"
)
OUT = "mac-mesh.json"
PALETTE_SIZE = 28          # quantise triangle colours so they group into few paths

COMP = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2),
        5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NUM = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def load_glb(path):
    d = open(path, "rb").read()
    assert d[:4] == b"glTF", "not a binary glTF"
    off, chunks = 12, {}
    while off < len(d):
        clen, ctype = struct.unpack("<II", d[off:off + 8])
        chunks[{0x4E4F534A: "JSON", 0x004E4942: "BIN"}.get(ctype, ctype)] = \
            d[off + 8: off + 8 + clen]
        off += 8 + clen + ((4 - clen % 4) % 4 if clen % 4 else 0)
    return json.loads(chunks["JSON"].decode("utf-8")), chunks["BIN"]


def read_accessor(g, blob, idx):
    a = g["accessors"][idx]
    bv = g["bufferViews"][a["bufferView"]]
    fmt, size = COMP[a["componentType"]]
    n = NUM[a["type"]]
    base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride") or (size * n)
    out = []
    for i in range(a["count"]):
        o = base + i * stride
        out.append(struct.unpack_from("<" + fmt * n, blob, o))
    return out


def mat_mul(a, b):
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4))
            for c in range(4) for r in range(4)]


def node_matrix(n):
    if "matrix" in n:
        return list(n["matrix"])
    m = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    if "scale" in n:
        s = n["scale"]
        m = mat_mul(m, [s[0], 0, 0, 0, 0, s[1], 0, 0, 0, 0, s[2], 0, 0, 0, 0, 1])
    if "rotation" in n:
        x, y, z, w = n["rotation"]
        r = [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w), 0,
             2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w), 0,
             2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y), 0,
             0, 0, 0, 1]
        m = mat_mul(r, m)
    if "translation" in n:
        t = n["translation"]
        m = mat_mul([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, t[0], t[1], t[2], 1], m)
    return m


def apply(m, p):
    x, y, z = p[:3]
    return (m[0] * x + m[4] * y + m[8] * z + m[12],
            m[1] * x + m[5] * y + m[9] * z + m[13],
            m[2] * x + m[6] * y + m[10] * z + m[14])


def main():
    g, blob = load_glb(GLB)

    # --- base colour texture, if the material has one ---
    img = None
    try:
        from PIL import Image
        import io
        mat = g["materials"][0]
        ti = mat.get("pbrMetallicRoughness", {}).get("baseColorTexture", {}).get("index")
        if ti is None:
            ti = 0
        src = g["textures"][ti]["source"]
        bv = g["bufferViews"][g["images"][src]["bufferView"]]
        raw = blob[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        print(f"texture: {img.size[0]}x{img.size[1]}")
    except Exception as e:
        print(f"no texture sampling ({e}); falling back to flat grey")

    # --- walk the scene graph, collecting world-space triangles ---
    verts, tris, uvs = [], [], []
    vmap = {}

    def visit(ni, parent):
        n = g["nodes"][ni]
        m = mat_mul(parent, node_matrix(n))
        if "mesh" in n:
            for prim in g["meshes"][n["mesh"]]["primitives"]:
                pos = read_accessor(g, blob, prim["attributes"]["POSITION"])
                uv = (read_accessor(g, blob, prim["attributes"]["TEXCOORD_0"])
                      if "TEXCOORD_0" in prim["attributes"] else None)
                idx = [i[0] for i in read_accessor(g, blob, prim["indices"])]
                for t in range(0, len(idx), 3):
                    tri = []
                    for k in idx[t:t + 3]:
                        w = apply(m, pos[k])
                        key = (round(w[0], 5), round(w[1], 5), round(w[2], 5))
                        if key not in vmap:
                            vmap[key] = len(verts)
                            verts.append(list(key))
                        tri.append(vmap[key])
                    tris.append(tri)
                    # keep all three corner UVs so we can sample the centroid
                    uvs.append([uv[k] for k in idx[t:t + 3]] if uv
                               else [(0.0, 0.0)] * 3)
        for c in n.get("children", []):
            visit(c, m)

    ident = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    for root in g["scenes"][g.get("scene", 0)]["nodes"]:
        visit(root, ident)

    # --- normalise: centre on origin, scale so height == 1 ---
    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
    bb = [(min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))]
    print(f"bbox X {bb[0][0]:.3f}..{bb[0][1]:.3f}  "
          f"Y {bb[1][0]:.3f}..{bb[1][1]:.3f}  Z {bb[2][0]:.3f}..{bb[2][1]:.3f}")
    cx = (bb[0][0] + bb[0][1]) / 2
    cy = (bb[1][0] + bb[1][1]) / 2
    cz = (bb[2][0] + bb[2][1]) / 2
    scale = 1.0 / max(bb[1][1] - bb[1][0], 1e-6)
    verts = [[round((v[0] - cx) * scale, 4),
              round((v[1] - cy) * scale, 4),
              round((v[2] - cz) * scale, 4)] for v in verts]

    # --- sample LUMINANCE per triangle at the UV centroid ---
    # Hue from this texture is noise for our purposes: danielrltan.com overrides
    # the material entirely, and sampling colour reproduced the baked-in desktop
    # screenshot as blue confetti across the CRT. Luminance keeps the useful
    # detail (vents, seams, the dark screen) and lets us recolour cleanly.
    W, H = (img.size if img else (1, 1))
    lumas = []
    for uv in uvs:
        if img is None:
            lumas.append(200)
            continue
        u = sum(c[0] for c in uv) / 3.0
        v = sum(c[1] for c in uv) / 3.0
        px = img.getpixel((int((u % 1.0) * (W - 1)), int((v % 1.0) * (H - 1))))
        lumas.append(int(0.2126 * px[0] + 0.7152 * px[1] + 0.0722 * px[2]))

    lumas = [min(255, max(0, l // 8 * 8)) for l in lumas]     # 32 levels

    # --- find the CRT geometrically ---
    # Texture luminance is useless for this: the baked map has dark vents, seams
    # and shadows all over the shell, so a luma threshold scattered "screen"
    # across the whole model. The glass is its own connected component: a thin
    # slab standing proud at the front - so detect it by shape instead.
    parent = list(range(len(verts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b, c in tris:
        union(a, b)
        union(b, c)

    comp_tris = {}
    for i, t in enumerate(tris):
        comp_tris.setdefault(find(t[0]), []).append(i)

    screen_root, best = None, None
    for root, idxs in comp_tris.items():
        if len(idxs) < 100:
            continue
        zs = [verts[k][2] for i in idxs for k in tris[i]]
        thickness, zc = max(zs) - min(zs), (max(zs) + min(zs)) / 2
        if thickness < 0.12 and zc > 0.15 and (best is None or zc > best):
            best, screen_root = zc, root
    screen = [0] * len(tris)
    if screen_root is not None:
        for i in comp_tris[screen_root]:
            screen[i] = 1
    print(f"components={len(comp_tris)}  screen tris={sum(screen)} "
          f"(z-centre {best:.2f})" if screen_root else "no screen component found")

    # --- drop sliver triangles (they render as long pale streaks) ---
    def aspect(t):
        a, b, c = (verts[i] for i in t)
        u = [b[i] - a[i] for i in range(3)]
        w = [c[i] - a[i] for i in range(3)]
        cr = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
              u[0] * w[1] - u[1] * w[0]]
        ar = 0.5 * math.sqrt(sum(x * x for x in cr))
        if ar < 1e-9:
            return 1e9
        longest = max(math.dist(a, b), math.dist(b, c), math.dist(c, a))
        return longest ** 2 / ar

    keep = [i for i, t in enumerate(tris) if aspect(t) <= 200]
    print(f"dropped {len(tris) - len(keep)} sliver triangles")
    tris = [tris[i] for i in keep]
    lumas = [lumas[i] for i in keep]
    screen = [screen[i] for i in keep]

    out = {"verts": verts, "tris": tris, "tri_luma": lumas, "tri_screen": screen}
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"wrote {OUT}: {len(verts):,} verts, {len(tris):,} tris, "
          f"{os.path.getsize(OUT)/1024:.0f} KB")


if __name__ == "__main__":
    main()
