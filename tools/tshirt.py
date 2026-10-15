"""Einfarbige T-Shirt-Motive (IT & KI) fuer den Silhouette Cameo: Flex-/Flockfolie zum Aufbuegeln.

Erzeugt pro Motiv: SVG (Silhouette Designer Edition, Cricut, Inkscape), DXF (Silhouette Basic Edition),
PNG 300 dpi (Nachzeichnen / Vorschau) und ein Shirt-Mockup.   Aufruf: python3 tools/tshirt.py
Einheiten: mm, y nach unten.
"""
import math
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont
from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
from lasergeo import _FlatPen, _font, circle, polys  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tshirt-plotter" / "serie1_it-ki"

MIN_HOLE = 3.0     # mm^2: kleinere Loecher werden zugefuellt (lassen sich nicht entgittern)
MIN_ISLAND = 3.0   # mm^2: kleinere Inseln fliegen raus (halten nicht auf dem Stoff)
WEED_MARGIN = 6.0  # mm Abstand des Entgitterrahmens

ARCHIVO = "ArchivoBlack-Regular.ttf"
MONO = "JetBrainsMono-ExtraBold.ttf"
ORBITRON = "Orbitron-Black.ttf"
PIXEL = "PressStart2P-Regular.ttf"


# ------------------------------------------------------------------ Schrift
def line(s, font, size, tracking=0.0):
    """Eine Textzeile als Flaeche: links bei x=0, Grundlinie bei y=0 (Glyphen nach oben = negatives y).
    Liefert (Geometrie, Vorschubbreite in mm)."""
    f = _font(font)
    gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm
    x, shapes = 0, []
    for ch in s:
        gname = cmap.get(ord(ch))
        if gname is None:
            raise ValueError(f"Zeichen {ch!r} fehlt in {font}")
        pen = _FlatPen(gs, steps=16)
        gs[gname].draw(pen)
        rings = [Polygon([(px + x, py) for px, py in c]).buffer(0) for c in pen.contours]
        g = None
        for r in rings:
            if r.is_empty:
                continue
            g = r if g is None else g.symmetric_difference(r)
        if g is not None:
            shapes.append(g)
        x += f["hmtx"][gname][0] + tracking * upm
    k = size / upm
    g = affinity.scale(unary_union(shapes), k, -k, origin=(0, 0))
    return g, (x - tracking * upm) * k


def text(s, font, size, cx, base, tracking=0.0, width=None):
    """Zeile horizontal zentriert auf cx, Grundlinie auf base. Optional auf Breite skaliert."""
    g, adv = line(s, font, size, tracking)
    if width:
        b = g.bounds
        k = width / (b[2] - b[0])
        g = affinity.scale(g, k, k, origin=(0, 0))
    b = g.bounds
    return affinity.translate(g, cx - (b[0] + b[2]) / 2, base)


def mono(s, size, x, base):
    """Monospace-Zeile linksbuendig (Einrueckung bleibt erhalten)."""
    g, _ = line(s, MONO, size)
    return affinity.translate(g, x, base)


def char_w(size):
    f = _font(MONO)
    return f["hmtx"][f.getBestCmap()[ord("a")]][0] / f["head"].unitsPerEm * size


# ------------------------------------------------------------------ Formen
def rrect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=24)


def frame(x0, y0, x1, y1, r, t):
    return rrect(x0, y0, x1, y1, r).difference(rrect(x0 + t, y0 + t, x1 - t, y1 - t, max(r - t, 0.5)))


def bar(p, q, w, cap="round"):
    return LineString([p, q]).buffer(w / 2, cap_style=cap, join_style="round")


def sparkle(cx, cy, r, waist=0.22):
    """KI-Funkeln: vierzackiger Stern mit nach innen gewoelbten Flanken."""
    pts = []
    for i in range(4):
        a0 = math.radians(-90 + i * 90)
        tip = (cx + r * math.cos(a0), cy + r * math.sin(a0))
        nxt = math.radians(-90 + (i + 1) * 90)
        tip2 = (cx + r * math.cos(nxt), cy + r * math.sin(nxt))
        mid = (cx + waist * r * math.cos(a0 + math.pi / 4) * 1.4, cy + waist * r * math.sin(a0 + math.pi / 4) * 1.4)
        for t in [j / 24 for j in range(24)]:  # quadratische Bezier: Spitze -> Taille -> naechste Spitze
            u = 1 - t
            pts.append((u * u * tip[0] + 2 * u * t * mid[0] + t * t * tip2[0],
                        u * u * tip[1] + 2 * u * t * mid[1] + t * t * tip2[1]))
    return Polygon(pts)


