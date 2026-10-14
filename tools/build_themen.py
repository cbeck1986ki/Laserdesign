"""Themenserien (Vater, Mutter, Oma, Opa, Versicherung, Finanzen): Laserdateien, Vorschauen, Mockups.

Aufruf:  python3 tools/build_themen.py                 (alle sechs Serien)
         python3 tools/build_themen.py oma              (eine Serie)
         python3 tools/build_themen.py vater 03 07      (einzelne Entwuerfe)
"""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
import build as B  # noqa: E402
import build_autos as BA  # noqa: E402
import build_saaletal as BS  # noqa: E402
import render as R  # noqa: E402
import themen as TH  # noqa: E402
from build_saaletal import place, rotated, split_ring, table_bg, wall_bg  # noqa: E402
from designs import MAT  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = BS.W, BS.H
WOOD = (232, 200, 152)


# ------------------------------------------------------------------ Hintergruende
def bg(name, seed=1):
    walls = {"dark": (52, 52, 58), "rose": (232, 208, 206), "cream": (236, 226, 206), "green": (156, 174, 152),
             "office": (204, 212, 222), "money_wall": (192, 208, 198)}
    if name in walls:
        return wall_bg(seed, walls[name], (0.5, 0.3))
    tables = {"wood_dark": (84, 58, 42), "wood_light": (150, 112, 80), "office_desk": (96, 92, 92)}
    if name in tables:
        return table_bg(seed, tables[name])
    scenes = {"dark_bokeh": ((44, 38, 30), None), "dark_table": ((44, 38, 32), 0.80),
              "rose_table": ((176, 132, 132), 0.80), "cream_table": ((186, 166, 136), 0.80),
              "green_table": ((52, 76, 54), 0.80), "green_bokeh": ((44, 70, 48), None),
              "office_table": ((84, 96, 112), 0.80), "money_table": ((34, 64, 48), 0.80)}
    c1, table = scenes[name]
    c2 = tuple(int(v * 0.22) for v in c1)
    return B.R.background(W, H, seed, c1=c1, c2=c2, bokeh=35, table=table)


def fit(parts, maxw, maxh, cap=6.4):
    b = [p.solid.bounds for p in parts]
    w = max(x[2] - x[0] for x in b)
    h = max(x[3] - x[1] for x in b)
    return min(cap, maxw / w, maxh / h)


# ------------------------------------------------------------------ Mockups
def m_wall(parts, c, title, sub, **kw):
    p = parts[0]
    sc = fit([p], 1380, 900, 6.0)
    img, px = R.render_part(p, sc, seed=11, base=WOOD)
    pos = ((W - img.width) / 2, max(30, (H - 130 - img.height) / 2))
    place(c, img, pos, (12, 20), 14, 0.5)
    R.label(c, title, sub)
    return c


def m_clock(parts, c, title, sub, **kw):
    return BA.mock_clock(parts[0], c, title, sub)


def m_table(parts, c, title, sub, ring=False, glasses=False, **kw):
    n = len(parts)
    if n <= 4:
        spots = [(420, 330), (1150, 320), (440, 830), (1170, 820)][:n]
        sc = fit(parts, 470, 420, 5.2)
    else:
        spots = [(330, 300), (800, 280), (1270, 320), (360, 740), (830, 720), (1260, 760)][:n]
        sc = fit(parts, 330, 300, 6.4)
    gl = [(800, 570, 96, (90, 50, 26)), (1490, 1070, 96, (226, 196, 110))] if glasses else []
    return BA.mock_table_set(parts, c, title, sub, sc, spots, ring=ring, seed=50, glasses=gl)


def m_hanging(parts, c, title, sub, ribbon=False, **kw):
    n = len(parts)
    sc = fit(parts, 900 / n, 700, 7.0)
    xs = [W / 2] if n == 1 else [W * (i + 1) / (n + 1) for i in range(n)]
    ys = [300] * n
    if not ribbon:
        return BA.mock_hanging(parts, c, title, sub, sc, xs, ys)
    for i, (p, x, y) in enumerate(zip(parts, xs, ys)):
        img, px = R.render_part(p, sc, seed=20 + i, base=WOOD)
        hx, hy = px(*p.hang)
        pos = (x - hx, y - hy)
        d = ImageDraw.Draw(c)
        bw = 26 * sc / 2
        for k, col in enumerate([(30, 60, 140), (240, 240, 240), (200, 30, 40), (240, 240, 240), (30, 60, 140)]):
            x0 = x - bw + k * 2 * bw / 5
            d.polygon([(x0 - 120, 0), (x0 - 120 + 2 * bw / 5, 0), (x0 + 2 * bw / 5, y), (x0, y)], fill=col)
        place(c, img, pos, (12, 18), 12, 0.55)
        d = ImageDraw.Draw(c)
        d.rectangle([x - bw, y - 2 * sc, x + bw, y + 2 * sc], fill=(30, 60, 140))
    R.label(c, title, sub)
    return c


