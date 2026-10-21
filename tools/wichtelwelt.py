"""Pixel-Wichtelwelt: 8-Bit-Diorama mit Wichteltuer, Figuren und Steck-Bodenplatte.

Alle Sprites sind ASCII-Raster. Zeichen:
  .  leer          #  Holz          E  Gravur (voll)
  d  Gravur im Schachbrettmuster    x  kleiner Gravurpunkt (Textur)
  o  Loch (Schneiden)               N  Holz mit Linien-Umriss
Aufruf: python3 tools/wichtelwelt.py
"""
import random
import sys
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
import render as R  # noqa: E402
from designs import MAT, SLOT, fit_test  # noqa: E402
from lasergeo import Part, layout, lines, polys, write_svg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "entwuerfe" / "07_pixel-wichtelwelt"
TAB_W = 10.0   # Breite der Steckzapfen

# ---------------------------------------------------------------- 5x7-Pixelschrift
FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    " ": "00000 00000 00000 00000 00000 00000 00000",
    ">": "01000 00100 00010 00001 00010 00100 01000",
    "_": "00000 00000 00000 00000 00000 00000 11111",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    "-": "00000 00000 00000 11111 00000 00000 00000",
    "\\": "10000 10000 01000 00100 00010 00001 00001",
}


def pixel_text(s, px, x=0.0, y=0.0, anchor="center"):
    """Text aus quadratischen Pixeln. anchor: 'center' (x,y = Mitte) oder 'left' (x,y = oben links)."""
    w = (len(s) * 6 - 1) * px
    h = 7 * px
    if anchor == "center":
        x, y = x - w / 2, y - h / 2
    out = []
    for i, ch in enumerate(s):
        rows = FONT[ch].split()
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "1":
                    X = x + (i * 6 + c) * px
                    Y = y + r * px
                    out.append(box(X, Y, X + px, Y + px))
    return unary_union(out)


# ---------------------------------------------------------------- Sprite-Helfer
def sprite(rows, P):
    """ASCII-Raster -> (Umriss mit Loechern, Gravur, Linien)."""
    assert len({len(r) for r in rows}) == 1, [len(r) for r in rows]
    solid, holes, eng, nose = [], [], [], []
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch == ".":
                continue
            b = box(c * P, r * P, (c + 1) * P, (r + 1) * P)
            solid.append(b)
            if ch == "o":
                holes.append(b)
            elif ch == "E" or (ch == "d" and (r + c) % 2 == 0):
                eng.append(b)
            elif ch == "x" and (r + c) % 2 == 0:
                cx, cy, k = (c + 0.5) * P, (r + 0.5) * P, P * 0.22
                eng.append(box(cx - k, cy - k, cx + k, cy + k))
            elif ch == "N":
                nose.append(b)
    g = unary_union(solid).difference(unary_union(holes)).simplify(0.01)
    score = lines(unary_union(nose).simplify(0.01)) if nose else []
    return g, unary_union(eng), score


def stepped_rect(x0, y0, x1, y1, step, n=2):
    """Rechteck mit pixelig abgetreppten Ecken."""
    g = box(x0, y0, x1, y1)
    for k in range(n):
        w, h = step * (n - k), step * (k + 1)
        for cx, sx in ((x0, 1), (x1, -1)):
            for cy, sy in ((y0, 1), (y1, -1)):
                g = g.difference(box(min(cx, cx + sx * w), min(cy, cy + sy * h),
                                     max(cx, cx + sx * w), max(cy, cy + sy * h)))
    return g


def tabs(g, ground, xs):
    """Steckzapfen (Materialstaerke tief) an der Unterkante y=ground."""
    return unary_union([g] + [box(x - TAB_W / 2, ground, x + TAB_W / 2, ground + MAT)
                              for x in xs])


class Standing(Part):
    """Stehendes Teil mit Bodenlinie und Zapfen-Positionen (fuer Bodenplatte & Mockup)."""

    def __init__(self, name, solid, engrave=None, score=None, ground=0.0, tab_xs=()):
        super().__init__(name, tabs(solid, ground, tab_xs), engrave, score or [])
        self.ground, self.tab_xs = ground, list(tab_xs)
        self.width = solid.bounds[2] - solid.bounds[0]


