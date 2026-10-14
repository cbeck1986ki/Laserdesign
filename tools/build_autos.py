"""Auto-Serien (JDM und Luxus): Laserdateien, Vorschauen und Mockups.

Aufruf:  python3 tools/build_autos.py jdm            (alle JDM-Entwuerfe)
         python3 tools/build_autos.py luxus 03 07    (nur einzelne Entwuerfe)
"""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
import build as B  # noqa: E402
import build_saaletal as BS  # noqa: E402
import render as R  # noqa: E402
from build_saaletal import place, rotated, split_ring, table_bg, wall_bg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = BS.W, BS.H


# ------------------------------------------------------------------ Szenen-Helfer
def neon(c, center, radius, color, strength):
    c.alpha_composite(R.glow_layer((W, H), center, radius, color, strength))


def concrete_bg(seed=1, base=(70, 72, 78), light=(0.5, 0.3)):
    return wall_bg(seed, base, light)


def brick_bg(seed=4, base=(132, 70, 52)):
    rng = random.Random(seed)
    c = Image.new("RGBA", (W, H), (70, 64, 60, 255))
    d = ImageDraw.Draw(c)
    bw, bh, gap = 150, 54, 8
    for row in range(H // (bh + gap) + 2):
        off = (bw // 2) * (row % 2)
        for col in range(-1, W // (bw + gap) + 2):
            x = col * (bw + gap) - off
            y = row * (bh + gap)
            k = rng.uniform(0.75, 1.1)
            d.rectangle([x, y, x + bw, y + bh], fill=tuple(int(v * k) for v in base) + (255,))
    noise = np.random.default_rng(seed).normal(0, 9, (H, W, 1))
    arr = np.clip(np.asarray(c, np.float32)[..., :3] + noise, 0, 255)
    c = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * 0.35) / H) ** 2)
    v = np.clip(1.15 - r * 1.1, 0.25, 1)[..., None]
    arr = np.asarray(c, np.float32)
    arr[..., :3] *= v
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def clock_hands(c, ox, oy, scale, hand=(28, 28, 30), second=(200, 30, 36), needle=False):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for ang, L, wdt in ((-90 + 30 * 10 + 5, 0.24, 16), (-90 + 6 * 9, 0.36, 10)):   # 10:09 Uhr
        a = math.radians(ang)
        L *= scale
        tip = (ox + L * math.cos(a), oy + L * math.sin(a))
        back = (ox - 0.06 * scale * math.cos(a), oy - 0.06 * scale * math.sin(a))
        nx, ny = -math.sin(a) * wdt / 2, math.cos(a) * wdt / 2
        d.polygon([(back[0] + nx, back[1] + ny), (tip[0] + nx * 0.25, tip[1] + ny * 0.25),
                   (tip[0] - nx * 0.25, tip[1] - ny * 0.25), (back[0] - nx, back[1] - ny)],
                  fill=hand + (255,))
    a = math.radians(-90 + 6 * 41)
    d.line([(ox - 0.08 * scale * math.cos(a), oy - 0.08 * scale * math.sin(a)),
            (ox + 0.4 * scale * math.cos(a), oy + 0.4 * scale * math.sin(a))],
           fill=second + (255,), width=6 if needle else 4)
    d.ellipse([ox - 18, oy - 18, ox + 18, oy + 18], fill=(36, 36, 38, 255))
    d.ellipse([ox - 6, oy - 6, ox + 6, oy + 6], fill=second + (255,))
    R.shadow(c, lay, (0, 0), (8, 12), 6, 0.45)
    c.alpha_composite(lay)


def mock_wall_piece(part, sc, bg, title, sub, y=None, glow=None, seed=1, base=(228, 196, 150)):
    c = bg
    img, px = R.render_part(part, sc, seed=seed, base=base)
    pos = ((W - img.width) / 2, y if y is not None else (H - 120 - img.height) / 2)
    for g in glow or []:
        neon(c, (pos[0] + img.width * g[0], pos[1] + img.height * g[1]), g[2], g[3], g[4])
    place(c, img, pos, (12, 20), 14, 0.55)
    R.label(c, title, sub)
    return c, pos, img, px