def _photo(w, h, seed=0):
    """Platzhalter-Foto: Himmel, Huegel, Sonne, zwei Personen-Silhouetten."""
    rng = random.Random(seed)
    y = np.linspace(0, 1, h)[:, None]
    sky = np.array([120, 170, 220]) * (1 - y) + np.array([250, 220, 180]) * y
    img = Image.fromarray(np.repeat(sky[:, None, :], w, 1).reshape(h, w, 3).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.ellipse([w * 0.62, h * 0.18, w * 0.84, h * 0.18 + w * 0.22], fill=(255, 236, 170))
    d.polygon([(0, h * 0.62), (w * 0.4, h * 0.5), (w, h * 0.6), (w, h), (0, h)], fill=(110, 150, 90))
    d.polygon([(0, h * 0.75), (w * 0.6, h * 0.66), (w, h * 0.74), (w, h), (0, h)], fill=(80, 124, 70))
    for x, s in ((0.38, 1.0), (0.58, 0.72)):
        cx, base = w * x, h * 0.86
        hh = h * 0.34 * s
        d.ellipse([cx - hh * 0.13, base - hh, cx + hh * 0.13, base - hh + hh * 0.26], fill=(50, 44, 50))
        d.rounded_rectangle([cx - hh * 0.2, base - hh * 0.72, cx + hh * 0.2, base], 20, fill=(50, 44, 50))
    return img.filter(ImageFilter.GaussianBlur(1.2))


def m_frame(parts, c, title, sub, **kw):
    front = parts[0]
    sc = fit([front], 900, 860, 5.0)
    img, px = R.render_part(front, sc, seed=31, base=WOOD)
    ground = int(H * 0.86)
    pos = ((W - img.width) / 2, ground - img.height)
    x0, y0 = px(23, 23)
    pw, ph = 100 - 6, 150 - 6
    ph_img = _photo(int((pw + 4) * sc), int((ph + 4) * sc))
    c.alpha_composite(ph_img, (int(pos[0] + x0 - 2 * sc), int(pos[1] + y0 - 2 * sc)))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([pos[0] - 20, ground - 24, pos[0] + img.width + 70, ground + 26], fill=(0, 0, 0, 150))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    c.alpha_composite(img, (int(pos[0]), int(pos[1])))
    R.label(c, title, sub)
    return c


def _standing(c, part, sc, cx, ground, seed=40, crop_tabs=True, base=WOOD):
    img, px = R.render_part(part, sc, seed=seed, base=base)
    if crop_tabs:
        img = img.crop((0, 0, img.width, int(px(0, 0)[1])))
    x = cx - px(0, 0)[0]
    y = ground - px(0, 0)[1]
    c.alpha_composite(img, (int(x), int(y)))
    return x, y, img, px


def _floor_shadow(c, x0, x1, ground, a=150):
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([x0 - 30, ground - 26, x1 + 60, ground + 28], fill=(0, 0, 0, a))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))


def m_trophy(parts, c, title, sub, **kw):
    a, b = parts
    sc = fit([a], 900, 820, 5.6)
    ground = int(H * 0.84)
    ba = a.solid.bounds
    _floor_shadow(c, W / 2 + ba[0] * sc, W / 2 + ba[2] * sc, ground)
    x, y, img, px = _standing(c, a, sc, W / 2, ground, crop_tabs=False)
    # Teil B steht quer: als schmale Kante in der Mitte sichtbar
    bb = b.solid.bounds
    d = ImageDraw.Draw(c)
    t = MAT * sc
    d.rectangle([W / 2 - t / 2, ground + bb[1] * sc, W / 2 + t / 2, ground - 66 * sc], fill=(196, 160, 112))
    R.label(c, title, sub)
    return c


