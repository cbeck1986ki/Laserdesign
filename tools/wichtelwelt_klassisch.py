"""Klassische Wichtelwelt: Wichteltuer mit Steinbogen, Figuren und Steck-Bodenplatte.

Gleiches Stecksystem wie die Pixel-Wichtelwelt, aber mit runden Formen,
Natursteinen, Holzmaserung und Schreibschrift.
Aufruf: python3 tools/wichtelwelt_klassisch.py
"""
import math
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
import wichtelwelt as PX  # noqa: E402
from designs import DECO, MAT, SCRIPT, SLOT, fit_test  # noqa: E402
from lasergeo import (Part, circle, layout, lines, polys, round_convex, star,  # noqa: E402
                      stroke, text, write_svg)
from wichtelwelt import TAB_W, Standing, crop  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "entwuerfe" / "08_wichtelwelt-klassisch"


# ---------------------------------------------------------------- Helfer
def smooth(pts, n=4, closed=True):
    """Chaikin-Glaettung einer Punktfolge."""
    for _ in range(n):
        out = []
        m = len(pts) if closed else len(pts) - 1
        for i in range(m):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            out += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1),
                    (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        pts = out if closed else [pts[0]] + out + [pts[-1]]
    return pts


def arch(x0, y0, w, h):
    """Rundbogen: Breite w, Gesamthoehe h, oben links (x0, y0)."""
    r = w / 2
    return unary_union([box(x0, y0 + r, x0 + w, y0 + h), circle(x0 + r, y0 + r, r, 64)])


def heart(cx, cy, s):
    r = s * 0.3
    g = unary_union([circle(cx - r * 0.95, cy, r), circle(cx + r * 0.95, cy, r),
                     Polygon([(cx - r * 1.85, cy + r * 0.35), (cx + r * 1.85, cy + r * 0.35),
                              (cx, cy + s * 0.75)])])
    return round_convex(g, s * 0.05)


def wavy(x0, y0, x1, amp, period, phase=0.0):
    xs = np.linspace(x0, x1, 40)
    return LineString([(x, y0 + amp * math.sin((x - x0) / period * 2 * math.pi + phase))
                       for x in xs])


def grain(region, spacing, seed, vertical=True):
    """Holzmaserung: leicht gewellte Linien in einer Flaeche."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = region.bounds
    out = []
    for k in np.arange(x0 + spacing / 2, x1, spacing):
        amp, per, ph = rng.uniform(0.4, 1.1), rng.uniform(18, 35), rng.uniform(0, 6)
        ln = LineString([(k + amp * math.sin(y / per * 2 * math.pi + ph), y)
                         for y in np.linspace(y0, y1, 60)])
        out += lines(ln.intersection(region))
    return out


# =========================================================== Wichteltuer
FW, FH = 86.0, 128.0          # Rahmen aussen
LX, LY, LW = 15.0, 15.0, 56.0  # Tuerblatt im Rahmen


def door_frame():
    outer = arch(0, 0, FW, FH)
    leaf = arch(LX, LY, LW, FH - LY)
    band = outer.difference(leaf)
    rng = random.Random(11)
    cuts = []
    cx, cy = FW / 2, FW / 2
    # Bogensteine radial
    a = 180.0
    while a < 360:
        da = rng.uniform(15, 21)
        a = min(360.0, a + da)
        if a < 358:
            t = math.radians(a + rng.uniform(-3, 3))
            cuts.append(LineString([(cx + 20 * math.cos(t), cy + 20 * math.sin(t)),
                                    (cx + 50 * math.cos(t), cy + 50 * math.sin(t))]))
    # Seitensteine: Fugen mit Versatz, ab und zu geteilt
    for side, xa, xb in ((0, 0, LX), (1, LX + LW, FW)):
        y = cy + rng.uniform(0, 4)
        while y < FH - 4:
            cuts.append(LineString([(xa - 1, y), (xb + 1, y + rng.uniform(-1.5, 1.5))]))
            h = rng.uniform(9, 14)
            if rng.random() < 0.35:
                xm = rng.uniform(xa + 5, xb - 5)
                cuts.append(LineString([(xm, y), (xm, y + h)]))
            y += h
    stones = polys(band.difference(unary_union([c.buffer(0.9) for c in cuts])))
    score, eng = [], []
    for s in stones:
        r = s.buffer(-0.9, join_style="round").buffer(0.6, join_style="round")
        score += lines(r)
        if rng.random() < 0.25:     # ein paar Steine mit Struktur
            c = r.centroid
            eng.append(circle(c.x + rng.uniform(-2, 2), c.y + rng.uniform(-2, 2),
                              rng.uniform(0.6, 1.1)))
    eng.append(star(cx, 7.5, 4.2, 1.8))
    return Standing("Tuerrahmen (Steinbogen)", outer, unary_union(eng), score, ground=FH,
                    tab_xs=[LX / 2 + 2, FW - LX / 2 - 2])


def door_leaf():
    H = FH - LY
    g = arch(0, 0, LW, H)
    wc = (LW / 2, 26.0)
    win = circle(*wc, 10.5).difference(unary_union([box(wc[0] - 1.3, 0, wc[0] + 1.3, 40),
                                                    box(0, wc[1] - 1.3, LW, wc[1] + 1.3)]))
    g = g.difference(win)
    planks = [LineString([(x, 0), (x, H)]) for x in np.arange(LW / 5, LW - 1, LW / 5)]
    score = [s for l in planks for s in lines(l.difference(circle(*wc, 12.5)))]
    inner = g.buffer(-1.0).difference(circle(*wc, 12.8))
    score += grain(inner.difference(unary_union([p.buffer(1.2) for p in planks])), 3.7, 5)
    score += lines(circle(*wc, 12.5))
    # Beschlaege: Langbaender mit Ringende, Knauf, Schluesselloch, Tuerklopfer
    hinge = unary_union([box(0, y - 2, 30, y + 2).union(circle(30, y, 3.2))
                         for y in (48.0, 92.0)])
    nails = unary_union([circle(x, y, 0.7) for y in (48.0, 92.0) for x in (6, 14, 22)])
    knob = circle(47, 70, 2.8)
    keyhole = unary_union([circle(47, 77, 1.1), Polygon([(46.2, 77), (47.8, 77), (48.3, 80.5),
                                                          (45.7, 80.5)])])
    eng = unary_union([hinge.difference(nails), knob, keyhole])
    score.append(circle(LW / 2, 62, 4.2).exterior)          # Tuerklopfer-Ring
    eng = unary_union([eng, circle(LW / 2, 57.2, 1.3)])
    return Part("Tuerblatt (aufkleben)", g, eng, score).clean()


def doormat():
    w, h = 72.0, 22.0
    g = round_convex(box(0, 0, w, h), 3)
    for y in np.arange(2, h - 1, 3.0):
        g = g.union(round_convex(box(-2.5, y, 1, y + 1.6), 0.6))
        g = g.union(round_convex(box(w - 1, y, w + 2.5, y + 1.6), 0.6))
    eng = text("Willkommen", SCRIPT, cx=w / 2, cy=h / 2 + 0.5, width=50, max_h=13)
    score = lines(round_convex(box(2.5, 2.5, w - 2.5, h - 2.5), 1.8))
    return Part("Fussmatte", g, eng, score).clean()


def ladder():
    w, h = 28.0, 92.0
    g = unary_union([round_convex(box(0, 0, 4.5, h), 2), round_convex(box(w - 4.5, 0, w, h), 2)]
                    + [round_convex(box(1, y, w - 1, y + 3.4), 1.2)
                       for y in np.arange(8, h - 6, 12)])
    score = grain(box(0.8, 1, 3.7, h - 1), 1.5, 3) + grain(box(w - 3.7, 1, w - 0.8, h - 1), 1.5, 4)
    return Part("Leiter", g, None, score).clean()


def window():
    """Wichtelfenster mit Fensterlaeden zum Aufkleben an die Wand."""
    fw, fh = 30.0, 40.0
    x0 = 17.0
    frame = arch(x0, 0, fw, fh)
    pane = arch(x0 + 3.5, 3.5, fw - 7, fh - 7).difference(unary_union(
        [box(x0 + fw / 2 - 1.2, 0, x0 + fw / 2 + 1.2, fh), box(0, 22, 70, 24.4)]))
    shutters = [round_convex(box(0, 10, 15.5, fh), 1), round_convex(box(x0 + fw + 1.5, 10,
                                                                        x0 + fw + 17, fh), 1)]
    sill = round_convex(box(x0 - 4, fh - 1, x0 + fw + 4, fh + 4), 1.2)
    g = unary_union([frame, *shutters, sill]).difference(pane)
    holes = [heart(7.75, 18, 7), heart(x0 + fw + 9.25, 18, 7)]
    g = g.difference(unary_union(holes))
    score = []
    for s in shutters:
        b = s.bounds
        score += [LineString([(x, b[1]), (x, b[3])]) for x in np.linspace(b[0], b[2], 4)[1:-1]]
        score += [LineString([(b[0], 30), (b[2], 34)])]
    score = [p for l in score for p in lines(l.difference(unary_union(holes).buffer(1)))]
    score += lines(arch(x0 + 1.5, 1.5, fw - 3, fh - 2.5))
    return Part("Wichtelfenster", g, None, score).clean()


# =========================================================== Figuren
def wichtel():
    hat = Polygon(smooth([(-25, 0), (-20, -20), (-12, -38), (-2, -52), (10, -62), (22, -64),
                          (16, -56), (10, -44), (12, -26), (18, -12), (25, 0)], 3))
    pom = circle(22, -64, 5)
    brim = round_convex(box(-27, -5, 27, 4), 3)
    nose = circle(0, 9, 6.5)
    beard = Polygon(smooth([(-21, 2), (-23, 18), (-14, 36), (0, 52), (14, 36), (23, 18), (21, 2)], 3))
    coat = Polygon(smooth([(-20, 6), (-27, 40), (-26, 58), (26, 58), (27, 40), (20, 6)], 2))
    hands = [circle(-27, 34, 5), circle(27, 34, 5)]
    boots = [round_convex(box(-24, 55, -2, 64), 4), round_convex(box(2, 55, 24, 64), 4)]
    g = unary_union([hat, pom, brim, nose, beard, coat, *hands, *boots])
    eng = unary_union([hat.difference(brim.buffer(0.8)).difference(pom.buffer(0.8)),
                       coat.difference(beard.buffer(0.8)).difference(
                           unary_union(hands).buffer(0.8)).difference(box(-30, 54, 30, 70)),
                       *boots])
    score = [LineString([(x, -4), (x, 3)]) for x in np.arange(-23, 24, 3.2)]
    score += lines(nose)
    for k, y in enumerate(np.arange(16, 48, 5)):
        score += lines(wavy(-22, y, 22, 1.0, 9, k).intersection(beard.buffer(-1.5)
                                                              .difference(nose.buffer(1))))
    score += lines(LineString([(0, 55), (0, 58)]))
    return Standing("Wichtel", g, eng, score, ground=64, tab_xs=[-13, 13])


def tree():
    tiers = []
    for top, bot, w in [(10, 40, 30), (26, 62, 44), (44, 86, 60), (64, 110, 76)]:
        tiers.append(Polygon(smooth([(0, top), (w / 2, bot), (w / 4, bot + 3), (0, bot),
                                     (-w / 4, bot + 3), (-w / 2, bot)], 3)))
    st = round_convex(star(0, 8, 9.5, 4.2), 0.6)
    trunk = round_convex(box(-7, 108, 7, 122), 1)
    g = unary_union(tiers + [st, trunk])
    rng = random.Random(3)
    balls, score = [], []
    for y, w in [(36, 18), (58, 30), (82, 44), (104, 58)]:
        for x in np.linspace(-w / 2 + 4, w / 2 - 4, 2 if w < 30 else 4):
            balls.append(circle(x + rng.uniform(-1, 1), y - rng.uniform(0, 2.5),
                                rng.uniform(1.8, 2.4)))
    for top, w in [(30, 28), (52, 42), (76, 58)]:
        score += lines(wavy(-w / 2, top, w / 2, 2.2, w / 1.2).intersection(g.buffer(-1.5)))
    eng = unary_union(balls + [st.buffer(-1.6)])
    return Standing("Tannenbaum", g, eng, score, ground=122, tab_xs=[0])


def mailbox():
    post = box(-4.5, 30, 4.5, 82)
    foot = round_convex(box(-11, 77, 11, 82), 1.5)
    body = round_convex(arch(-17, 0, 34, 32), 1)
    flag = unary_union([box(17, 8, 20, 22), round_convex(box(17, 6, 27, 12), 0.8)])
    g = unary_union([post, foot, body, flag])
    eng = unary_union([text("Post", SCRIPT, cx=0, cy=19, width=20),
                       heart(0, 6.8, 6)])
    score = lines(arch(-14, 3, 28, 26.5)) + grain(box(-3.5, 33, 3.5, 76), 2.2, 7)
    return Standing("Briefkasten", g, eng, score, ground=82, tab_xs=[0])


def signpost():
    post = round_convex(box(-4.5, 0, 4.5, 100), 1.5)
    foot = round_convex(box(-11, 95, 11, 100), 1.5)
    a1 = Polygon([(-8, 12), (36, 12), (44, 20.5), (36, 29), (-8, 29)])
    a2 = Polygon([(-44, 36), (8, 36), (8, 53), (-44, 53), (-52, 44.5)])
    a1, a2 = round_convex(a1, 1.2), round_convex(a2, 1.2)
    cap = Polygon(smooth([(-6, 2), (-4, -2), (2, -3), (7, 1), (5, 3)], 3))
    g = unary_union([post, foot, a1, a2, cap])
    eng = unary_union([text("Nordpol", DECO, cx=16, cy=20.7, width=34, max_h=11),
                       text("Wichtelweg", DECO, cx=-20, cy=44.7, width=46, max_h=11)])
    score = lines(a1.buffer(-1.8)) + lines(a2.buffer(-1.8))
    score += grain(box(-3.5, 56, 3.5, 94), 2.2, 9)
    return Standing("Wegweiser", g, eng, score, ground=100, tab_xs=[0])


def lantern():
    post = round_convex(box(-3, 34, 3, 90), 1)
    foot = round_convex(box(-10, 85, 10, 90), 1.5)
    roof = Polygon([(-14, 12), (0, 2), (14, 12)])
    body = round_convex(box(-10, 11, 10, 34), 1.5)
    ring = circle(0, 0, 3.5).difference(circle(0, 0, 1.6))
    hole = arch(-6.5, 15, 13, 15)
    # Kerze mit Flamme bleibt als Steg im Fensterloch stehen
    candle = unary_union([box(-1.6, 24, 1.6, 30.5),
                          Polygon(smooth([(0, 18), (2.3, 22.2), (0, 24.6), (-2.3, 22.2)], 2))])
    g = unary_union([post, foot, roof, body, ring, box(-1, 0, 1, 4)]).difference(hole)
    g = g.union(candle)
    return Standing("Laterne", g, None, lines(roof.buffer(-1.5)), ground=90, tab_xs=[0])


# =========================================================== Kleinteile
def snowman():
    g = unary_union([circle(0, 30, 13), circle(0, 12, 9.5), round_convex(box(-8, -1, 8, 3), 0.8),
                     round_convex(box(-5, -10, 5, 1), 0.8)])
    eng = unary_union([box(-5, -2.2, 5, 0.2), circle(-3.3, 10, 1.1), circle(3.3, 10, 1.1),
                       Polygon([(0, 12.5), (8, 14.2), (0, 15.2)]),
                       *[circle(0, y, 1.2) for y in (25, 30, 35)]])
    score = [LineString(smooth([(-6, 22), (0, 24.5), (6, 22)], 2, False)),
             LineString([(-4, 21), (-9, 34)])]
    return Part("Schneemann", g, eng, score).clean()


def woodpile():
    rng = random.Random(8)
    logs, score = [], []
    for row, n in enumerate([4, 3, 2]):
        for i in range(n):
            x = i * 9.6 + row * 4.8
            y = -row * 8.4
            r = rng.uniform(4.2, 4.8)
            logs.append(circle(x, y, r))
            score += [circle(x, y, r * 0.6).exterior, circle(x, y, r * 0.25).exterior]
    g = unary_union(logs)
    return Part("Brennholz", g, None, score).clean()


def gift():
    g = unary_union([round_convex(box(0, 8, 28, 30), 1), box(0, 6, 28, 12),
                     circle(9, 4.5, 4.5), circle(19, 4.5, 4.5)]).difference(
        unary_union([circle(9, 4.5, 1.8), circle(19, 4.5, 1.8)]))
    eng = unary_union([box(12, 6, 16, 30), box(0, 17, 28, 21)])
    return Part("Geschenk", g, eng, lines(box(0, 12, 28, 12.01))).clean()


def envelope():
    g = round_convex(box(0, 0, 30, 20), 1).difference(heart(15, 2.5, 4))
    score = [LineString([(0.5, 0.5), (15, 11), (29.5, 0.5)]),
             LineString([(0.5, 19.5), (11, 9)]), LineString([(29.5, 19.5), (19, 9)])]
    eng = text("Wunschzettel", SCRIPT, cx=15, cy=15.8, width=17)
    return Part("Wunschbrief", g, eng, score, hang=(15, 4)).clean()


# =========================================================== Bodenplatte
PLATE_W = 310.0
BACK_Y, FRONT_Y = 24.0, 88.0
PLACES = {
    "Briefkasten": (30, BACK_Y),
    "Tuerrahmen (Steinbogen)": (130, BACK_Y),
    "Tannenbaum": (250, BACK_Y),
    "Wegweiser": (52, FRONT_Y),
    "Wichtel": (190, FRONT_Y),
    "Laterne": (288, FRONT_Y),
}


def plate(standing):
    rng = random.Random(5)
    front = [(x, rng.uniform(116, 128)) for x in np.linspace(PLATE_W, 0, 14)]
    front = smooth([(PLATE_W, 100)] + front + [(0, 100)], 4, closed=False)
    g = round_convex(Polygon([(0, 0), (PLATE_W, 0)] + front), 6)
    slots = []
    for p in standing:
        cx, y = PLACES[p.name]
        x0 = cx - p.width / 2 - p.solid.bounds[0]
        for tx in p.tab_xs:
            slots.append(box(x0 + tx - TAB_W / 2, y - SLOT / 2, x0 + tx + TAB_W / 2, y + SLOT / 2))
    g = g.difference(unary_union(slots))
    # Trittsteine vom Tuerplatz nach vorne, Schneeflocken-Sterne, Hausnummer
    score = []
    for k, (x, y) in enumerate([(132, 60), (124, 72), (134, 84), (126, 97), (136, 110)]):
        st = Polygon(smooth([(x - 6, y - 3), (x + 1, y - 5), (x + 7, y - 2), (x + 5, y + 4),
                             (x - 3, y + 5), (x - 7, y + 1)], 3))
        score += lines(affinity.rotate(st, rng.uniform(-30, 30)))
    eng = [text("Wichtelweg 24", SCRIPT, cx=250, cy=113, width=48)]
    for x, y in [(90, 60), (220, 62), (160, 112), (26, 112), (300, 56), (105, 100)]:
        sf = unary_union([stroke([(x, y), (x + 4.2 * math.cos(a), y + 4.2 * math.sin(a))], 0.9)
                          for a in np.linspace(0, 2 * math.pi, 7)[:-1]])
        eng.append(sf)
    return Part("Bodenplatte", g, unary_union(eng), score).clean()


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
W, H, SC, SQ = PX.W, PX.H, PX.SC, PX.SQ
WARM = [(255, 200, 110)]


def mockup(d):
    c = R.background(W, H, 12, c1=(28, 52, 44), c2=(6, 14, 12), bokeh=55)
    c = R.snow(c, 140, 9)
    px0 = (W - PLATE_W * SC) / 2
    top = 700
    X = lambda mm: px0 + mm * SC
    Y = lambda mm: top + mm * SC * SQ
    pl = d["plate"]
    img, _ = R.render_part(pl, SC, seed=60, base=(238, 222, 196))
    img = img.resize((img.width, int(img.height * SQ)), Image.LANCZOS)
    pad = int(4 * SC)
    edge = R.shade(img, 0.55)
    for k in range(int(MAT * SC), 0, -2):
        c.alpha_composite(edge, (int(px0 - pad), int(top - pad * SQ + k)))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([X(0) + 20, Y(40), X(PLATE_W) + 30, Y(150)], fill=(0, 0, 0, 160))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
    c.alpha_composite(img, (int(px0 - pad), int(top - pad * SQ)))
    PX.flat(c, d["mat"], X(94), Y(32), 61)

    def stand(p, seed, glow=None):
        cx, y = PLACES[p.name]
        b = p.solid.bounds
        return PX.place(c, crop(p), X(cx - (b[2] - b[0]) / 2), Y(y), seed, glow)

    stand(d["mailbox"], 62)
    PX.place(c, d["ladder"], X(64), Y(BACK_Y) + 2, 63)
    pos, px = stand(d["frame"], 64)
    leaf = d["leaf"]
    limg, lpx = R.render_part(leaf, SC, seed=65, base=(200, 150, 100))
    lpos = (pos[0] + px(LX, LY)[0] - lpx(0, 0)[0], pos[1] + px(LX, LY)[1] - lpx(0, 0)[1])
    R.shadow(c, limg, lpos, (5, 4), 4, 0.6)
    c.alpha_composite(limg, (int(lpos[0]), int(lpos[1])))
    stand(d["tree"], 66)
    PX.place(c, d["wood"], X(212), Y(BACK_Y + 30), 67)
    stand(d["sign"], 68)
    PX.place(c, d["snowman"], X(6), Y(FRONT_Y + 22), 69)
    stand(d["wichtel"], 70)
    PX.place(c, d["gift"], X(232), Y(FRONT_Y + 6), 71)
    stand(d["lantern"], 72, WARM)
    R.label(c, "Wichtelwelt klassisch",
            "Steinbogen-Tür · 310 × 125 mm Bodenplatte · Stecksystem · 3 mm Sperrholz")
    return c


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = dict(frame=door_frame().clean(), leaf=door_leaf(), mat=doormat(), ladder=ladder(),
             window=window(), wichtel=wichtel().clean(), tree=tree().clean(),
             mailbox=mailbox().clean(), sign=signpost().clean(), lantern=lantern().clean(),
             snowman=snowman(), wood=woodpile(), gift=gift(), letter=envelope())
    d["plate"] = plate([d[k] for k in ("frame", "wichtel", "tree", "mailbox", "sign", "lantern")])
    write("08a_wichteltuer", "Wichtelwelt klassisch: Wichteltuer",
          [d[k] for k in ("frame", "leaf", "window", "mat", "ladder")], 300)
    write("08b_figuren", "Wichtelwelt klassisch: Figuren",
          [d[k] for k in ("tree", "wichtel", "sign", "mailbox", "lantern")], 330)
    write("08c_bodenplatte", "Wichtelwelt klassisch: Bodenplatte & Kleinteile",
          [d["plate"]] + [d[k] for k in ("snowman", "wood", "gift", "letter")] + [fit_test()], 330)
    mockup(d).convert("RGB").save(OUT / "08_wichtelwelt-klassisch_mockup.jpg", quality=92)


if __name__ == "__main__":
    main()