def mock_clock(part, bg, title, sub, **kw):
    sc = 4.1
    c, pos, img, px = mock_wall_piece(part, sc, bg, title, sub, y=(H - 1066) / 2 - 40, seed=45)
    cx, cy = px(0, 0)
    clock_hands(c, pos[0] + cx, pos[1] + cy, 130 * sc * 2, **kw)
    R.label(c, title, sub)
    return c


def mock_table_set(parts, bg, title, sub, sc, spots, ring=False, seed=50, rng_seed=3, glasses=()):
    c = bg
    rng = random.Random(rng_seed)
    for i, (p, (x, y)) in enumerate(zip(parts, spots)):
        img, px = R.render_part(p, sc, seed=seed + i, base=(234, 204, 158))
        hx, hy = px(*p.hang) if p.hang else (img.width / 2, img.height / 2)
        rot, (rx, ry) = rotated(img, (hx, hy), rng.uniform(-12, 12))
        pos = (x - rot.width / 2, y - rot.height / 2)
        place(c, rot, pos, (8, 12), 8, 0.55)
        if ring and p.hang:
            split_ring(c, pos[0] + rx - 22, pos[1] + ry, 34)
    for gx, gy, gr, col in glasses:
        BS.wine_glass_top(c, gx, gy, gr, col)
    R.label(c, title, sub)
    return c


def mock_hanging(parts, bg, title, sub, sc, xs, ys, cord=(176, 30, 38), seed=90, tassel=False):
    c = bg
    for i, (p, x, y) in enumerate(zip(parts, xs, ys)):
        img, px = R.render_part(p, sc, seed=seed + i, base=(234, 206, 162))
        hx, hy = px(*p.hang)
        pos = (x - hx, y - hy)
        place(c, img, pos, (12, 18), 12, 0.55)
        R.ribbon(c, (x, 0), (x, y), color=cord, width=4)
        if tassel:
            d = ImageDraw.Draw(c)
            by = pos[1] + img.height - 10
            for k in range(-4, 5):
                d.line([(x, by), (x + k * 4, by + 90)], fill=cord, width=3)
            d.ellipse([x - 9, by - 6, x + 9, by + 10], fill=tuple(int(v * 0.8) for v in cord))
    R.label(c, title, sub)
    return c


def mock_steck(parts, bg, title, sub, sc=6.4, base=(232, 200, 154)):
    side = parts[0]
    c = bg
    img, px = R.render_part(side, sc, seed=110, base=base)
    ground = int(H * 0.80)
    x0 = (W - img.width) / 2
    gx, gy = px(0, 0)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([x0 - 40, ground - 30, x0 + img.width + 60, ground + 40], fill=(0, 0, 0, 150))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    c.alpha_composite(img, (int(x0), int(ground - gy)))
    R.label(c, title, sub)
    return c


def mock_phone_stand(parts, bg, title, sub, sc=5.6, screen=(40, 110, 200)):
    import autos as A
    from designs import MAT
    pa, pb = parts
    c = bg
    ground = int(H * 0.84)
    # Seitenansicht links: Fuss + Rueckwand als schraeges Brett + Handy
    b, pxb = R.render_part(pb, sc, seed=120)
    k = (pb.solid.bounds[2] - pb.solid.bounds[0]) / 96.0      # Skalierung des Staenders (1 = Handy)
    bx = 120 - pxb(22 * k, 0)[0] + 60
    by = ground - pxb(0, 0)[1]
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([bx + 40, ground - 20, bx + b.width + 40, ground + 26], fill=(0, 0, 0, 140))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    import jdm
    a = math.radians(jdm.ANG)
    P0 = (bx + pxb(44 * k, 0)[0], ground)
    L = (pa.solid.bounds[3] - pa.solid.bounds[1]) * sc
    d = ImageDraw.Draw(c)
    edge = [(P0[0], P0[1]), (P0[0] + L * math.cos(a), P0[1] - L * math.sin(a))]
    tA = MAT * sc
    nx, ny = math.sin(a) * tA, math.cos(a) * tA
    d.polygon([edge[0], edge[1], (edge[1][0] + nx, edge[1][1] + ny), (edge[0][0] + nx, edge[0][1] + ny)],
              fill=(196, 160, 112))
    # Handy (seitlich) lehnt vorn an der Rueckwand
    ph_t = 9 * sc
    ph_L = (150 if k < 1.2 else 240) * sc
    p0 = (P0[0] - 15 * sc * k, ground - 6 * sc)
    q0 = (p0[0] + ph_L * math.cos(a), p0[1] - ph_L * math.sin(a))
    d.polygon([p0, q0, (q0[0] + math.sin(a) * ph_t, q0[1] + math.cos(a) * ph_t),
               (p0[0] + math.sin(a) * ph_t, p0[1] + math.cos(a) * ph_t)], fill=(30, 32, 36))
    c.alpha_composite(b, (int(bx), int(by)))
    # Frontansicht rechts: Rueckwand mit Handy davor angedeutet
    img, pxa = R.render_part(pa, sc * 0.95, seed=121)
    img = img.resize((img.width, int(img.height * math.sin(a))), Image.LANCZOS)
    fx = W - img.width - 160
    fy = ground - img.height
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([fx - 20, ground - 20, fx + img.width + 50, ground + 24], fill=(0, 0, 0, 140))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    # Fuss von vorn: schmale Kante
    d = ImageDraw.Draw(c)
    cx = fx + img.width / 2
    d.rectangle([cx - tA / 2, ground - 14 * sc * k, cx + tA / 2, ground], fill=(176, 140, 96))
    c.alpha_composite(img, (int(fx), int(fy)))
    R.label(c, title, sub)
    return c