# ------------------------------------------------------------------ Motive
def d_localhost():
    """There's no place like 127.0.0.1"""
    W = 250
    parts = [text("THERE'S NO", ARCHIVO, 40, 0, 0, width=W),
             text("PLACE LIKE", ARCHIVO, 40, 0, 46, width=W)]
    # Haus: Dach als dicker Winkel, Korpus mit Tuer und Fenstern als Aussparung
    top, hx = 70, 62
    roof = LineString([(-hx - 14, top + 52), (0, top), (hx + 14, top + 52)]).buffer(9, join_style="mitre",
                                                                                  cap_style="flat")
    chimney = box(hx - 30, top + 6, hx - 14, top + 36)
    body = box(-hx + 2, top + 54, hx - 2, top + 122)
    door = rrect(-12, top + 82, 12, top + 123, 3)
    win1, win2 = box(-hx + 16, top + 68, -hx + 40, top + 90), box(hx - 40, top + 68, hx - 16, top + 90)
    house = unary_union([roof, body, chimney]).difference(unary_union([door, win1, win2]))
    # Fensterkreuze
    house = house.union(unary_union([bar((-hx + 28, top + 68), (-hx + 28, top + 90), 3, "flat"),
                                     bar((-hx + 16, top + 79), (-hx + 40, top + 79), 3, "flat"),
                                     bar((hx - 28, top + 68), (hx - 28, top + 90), 3, "flat"),
                                     bar((hx - 40, top + 79), (hx - 16, top + 79), 3, "flat")]))
    parts.append(house)
    parts.append(text("127.0.0.1", MONO, 40, 0, top + 168, width=W))
    return unary_union(parts)


def d_prompt():
    """Ich prompte, also bin ich."""
    s = [sparkle(0, -78, 62), sparkle(70, -112, 22), sparkle(-62, -40, 15)]
    t1 = text("ICH PROMPTE,", ARCHIVO, 40, 0, 40, width=250)
    t2 = text("ALSO BIN ICH.", ARCHIVO, 40, 0, 86, width=250)
    return unary_union(s + [t1, t2])


def d_deeplearning():
    """Neuronales Netz + DEEP LEARNING / SHALLOW SLEEPING"""
    layers = [3, 4, 4, 2]
    dx, dy, r, ring, edge = 66, 38, 10, 3.2, 2.0
    nodes = []
    for i, n in enumerate(layers):
        x = (i - (len(layers) - 1) / 2) * dx
        nodes.append([(x, (j - (n - 1) / 2) * dy) for j in range(n)])
    edges = [bar(a, b, edge) for L, R in zip(nodes, nodes[1:]) for a in L for b in R]
    outer = [circle(x, y, r) for L in nodes for (x, y) in L]
    inner = unary_union([circle(x, y, r - ring) for L in nodes for (x, y) in L])
    net = unary_union(edges + outer).difference(inner)
    net = affinity.translate(net, 0, -95)
    t1 = text("DEEP LEARNING", ORBITRON, 40, 0, 20, width=260)
    t2 = text("SHALLOW SLEEPING", ORBITRON, 40, 0, 52, width=200)
    return unary_union([net, t1, t2])


def d_binary():
    """Es gibt 10 Arten von Menschen ..."""
    W = 250
    g = [text("ES GIBT", ARCHIVO, 30, 0, 0, width=120),
         text("10", MONO, 160, 0, 112, width=150),
         text("ARTEN VON MENSCHEN:", ARCHIVO, 30, 0, 150, width=W),
         text("DIE, DIE BINÄR VERSTEHEN,", ARCHIVO, 30, 0, 182, width=W),
         text("UND DIE ANDEREN.", ARCHIVO, 30, 0, 214, width=W * 0.66)]
    return unary_union(g)


