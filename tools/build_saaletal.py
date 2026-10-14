"""Saaletal-Serie: Laserdateien (SVG), Vorschauen und Mockups.  Aufruf: python3 tools/build_saaletal.py"""
import math
import random
import sys
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import build as B  # noqa: E402
import render as R  # noqa: E402
import saaletal as S  # noqa: E402
from lasergeo import FONT_DIR, layout, write_svg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "entwuerfe" / "saaletal"
W, H = 1600, 1200

DESIGNS = [  # slug, Titel, Geometrie, max. Zeilenbreite fuer die Anordnung
    ("01_skyline-saaletal", "Wandschild Skyline Saaletal", S.skyline, 400),
    ("02_flusskarte-saale", "Flusskarte Fränkische Saale", S.river_map, 320),
    ("03_wanduhr-saaletal", "Wanduhr Saaletal-Zeit", S.wall_clock, 280),
    ("04_untersetzer-saaletal", "Untersetzer-Set Saaletal", S.coasters, 210),
    ("05_bocksbeutel-anhaenger", "Bocksbeutel-Flaschenanhänger", S.bottle_tags, 220),
    ("06_ortsschild-anhaenger", "Ortsschild-Schlüsselanhänger", S.keytags, 230),
    ("07_lesezeichen", "Lesezeichen Saaletal", S.bookmarks, 160),
    ("08_christbaumanhaenger", "Christbaumanhänger Saaletal", S.ornaments, 190),
    ("09_steckfigur-rhoenschaf", "Steckfigur Hammelburger Rhönschaf", S.sheep, 300),
    ("10_laterne-kurstadt", "Teelicht-Laterne Kurstadt Bad Kissingen", S.kur_lantern, 300),
]


def export(slug, title, parts, max_w):
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    placed, size = layout(parts, max_w=max_w)
    assert size[0] <= 432 and size[1] <= 406, f"{slug} passt nicht auf den D1 Pro: {size}"
    svg = d / f"{slug}.svg"
    write_svg(svg, placed, size, title)
    cairosvg.svg2png(url=str(svg), write_to=str(d / f"{slug}_laservorschau.png"),
                     output_width=1400, background_color="white")
    print(f"{slug}: {len(parts)} Teile, Arbeitsfläche {size[0]:.0f} x {size[1]:.0f} mm")
    return size