def m_on_base(parts, c, title, sub, upright, base_p, extra=None, **kw):
    """Stehendes Teil (mit Zapfen) auf einer liegenden Bodenplatte (perspektivisch gestaucht)."""
    sc = fit([upright, base_p], 1100, 640, 6.0)
    b, pb = R.render_part(base_p, sc, seed=60)
    k = 0.36
    bsq = R.shade(b.resize((b.width, int(b.height * k)), Image.LANCZOS), 0.92)
    bx = (W - bsq.width) / 2
    by = 900 - bsq.height / 2
    _floor_shadow(c, bx, bx + bsq.width, by + bsq.height * 0.8)
    c.alpha_composite(R.shade(bsq, 0.5), (int(bx), int(by + 3 * sc * 0.9)))
    c.alpha_composite(bsq, (int(bx), int(by)))
    return sc, bx, by, k, pb


def m_desk(parts, c, title, sub, **kw):
    plate, base = parts
    sc, bx, by, k, pb = m_on_base(parts, c, title, sub, plate, base)
    sx, sy = pb(0, 0)
    _standing(c, plate, sc, bx + sx, by + sy * k, seed=61)
    R.label(c, title, sub)
    return c


def m_cards(parts, c, title, sub, **kw):
    back, front, base = parts
    sc, bx, by, k, pb = m_on_base(parts, c, title, sub, back, base)
    sx, sy = pb(0, -8)
    _standing(c, back, sc, bx + sx, by + sy * k, seed=62)
    # Visitenkarten zwischen den Waenden
    fx, fy = pb(0, 16)
    d = ImageDraw.Draw(c)
    cw, ch = 85 * sc, 55 * sc
    cx = bx + fx
    for i in range(3):
        top = by + (sy + (fy - sy) * 0.5) * k - ch + i * 3
        d.rounded_rectangle([cx - cw / 2 + i * 2, top, cx + cw / 2 + i * 2, top + ch], 6, fill=(246, 246, 242),
                            outline=(200, 200, 196))
    d.rectangle([cx - cw / 2 + 20, top + 20, cx - cw / 2 + 140, top + 36], fill=(60, 70, 90))
    _standing(c, front, sc, bx + fx, by + fy * k, seed=63)
    R.label(c, title, sub)
    return c


def m_glasses(parts, c, title, sub, **kw):
    head, base = parts
    sc, bx, by, k, pb = m_on_base(parts, c, title, sub, head, base)
    sx, sy = pb(-10, 0)
    x, y, img, px = _standing(c, head, sc, bx + sx + 10 * sc, by + sy * k, seed=64)
    # Brille auf der Nase
    nx, ny = px(22, -96)
    d = ImageDraw.Draw(c)
    gx, gy = x + nx, y + ny
    L = 26 * sc
    ex, ey = px(-22, -92)                    # Ohr
    d.line([(gx + 0.1 * L, gy - 0.3 * L), (x + ex, y + ey)], fill=(40, 40, 44), width=max(5, int(0.9 * sc)))
    d.ellipse([gx - 0.05 * L, gy - 0.6 * L, gx + 0.3 * L, gy + 0.5 * L], outline=(30, 30, 34), width=max(6, int(sc)))
    R.label(c, title, sub)
    return c


def m_steck(parts, c, title, sub, **kw):
    sc = fit([parts[0]], 1100, 700, 6.4)
    return BA.mock_steck(parts, c, title, sub, sc=sc, base=WOOD)


def m_stand(parts, c, title, sub, **kw):
    a = parts[0].solid.bounds
    sc = min(5.6, 560 / (a[3] - a[1]))
    return BA.mock_phone_stand(parts, c, title, sub, sc=sc)


def _lid_top(lid_img, fw, sw, rise):
    """Deckelbild (Draufsicht) auf die Oberseite einer schraeg gesehenen Kiste abbilden."""
    w, h = lid_img.size
    ow, oh = int(fw + sw), int(rise)
    # Ausgabe (X, Y) -> Eingabe (x, y):  X = x*fw/w + (h - y)*sw/h ;  Y = rise - (h - y)*rise/h
    a, bb = fw / w, -sw / h
    e = rise / h
    # inverse Abbildung
    inv = np.linalg.inv(np.array([[a, bb, sw], [0, e, 0], [0, 0, 1]]))
    coeffs = tuple(inv[:2].flatten())
    return lid_img.transform((ow, oh), Image.AFFINE, coeffs, resample=Image.BICUBIC)