def mock_box(parts, bg, title, sub, sc=5.4, base=(226, 192, 146)):
    """Offene Kiste schraeg von vorn (ohne Innenlicht)."""
    from designs import MAT
    front_p, side_p = parts[0], parts[2]
    c = bg
    f, _ = R.render_part(front_p, sc, seed=131, pad=0, base=base)
    s_, _ = R.render_part(side_p, sc, seed=132, pad=0, base=base)
    s_img, sw, rise = R.skew_side(R.shade(s_, 0.72), 0.5, 0.42)
    ground = int(H * 0.86)
    fx = W // 2 - (f.width + sw) // 2
    fy = ground - f.height
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(fx - 10, ground), (fx + f.width + sw + 30, ground - rise),
                                (fx + f.width + sw + 90, ground + 20), (fx + 40, ground + 30)], fill=(0, 0, 0, 130))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    # Innenraum: Rueckwand-Innenseite und Boden (dunkler)
    d = ImageDraw.Draw(c)
    d.polygon([(fx, fy), (fx + sw, fy - rise), (fx + f.width + sw, fy - rise), (fx + f.width, fy)], fill=(120, 92, 64))
    t = int(MAT * sc)
    c.alpha_composite(R.joint_strips(f.width, f.height, t, 133), (fx, fy))
    js, _, _ = R.skew_side(R.joint_strips(s_.width, s_.height, t, 134, k=0.5), 0.5, 0.42)
    c.alpha_composite(js, (fx + f.width, fy - rise))
    c.alpha_composite(f, (fx, fy))
    c.alpha_composite(s_img, (fx + f.width, fy - rise))
    d = ImageDraw.Draw(c)
    d.line([(fx, fy), (fx + f.width, fy)], fill=(250, 214, 160), width=3)
    d.line([(fx + f.width, fy), (fx + f.width + sw, fy - rise)], fill=(210, 170, 120), width=3)
    d.line([(fx + t, fy - 2), (fx + t + sw, fy - rise - 2), (fx + f.width + sw, fy - rise - 2)],
           fill=(180, 140, 96), width=2)
    # Schluessel ragt heraus
    kx, ky = fx + f.width * 0.62, fy - rise * 0.4
    d.rounded_rectangle([kx - 26, ky - 70, kx + 26, ky + 10], 22, fill=(24, 24, 28))
    d.ellipse([kx - 9, ky - 52, kx + 9, ky - 34], outline=(150, 150, 156), width=3)
    R.label(c, title, sub)
    return c