# ------------------------------------------------------------------ Szenen-Helfer
def wall_bg(seed=1, base=(222, 214, 200), light=(0.35, 0.25)):
    """Verputzte Wand mit weichem Lichtkegel."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    n = R._noise(W, H, 6, rng) * 0.5 + R._noise(W, H, 40, rng) * 0.5
    r = np.sqrt(((x - W * light[0]) / W) ** 2 + ((y - H * light[1]) / H) ** 2)
    lum = (1.08 - 0.55 * np.clip(r, 0, 1.2))[..., None] * (0.96 + 0.06 * n[..., None])
    img = np.clip(np.array(base, np.float32) * lum, 0, 255).astype(np.uint8)
    return Image.fromarray(img, "RGB").convert("RGBA")


def table_bg(seed=1, base=(120, 80, 52), planks=5):
    """Holztisch von oben, Dielen mit Fugen."""
    t = np.transpose(R.wood(H, W, seed, base), (1, 0, 2))     # Maserung waagrecht
    img = Image.fromarray(np.clip(t, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img)
    for k in range(1, planks):
        y = int(H * k / planks)
        d.line([(0, y), (W, y)], fill=(40, 26, 18, 255), width=4)
        d.line([(0, y + 3), (W, y + 3)], fill=(170, 120, 82, 120), width=1)
    v = Image.new("L", (W, H), 0)
    ImageDraw.Draw(v).ellipse([-300, -250, W + 300, H + 250], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 150))
    dark.putalpha(Image.eval(v, lambda a: 150 - int(a * 150 / 255)))
    img.alpha_composite(dark)
    return img


def place(c, img, pos, sh=(12, 16), blur=12, alpha=0.5):
    R.shadow(c, img, pos, sh, blur, alpha)
    c.alpha_composite(img, (int(pos[0]), int(pos[1])))


def rotated(img, px_pt, ang):
    """Bild drehen und den Pixelpunkt px_pt im gedrehten Bild mitfuehren."""
    cx, cy = img.width / 2, img.height / 2
    rot = img.rotate(ang, Image.BICUBIC, expand=True)
    a = math.radians(-ang)
    hx, hy = px_pt
    rx = (hx - cx) * math.cos(a) - (hy - cy) * math.sin(a) + rot.width / 2
    ry = (hx - cx) * math.sin(a) + (hy - cy) * math.cos(a) + rot.height / 2
    return rot, (rx, ry)


def split_ring(c, x, y, r=34, seed=0):
    d = ImageDraw.Draw(c)
    for k, col in ((0, (90, 92, 98)), (-2, (200, 204, 212)), (2, (140, 144, 150))):
        d.ellipse([x - r + k, y - r * 0.55 + k, x + r + k, y + r * 0.55 + k], outline=col, width=4)


# ------------------------------------------------------------------ Mockups
def mock_skyline(parts):
    c = wall_bg(2, (214, 210, 202), (0.5, 0.35))
    sc = 3.85
    img, px = R.render_part(parts[0], sc, seed=41, base=(226, 192, 146))
    pos = ((W - img.width) / 2, 330)
    # indirektes LED-Licht hinter dem Schild
    c.alpha_composite(R.glow_layer((W, H), (W / 2, pos[1] + img.height * 0.55), 820,
                                   (255, 196, 120), 0.55))
    place(c, img, pos, (10, 22), 14, 0.55)
    # Sideboard mit Deko
    ty = 900
    tw = np.transpose(R.wood(140, W, 7, (96, 62, 40)), (1, 0, 2))
    c.paste(Image.fromarray(np.clip(tw, 0, 255).astype(np.uint8)).convert("RGBA"), (0, ty))
    d = ImageDraw.Draw(c)
    d.rectangle([0, ty, W, ty + 6], fill=(150, 104, 70))
    d.rectangle([0, ty + 140, W, H], fill=(46, 36, 30))
    # Vase mit Zweig und Weinflasche
    d.rounded_rectangle([250, 760, 330, ty], 26, fill=(70, 96, 104))
    for k in range(5):
        d.line([(290, 762), (290 + (k - 2) * 50, 600 + abs(k - 2) * 40)], fill=(80, 64, 40), width=4)
        d.ellipse([290 + (k - 2) * 50 - 14, 590 + abs(k - 2) * 40 - 8, 290 + (k - 2) * 50 + 14,
                   590 + abs(k - 2) * 40 + 8], fill=(108, 140, 78))
    R.label(c, "Wandschild „Skyline Saaletal“", "380 × 100 mm · Bad Neustadt bis Schloss Saaleck · "
            "3 mm Pappel")
    return c


def mock_map(parts):
    c = wall_bg(5, (196, 210, 206), (0.3, 0.2))
    sc = 4.25
    img, _ = R.render_part(parts[0], sc, seed=43, base=(230, 200, 156))
    pos = ((W - img.width) / 2, 40)
    place(c, img, pos, (12, 20), 14, 0.5)
    R.label(c, "Flusskarte „Fränkische Saale“", "300 × 215 mm · 11 Orte von der Quelle bis Gemünden")
    return c


def mock_clock(parts):
    c = wall_bg(8, (232, 226, 214), (0.6, 0.3))
    sc = 4.1
    img, px = R.render_part(parts[0], sc, seed=45, base=(232, 202, 160))
    cx, cy = px(0, 0)
    pos = ((W - img.width) / 2, (H - img.height) / 2 - 40)
    place(c, img, pos, (14, 22), 16, 0.5)
    ox, oy = pos[0] + cx, pos[1] + cy
    hands = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(hands)
    for ang, L, wdt in ((-90 + 30 * 10 + 5, 260, 16), (-90 + 6 * 9, 380, 10)):   # 10:09 Uhr
        a = math.radians(ang)
        tip = (ox + L * math.cos(a), oy + L * math.sin(a))
        back = (ox - 60 * math.cos(a), oy - 60 * math.sin(a))
        nx, ny = -math.sin(a) * wdt / 2, math.cos(a) * wdt / 2
        d.polygon([(back[0] + nx, back[1] + ny), (tip[0] + nx * 0.3, tip[1] + ny * 0.3),
                   (tip[0] - nx * 0.3, tip[1] - ny * 0.3), (back[0] - nx, back[1] - ny)],
                  fill=(28, 28, 30, 255))
    a = math.radians(-90 + 6 * 41)
    d.line([(ox - 80 * math.cos(a), oy - 80 * math.sin(a)),
            (ox + 420 * math.cos(a), oy + 420 * math.sin(a))], fill=(170, 40, 34, 255), width=4)
    d.ellipse([ox - 18, oy - 18, ox + 18, oy + 18], fill=(36, 36, 38, 255))
    d.ellipse([ox - 6, oy - 6, ox + 6, oy + 6], fill=(170, 40, 34, 255))
    R.shadow(c, hands, (0, 0), (8, 12), 6, 0.45)
    c.alpha_composite(hands)
    R.label(c, "Wanduhr „Saaletal-Zeit“", "Ø 260 mm · 12 Orte an der Saale · Loch Ø 8 mm für Quarzwerk")
    return c


def wine_glass_top(c, x, y, r=118, wine=(232, 214, 120)):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 30), outline=(255, 255, 255, 120),
              width=5)
    d.ellipse([x - r * 0.72, y - r * 0.72, x + r * 0.72, y + r * 0.72], fill=wine + (150,))
    d.ellipse([x - r * 0.72, y - r * 0.72, x + r * 0.72, y + r * 0.72], outline=wine + (220,), width=3)
    d.arc([x - r + 14, y - r + 14, x + r - 14, y + r - 14], 200, 260, fill=(255, 255, 255, 200), width=6)
    c.alpha_composite(lay)


def mock_coasters(parts):
    c = table_bg(3, (110, 74, 50))
    sc = 5.0
    spots = [(420, 330, -8), (1150, 320, 12), (440, 830, 6), (1170, 820, -14)]
    for i, (p, (x, y, ang)) in enumerate(zip(parts, spots)):
        img, px = R.render_part(p, sc, seed=50 + i, base=(232, 202, 160))
        rot, _ = rotated(img, (0, 0), ang)
        place(c, rot, (x - rot.width / 2, y - rot.height / 2), (8, 12), 8, 0.55)
    wine_glass_top(c, 800, 570, 105)
    wine_glass_top(c, 1490, 1060, 105, (150, 30, 44))
    R.label(c, "Untersetzer-Set Saaletal", "4 Stück · Ø 95 mm · Hammelburg, Bad Kissingen, Saaleck, Saale")
    return c


def bottle(c, x, ground, sc):
    """Bocksbeutel (Frontansicht, Masse in mm * sc); liefert Ober- und Unterkante des Halses."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    br = 74 * sc                       # Bauch Ø 148 mm
    by = ground - br
    nw = 29 * sc / 2                   # Hals Ø 29 mm
    col = (38, 72, 44, 255)
    d.ellipse([x - br, by - br, x + br, by + br], fill=col)
    sh_top = by - br - 22 * sc
    d.polygon([(x - br * 0.7, by - br * 0.6), (x - nw, sh_top), (x + nw, sh_top),
               (x + br * 0.7, by - br * 0.6)], fill=col)
    nt = sh_top - 85 * sc
    d.rectangle([x - nw, nt, x + nw, sh_top + 4], fill=col)
    d.rounded_rectangle([x - nw - 2 * sc, nt - 6 * sc, x + nw + 2 * sc, nt + 30 * sc], 8,
                        fill=(150, 30, 40, 255))
    d.ellipse([x - br * 0.78, by - br * 0.75, x - br * 0.5, by + br * 0.15], fill=(255, 255, 255, 38))
    d.line([(x - nw * 0.45, nt + 33 * sc), (x - nw * 0.45, sh_top)], fill=(255, 255, 255, 70), width=7)
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([x - br * 1.05, ground - 22, x + br * 1.2, ground + 26], fill=(0, 0, 0, 140))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    c.alpha_composite(lay)
    return x, nt + 30 * sc, sh_top, nw