# =========================================================== Teile
def door_frame():
    P, C, H = 4.0, 18, 28
    inset = [5, 3, 2, 1, 1]
    rows = []
    for r in range(H):
        i = inset[r] if r < len(inset) else 0
        rows.append("." * i + "#" * (C - 2 * i) + "." * i)
    g, _, _ = sprite(rows, P)
    leaf = door_leaf_shape().buffer(0.01)
    leaf = affinity.translate(leaf, 3 * P, 3 * P)
    windows = unary_union([Polygon(r).buffer(1.5, join_style="mitre") for r in leaf.interiors])
    leaf = Polygon(leaf.exterior)
    sign = pixel_text("LVL 24", 0.8, 36, 7.6)
    pad = box(60.6, 50.6, 71.4, 64.4)  # Tastenfeld
    keep_out = unary_union([leaf.buffer(0.4), sign.envelope.buffer(1.2), pad.buffer(0.8)])
    # Ziegel: Fugen als Linie, ein Teil der Steine pixelig graviert
    rng = random.Random(24)
    score, eng = [], [sign]
    for r in range(H):
        y0, y1 = r * P, (r + 1) * P
        score.append(LineString([(0, y1), (C * P, y1)]))
        off = 0 if r % 2 == 0 else P
        for x in np.arange(-off, C * P, 2 * P):
            score.append(LineString([(x, y0), (x, y1)]))
            if rng.random() < 0.22:
                eng.append(box(x + 0.8, y0 + 0.8, x + 2 * P - 0.8, y1 - 0.8))
    score = [s for l in score for s in lines(l.difference(keep_out))]
    eng = unary_union(eng[1:]).difference(keep_out)
    eng = unary_union([eng, sign, windows])     # dunkler "Innenraum" hinter den Fenstern
    eng = unary_union([eng] + [box(62 + c * 3, 52 + r * 3, 64 + c * 3, 54 + r * 3)
                               for c in range(3) for r in range(4)])
    score += lines(pad)
    return Standing("Wichteltuer Rahmen", g, eng, score, ground=H * P,
                    tab_xs=[14, C * P - 14])


def door_leaf_shape():
    P, C, H = 4.0, 12, 25
    inset = [3, 2, 1]
    rows = []
    for r in range(H):
        i = inset[r] if r < len(inset) else 0
        rows.append("." * i + "#" * (C - 2 * i) + "." * i)
    for r in (5, 6, 8, 9):                       # Fenster: 4 Pixel-Scheiben
        rows[r] = rows[r][:3] + "oo" + rows[r][5:7] + "oo" + rows[r][9:]
    g, _, _ = sprite(rows, P)
    return g


def door_leaf():
    g = door_leaf_shape()
    P = 4.0
    score = [LineString([(x, 0), (x, 25 * P)]) for x in (8, 16, 24, 32, 40)]
    score = [s for l in score for s in lines(l.difference(box(11, 19, 37, 41)))]
    eng = [box(0.6, 6 * P, 2 * P + 2, 7 * P),            # Scharniere
           box(0.6, 19 * P, 2 * P + 2, 20 * P),
           box(9 * P, 14 * P, 10 * P, 15 * P),            # Pixel-Tuerknauf + Schluesselloch
           box(9 * P + 1.4, 15 * P + 0.8, 10 * P - 1.4, 15 * P + 3.2)]
    for y in (3 * P + 2, 23 * P + 2):                      # Naegel
        for x in (4, 12, 20, 28, 36, 44):
            eng.append(box(x - 0.7, y - 0.7, x + 0.7, y + 0.7))
    return Part("Wichteltuer Tuerblatt (aufkleben)", g, unary_union(eng), score).clean()


def doormat():
    w, h = 80.0, 20.0
    g = box(0, 0, w, h)
    for y in np.arange(0, h, 4):                           # Fransen links/rechts
        g = g.union(box(-2, y + 0.5, 0.1, y + 2.5)).union(box(w - 0.1, y + 0.5, w + 2, y + 2.5))
    eng = pixel_text("PRESS START", 1.0, w / 2, h / 2).buffer(0)
    dots = [box(x, y, x + 1, y + 1) for x in np.arange(2, w - 2, 2)
            for y in (1.5, h - 2.5) if int(x) % 4 == 2]
    eng = unary_union([eng] + dots)
    return Part("Fussmatte", g, eng).clean()


def ladder():
    w, h, rail = 26.0, 90.0, 4.0
    g = unary_union([box(0, 0, rail, h), box(w - rail, 0, w, h)] +
                    [box(0, y, w, y + 3) for y in np.arange(6, h - 4, 11)])
    eng = [box(0.8, y, rail - 0.8, y + 1.6) for y in np.arange(2, h - 2, 4)]
    eng += [box(w - rail + 0.8, y, w - 0.8, y + 1.6) for y in np.arange(2, h - 2, 4)]
    return Part("Leiter", g, unary_union(eng)).clean()