def mock_display(parts, bg, title, sub, sc=5.6, paint=(176, 22, 30)):
    import autos as A
    from lasergeo import Part
    base_p, wall_p = parts
    c = bg
    b, pb = R.render_part(base_p, sc, seed=140)
    k = 0.36
    bsq = R.shade(b.resize((b.width, int(b.height * k)), Image.LANCZOS), 0.92)
    w, pw = R.render_part(wall_p, sc, seed=141)
    w = w.crop((0, 0, w.width, int(pw(0, 0)[1])))      # Zapfen stecken in der Platte
    bx = (W - bsq.width) / 2
    by = 900 - bsq.height / 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([bx - 20, by + 20, bx + bsq.width + 40, by + bsq.height + 50], fill=(0, 0, 0, 150))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))
    c.alpha_composite(R.shade(bsq, 0.5), (int(bx), int(by + 3 * sc * 0.9)))
    c.alpha_composite(bsq, (int(bx), int(by)))
    sx, sy = pb(0, 38 - 9)
    wx = bx + sx - pw(0, 0)[0]
    wy = by + sy * k - pw(0, 0)[1]
    R.shadow(c, w, (wx, wy), (20, 6), 14, 0.35)
    c.alpha_composite(w, (int(wx), int(wy)))
    # Modellauto (lackiert) auf der Platte
    g, e, s = A.car("gt", 100, 0, 0, wheels="eng")
    img, px = R.render_part(Part("Modell", g, e, s), sc, seed=142, base=paint)
    cx, cy = pb(0, -6)
    mx = bx + cx - px(50, 0)[0]
    my = by + cy * k - px(0, 0)[1]
    R.shadow(c, img, (mx, my), (24, 4), 10, 0.45)
    c.alpha_composite(img, (int(mx), int(my)))
    R.label(c, title, sub)
    return c


def mock_bookmarks(parts, bg, title, sub, sc=5.6):
    c = bg
    BS.open_book(c)
    for i, (p, x, ang) in enumerate(zip(parts, [470, 800, 1130], [-8, 2, 9])):
        img, px = R.render_part(p, sc, seed=150 + i, base=(234, 206, 162))
        hx, hy = px(*p.hang)
        rot, (rx, ry) = rotated(img, (hx, hy), ang)
        pos = (x - rot.width / 2, 600 - rot.height / 2)
        place(c, rot, pos, (10, 14), 9, 0.5)
        d = ImageDraw.Draw(c)
        hx, hy = pos[0] + rx, pos[1] + ry
        pts = [(hx + 20 * math.sin(t * 2.4) * t, hy - 150 * t) for t in [k / 24 for k in range(25)]]
        d.line(pts, fill=(20, 20, 22), width=5, joint="curve")
        d.line(pts, fill=(60, 60, 64), width=3, joint="curve")
        ex, ey = pts[-1]
        for k in range(-3, 4):
            d.line([(ex, ey), (ex + k * 6, ey - 60)], fill=(190, 160, 70), width=3)
    R.label(c, title, sub)
    return c


def mock_lantern(parts, title, sub):
    return B.mock_lantern(parts, title, sub)


