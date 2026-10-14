"""Erzeugt alle Laserdateien (SVG), Vorschauen und Mockups.  Aufruf: python3 tools/build.py"""
import math
import random
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
import designs as D  # noqa: E402
import render as R  # noqa: E402
from lasergeo import layout, write_svg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "entwuerfe"
W, H = 1600, 1200

DESIGNS = [
    ("01_schneeflocken", "Schneeflocken-Anhänger", D.snowflakes),
    ("02_steck-tannenbaum", "3D-Steck-Tannenbaum", D.tree),
    ("03_sterne", "Weihnachtssterne", D.stars),
    ("04_teelicht-laterne", "Teelicht-Laterne „Winterdorf“", D.lantern),
    ("05_geschenkanhaenger", "Geschenkanhänger-Set", D.tags),
]


def export(slug, title, parts):
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    placed, size = layout(parts, max_w=300 if slug.startswith("04") else 260)
    svg = d / f"{slug}.svg"
    write_svg(svg, placed, size, title)
    cairosvg.svg2png(url=str(svg), write_to=str(d / f"{slug}_laservorschau.png"),
                     output_width=1400, background_color="white")
    print(f"{slug}: {len(parts)} Teile, Arbeitsfläche {size[0]:.0f} x {size[1]:.0f} mm")
    return d, size


# ------------------------------------------------------------------ Mockups
def mock_flakes(parts):
    c = R.background(W, H, 1)
    c = R.snow(c)
    sc = 5.9
    for i, (p, x, y) in enumerate(zip(parts, [300, 800, 1300], [300, 430, 270])):
        img, px = R.render_part(p, sc, seed=i + 1, base=(232, 204, 160))
        hx, hy = px(*p.hang)
        pos = (x - hx, y - hy)
        R.shadow(c, img, pos, (10, 14), 10, 0.5)
        c.alpha_composite(img, (int(pos[0]), int(pos[1])))
        R.ribbon(c, (x, 0), (x, y))
    R.label(c, "Schneeflocken-Anhänger", "3 Varianten · Ø ca. 85 mm · 3 mm Pappelsperrholz")
    return c


def mock_tree(parts):
    a_part, b_part = parts[0], parts[1]
    c = R.background(W, H, 4, c1=(40, 28, 22), c2=(10, 7, 6), table=0.80)
    sc = 5.2
    a, pa = R.render_part(a_part, sc, seed=2)
    b, pb = R.render_part(b_part, sc, seed=5)
    ground = int(H * 0.86)
    cx = W // 2
    # Bodenschatten
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([cx - 380, ground - 40, cx + 420, ground + 40],
                               fill=(0, 0, 0, 150))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(25)))
    # Teil B seitlich (gestaucht), in hintere und vordere Haelfte geteilt
    bw = int(b.width * 0.36)
    bs = R.shade(b.resize((bw, b.height), Image.LANCZOS), 0.72)
    bx0, _ = pb(0, 0)
    bcx = int(bx0 * 0.36)
    by = ground - int(pb(0, 0)[1])
    back = bs.crop((0, 0, bcx, bs.height))
    front = bs.crop((bcx, 0, bs.width, bs.height))
    c.alpha_composite(back, (cx - bcx, by))
    aw = int(a.width * 0.93)
    asz = a.resize((aw, a.height), Image.LANCZOS)
    ax0, ay0 = pa(0, 0)
    c.alpha_composite(asz, (cx - int(ax0 * 0.93), ground - int(ay0)))
    c.alpha_composite(R.shade(front, 0.85), (cx, by))
    # Lichterglanz
    c.alpha_composite(R.glow_layer((W, H), (cx, ground - 520), 700, (255, 190, 110), 0.18))
    R.label(c, "3D-Steck-Tannenbaum", "2 Steckteile · Höhe 180 mm · ohne Kleber")
    return c


def mock_stars(parts):
    c = R.background(W, H, 7, c1=(70, 18, 24), c2=(18, 4, 6))
    c = R.snow(c, 120, 8)
    sc = 5.6
    for i, (p, x, y) in enumerate(zip(parts, [500, 1110], [300, 380])):
        img, px = R.render_part(p, sc, seed=10 + i, base=(234, 206, 162))
        hx, hy = px(*p.hang)
        pos = (x - hx, y - hy)
        R.shadow(c, img, pos, (12, 16), 12, 0.55)
        c.alpha_composite(img, (int(pos[0]), int(pos[1])))
        R.ribbon(c, (x, 0), (x, y), color=(214, 178, 92), width=4)
    R.label(c, "Weihnachtssterne", "Gruß-Stern mit Gravur & Filigran-Stern · 100 mm")
    return c