def m_box(parts, c, title, sub, lid=False, coins=False, **kw):
    front_p, side_p = parts[0], parts[2]
    fb = front_p.solid.bounds
    sc = min(5.4, 760 / (fb[2] - fb[0]), 520 / (fb[3] - fb[1]))
    f, _ = R.render_part(front_p, sc, seed=131, pad=0, base=WOOD)
    s_, _ = R.render_part(side_p, sc, seed=132, pad=0, base=WOOD)
    s_img, sw, rise = R.skew_side(R.shade(s_, 0.72), 0.5, 0.42)
    ground = int(H * 0.84)
    fx = W // 2 - (f.width + sw) // 2
    fy = ground - f.height
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(fx - 10, ground), (fx + f.width + sw + 30, ground - rise),
                                (fx + f.width + sw + 90, ground + 20), (fx + 40, ground + 30)], fill=(0, 0, 0, 130))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(c)
    d.polygon([(fx, fy), (fx + sw, fy - rise), (fx + f.width + sw, fy - rise), (fx + f.width, fy)], fill=(120, 92, 64))
    divs = [p for p in parts if "Trennwand" in p.name]
    for i, p in enumerate(divs):
        t = (i + 1) / (len(divs) + 1)
        img, pp = R.render_part(p, sc * 0.98, seed=150 + i, base=WOOD)
        dx, dy = fx + sw * t, fy - rise * t
        c.alpha_composite(R.shade(img, 0.9 - 0.05 * i), (int(dx + 3 * sc), int(dy - pp(0, 0)[1] + 2 * sc)))
    if coins:
        for i in range(14):
            rx, ry = fx + f.width * random.Random(i).uniform(0.4, 0.9), fy - rise * 0.3 - i * 3
            d.ellipse([rx - 40, ry - 14, rx + 40, ry + 14], fill=(200, 160, 70), outline=(150, 110, 40), width=3)
    t = int(MAT * sc)
    c.alpha_composite(R.joint_strips(f.width, f.height, t, 133), (fx, fy))
    js, _, _ = R.skew_side(R.joint_strips(s_.width, s_.height, t, 134, k=0.5), 0.5, 0.42)
    c.alpha_composite(js, (fx + f.width, fy - rise))
    c.alpha_composite(f, (fx, fy))
    c.alpha_composite(s_img, (fx + f.width, fy - rise))
    d = ImageDraw.Draw(c)
    d.line([(fx, fy), (fx + f.width, fy)], fill=(250, 214, 160), width=3)
    d.line([(fx + f.width, fy), (fx + f.width + sw, fy - rise)], fill=(210, 170, 120), width=3)
    lids = [p for p in parts if p.name.endswith("Deckel")]
    if lid and lids:
        li, _ = R.render_part(lids[0], sc, seed=140, pad=0, base=WOOD)
        top = _lid_top(li, f.width, sw, rise)
        c.alpha_composite(top, (int(fx - 2), int(fy - rise - 3 * sc)))
        d.line([(fx - 2, fy - 3 * sc), (fx + f.width, fy - 3 * sc)], fill=(176, 140, 96), width=int(3 * sc))
    R.label(c, title, sub)
    return c


def m_lantern(parts, c, title, sub, **kw):
    return B.mock_lantern(parts, title, sub)


def m_book(parts, c, title, sub, **kw):
    return BA.mock_bookmarks(parts, c, title, sub, sc=5.6)


def m_garden(parts, c, title, sub, **kw):
    rng = random.Random(3)
    c = B.R.background(W, H, 77, c1=(140, 180, 120), c2=(40, 70, 40), bokeh=30)
    soil_y = 840
    d = ImageDraw.Draw(c)
    d.rectangle([0, soil_y, W, H], fill=(86, 60, 40))
    for _ in range(3000):
        x, y = rng.uniform(0, W), rng.uniform(soil_y, H)
        d.ellipse([x, y, x + 4, y + 3], fill=(60 + rng.randint(-10, 20), 42, 28))
    sc = fit(parts, 400, 760, 4.4)
    for i, (p, x) in enumerate(zip(parts, [330, 800, 1270])):
        img, px = R.render_part(p, sc, seed=70 + i, base=WOOD)
        b = p.solid.bounds
        top = soil_y - (b[3] - b[1]) * sc * 0.62 - [0, 40, -20][i]
        vis = img.crop((0, 0, img.width, int(soil_y - top)))
        R.shadow(c, vis, (x - img.width / 2, top), (10, 12), 10, 0.45)
        c.alpha_composite(vis, (int(x - img.width / 2), int(top)))
    d = ImageDraw.Draw(c)
    for _ in range(500):
        x = rng.uniform(0, W)
        hgt = rng.uniform(20, 70)
        g = rng.randint(90, 150)
        d.line([(x, soil_y + 8), (x + rng.uniform(-14, 14), soil_y - hgt)], fill=(50, g, 50), width=3)
    R.label(c, title, sub)
    return c