WICHTEL = [
    ".........#.....",
    "........EE.....",
    ".......EEE.....",
    "......EEEE.....",
    "......EEEEE....",
    ".....dEdEdE....",
    ".....EEEEEEE...",
    "....EEEEEEEE...",
    "....dEdEdEdEd..",
    "...EEEEEEEEEE..",
    "...EEEEEEEEEEE.",
    ".#############.",
    "..xxxxNNNxxxx..",
    ".xxxxNNNNNxxxx.",
    ".xxxxNNNNNxxxx.",
    "ddxxxxNNNxxxxdd",
    "dEdxxxxxxxxxdEd",
    "dEdxxxxxxxxxdEd",
    "##dExxxxxxxEd##",
    "##EdExxxxxEdE##",
    "..dEdExxxEdEd..",
    "..EEEEExEEEEE..",
    "..#####E#####..",
    "..dddd...dddd..",
    "..dddd...dddd..",
    ".EEEEE...EEEEE.",
]


def wichtel():
    P = 3.5
    g, eng, score = sprite(WICHTEL, P)
    return Standing("Pixel-Wichtel", g, eng, score, ground=len(WICHTEL) * P,
                    tab_xs=[3.5 * P, 11.5 * P])


TREE = [
    "..........#..........",
    ".........###.........",
    "......#########......",
    "........#####........",
    ".......###.###.......",
    ".........###.........",
    "........##E##........",
    ".......###o###.......",
    "......#E#####E#......",
    ".....###########.....",
    "......####o####......",
    ".....#E#######E#.....",
    "....###o#####o###....",
    "...######E#E######...",
    ".....###########.....",
    "....##o##E#E##o##....",
    "...#E###########E#...",
    "..#####o#####o#####..",
    ".#E#######E#######E#.",
    "#####################",
    "........#####........",
    "........#####........",
    "........#####........",
]


def tree():
    P = 4.0
    g, eng, score = sprite(TREE, P)
    # Lichterkette: diagonale Pixelreihen
    chain = []
    for r0, c0, n, d in [(8, 7, 6, 1), (12, 13, 7, -1), (16, 5, 10, 1)]:
        for k in range(n):
            r, c = r0 + k // 2, c0 + d * k
            cx, cy = (c + 0.5) * P, (r + 0.5) * P
            chain.append(box(cx - 0.9, cy - 0.9, cx + 0.9, cy + 0.9))
    eng = unary_union([eng] + chain)
    return Standing("Pixel-Tannenbaum", g, eng, score, ground=len(TREE) * P,
                    tab_xs=[10.5 * P])


def terminal():
    W = 66.0
    body = stepped_rect(0, 0, W, 52, 1.5)
    neck = box(25, 51, 41, 57)
    foot = stepped_rect(15, 56, 51, 62, 1.5, 1)
    led = box(56, 44, 59, 47)
    g = unary_union([body, neck, foot]).difference(led)
    scr = stepped_rect(6, 6, 60, 42, 1.5, 1)
    px = 0.75
    txt = [pixel_text("C:\\>WICHTEL", px, 9, 9.5, "left"),
           pixel_text("LADE...", px, 9, 9.5 + 9 * px, "left")]
    y_bar = 9.5 + 18 * px
    bar = box(9, y_bar, 57, y_bar + 7 * px).difference(box(9 + px, y_bar + px, 57 - px,
                                                             y_bar + 6 * px))
    blocks = [box(9 + 2 * px + i * 3.2, y_bar + 2 * px, 9 + 2 * px + i * 3.2 + 2.4,
                  y_bar + 5 * px) for i in range(10)]
    txt += [bar, *blocks, pixel_text("HO HO HO!_", px, 9, 9.5 + 27 * px, "left")]
    eng = scr.difference(unary_union(txt))
    eng = unary_union([eng, pixel_text("W-64", 0.6, 12, 47)])
    score = lines(box(4, 4, 62, 44)) + [LineString([(20, 59), (46, 59)])]
    return Standing("Retro-Terminal", g, eng, score, ground=62, tab_xs=[22, 44])


