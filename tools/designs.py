"""Die fuenf Weihnachts-Entwuerfe als Geometrie (mm, y nach unten)."""
import math
import random

from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from lasergeo import (Part, circle, polar, polys, round_concave, round_convex, star,
                      stroke, text)

MAT = 3.0      # Materialstaerke in mm
SLOT = 2.9     # Schlitzbreite fuer Steckverbindungen (Materialstaerke - ~0.1 Kerf)
SCRIPT = "GreatVibes-Regular.ttf"
DECO = "BerkshireSwash-Regular.ttf"


# =========================================================== 1 Schneeflocken
def _flake(arm_len, w, branches, tips=0.0, spikes=None, center=None, deco=None):
    g = []
    for k in range(6):
        a = -90 + 60 * k
        g.append(stroke([(0, 0), polar(arm_len, a)], w))
        for r, L, ang in branches:
            p = polar(r, a)
            for s in (-1, 1):
                g.append(stroke([p, polar(L, a + s * ang, *p)], w))
        if tips:
            g.append(circle(*polar(arm_len, a), tips))
        if spikes:
            g.append(stroke([(0, 0), polar(spikes, a + 30)], w * 0.9))
        if deco == "diamond":
            c = polar(arm_len * 0.72, a)
            d = Polygon([polar(5.5, a, *c), polar(3.4, a + 90, *c),
                         polar(5.5, a + 180, *c), polar(3.4, a - 90, *c)])
            g.append(d.exterior.buffer(w / 2.4))
    flake = unary_union(g)
    if center == "ring":
        hexo = Polygon([polar(9, -90 + 60 * k) for k in range(6)])
        flake = unary_union([flake, hexo.buffer(1.2)]).difference(
            Polygon([polar(4.8, -60 + 60 * k) for k in range(6)]))
    elif center == "disc":
        flake = unary_union([flake, circle(0, 0, 10.5)])
    # Aufhaengeoese an der oberen Spitze
    top = arm_len + 3.2
    flake = unary_union([flake, circle(0, -top, 4.6)]).difference(circle(0, -top, 2.0))
    return round_concave(flake, 0.6), (0, -top)


def snowflakes():
    parts = []
    f1, h1 = _flake(35, 3.2, [(13, 11, 60), (23.5, 7, 60)], tips=2.6, center="ring")
    parts.append(Part("Flocke Stern", f1, hang=h1))

    f2, h2 = _flake(35, 3.0, [(14, 9, 42), (21, 10, 42), (28, 6, 42)], center="disc",
                    spikes=15)
    eng2 = unary_union([text("2026", "BerkshireSwash-Regular.ttf", cx=0, cy=0.4,
                             width=13.5)])
    parts.append(Part("Flocke Jahreszahl", f2, eng2, [circle(0, 0, 8.6).exterior],
                      hang=h2))

    f3, h3 = _flake(35, 3.0, [(11, 8, 60)], tips=2.2, deco="diamond", spikes=19,
                    center="ring")
    parts.append(Part("Flocke Kristall", f3, hang=h3))
    return [p.clean() for p in parts]


# =========================================================== 2 Steck-Tannenbaum
TIERS = [(-14, -80, 62), (-50, -110, 50), (-82, -138, 38), (-110, -160, 26)]


def _tree_shape(with_star=True):
    g = [box(-9, -24, 9, 0)]  # Stamm
    for yb, yt, hw in TIERS:
        pts = [(0, yt)]
        for i in range(21):
            x = hw - 2 * hw * i / 20
            pts.append((x, yb - 7 * (1 - (x / hw) ** 2)))   # leicht geschwungene Unterkante
        g.append(Polygon(pts))
    if with_star:
        g.append(star(0, -165, 14, 6.2).buffer(0.01))
    return round_concave(round_convex(unary_union(g), 1.0), 0.8)