def m_puzzle(parts, c, title, sub, **kw):
    b = [p.solid.bounds for p in parts]
    x0, y0 = min(v[0] for v in b), min(v[1] for v in b)
    x1, y1 = max(v[2] for v in b), max(v[3] for v in b)
    sc = min(4.0, 1100 / (x1 - x0), 900 / (y1 - y0))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for i, p in enumerate(parts):
        img, px = R.render_part(p, sc, seed=80 + i, base=WOOD)
        pc = p.solid.centroid
        ex = 1.06 if i % 3 == 1 else 1.0
        ox, oy = px(p.solid.bounds[0], p.solid.bounds[1])
        X = W / 2 + ((p.solid.bounds[0] - cx) * ex) * sc - ox + (pc.x - cx) * 0.08 * sc
        Y = (H - 120) / 2 + (p.solid.bounds[1] - cy) * sc - oy + (pc.y - cy) * 0.08 * sc
        place(c, img, (X, Y), (8, 12), 8, 0.5)
    R.label(c, title, sub)
    return c


def m_game(parts, c, title, sub, **kw):
    board, stones = parts[0], parts[1:]
    sc = 3.4
    img, px = R.render_part(board, sc, seed=90, base=WOOD)
    pos = (200, (H - 120 - img.height) / 2)
    place(c, img, pos, (10, 16), 12, 0.5)
    S = 240.0
    pts = [(S / 2 + S * r * dx, S / 2 + S * r * dy) for r in (0.40, 0.27, 0.14) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
    rng = random.Random(5)
    used = rng.sample(range(len(pts)), 10)
    for i, k in enumerate(used):
        st = stones[0 if i % 2 else 9]
        si, sp = R.render_part(st, sc, seed=91 + i, base=WOOD if i % 2 else (196, 150, 104))
        x, y = px(*pts[k])
        place(c, si, (pos[0] + x - si.width / 2, pos[1] + y - si.height / 2), (5, 7), 5, 0.6)
    for i in range(8):
        st = stones[0 if i % 2 else 9]
        si, _ = R.render_part(st, sc, seed=120 + i, base=WOOD if i % 2 else (196, 150, 104))
        place(c, si, (1150 + (i % 2) * 110, 230 + (i // 2) * 110), (5, 7), 5, 0.6)
    R.label(c, title, sub)
    return c


def m_tree(parts, c, title, sub, **kw):
    tree, foot = parts
    sc = fit([tree], 900, 800, 5.0)
    ground = int(H * 0.86)
    tb = tree.solid.bounds
    _floor_shadow(c, W / 2 + tb[0] * sc, W / 2 + tb[2] * sc, ground)
    # Fuss quer: von vorn nur als schmale Kante zu sehen
    d = ImageDraw.Draw(c)
    fb = foot.solid.bounds
    x, y, img, px = _standing(c, tree, sc, W / 2, ground, crop_tabs=False)
    d = ImageDraw.Draw(c)
    t = MAT * sc
    d.rectangle([W / 2 - t / 2, ground - 36 * sc, W / 2 + t / 2, ground], fill=(176, 140, 96))
    # gefaltete Geldscheine in den Schlitzen
    from lasergeo import polar
    tips = [polar(L, ang, 0, yy) for ang, L, yy in [(-150, 62, -78), (-125, 70, -92), (-100, 60, -100), (-80, 60, -100),
                                                    (-55, 70, -92), (-30, 62, -78), (-140, 40, -60), (-40, 40, -60)]]
    for i, (tx, ty) in enumerate(tips):
        X, Y = x + px(tx, ty)[0], y + px(tx, ty)[1]
        col = [(120, 170, 200), (200, 150, 110), (150, 190, 140)][i % 3]
        poly = [(X - 26, Y - 70), (X + 26, Y - 70), (X + 14, Y + 4), (X - 14, Y + 4)]
        d.polygon(poly, fill=col, outline=tuple(int(v * 0.7) for v in col))
        d.line([(X, Y - 66), (X, Y)], fill=tuple(int(v * 0.8) for v in col), width=2)
    R.label(c, title, sub)
    return c


def _beer_bottle(c, x, ground, sc):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    col = (96, 52, 20, 255)
    bw = 62 * sc / 2
    body_top = ground - 150 * sc
    d.rounded_rectangle([x - bw, body_top, x + bw, ground], 30, fill=col)
    nw = 26 * sc / 2
    sh_top = body_top - 40 * sc
    d.polygon([(x - bw, body_top + 10), (x - nw, sh_top), (x + nw, sh_top), (x + bw, body_top + 10)], fill=col)
    nt = sh_top - 55 * sc
    d.rectangle([x - nw, nt, x + nw, sh_top + 2], fill=col)
    d.rounded_rectangle([x - nw - 2 * sc, nt - 6 * sc, x + nw + 2 * sc, nt + 4 * sc], 4, fill=(200, 170, 60, 255))
    d.rectangle([x - bw * 0.7, body_top + 30 * sc, x - bw * 0.5, ground - 30 * sc], fill=(255, 255, 255, 40))
    c.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1)))
    return x, sh_top, nw


def m_bottles(parts, c, title, sub, **kw):
    ground = int(H * 0.92)
    sc = 3.0
    for i, (p, x) in enumerate(zip(parts, [330, 800, 1270])):
        nx, sh_top, nw = _beer_bottle(c, x, ground, sc)
        img, px = R.render_part(p, sc, seed=100 + i, base=WOOD)
        hx, hy = px(*p.hang)
        cy = sh_top - 10 * sc
        place(c, img, (nx - hx, cy - hy), (10, 14), 10, 0.5)
        d = ImageDraw.Draw(c)
        rr_ = 15 * sc
        d.rectangle([nx - nw, cy - rr_ - 7 * sc - 2, nx + nw, cy - rr_ + 2], fill=(96, 52, 20))
    R.label(c, title, sub)
    return c


def export(slug, title, parts, max_w):
    """Wie BS.export, verteilt aber auf mehrere Platten, wenn alles zusammen nicht auf den D1 Pro passt."""
    import cairosvg
    from lasergeo import layout, write_svg
    groups, cur = [], []
    for p in parts:
        trial = cur + [p]
        _, size = layout(trial, max_w=max_w)
        if cur and (size[0] > 432 or size[1] > 406):
            groups.append(cur)
            cur = [p]
        else:
            cur = trial
    groups.append(cur)
    if len(groups) == 1:
        return BS.export(slug, title, parts, max_w)
    d = BS.OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    for i, grp in enumerate(groups, 1):
        placed, size = layout(grp, max_w=max_w)
        assert size[0] <= 432 and size[1] <= 406, (slug, size)
        svg = d / f"{slug}_platte{i}.svg"
        write_svg(svg, placed, size, f"{title} (Platte {i}/{len(groups)})")
        cairosvg.svg2png(url=str(svg), write_to=str(d / f"{slug}_platte{i}_laservorschau.png"),
                         output_width=1400, background_color="white")
        print(f"{slug} Platte {i}: {len(grp)} Teile, Arbeitsfläche {size[0]:.0f} x {size[1]:.0f} mm")


MOCKS = {"wall": m_wall, "clock": m_clock, "table": m_table, "hanging": m_hanging, "frame": m_frame,
         "trophy": m_trophy, "desk": m_desk, "cards": m_cards, "glasses": m_glasses, "steck": m_steck,
         "stand": m_stand, "box": m_box, "lantern": m_lantern, "book": m_book, "garden": m_garden,
         "puzzle": m_puzzle, "game": m_game, "tree": m_tree, "bottles": m_bottles}


def build_series(key, only=()):
    key_, label, designs = TH.THEMEN[key]()
    out = ROOT / "entwuerfe" / key
    BS.OUT = out
    imgs = []
    for i, (slug, title, fn, max_w, (kind, opts)) in enumerate(designs):
        if only and not any(slug.startswith(o) for o in only):
            continue
        parts = fn()
        export(slug, title, parts, max_w)
        opts = dict(opts)
        bgname = opts.pop("bg", "dark")
        c = bg(bgname, seed=10 + i) if kind not in ("lantern", "garden") else None
        m = MOCKS[kind](parts, c, title, opts.pop("sub", ""), **opts)
        m.convert("RGB").save(out / slug / f"{slug}_mockup.jpg", quality=90)
        imgs.append(m)
    if not only:
        BS.overview(imgs).save(out / f"uebersicht_{key}.jpg", quality=88)


if __name__ == "__main__":
    args = sys.argv[1:]
    keys = [args[0]] if args and args[0] in TH.THEMEN else list(TH.THEMEN)
    for k in keys:
        build_series(k, args[1:] if args and args[0] in TH.THEMEN else ())