def mock_lantern(parts, title="Teelicht-Laterne „Winterdorf“",
                 sub="90 × 90 × 110 mm · Fingerzinken · nur für LED-Teelichter"):
    front_p, side_p = parts[0], parts[2]
    c = R.background(W, H, 9, c1=(22, 26, 44), c2=(5, 6, 12), bokeh=45, table=0.80)
    sc = 6.0
    f, pf = R.render_part(front_p, sc, seed=21, pad=0)
    s, _ = R.render_part(side_p, sc, seed=22, pad=0)
    f = R.shade(f, 0.95)
    s_img, sw, rise = R.skew_side(R.shade(s, 0.7), 0.5, 0.42)
    ground = int(H * 0.88)
    fx = W // 2 - (f.width + sw) // 2
    fy = ground - f.height
    # Bodenglanz + Schatten
    c.alpha_composite(R.glow_layer((W, H), (W // 2, ground), 620, (255, 160, 60), 0.55))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(fx - 10, ground), (fx + f.width + sw + 30, ground - rise),
                                (fx + f.width + sw + 90, ground + 20), (fx + 40, ground + 30)],
                               fill=(0, 0, 0, 120))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    # Innenleuchten hinter den Waenden
    inner = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(inner).polygon(
        [(fx, fy), (fx + sw, fy - rise), (fx + f.width + sw, fy - rise),
         (fx + f.width + sw, ground - rise), (fx + f.width, ground), (fx, ground)],
        fill=(196, 96, 30, 255))
    inner.alpha_composite(R.glow_layer((W, H), (fx + f.width * 0.55, ground - f.height * 0.25),
                                       f.height * 0.95, (255, 226, 150), 1.0))
    c.alpha_composite(inner)
    t = int(3 * sc)
    c.alpha_composite(R.joint_strips(f.width, f.height, t, 23), (fx, fy))
    js, _, _ = R.skew_side(R.joint_strips(s.width, s.height, t, 24, k=0.5), 0.5, 0.42)
    c.alpha_composite(js, (fx + f.width, fy - rise))
    c.alpha_composite(f, (fx, fy))
    c.alpha_composite(s_img, (fx + f.width, fy - rise))
    # Oberkante (Wandstaerke) andeuten
    d = ImageDraw.Draw(c)
    d.line([(fx, fy), (fx + f.width, fy)], fill=(250, 214, 160), width=3)
    d.line([(fx + f.width, fy), (fx + f.width + sw, fy - rise)], fill=(210, 170, 120), width=3)
    d.line([(fx + t, fy - 2), (fx + t + sw, fy - rise - 2), (fx + f.width + sw, fy - rise - 2)],
           fill=(255, 190, 110), width=2)
    # Bloom: Licht ueberstrahlt die Ausschnitte
    lum = c.convert("L").point(lambda v: 255 if v > 200 else 0)
    bloom = Image.new("RGBA", (W, H), (255, 170, 80, 0))
    bloom.putalpha(lum.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.55)))
    c.alpha_composite(bloom)
    R.label(c, title, sub)
    return c


def mock_tags(parts):
    c = R.background(W, H, 12, c1=(26, 48, 36), c2=(6, 14, 10), bokeh=40)
    rng = random.Random(4)
    sc = 5.3
    order = [0, 2, 4, 1, 3, 5]
    for k, idx in enumerate(order):
        p = parts[idx]
        img, px = R.render_part(p, sc, seed=30 + k, base=(230, 198, 150))
        ang = rng.uniform(-14, 14)
        hx, hy = px(*p.hang)
        cxp, cyp = img.width / 2, img.height / 2
        rot = img.rotate(ang, Image.BICUBIC, expand=True)
        a = math.radians(-ang)
        rx = (hx - cxp) * math.cos(a) - (hy - cyp) * math.sin(a) + rot.width / 2
        ry = (hx - cxp) * math.sin(a) + (hy - cyp) * math.cos(a) + rot.height / 2
        x = [300, 800, 1300, 330, 800, 1290][k]
        y = [320, 300, 330, 790, 780, 800][k]
        pos = (x - rot.width / 2, y - rot.height / 2)
        R.shadow(c, rot, pos, (10, 14), 10, 0.5)
        c.alpha_composite(rot, (int(pos[0]), int(pos[1])))
        hole = (pos[0] + rx, pos[1] + ry)
        # Kordel aus dem Loch
        d = ImageDraw.Draw(c)
        ex = hole[0] + rng.uniform(-80, 80)
        pts = [(hole[0] + (ex - hole[0]) * t + 25 * math.sin(t * 3.1),
                hole[1] - (140 if k < 3 else 70) * t) for t in [i / 20 for i in range(21)]]
        d.line(pts, fill=(120, 20, 26), width=6, joint="curve")
        d.line(pts, fill=(190, 36, 42), width=4, joint="curve")
    R.label(c, "Geschenkanhänger-Set", "6 Anhänger · 3 Formen · Gravur „Für / Von“")
    return c


def overview(images):
    o = Image.new("RGB", (2400, 1230), (16, 22, 20))
    th = [im.convert("RGB").resize((780, 585), Image.LANCZOS) for im in images]
    pos = [(20, 20), (810, 20), (1600, 20), (415, 625), (1205, 625)]
    for im, p in zip(th, pos):
        o.paste(im, p)
    return o


MOCKS = [mock_flakes, mock_tree, mock_stars, mock_lantern, mock_tags]


def main():
    imgs = []
    for (slug, title, fn), mock in zip(DESIGNS, MOCKS):
        parts = fn()
        d, _ = export(slug, title, parts)
        m = mock(parts)
        m.convert("RGB").save(d / f"{slug}_mockup.jpg", quality=92)
        imgs.append(m)
    overview(imgs).save(OUT / "uebersicht_mockups.jpg", quality=90)


if __name__ == "__main__":
    main()