def _tree_deco(shape, seed, slot_zone):
    rnd = random.Random(seed)
    safe = shape.buffer(-4).difference(slot_zone.buffer(2.5))
    eng, score = [], []
    for yb, yt, hw in TIERS:
        # Girlande als Bogen ueber die Etage
        y0 = yb - (yb - yt) * 0.38
        pts = [(x, y0 + 7 * (1 - (x / (hw * 0.8)) ** 2) - 5)
               for x in [hw * 0.8 * (i / 15 * 2 - 1) for i in range(16)]]
        score.append(LineString(pts))
        # Christbaumkugeln
        for _ in range(4):
            for _try in range(30):
                y = rnd.uniform(yt + 12, yb - 4)
                x = rnd.uniform(-hw, hw)
                c = circle(x, y, 3.0)
                if safe.contains(c) and all(c.distance(e) > 5 for e in eng):
                    eng.append(c)
                    break
    star_eng = star(0, -165, 8.5, 3.8)
    return unary_union(eng + [star_eng]), score


def tree():
    full = _tree_shape(True)
    slot_a = box(-SLOT / 2, -70.5, SLOT / 2, 1)
    a = full.difference(slot_a)
    eng_a, sc_a = _tree_deco(full, 7, slot_a)
    pa = Part("Baum A (Schlitz unten)", a, eng_a, sc_a)

    b_shape = _tree_shape(False).intersection(box(-100, -140, 100, 1))
    b_shape = round_convex(b_shape, 1.0)
    slot_b = box(-SLOT / 2, -141, SLOT / 2, -69.5)
    b = b_shape.difference(slot_b)
    eng_b, sc_b = _tree_deco(b_shape, 11, slot_b)
    eng_b = eng_b.difference(star(0, -165, 9, 4))
    pb = Part("Baum B (Schlitz oben)", b, eng_b, sc_b)
    return [pa.clean(), pb.clean(), fit_test()]


def fit_test():
    """Passungstest-Streifen: Schlitze 2.7-3.2 mm, um die richtige Schlitzbreite zu finden."""
    w = 6 * 13 + 4
    g = box(0, 0, w, 22)
    eng = []
    for i, s in enumerate([2.7, 2.8, 2.9, 3.0, 3.1, 3.2]):
        x = 8 + i * 13
        g = g.difference(box(x - s / 2, 10, x + s / 2, 23))
        eng.append(text(f"{s:.1f}", "BerkshireSwash-Regular.ttf", cx=x, cy=5, width=7))
    return Part("Passungstest", round_convex(g, 0.4), unary_union(eng)).clean()


# =========================================================== 3 Sterne
def stars():
    R, r = 50, 22
    base = round_concave(round_convex(star(0, 0, R, r), 2.2), 1.5)

    # Stern A: Gravur "Frohe Weihnachten"
    hole = circle(0, -38, 2.1)
    a = base.difference(hole)
    eng = unary_union([
        text("Frohe", SCRIPT, cx=0, cy=-21, width=19),
        text("Weihnachten", SCRIPT, cx=0, cy=-6.5, width=52),
        text("2026", DECO, cx=0, cy=10, width=15),
    ])
    sc = [base.buffer(-4.2).exterior.difference(circle(0, -38, 5.5))]
    pa = Part("Stern Gruss", a, eng, sc, hang=(0, -38))

    # Stern B: Rahmen mit Strahlen und Mittelscheibe (Filigran)
    frame_in = round_convex(star(0, 0, R, r).buffer(-5.2, join_style="mitre"), 1.0)
    rays = [stroke([(0, 0), polar(R, -90 + 72 * k)], 3.0) for k in range(5)]
    rays += [stroke([polar(9, -54 + 72 * k), polar(r, -54 + 72 * k)], 2.2) for k in range(5)]
    inner = unary_union(rays + [circle(0, 0, 10.5)]).intersection(frame_in.buffer(0.5))
    b = unary_union([base.difference(frame_in), inner])
    b = round_concave(b, 1.0).difference(hole)
    eng_b = star(0, 0, 7.5, 3.3, rot=-90)
    pb = Part("Stern Filigran", b, eng_b.intersection(b), [circle(0, 0, 9.3).exterior],
              hang=(0, -38))
    return [pa.clean(), pb.clean()]


# =========================================================== 4 Teelicht-Laterne
LX, LY, LZ = 90.0, 90.0, 110.0   # Aussenmasse Laterne (B x T x H)


def _fingers(L, n):
    return [(L * i / n, L * (i + 1) / n) for i in range(n)]