def d_kiupdate():
    """KI-Update wird installiert, bitte nicht ansprechen"""
    W = 260
    t1 = text("KI-UPDATE", ORBITRON, 40, 0, 0, width=W)
    # Fortschrittsbalken: Rahmen + 7 von 10 Segmenten
    y0, h, t, gap = 16, 40, 3.5, 3.0
    fr = frame(-W / 2, y0, W / 2, y0 + h, 8, t)
    n, filled = 10, 7
    ix0, ix1 = -W / 2 + t + gap, W / 2 - t - gap
    sw = (ix1 - ix0 - (n - 1) * gap) / n
    segs = [rrect(ix0 + i * (sw + gap), y0 + t + gap, ix0 + i * (sw + gap) + sw, y0 + h - t - gap, 2)
            for i in range(filled)]
    t2 = text("WIRD INSTALLIERT ... 73 %", MONO, 20, 0, y0 + h + 26, width=W)
    t3 = text("BITTE NICHT ANSPRECHEN.", ARCHIVO, 20, 0, y0 + h + 62, width=W)
    return unary_union([t1, fr, *segs, t2, t3])


ROBOT = """
......XXX......
......XXX......
.......X.......
.......X.......
.XXXXXXXXXXXXX.
.X...........X.
.X..XX...XX..X.
XX..XX...XX..XX
XX...........XX
.X...........X.
.X..XXXXXXX..X.
.X..X.X.X.X..X.
.X..XXXXXXX..X.
.X...........X.
.XXXXXXXXXXXXX.
"""


def d_robot():
    """Pixel-Roboter: HUMAN IN THE LOOP"""
    rows = ROBOT.strip().splitlines()
    px = 12
    cells = []
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c == "X":
                cells.append(box(i * px, j * px, (i + 1) * px, (j + 1) * px))
    bot = unary_union(cells).buffer(0.05, join_style="mitre").buffer(-0.05, join_style="mitre")
    b = bot.bounds
    bot = affinity.translate(bot, -(b[0] + b[2]) / 2, -b[3] - 12)
    t1 = text("HUMAN", PIXEL, 32, 0, 30, width=170)
    t2 = text("IN THE LOOP", PIXEL, 32, 0, 62, width=250)
    return unary_union([bot, t1, t2])


def d_terminal():
    """Terminal: sudo rm -rf /sorgen"""
    W, H, t, tb = 270, 160, 3.5, 20
    win = frame(0, 0, W, H, 10, t).union(rrect(0, 0, W, tb + 5, 10).intersection(box(0, 0, W, tb)))
    dots = unary_union([circle(16 + i * 15, tb / 2, 4.2) for i in range(3)])
    win = win.difference(dots)
    size, x0 = 14.5, 13
    lines_ = ["$ sudo rm -rf /sorgen",
              "[sudo] Passwort: ****",
              "Sorgen gelöscht. 0 übrig.",
              "$ "]
    lh = 29
    g = [win]
    for k, s in enumerate(lines_):
        if s.strip():
            g.append(mono(s, size, x0, tb + 32 + k * lh))
    cw = char_w(size)
    cur_y = tb + 32 + 3 * lh
    g.append(box(x0 + 2 * cw + 1, cur_y - size * 0.73, x0 + 3 * cw, cur_y + 1))  # Blockcursor
    return unary_union(g)


def d_whileloop():
    """while (lebendig) { kaffee(); code(); // schlafen(); }"""
    size = 19
    lh = 33
    src = ["while (lebendig) {",
           "    kaffee();",
           "    code();",
           "    // schlafen();",
           "}"]
    return unary_union([mono(s, size, 0, k * lh) for k, s in enumerate(src)])


DESIGNS = [
    ("01_localhost", "There's no place like 127.0.0.1", d_localhost, ((25, 25, 28), (245, 245, 245))),
    ("02_ich-prompte", "Ich prompte, also bin ich.", d_prompt, ((246, 244, 238), (20, 20, 24))),
    ("03_deep-learning", "Deep Learning – Shallow Sleeping", d_deeplearning, ((22, 34, 62), (120, 230, 255))),
    ("04_10-arten", "Es gibt 10 Arten von Menschen", d_binary, ((128, 132, 136), (18, 18, 20))),
    ("05_ki-update", "KI-Update wird installiert", d_kiupdate, ((18, 18, 20), (110, 255, 140))),
    ("06_human-in-the-loop", "Pixel-Roboter: Human in the Loop", d_robot, ((178, 34, 40), (250, 250, 250))),
    ("07_sudo-sorgen", "sudo rm -rf /sorgen", d_terminal, ((36, 40, 46), (250, 250, 250))),
    ("08_while-lebendig", "while (lebendig) – Kaffee statt Schlaf", d_whileloop, ((64, 84, 64), (245, 240, 225))),
]