# ------------------------------------------------------------------ Serien
def jdm_series():
    import jdm as J
    designs = [
        ("01_wandschild-touge", "Wandschild Touge", J.touge_sign, 400),
        ("02_wanduhr-drehzahlmesser", "Wanduhr Drehzahlmesser", J.rpm_clock, 280),
        ("03_untersetzer-garage", "Untersetzer-Set Garage", J.garage_coasters, 210),
        ("04_schluesselanhaenger-jdm", "Schlüsselanhänger JDM", J.keytags, 200),
        ("05_omamori-anhaenger", "Omamori-Rückspiegelanhänger", J.omamori, 170),
        ("06_rundbild-drift", "Rundbild Drift", J.drift_round, 260),
        ("07_steckauto-coupe", "3D-Steckauto Coupé", J.jdm_steck, 200),
        ("08_handyhalter-jdm", "Handyhalter JDM", J.phone_stand, 230),
        ("09_kennzeichen-schild", "Kennzeichen-Wandschild", J.plate_sign, 350),
        ("10_laterne-tokyo-night", "Laterne Tokyo Night", J.tokyo_lantern, 300),
    ]

    def m1(p):
        bg = concrete_bg(3, (58, 58, 66), (0.5, 0.35))
        c, *_ = mock_wall_piece(p[0], 3.9, bg, "Wandschild „Touge“",
                                "360 × 148 mm · Passstraße, Berge & 90er-Coupé",
                                y=300, glow=[(0.3, 0.6, 620, (255, 60, 170), 0.55),
                                             (0.75, 0.5, 620, (40, 200, 255), 0.5)], seed=41)
        return c

    def m2(p):
        return mock_clock(p[0], concrete_bg(8, (52, 54, 60), (0.55, 0.3)), "Wanduhr „Drehzahlmesser“",
                          "Ø 260 mm · roter Bereich ab 10 · Loch Ø 8 mm für Quarzwerk",
                          hand=(236, 236, 230), second=(230, 40, 40), needle=True)

    def m3(p):
        return mock_table_set(p, table_bg(5, (70, 60, 56)), "Untersetzer-Set „Garage“",
                              "4 Stück · Ø 95 mm · Turbo, Felge, Schaltschema, Kolben", 5.0,
                              [(420, 330), (1150, 320), (440, 830), (1170, 820)], seed=50,
                              glasses=[(800, 570, 100, (90, 46, 24)), (1490, 1070, 100, (230, 200, 90))])

    def m4(p):
        return mock_table_set(p, table_bg(9, (58, 52, 50)), "Schlüsselanhänger JDM",
                              "6 Motive · Kennzeichen, Turbo, Kolben, Schaltknauf, Felge, Coupé", 6.4,
                              [(330, 300), (800, 280), (1270, 320), (360, 740), (830, 720), (1260, 760)],
                              ring=True, seed=70)

    def m5(p):
        bg = B.R.background(W, H, 61, c1=(40, 30, 60), c2=(8, 6, 14), bokeh=60)
        return mock_hanging(p, bg, "Omamori-Rückspiegelanhänger",
                            "3 Stück · 46 × 83 mm · Verkehrssicherheit, Sieg, Glück", 6.8, [400, 800, 1200],
                            [250, 210, 250], cord=(210, 40, 50), tassel=True)

    def m6(p):
        bg = concrete_bg(12, (200, 198, 194), (0.4, 0.3))
        c, *_ = mock_wall_piece(p[0], 4.3, bg, "Rundbild „Drift“",
                                "Ø 240 mm · Seigaiha-Wellen, Sonne & Coupé", y=40, seed=47)
        return c

    def m7(p):
        bg = B.R.background(W, H, 63, c1=(30, 34, 46), c2=(6, 8, 12), bokeh=35, table=0.80)
        return mock_steck(p, bg, "3D-Steckauto Coupé", "3 Steckteile · 180 mm lang · ohne Kleber")

    def m8(p):
        bg = B.R.background(W, H, 64, c1=(36, 40, 52), c2=(8, 9, 12), bokeh=30, table=0.84)
        return mock_phone_stand(p, bg, "Handyhalter „JDM“", "2 Steckteile · 68° Neigung · Seiten- und Frontansicht")

    def m9(p):
        c, *_ = mock_wall_piece(p[0], 4.2, brick_bg(), "Kennzeichen-Wandschild",
                                "330 × 165 mm · im Stil japanischer Nummernschilder", y=200,
                                glow=[(0.5, 0.2, 700, (255, 230, 180), 0.35)], seed=49)
        return c

    def m10(p):
        return mock_lantern(p, "Laterne „Tokyo Night“",
                            "90 × 90 × 110 mm · Skyline, Passstraße, Torii · nur LED-Teelichter")

    return ROOT / "entwuerfe" / "jdm", "uebersicht_jdm.jpg", designs, [m1, m2, m3, m4, m5, m6, m7, m8, m9, m10]