def _wall(width, side, seed):
    """side=False: Vorder/Rueckwand (Zinken aussen), True: Seitenwand."""
    T, H = MAT, LZ
    g = box(0, 0, width, H)
    cuts = []
    for i, (a, b) in enumerate(_fingers(H, 5)):     # senkrechte Kanten
        gap = (i % 2 == 1) if not side else (i % 2 == 0)
        if gap:
            cuts += [box(0, a, T, b), box(width - T, a, width, b)]
    for i, (a, b) in enumerate(_fingers(width, 5)):  # Unterkante (y = H)
        if i % 2 == 0:
            cuts.append(box(a, H - T, b, H))
    g = g.difference(unary_union(cuts))
    hole, eng = _village_window(width, seed)
    return g.difference(hole), eng


def _village_window(W, seed):
    rnd = random.Random(seed)
    m, top, bot = 13.0, 13.0, 15.0 + MAT
    wx0, wx1 = m, W - m
    rad = (wx1 - wx0) / 2
    cy = top + rad
    win = unary_union([circle(W / 2, cy, rad, 64), box(wx0, cy, wx1, LZ - bot)])
    gy = LZ - bot   # Boden des Fensters
    solid = []
    # Schneehuegel
    pts = [(wx0 - 1, gy + 1)]
    ph = rnd.uniform(0, 6)
    for i in range(31):
        x = wx0 - 1 + (wx1 - wx0 + 2) * i / 30
        pts.append((x, gy - 6 - 2.5 * math.sin(x / 9 + ph)))
    pts.append((wx1 + 1, gy + 1))
    solid.append(Polygon(pts))
    windows = []
    # Haeuser
    xs = [wx0 + 6, W / 2 + rnd.uniform(-4, 4), wx1 - 6] if seed % 2 else [wx0 + 12, wx1 - 13]
    for i, x in enumerate(xs):
        hw = rnd.uniform(7, 9.5)
        hh = rnd.uniform(13, 20) if i != 1 else rnd.uniform(20, 26)
        base_y = gy - 5
        roof = rnd.uniform(8, 11)
        house = Polygon([(x - hw, base_y), (x - hw, base_y - hh), (x, base_y - hh - roof),
                         (x + hw, base_y - hh), (x + hw, base_y)])
        if rnd.random() < 0.6:   # Schornstein
            cx = x + hw * 0.45
            house = house.union(box(cx - 1.8, base_y - hh - roof * 0.9, cx + 1.8,
                                    base_y - hh - roof * 0.3))
        solid.append(house)
        # Fenster (Licht scheint durch)
        for wy in ([base_y - hh * 0.62] + ([base_y - hh * 0.25] if hh > 17 else [])):
            for wx in (x - hw * 0.45, x + hw * 0.45):
                windows.append(box(wx - 1.9, wy - 2.4, wx + 1.9, wy + 2.4))
        if hh < 17:
            windows.append(box(x - 1.8, base_y - 6, x + 1.8, base_y + 0.5))  # Tuer
        else:
            windows.append(circle(x, base_y - hh - roof * 0.45, 1.8))       # Rundfenster
    # Tannen zwischen den Haeusern
    for x in ([W / 2] if not seed % 2 else []):
        h = rnd.uniform(22, 32)
        tr = []
        for k in range(3):
            yb = gy - 5 - k * h * 0.27
            hw = 7.5 - k * 1.8
            tr.append(Polygon([(x - hw, yb), (x, yb - h * 0.45), (x + hw, yb)]))
        tr.append(box(x - 1.2, gy - 7, x + 1.2, gy - 4))
        solid.append(unary_union(tr))
    solid = round_convex(unary_union(solid), 0.7).intersection(win.buffer(2))
    hole = round_concave(win.difference(solid), 0.5)
    hole = unary_union([hole, *[w.intersection(solid.buffer(-1.4)) for w in windows]])
    hole = unary_union([p for p in polys(hole) if p.area > 2.0])   # Splitter entfernen
    # Sterne im oberen Rahmen als kleine Ausschnitte
    stars_g = []
    for k, sx in enumerate([7, W - 7]):
        stars_g.append(round_convex(star(sx, 9, 3.6, 1.6), 0.3))
    eng = text("Frohe Weihnachten", SCRIPT, cx=W / 2, cy=LZ - 10.5, width=W - 26)
    return unary_union([hole] + stars_g), eng