def mock_bottles(parts):
    c = B.R.background(W, H, 31, c1=(70, 56, 40), c2=(16, 12, 9), bokeh=35, table=0.84)
    ground = int(H * 0.93)
    sc = 2.6
    for i, (p, x) in enumerate(zip(parts, [300, 800, 1300])):
        nx, ntop, nbot, nw = bottle(c, x, ground, sc)
        img, px = R.render_part(p, sc, seed=60 + i, base=(234, 206, 162))
        hx, hy = px(*p.hang)
        cy = nbot - 22 * sc                 # Ring sitzt unten am Hals
        place(c, img, (nx - hx, cy - hy), (10, 14), 10, 0.5)
        # Hals vor dem oberen Ringbogen: der Ring liegt um den Hals herum
        d = ImageDraw.Draw(c)
        d.rectangle([nx - nw, cy - 23 * sc - 3, nx + nw, cy - 17 * sc + 3], fill=(38, 72, 44))
        d.line([(nx - nw * 0.45, cy - 23 * sc - 3), (nx - nw * 0.45, cy - 17 * sc + 3)],
               fill=(84, 112, 88), width=7)
    R.label(c, "Bocksbeutel-Flaschenanhänger", "3 Motive · Ring Ø 34 mm für den Flaschenhals")
    return c