# ------------------------------------------------------------------ Aufbereitung & Pruefung
def finalize(g, target_w):
    """Auf Zielbreite skalieren, Nullpunkt oben links, Mini-Loecher/-Inseln entfernen."""
    b = g.bounds
    k = target_w / (b[2] - b[0])
    g = affinity.scale(g, k, k, origin=(0, 0))
    b = g.bounds
    g = affinity.translate(g, WEED_MARGIN - b[0], WEED_MARGIN - b[1])
    out = []
    for p in polys(g.buffer(0)):
        if p.area < MIN_ISLAND:
            continue
        holes = [h for h in p.interiors if Polygon(h).area >= MIN_HOLE]
        out.append(Polygon(p.exterior, holes).simplify(0.02))
    return unary_union(out)


def check(g):
    """Wie viel der Flaeche ist duenner als 1,2 mm (schwer zu schneiden/entgittern)?"""
    thin = g.difference(g.buffer(-0.6).buffer(0.6))
    return thin.area / g.area * 100


# ------------------------------------------------------------------ Export
def rings(g):
    for p in polys(g):
        yield p.exterior
        yield from p.interiors


def path_d(g):
    d = []
    for r in rings(g):
        c = list(r.coords)[:-1]
        d.append("M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in c) + " Z")
    return " ".join(d)


def write_svg(path, g, size, title, color="#000000"):
    W, H = size
    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<!-- {title} | Plotterdatei fuer Flex-/Flockfolie. Einheiten mm. VOR DEM SCHNEIDEN SPIEGELN! -->\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}mm" height="{H:.2f}mm" '
        f'viewBox="0 0 {W:.3f} {H:.3f}">\n'
        f'<title>{title}</title>\n'
        f'<g id="Motiv"><path fill="{color}" fill-rule="evenodd" stroke="none" d="{path_d(g)}"/></g>\n'
        f'<g id="Entgitterrahmen"><rect x="0.5" y="0.5" width="{W - 1:.3f}" height="{H - 1:.3f}" '
        f'fill="none" stroke="#999999" stroke-width="0.25"/></g>\n'
        f'</svg>\n', encoding="utf-8")


def write_dxf(path, g, size):
    """DXF R12 mit geschlossenen POLYLINEs (mm, y nach oben) - liest auch Silhouette Studio Basic."""
    W, H = size
    o = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSUNITS", "70", "4",
         "9", "$EXTMIN", "10", "0.0", "20", "0.0", "9", "$EXTMAX", "10", f"{W:.3f}", "20", f"{H:.3f}",
         "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]

    def poly(coords, layer):
        o.extend(["0", "POLYLINE", "8", layer, "66", "1", "70", "1"])
        for x, y in coords:
            o.extend(["0", "VERTEX", "8", layer, "10", f"{x:.3f}", "20", f"{H - y:.3f}"])
        o.extend(["0", "SEQEND", "8", layer])

    for r in rings(g):
        poly(list(r.coords)[:-1], "MOTIV")
    poly([(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)], "ENTGITTERRAHMEN")
    o.extend(["0", "ENDSEC", "0", "EOF"])
    path.write_text("\n".join(o) + "\n", encoding="ascii")


def svg_doc(inner, W, H, px_w, bg=None):
    bgr = f'<rect width="100%" height="100%" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{px_w}" height="{px_w * H / W:.0f}" '
            f'viewBox="0 0 {W:.3f} {H:.3f}">{bgr}{inner}</svg>')


SHIRT = ("M -95 0 C -70 52 70 52 95 0 L 215 22 C 260 40 300 110 345 205 L 268 258 L 248 222 "
         "L 252 720 C 120 732 -120 732 -252 720 L -248 222 L -268 258 L -345 205 "
         "C -300 110 -260 40 -215 22 Z")