def luxus_series():
    import lux as X
    designs = [
        ("01_wandschild-supersportwagen", "Wandschild Supersportwagen", X.supercar_sign, 400),
        ("02_wanduhr-tacho", "Wanduhr Tacho", X.speedo_clock, 280),
        ("03_untersetzer-rennsport", "Untersetzer-Set Rennsport", X.race_coasters, 210),
        ("04_schluesselanhaenger-luxus", "Schlüsselanhänger Luxus", X.keytags, 200),
        ("05_steckauto-supersportwagen", "3D-Steckauto Supersportwagen", X.lux_steck, 210),
        ("06_rennstrecke-wandbild", "Rennstrecken-Wandbild", X.circuit_map, 320),
        ("07_schluesselbox", "Schlüsselbox", X.key_box, 320),
        ("08_modellauto-display", "Modellauto-Display", X.model_display, 200),
        ("09_lesezeichen-sportwagen", "Lesezeichen Sportwagen", X.bookmarks, 160),
        ("10_laterne-garage", "Laterne Garage", X.lux_lantern, 300),
    ]
    gold = (222, 180, 90)

    def m1(p):
        bg = concrete_bg(21, (40, 40, 44), (0.5, 0.3))
        c, *_ = mock_wall_piece(p[0], 3.85, bg, "Wandschild „Pure Performance“",
                                "380 × 124 mm · Supersportwagen, Rennlinie & Zielflagge", y=330,
                                glow=[(0.5, 0.55, 760, (255, 200, 120), 0.55)], seed=141)
        return c

    def m2(p):
        return mock_clock(p[0], concrete_bg(22, (34, 34, 38), (0.55, 0.3)), "Wanduhr „Tacho“",
                          "Ø 260 mm · 20–240 km/h statt Ziffern · Loch Ø 8 mm für Quarzwerk",
                          hand=(236, 236, 230), second=(220, 40, 36), needle=True)

    def m3(p):
        return mock_table_set(p, table_bg(23, (52, 34, 26)), "Untersetzer-Set „Rennsport“",
                              "4 Stück · Ø 95 mm · Startnummern im Stil klassischer Rennwagen", 5.0,
                              [(420, 330), (1150, 320), (440, 830), (1170, 820)], seed=160,
                              glasses=[(800, 570, 100, (190, 120, 40)), (1490, 1070, 100, (120, 20, 30))])

    def m4(p):
        return mock_table_set(p, table_bg(24, (36, 30, 30)), "Schlüsselanhänger Luxus",
                              "6 Motive · Lenkrad, Schaltkulisse, Zielflagge, Fob, V12, Hypercar", 6.4,
                              [(330, 300), (800, 280), (1270, 320), (360, 740), (830, 720), (1260, 760)],
                              ring=True, seed=170)

    def m5(p):
        bg = B.R.background(W, H, 65, c1=(44, 40, 36), c2=(8, 7, 6), bokeh=30, table=0.80)
        return mock_steck(p, bg, "3D-Steckauto Supersportwagen", "3 Steckteile · 190 mm lang · ohne Kleber")

    def m6(p):
        bg = concrete_bg(26, (190, 190, 192), (0.35, 0.25))
        c, *_ = mock_wall_piece(p[0], 4.25, bg, "Rennstrecken-Wandbild",
                                "300 × 215 mm · fiktiver Grand-Prix-Kurs mit 13 Kurven", y=40, seed=143)
        return c

    def m7(p):
        bg = B.R.background(W, H, 67, c1=(46, 40, 34), c2=(8, 7, 6), bokeh=25, table=0.78)
        return mock_box(p, bg, "Schlüsselbox „Keys“", "150 × 80 × 56 mm · Fingerzinken · für Autoschlüssel")

    def m8(p):
        bg = B.R.background(W, H, 68, c1=(40, 40, 46), c2=(6, 6, 8), bokeh=30, table=0.70)
        return mock_display(p, bg, "Modellauto-Display", "180 × 76 mm · Rückwand gesteckt · für Modelle 1:43")

    def m9(p):
        return mock_bookmarks(p, table_bg(29, (40, 30, 26)), "Lesezeichen Sportwagen",
                              "3 Stück · 40 × 170 mm · GT, Klassiker, Hypercar")

    def m10(p):
        return mock_lantern(p, "Laterne „Garage“",
                            "90 × 90 × 110 mm · Supersportwagen, Klassiker, Luftschlitze · nur LED-Teelichter")

    return ROOT / "entwuerfe" / "luxus", "uebersicht_luxus.jpg", designs, [m1, m2, m3, m4, m5, m6, m7, m8, m9, m10]


SERIES = {"jdm": jdm_series, "luxus": luxus_series}


def main(series, only=()):
    out, ov_name, designs, mocks = SERIES[series]()
    BS.OUT = out
    imgs = []
    for (slug, title, fn, max_w), mock in zip(designs, mocks):
        if only and not any(slug.startswith(o) for o in only):
            continue
        parts = fn()
        BS.export(slug, title, parts, max_w)
        m = mock(parts)
        m.convert("RGB").save(out / slug / f"{slug}_mockup.jpg", quality=92)
        imgs.append(m)
    if not only:
        BS.overview(imgs).save(out / ov_name, quality=90)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