def mock_keytags(parts):
    c = table_bg(9, (92, 62, 44))
    rng = random.Random(7)
    sc = 6.2
    spots = [(330, 300), (800, 270), (1270, 320), (360, 720), (830, 700), (1260, 740)]
    for i, (p, (x, y)) in enumerate(zip(parts, spots)):
        img, px = R.render_part(p, sc, seed=70 + i, base=(236, 208, 160))
        hx, hy = px(*p.hang)
        rot, (rx, ry) = rotated(img, (hx, hy), rng.uniform(-12, 12))
        pos = (x - rot.width / 2, y - rot.height / 2)
        place(c, rot, pos, (8, 12), 8, 0.55)
        split_ring(c, pos[0] + rx - 22, pos[1] + ry, 34)
    R.label(c, "Ortsschild-Schlüsselanhänger", "6 Orte · 72 × 30 mm · Gravur im Ortstafel-Stil")
    return c


def open_book(c):
    d = ImageDraw.Draw(c)
    x0, y0, x1, y1 = 180, 140, 1420, 1030
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([x0 + 20, y0 + 30, x1 + 30, y1 + 40], fill=(0, 0, 0, 160))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
    d.rectangle([x0 - 8, y0 - 8, x1 + 8, y1 + 10], fill=(110, 40, 36))
    mid = (x0 + x1) / 2
    for side in (0, 1):
        a, b = (x0, mid) if side == 0 else (mid, x1)
        page = Image.new("RGBA", (int(b - a), y1 - y0), (243, 236, 220, 255))
        arr = np.asarray(page).astype(np.float32)
        g = np.linspace(0, 1, page.width)
        g = (g if side == 0 else g[::-1])
        arr[..., :3] *= (1 - 0.22 * g ** 6)[None, :, None]
        page = Image.fromarray(arr.astype(np.uint8), "RGBA")
        pd = ImageDraw.Draw(page)
        rng = random.Random(side)
        for k in range(30):
            yy = 70 + k * 26
            if yy > page.height - 60:
                break
            ln = page.width - 140 - (rng.uniform(0, 200) if k % 7 == 6 else 0)
            pd.line([(70, yy), (70 + ln, yy)], fill=(150, 144, 132, 255), width=7)
        c.alpha_composite(page, (int(a), y0))


def mock_bookmarks(parts):
    c = table_bg(11, (84, 58, 42))
    open_book(c)
    sc = 6.0
    for i, (p, x, ang) in enumerate(zip(parts, [470, 800, 1130], [-8, 2, 9])):
        img, px = R.render_part(p, sc, seed=80 + i, base=(236, 208, 160))
        hx, hy = px(*p.hang)
        rot, (rx, ry) = rotated(img, (hx, hy), ang)
        pos = (x - rot.width / 2, 600 - rot.height / 2)
        place(c, rot, pos, (10, 14), 9, 0.5)
        d = ImageDraw.Draw(c)
        hx, hy = pos[0] + rx, pos[1] + ry
        pts = [(hx + 20 * math.sin(t * 2.4) * t, hy - 150 * t) for t in [k / 24 for k in range(25)]]
        d.line(pts, fill=(100, 20, 24), width=5, joint="curve")
        d.line(pts, fill=(170, 36, 40), width=3, joint="curve")
        ex, ey = pts[-1]
        for k in range(-3, 4):
            d.line([(ex, ey), (ex + k * 6, ey - 60)], fill=(160, 30, 36), width=3)
    R.label(c, "Lesezeichen Saaletal", "3 Stück · 40 × 150 mm · Weinrebe, Arkaden, Kanu auf der Saale")
    return c


