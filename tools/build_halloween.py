"""Erzeugt die Halloween-Dateien: Laser-SVGs (xTool D1 Pro), Plotter-SVG/DXF, Vorschauen, Mockups.
Aufruf: python3 tools/build_halloween.py"""
import math
import random
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFilter
from shapely import affinity
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
import build as B  # noqa: E402
import halloween as HW  # noqa: E402
import render as R  # noqa: E402
from lasergeo import Part, layout, polys, write_svg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "entwuerfe" / "halloween"
W, H = 1600, 1200
ORANGE = (255, 140, 40)
PURPLE = (60, 24, 70)

LASER = [
    ("01_candybar-schild", "Candy-Bar-Schild mit Standfüßen", HW.candybar_sign),
    ("02_kuerbis-laterne", "Halloween-Laterne „Kürbis & Friedhof“", HW.lantern),
    ("03_glas-anhaenger", "Anhänger für Bonbongläser", HW.jar_tags),
    ("04_steckfiguren", "Steckfiguren Gespenst, Kürbis, Katze", HW.figures),
    ("05_grabsteine", "Lustige Grabsteine", HW.tombstones),
    ("06_fledermaus-girlande", "Fledermaus-Girlande & Spinnennetz", HW.garland),
]


def export(slug, title, parts, max_w=300):
    d = OUT / "laser" / slug
    d.mkdir(parents=True, exist_ok=True)
    placed, size = layout(parts, max_w=max_w)
    svg = d / f"{slug}.svg"
    write_svg(svg, placed, size, title)
    cairosvg.svg2png(url=str(svg), write_to=str(d / f"{slug}_laservorschau.png"),
                     output_width=1400, background_color="white")
    print(f"laser/{slug}: {len(parts)} Teile, Arbeitsfläche {size[0]:.0f} x {size[1]:.0f} mm")
    return d


# ------------------------------------------------------------------ Mockups
def bg(seed):
    c = R.background(W, H, seed, c1=PURPLE, c2=(10, 4, 14), bokeh=45)
    return c


def bg_table(seed):
    return R.background(W, H, seed, c1=(54, 26, 52), c2=(8, 4, 10), bokeh=40, table=0.80)


def hang(c, parts, xs, ys, sc, seed, ribbon=(230, 110, 30)):
    for i, (p, x, y) in enumerate(zip(parts, xs, ys)):
        img, px = R.render_part(p, sc, seed=seed + i, base=(232, 204, 160))
        hx, hy = px(*p.hang)
        pos = (x - hx, y - hy)
        R.shadow(c, img, pos, (10, 14), 10, 0.55)
        c.alpha_composite(img, (int(pos[0]), int(pos[1])))
        R.ribbon(c, (x, 0), (x, y), color=ribbon, width=4)


def stand(c, items, sc, seed, ground):
    """items: (Teil, x-Mitte) – stehend auf dem Tisch, Unterkante = y 0 des Teils."""
    for i, (p, x) in enumerate(items):
        img, px = R.render_part(p, sc, seed=seed + i, base=(232, 204, 160), pad=0)
        ox, oy = px(0, 0)
        pos = (x - ox, ground - oy)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([x - img.width * 0.55, ground - 18, x + img.width * 0.6,
                                    ground + 22], fill=(0, 0, 0, 150))
        c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
        R.shadow(c, img, pos, (18, -6), 16, 0.35)
        c.alpha_composite(img, (int(pos[0]), int(pos[1])))
        # Standfuss als dunkler Querbalken andeuten
        fw = int(HW.FOOT_L * sc * 0.45)
        foot = Image.new("RGBA", (fw, int(8 * sc * 0.5)), (120, 84, 50, 255))
        c.alpha_composite(foot, (int(x - fw / 2), int(ground - foot.height + 4)))


def glow(c, center, radius, strength=0.35, color=ORANGE):
    c.alpha_composite(R.glow_layer((W, H), center, radius, color, strength))