def lantern():
    parts = []
    for i, (name, side, seed) in enumerate([("Vorderwand", False, 1), ("Rueckwand", False, 2),
                                            ("Seitenwand links", True, 3),
                                            ("Seitenwand rechts", True, 4)]):
        w, eng = _wall(LX if not side else LY, side, seed)
        if i > 0:
            eng = None
        parts.append(Part(name, w, eng))
    # Boden: Zinken an den Enden (Ecken voll)
    T = MAT
    g = box(0, 0, LX, LY)
    cuts = []
    for i, (a, b) in enumerate(_fingers(LX, 5)):
        if i % 2 == 1:
            cuts += [box(a, 0, b, T), box(a, LY - T, b, LY)]
    for i, (a, b) in enumerate(_fingers(LY, 5)):
        if i % 2 == 1:
            cuts += [box(0, a, T, b), box(LX - T, a, LX, b)]
    g = g.difference(unary_union(cuts)).difference(circle(LX / 2, LY / 2, 11))
    eng = unary_union([star(LX / 2 + 24 * math.cos(math.radians(a)), LY / 2 + 24 *
                            math.sin(math.radians(a)), 3.2, 1.4) for a in range(0, 360, 45)])
    parts.append(Part("Boden", g, eng))
    return [p.clean() for p in parts]


# =========================================================== 5 Geschenkanhaenger
def _bauble_tag(line1, line2):
    g = unary_union([circle(0, 0, 27), box(-8, -32, 8, -24), circle(0, -35, 5.2)])
    g = round_concave(g, 1.2).difference(circle(0, -35, 2.2))
    eng = unary_union([text(line1, SCRIPT, cx=0, cy=-6, width=26, max_h=11),
                       text(line2, SCRIPT, cx=0, cy=5.5, width=42, max_h=11)])
    sc = [LineString([(-8, -26.5), (8, -26.5)])]
    for y in (-17, 16.5):
        pts = [(x, y + 1.3 * math.sin(x / 2.2)) for x in [-27 + i * 0.5 for i in range(109)]]
        sc.append(LineString(pts))
    return Part("Anhaenger Kugel", g, eng, sc, hang=(0, -35))


def _tree_tag(word):
    tr = [Polygon([(-hw, yb), (0, yb - h), (hw, yb)])
          for yb, h, hw in [(28, 30, 30), (12, 28, 24), (-4, 26, 18)]]
    g = round_convex(unary_union(tr + [box(-5, 26, 5, 34)]), 1.4)
    g = round_concave(g, 0.8).difference(circle(0, -20, 2.1))
    eng = unary_union([text(word, SCRIPT, cx=0, cy=18.5, width=27, max_h=10),
                       star(0, 2, 4.2, 1.8)])
    sc = [LineString([(-14 + i * 0.5, 7 + 3 * math.sin(i / 9)) for i in range(57)])]
    return Part("Anhaenger Baum", g, eng, sc, hang=(0, -20))


def _classic_tag(headline):
    pts = [(-22, -28), (-12, -40), (12, -40), (22, -28), (22, 40), (-22, 40)]
    g = round_convex(Polygon(pts), 2.0).difference(circle(0, -32, 2.6))
    flake = unary_union([stroke([(0, -14), polar(6, -90 + 60 * k, 0, -14)], 0.9)
                         for k in range(6)] +
                        [stroke([polar(3.6, -90 + 60 * k, 0, -14),
                                 polar(5.6, -90 + 60 * k + s * 22, 0, -14)], 0.8)
                         for k in range(6) for s in (-1, 1)])
    eng = unary_union([flake,
                       text(headline, DECO, cx=0, cy=2, width=34),
                       text("Für:", SCRIPT, cx=-14, cy=17, width=9),
                       text("Von:", SCRIPT, cx=-13.6, cy=28, width=10)])
    sc = [circle(0, -32, 4.6).exterior, LineString([(-7.5, 19), (17, 19)]),
          LineString([(-7.5, 30), (17, 30)])]
    return Part("Anhaenger klassisch", g, eng, sc, hang=(0, -32))


def tags():
    parts = [_bauble_tag("Frohe", "Weihnachten"), _bauble_tag("Frohes", "Fest"),
             _tree_tag("Für dich"), _tree_tag("Danke"),
             _classic_tag("Ho Ho Ho!"), _classic_tag("Frohes Fest")]
    return [p.clean() for p in parts]