def mock_ornaments(parts):
    c = B.R.background(W, H, 33, c1=(30, 56, 40), c2=(6, 14, 10), bokeh=55)
    c = R.snow(c, 120, 11)
    sc = 6.4
    xs, ys = [250, 640, 1010, 1380], [430, 330, 400, 310]
    for i, (p, x, y) in enumerate(zip(parts, xs, ys)):
        img, px = R.render_part(p, sc, seed=90 + i, base=(234, 206, 162))
        hx, hy = px(*p.hang)
        pos = (x - hx, y - hy)
        place(c, img, pos, (12, 18), 12, 0.55)
        R.ribbon(c, (x, 0), (x, y), color=(176, 30, 38), width=4)
    R.label(c, "Christbaumanhänger Saaletal", "4 Motive · Ø 80 mm · Hammelburg, Bad Kissingen, Saaleck, "
            "Trimburg")
    return c


def mock_sheep(parts):
    sheep_p, base_p = parts
    c = B.R.background(W, H, 35, c1=(64, 80, 48), c2=(14, 18, 10), bokeh=30, table=0.70)
    sc = 7.4
    b, pb = R.render_part(base_p, sc, seed=100)
    k = 0.36
    bsq = R.shade(b.resize((b.width, int(b.height * k)), Image.LANCZOS), 0.92)
    s, ps = R.render_part(sheep_p, sc, seed=101)
    s = s.crop((0, 0, s.width, int(ps(0, 0)[1])))      # Zapfen steckt in der Platte
    bx = (W - bsq.width) / 2
    by = 920 - bsq.height / 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([bx - 20, by + 20, bx + bsq.width + 40, by + bsq.height + 50],
                               fill=(0, 0, 0, 140))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))
    # Materialkante der Bodenplatte
    edge = R.shade(bsq, 0.5)
    c.alpha_composite(edge, (int(bx), int(by + 3 * sc * 0.9)))
    c.alpha_composite(bsq, (int(bx), int(by)))
    # Schaf: Zapfen sitzen in den Schlitzen (y=-8 auf der Platte)
    slot_x, slot_y = pb(-26, -8)
    foot_x, foot_y = ps(-26, 0)
    sx = bx + slot_x - foot_x
    sy = by + slot_y * k - foot_y
    R.shadow(c, s, (sx, sy), (30, 6), 14, 0.35)
    c.alpha_composite(s, (int(sx), int(sy)))
    R.label(c, "Steckfigur „Hammelburger Rhönschaf“", "2 Steckteile · Schaf 114 × 80 mm · "
            "Bodenplatte 132 × 58 mm")
    return c


def mock_kur_lantern(parts):
    return B.mock_lantern(parts, "Teelicht-Laterne „Kurstadt“",
                          "90 × 90 × 110 mm · Arkaden, Kirchen & Gradierbau · nur LED-Teelichter")


def overview(images):
    tw, th, g = 760, 570, 16
    o = Image.new("RGB", (5 * tw + 6 * g, 2 * th + 3 * g), (20, 24, 22))
    for i, im in enumerate(images):
        o.paste(im.convert("RGB").resize((tw, th), Image.LANCZOS),
                (g + (i % 5) * (tw + g), g + (i // 5) * (th + g)))
    return o


MOCKS = [mock_skyline, mock_map, mock_clock, mock_coasters, mock_bottles, mock_keytags,
         mock_bookmarks, mock_ornaments, mock_sheep, mock_kur_lantern]


def main(only=None):
    imgs = []
    for (slug, title, fn, max_w), mock in zip(DESIGNS, MOCKS):
        if only and not any(slug.startswith(o) for o in only):
            continue
        parts = fn()
        export(slug, title, parts, max_w)
        m = mock(parts)
        m.convert("RGB").save(OUT / slug / f"{slug}_mockup.jpg", quality=92)
        imgs.append(m)
    if not only:
        overview(imgs).save(OUT / "uebersicht_saaletal.jpg", quality=90)


if __name__ == "__main__":
    main(sys.argv[1:])