def keyboard():
    g = stepped_rect(0, 0, 64, 24, 1.5, 1)
    keys = [box(3 + c * 5, 3 + r * 5, 3 + c * 5 + 4, 3 + r * 5 + 4)
            for r in range(3) for c in range(12)]
    keys += [box(3, 18, 13, 21.5), box(18, 18, 46, 21.5), box(51, 18, 61, 21.5)]
    eng = box(2, 2, 62, 22.5).difference(unary_union(keys))
    return Part("Tastatur (flach)", g, eng).clean()


def sign404():
    board = stepped_rect(-2, 0, 58, 40, 2)
    post = unary_union([box(23, 39, 33, 76), stepped_rect(17, 72, 39, 80, 2, 1)])
    g = unary_union([board, post])
    eng = unary_union([pixel_text("404", 2.0, 28, 11.5),
                       pixel_text("WICHTEL", 0.9, 28, 24.5),
                       pixel_text("NOT FOUND", 0.9, 28, 33)])
    score = lines(stepped_rect(0.5, 2.5, 55.5, 37.5, 1.5, 1))
    score += [LineString([(25, y), (31, y)]) for y in (48, 56, 64)]
    return Standing("Schild 404", g, eng, score, ground=80, tab_xs=[28])


def server():
    W, H = 44.0, 86.0
    g = stepped_rect(0, 0, W, H - 4, 2)
    g = unary_union([g, box(3, H - 6, 13, H), box(W - 13, H - 6, W - 3, H)])
    eng = [box(3, 3, W - 3, 12).difference(pixel_text("NORDPOL", 0.8, W / 2, 7.5))]
    score, holes = [], []
    for i in range(6):
        y = 15 + i * 11
        score += lines(box(3, y, W - 3, y + 9.5))
        for k in range(3):
            holes.append(box(6 + k * 4.5, y + 3.5, 8.5 + k * 4.5, y + 6))
        eng += [box(22 + j * 2.4, y + 2, 23.2 + j * 2.4, y + 7.5) for j in range(7)]
    g = g.difference(unary_union(holes))
    return Standing("Server NORDPOL-CLOUD", g, unary_union(eng), score, ground=H,
                    tab_xs=[8, W - 8])


def floppy():
    g = box(0, 0, 34, 34).difference(box(31, 0, 34, 3)).difference(box(32.5, 3, 34, 4.5))
    slot = box(18, 2.5, 22, 10)
    g = g.difference(slot)
    eng = unary_union([box(9, 0.6, 25, 12).difference(slot.buffer(0.6)),
                       pixel_text("WUNSCH", 0.6, 17, 21.5),
                       pixel_text("LISTE", 0.6, 17, 27.5),
                       box(2, 30, 4, 32), box(30, 30, 32, 32)])
    return Part("Diskette Wunschliste", g, eng, lines(box(5, 16, 29, 32.5)),
                hang=(20, 6)).clean()


HEART = [
    ".##.##.",
    "#E#####",
    "#######",
    "#######",
    ".#####.",
    "..###..",
    "...#...",
]

COIN = [
    ".####.",
    "##EE##",
    "#E##E#",
    "#E##E#",
    "#E##E#",
    "#E##E#",
    "##EE##",
    ".####.",
]

GIFT = [
    "..#.#...",
    "...#....",
    "########",
    "dEdE#dEd",
    "EdEd#EdE",
    "dEdE#dEd",
    "EdEd#EdE",
    "dEdE#dEd",
]


def small_parts():
    out = []
    g, e, s = sprite(HEART, 3.0)
    out.append(Part("Herz 1UP", g, e, s).clean())
    for i in range(3):
        g, e, s = sprite(COIN, 2.5)
        out.append(Part(f"Muenze {i + 1}", g, e, s).clean())
    g, e, s = sprite(GIFT, 3.0)
    out.append(Part("Geschenk", g, e, s).clean())
    out.append(floppy())
    return out


# =========================================================== Bodenplatte
PLATE_W = 310.0
BACK_Y, FRONT_Y = 24.0, 86.0
# (Teilname, Mitte x auf der Platte, Reihe)
PLACES = {
    "Server NORDPOL-CLOUD": (34, BACK_Y),
    "Wichteltuer Rahmen": (135, BACK_Y),
    "Pixel-Tannenbaum": (245, BACK_Y),
    "Retro-Terminal": (52, FRONT_Y),
    "Pixel-Wichtel": (188, FRONT_Y),
    "Schild 404": (280, FRONT_Y),
}