def rgb(c):
    return "#%02x%02x%02x" % c


def mockup(g, size, shirt_c, vinyl_c, title, sub):
    W, H = size
    k = 0.92  # Motiv inkl. Rahmen -> Shirtkoordinaten (Motiv ist ~26-28 cm breit, Shirt Gr. L ~ 52 cm)
    inner = path_d(g)
    sx = -W * k / 2
    shade = tuple(max(0, int(v * 0.82)) for v in shirt_c)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1400" viewBox="-400 -60 800 935">'
           f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="#ecebe7"/><stop offset="1" stop-color="#d6d4cf"/></linearGradient>'
           f'<radialGradient id="sh" cx="0.5" cy="0.35" r="0.75">'
           f'<stop offset="0" stop-color="{rgb(shirt_c)}"/><stop offset="1" stop-color="{rgb(shade)}"/>'
           f'</radialGradient></defs>'
           f'<rect x="-400" y="-60" width="800" height="935" fill="url(#bg)"/>'
           f'<path d="{SHIRT}" transform="translate(6,10)" fill="#000" opacity="0.18"/>'
           f'<path d="{SHIRT}" fill="url(#sh)"/>'
           f'<path d="M -95 0 C -70 52 70 52 95 0" fill="none" stroke="{rgb(shade)}" stroke-width="12"/>'
           f'<g transform="translate({sx:.2f},95) scale({k})">'
           f'<path d="{inner}" fill="{rgb(vinyl_c)}" fill-rule="evenodd"/></g></svg>')
    img = Image.open(__import__("io").BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGB")
    d = ImageDraw.Draw(img)
    try:
        f1 = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 40)
        f2 = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 26)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    d.text((50, 1290), title, font=f1, fill=(30, 30, 30))
    d.text((50, 1342), sub, font=f2, fill=(90, 90, 90))
    return img


def main():
    OUT.mkdir(exist_ok=True)
    thumbs = []
    rows = []
    for slug, title, fn, (shirt_c, vinyl_c) in DESIGNS:
        target_w = 260
        g = finalize(fn(), target_w)
        b = g.bounds
        size = (b[2] + WEED_MARGIN, b[3] + WEED_MARGIN)
        if size[1] > 300:  # zu hoch fuer eine Shirt-Front -> auf 290 mm Hoehe begrenzen
            g = finalize(g, target_w * 290 / (b[3] - b[1]))
            b = g.bounds
            size = (b[2] + WEED_MARGIN, b[3] + WEED_MARGIN)
        d = OUT / slug
        d.mkdir(exist_ok=True)
        write_svg(d / f"{slug}.svg", g, size, title)
        write_dxf(d / f"{slug}.dxf", g, size)
        W, H = size
        dpi_px = round(W / 25.4 * 300)
        png = Image.open(__import__("io").BytesIO(cairosvg.svg2png(bytestring=svg_doc(
            f'<path fill="#000" fill-rule="evenodd" d="{path_d(g)}"/>', W, H, dpi_px).encode())))
        png.save(d / f"{slug}_300dpi.png", dpi=(300, 300))
        mw, mh = b[2] - b[0], b[3] - b[1]
        sub = f"Motiv {mw / 10:.1f} × {mh / 10:.1f} cm · einfarbig · Flexfolie"
        m = mockup(g, size, shirt_c, vinyl_c, title, sub)
        m.save(d / f"{slug}_mockup.jpg", quality=88)
        thumbs.append(m)
        thin = check(g)
        rows.append((slug, title, mw, mh, len(list(rings(g))), thin))
        print(f"{slug:24s} {mw:6.1f} x {mh:6.1f} mm  Konturen {len(list(rings(g))):4d}  "
              f"<1,2 mm: {thin:4.1f} %")
    # Uebersicht 4 x 2
    tw, th = 600, 700
    ov = Image.new("RGB", (tw * 4, th * 2), (236, 235, 231))
    for i, m in enumerate(thumbs):
        ov.paste(m.resize((tw, th), Image.LANCZOS), ((i % 4) * tw, (i // 4) * th))
    ov.save(OUT / "uebersicht.jpg", quality=86)
    return rows


if __name__ == "__main__":
    main()