def mock_sign(parts):
    c = bg_table(31)
    glow(c, (W // 2, H * 0.55), 760, 0.22)
    stand(c, [(parts[0], W / 2)], 4.6, 40, int(H * 0.86))
    R.label(c, "Candy-Bar-Schild", "280 × 160 mm · zum Aufstellen oder Aufhängen")
    return c


def mock_lantern(parts):
    old = R.label
    R.label = lambda *a, **k: None
    try:
        c = B.mock_lantern(parts)
    finally:
        R.label = old
    R.label(c, "Halloween-Laterne", "90 × 90 × 110 mm · Kürbisgesicht & Friedhof · nur LED")
    return c


def mock_tags(parts):
    c = bg(33)
    rng = random.Random(5)
    sc = 5.4
    xs = [290, 800, 1310, 290, 800, 1310]
    ys = [330, 320, 330, 790, 780, 790]
    for k, p in enumerate(parts):
        img, px = R.render_part(p, sc, seed=50 + k, base=(232, 200, 152))
        ang = rng.uniform(-10, 10)
        hx, hy = px(*p.hang)
        cxp, cyp = img.width / 2, img.height / 2
        rot = img.rotate(ang, Image.BICUBIC, expand=True)
        a = math.radians(-ang)
        rx = (hx - cxp) * math.cos(a) - (hy - cyp) * math.sin(a) + rot.width / 2
        ry = (hx - cxp) * math.sin(a) + (hy - cyp) * math.cos(a) + rot.height / 2
        pos = (xs[k] - rot.width / 2, ys[k] - rot.height / 2)
        R.shadow(c, rot, pos, (10, 14), 10, 0.5)
        c.alpha_composite(rot, (int(pos[0]), int(pos[1])))
        hole = (pos[0] + rx, pos[1] + ry)
        d = ImageDraw.Draw(c)
        pts = [(hole[0] + 30 * math.sin(t * 3), hole[1] - (150 if k < 3 else 80) * t)
               for t in [i / 20 for i in range(21)]]
        d.line(pts, fill=(20, 12, 10), width=6, joint="curve")
        d.line(pts, fill=(230, 110, 30), width=4, joint="curve")
    R.label(c, "Anhänger für Bonbongläser", "6 Formen · ca. 60 × 70 mm · Gravur mit Sortennamen")
    return c


def mock_figures(parts):
    c = bg_table(35)
    glow(c, (W // 2, H * 0.6), 700, 0.25)
    stand(c, [(parts[2], 330), (parts[0], 790), (parts[1], 1260)], 3.9, 60, int(H * 0.88))
    R.label(c, "Steckfiguren", "Gespenst · Kürbis · Katze · ca. 130 mm hoch · ohne Kleber")
    return c


def mock_tombs(parts):
    c = bg_table(37)
    glow(c, (W // 2, H * 0.62), 700, 0.22, (150, 220, 140))
    stand(c, [(parts[0], 360), (parts[1], 800), (parts[2], 1240)], 4.4, 70, int(H * 0.88))
    R.label(c, "Lustige Grabsteine", "„R.I.P. der letzte Lolli“ · „Graf Karies“ · „Nimm nur zwei!“")
    return c


def mock_garland(parts):
    c = bg(39)
    bats, netz = parts[:-1], parts[-1]
    xs = [160 + i * 150 for i in range(len(bats))]
    ys = [190 + 60 * math.sin(i * 0.8 + 0.4) + 18 * i for i in range(len(bats))]
    d = ImageDraw.Draw(c)
    sc = 2.4
    # Schnur durch die Fluegelloecher
    d.line([(0, 150)] + [(x, y) for x, y in zip(xs, ys)] + [(W, 260)], fill=(30, 20, 20),
           width=4, joint="curve")
    for i, (p, x, y) in enumerate(zip(bats, xs, ys)):
        img, px = R.render_part(p, sc, seed=80 + i, base=(46, 40, 44))
        hx, hy = px(*p.hang)
        pos = (x - hx, y - hy)
        R.shadow(c, img, pos, (8, 12), 8, 0.5)
        c.alpha_composite(img, (int(pos[0]), int(pos[1])))
    hang(c, [netz], [W * 0.62], [430], 3.0, 90, ribbon=(200, 200, 200))
    R.label(c, "Fledermaus-Girlande & Spinnennetz", "8 Fledermäuse (64–96 mm) · Netz Ø 150 mm")
    return c


MOCKS = [mock_sign, mock_lantern, mock_tags, mock_figures, mock_tombs, mock_garland]


# ------------------------------------------------------------------ Plotter
def write_plot_svg(path, geom, size, title):
    w, h = size
    d = []
    for p in polys(geom):
        for ring in [p.exterior, *p.interiors]:
            c = list(ring.coords)
            d.append("M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in c[:-1]) + " Z")
    Path(path).write_text("\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<!-- {title} | Schneideplotter: schwarze Flaechen = Schnittkontur. Einheiten mm. -->',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h:.2f}mm" '
        f'viewBox="0 0 {w:.3f} {h:.3f}">',
        f'<path fill="#000000" fill-rule="evenodd" stroke="none" d="{" ".join(d)}"/>',
        "</svg>"]), encoding="utf-8")


def write_dxf(path, geom, size):
    """DXF R12 (POLYLINE) – laeuft auch in Silhouette Studio Basic. y nach oben gespiegelt."""
    h = size[1]
    out = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009",
           "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
           "0", "SECTION", "2", "ENTITIES"]
    for p in polys(geom):
        for ring in [p.exterior, *p.interiors]:
            out += ["0", "POLYLINE", "8", "Schnitt", "66", "1", "70", "1"]
            for x, y in list(ring.coords)[:-1]:
                out += ["0", "VERTEX", "8", "Schnitt", "10", f"{x:.3f}", "20",
                        f"{h - y:.3f}"]
            out += ["0", "SEQEND"]
    out += ["0", "ENDSEC", "0", "EOF"]
    Path(path).write_text("\n".join(out) + "\n", encoding="ascii")


def export_plot(slug, title, fn, separate):
    d = OUT / "plotter"
    d.mkdir(parents=True, exist_ok=True)
    geoms = fn()
    if separate:
        parts = [Part(str(i), g) for i, g in enumerate(geoms)]
        placed, size = layout(parts, max_w=HW.PLOT_W + 10, gap=10)
    else:
        placed, size = layout([Part(slug, unary_union(geoms))], max_w=1000)
    geom = unary_union([p.solid for p in placed])
    write_plot_svg(d / f"{slug}.svg", geom, size, title)
    write_dxf(d / f"{slug}.dxf", geom, size)
    cairosvg.svg2png(url=str(d / f"{slug}.svg"), write_to=str(d / f"{slug}_vorschau.png"),
                     output_width=1000, background_color="white")
    print(f"plotter/{slug}: {size[0]:.0f} x {size[1]:.0f} mm")
    return geom


def vinyl(geom, scale, color=(18, 14, 16)):
    b = geom.bounds
    m = R._mask(geom, b, scale, 2)
    img = Image.new("RGBA", m.size, color + (255,))
    img.putalpha(m)
    return img


def mock_plotter():
    """Candybar-Front aus Holz mit Folienplot."""
    c = R.background(W, H, 41, c1=(40, 18, 46), c2=(6, 3, 8), bokeh=30)
    board = R.wood(1400, 900, 7, base=(196, 150, 104))
    bimg = Image.fromarray(board.clip(0, 255).astype("uint8"), "RGB").convert("RGBA")
    d = ImageDraw.Draw(bimg)
    for x in range(0, 1400, 175):       # Bretterfugen
        d.line([(x, 0), (x, 900)], fill=(110, 76, 48), width=4)
    c.alpha_composite(bimg, (100, 150))
    s1 = unary_union(HW.plot_sweet_or_sour())
    img = vinyl(s1, 3.3, (250, 120, 20))
    c.alpha_composite(img, (W // 2 - img.width // 2, 330))
    webg = HW.plot_web_corner()[0]
    w2 = vinyl(webg, 1.2, (245, 245, 245))
    c.alpha_composite(w2, (100, 150))
    w3 = vinyl(affinity.scale(webg, -1, 1, origin=(0, 0)), 1.2, (245, 245, 245))
    c.alpha_composite(w3, (1500 - w3.width, 150))
    for x, y, s, r in [(560, 250, 40, -12), (820, 190, 28, 8), (1010, 200, 48, 10),
                       (1250, 290, 30, -6), (300, 840, 44, 12), (420, 930, 26, -10),
                       (1150, 860, 52, -8), (1300, 950, 30, 14), (1020, 950, 24, 4)]:
        im = vinyl(HW.bat(s, 0, 0, r), 3.0)
        c.alpha_composite(im, (x - im.width // 2, y - im.height // 2))
    R.label(c, "Folienplot auf der Candybar", "„Süßes oder Saures!“ · Fledermäuse · Spinnennetz-Ecken")
    return c


def overview(images):
    o = Image.new("RGB", (2400, 1230), (14, 8, 16))
    th = [im.convert("RGB").resize((780, 585), Image.LANCZOS) for im in images]
    pos = [(20, 20), (810, 20), (1600, 20), (20, 625), (810, 625), (1600, 625)]
    for im, p in zip(th, pos):
        o.paste(im, p)
    return o


def main():
    imgs = []
    for (slug, title, fn), mock in zip(LASER, MOCKS):
        parts = fn()
        d = export(slug, title, parts)
        m = mock(parts)
        m.convert("RGB").save(d / f"{slug}_mockup.jpg", quality=92)
        imgs.append(m)
    overview(imgs).save(OUT / "uebersicht_laser.jpg", quality=90)
    for slug, title, fn, separate in HW.PLOTTER:
        export_plot(slug, title, fn, separate)
    mock_plotter().convert("RGB").save(OUT / "plotter" / "candybar_folienplot_mockup.jpg",
                                       quality=92)


if __name__ == "__main__":
    main()