def plate(standing):
    rng = random.Random(7)
    pts = [(0, 0), (PLATE_W, 0)]
    x = PLATE_W
    while x > 0:
        d = rng.choice([118, 122, 126])
        nx = max(0.0, x - rng.choice([10, 14, 18]))
        pts += [(x, d), (nx, d)]
        x = nx
    g = stepped_rect(0, 0, PLATE_W, 200, 3).intersection(Polygon(pts))
    slots = []
    for p in standing:
        cx, y = PLACES[p.name]
        x0 = cx - p.width / 2 - p.solid.bounds[0]
        for tx in p.tab_xs:
            slots.append(box(x0 + tx - TAB_W / 2, y - SLOT / 2, x0 + tx + TAB_W / 2, y + SLOT / 2))
    g = g.difference(unary_union(slots))
    # Tron-Raster als Linie, Pixel-Fussspuren als Gravur
    grid = [LineString([(x, 0), (x, 130)]) for x in np.arange(12.5, PLATE_W, 12.5)]
    grid += [LineString([(0, y), (PLATE_W, y)]) for y in np.arange(12.5, 130, 12.5)]
    clear = unary_union([s.buffer(2.5) for s in slots] + [box(93, 29, 177, 53)])
    score = [s for l in grid for s in lines(l.difference(clear))]
    prints = []
    for k in range(4):
        x, y = 128 - k * 7 + (k % 2) * 5, 58 + k * 9
        prints += [box(x, y, x + 3, y + 4), box(x + 0.5, y + 4.6, x + 2.5, y + 5.8)]
    eng = unary_union(prints + [pixel_text("PLAYER 1", 0.9, 270, 108)])
    return Part("Bodenplatte", g, eng, score).clean()


# =========================================================== Export
def write(slug, title, parts, max_w):
    placed, size = layout(parts, max_w=max_w)
    svg = OUT / f"{slug}.svg"
    write_svg(svg, placed, size, title)
    cairosvg.svg2png(url=str(svg), write_to=str(OUT / f"{slug}_laservorschau.png"),
                     output_width=1400, background_color="white")
    assert size[0] <= 432 and size[1] <= 406, size
    print(f"{slug}: {len(parts)} Teile, {size[0]:.0f} x {size[1]:.0f} mm")


# =========================================================== Mockup
W, H = 1600, 1200
SC = 4.6
SQ = 0.36  # Stauchung der Bodenplatte (Draufsicht -> Perspektive)
GLOW = [(255, 60, 60), (255, 210, 60), (60, 220, 255), (255, 80, 220), (90, 255, 120)]


def crop(p):
    return Part(p.name, p.solid.intersection(box(-1e3, -1e3, 1e3, p.ground)), p.engrave,
                p.score)


def pixel_sky():
    c = R.background(W, H, 31, c1=(26, 30, 70), c2=(5, 6, 20), bokeh=0)
    d = ImageDraw.Draw(c)
    rng = random.Random(5)
    for _ in range(170):
        x, y, s = rng.randrange(0, W), rng.randrange(0, int(H * 0.75)), rng.choice([4, 6, 8, 10])
        a = rng.randint(90, 230)
        d.rectangle([x, y, x + s, y + s], fill=(235, 240, 255, a))
    # Pixel-Mond
    mx, my, m = 1360, 170, 12
    for i in range(-6, 7):
        for j in range(-6, 7):
            if i * i + j * j <= 36 and (i - 2) ** 2 + (j + 2) ** 2 > 20:
                d.rectangle([mx + i * m, my + j * m, mx + i * m + m - 1, my + j * m + m - 1],
                            fill=(255, 236, 170))
    return c


def place(c, part, x, y_ground, seed, glow=None, alpha=0.5):
    img, px = R.render_part(part, SC, seed=seed, base=(232, 200, 154))
    b = part.solid.bounds
    ox, oy = px(b[0], b[3])
    pos = (x - ox, y_ground - oy)
    if glow:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        holes = [ring for p in polys(part.solid) for ring in p.interiors]
        for i, h in enumerate(holes):
            hx, hy = Polygon(h).centroid.coords[0]
            gx, gy = px(hx, hy)
            col = glow[i % len(glow)]
            r = 16
            dl.ellipse([pos[0] + gx - r, pos[1] + gy - r, pos[0] + gx + r, pos[1] + gy + r],
                       fill=col + (255,))
        c.alpha_composite(lay.filter(ImageFilter.GaussianBlur(5)))
        c.alpha_composite(lay.filter(ImageFilter.GaussianBlur(14)))
    R.shadow(c, img, pos, (10, 8), 9, alpha)
    c.alpha_composite(img, (int(pos[0]), int(pos[1])))
    return pos, px


def flat(c, part, x, y, seed):
    img, px = R.render_part(part, SC, seed=seed, base=(232, 200, 154))
    img = img.resize((img.width, int(img.height * SQ)), Image.LANCZOS)
    b = part.solid.bounds
    ox, oy = px(b[0], b[1])
    pos = (int(x - ox), int(y - oy * SQ))
    R.shadow(c, img, pos, (3, 4), 4, 0.5)
    c.alpha_composite(img, pos)


def mockup(parts):
    frame, leaf, mat, lad, wi, tr, term, kb, sg, srv, small, pl = parts
    c = pixel_sky()
    px0 = (W - PLATE_W * SC) / 2
    top = 700
    X = lambda mm: px0 + mm * SC
    Y = lambda mm: top + mm * SC * SQ
    # Bodenplatte mit Kante
    img, _ = R.render_part(pl, SC, seed=40, base=(236, 214, 178))
    img = img.resize((img.width, int(img.height * SQ)), Image.LANCZOS)
    pad = int(4 * SC)
    edge = R.shade(img, 0.55)
    for k in range(int(MAT * SC), 0, -2):
        c.alpha_composite(edge, (int(px0 - pad), int(top - pad * SQ + k)))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([X(0) + 20, Y(40), X(PLATE_W) + 30, Y(150)], fill=(0, 0, 0, 160))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
    c.alpha_composite(img, (int(px0 - pad), int(top - pad * SQ)))
    flat(c, mat, X(95), Y(31), 41)
    flat(c, kb, X(20), Y(94), 42)

    def stand(p, seed, glow=None, x_mm=None, y_mm=None):
        cx, y = PLACES.get(p.name, (x_mm, y_mm))
        b = p.solid.bounds
        return place(c, crop(p), X(cx - (b[2] - b[0]) / 2), Y(y), seed, glow)

    stand(srv, 43, [(90, 255, 120), (90, 255, 120), (255, 200, 60)])
    place(c, lad, X(70), Y(BACK_Y) + 2, 44)
    pos, px = stand(frame, 45)
    limg, lpx = R.render_part(leaf, SC, seed=46, base=(214, 170, 120))
    lpos = (pos[0] + px(12, 12)[0] - lpx(0, 0)[0], pos[1] + px(12, 12)[1] - lpx(0, 0)[1])
    R.shadow(c, limg, lpos, (5, 4), 4, 0.6)
    c.alpha_composite(limg, (int(lpos[0]), int(lpos[1])))
    stand(tr, 47, GLOW)
    stand(term, 48, [(90, 255, 120)])
    place(c, small[4], X(222), Y(FRONT_Y), 49)                 # Geschenk
    flat(c, small[5], X(104), Y(95), 50)                       # Diskette
    wpos, wpx = stand(wi, 51)
    stand(sg, 52)
    # Muenzen + 1UP ueber dem Wichtel ("Sprung")
    for k, p in enumerate(small[1:4]):
        place(c, p, X(178 + k * 17), Y(FRONT_Y) - 600 + (k % 2) * 28, 53 + k, alpha=0.25)
    place(c, small[0], X(236), Y(FRONT_Y) - 700, 57, alpha=0.25)
    R.label(c, "Pixel-Wichtelwelt",
            "8-Bit-Diorama · 310 × 125 mm Bodenplatte · Stecksystem · 3 mm Sperrholz")
    return c


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fr, lf, mt, ld = door_frame().clean(), door_leaf(), doormat(), ladder()
    wi, tr, te, kb, sg, sv = (wichtel().clean(), tree().clean(), terminal().clean(),
                              keyboard(), sign404().clean(), server().clean())
    small = small_parts()
    pl = plate([fr, wi, tr, te, sg, sv])
    write("07a_wichteltuer", "Pixel-Wichtelwelt: Wichteltuer", [fr, lf, mt, ld], 300)
    write("07b_figuren", "Pixel-Wichtelwelt: Figuren", [tr, wi, sv, te, sg, kb], 330)
    write("07c_bodenplatte", "Pixel-Wichtelwelt: Bodenplatte & Kleinteile",
          [pl] + small + [fit_test()], 330)
    m = mockup([fr, lf, mt, ld, wi, tr, te, kb, sg, sv, small, pl])
    m.convert("RGB").save(OUT / "07_pixel-wichtelwelt_mockup.jpg", quality=92)


if __name__ == "__main__":
    main()
