"""Halloween-Deko fuer die Candybar: Laser-Teile (xTool D1 Pro) und Schneideplotter-Motive.
Einheiten mm, y nach unten."""
import math
import random

from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from designs import MAT, SLOT, _fingers
from lasergeo import (Part, circle, polar, polys, round_concave, round_convex, star,
                      stroke, text)

SPOOKY = "Creepster-Regular.ttf"
DECO = "BerkshireSwash-Regular.ttf"


# =========================================================== Motive
def ellipse(cx, cy, rx, ry, res=48):
    return affinity.translate(affinity.scale(circle(0, 0, 1, res), rx, ry), cx, cy)


def mirror_x(g):
    return affinity.scale(g, -1, 1, origin=(0, 0))


def _qarc(p0, p1, lift, n=10):
    cx, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - lift
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t * t * p1[1])
            for t in [i / n for i in range(1, n + 1)]]


def bat(span, cx=0.0, cy=0.0, rot=0.0):
    """Fledermaus-Silhouette, Spannweite span, Mittelpunkt = Koerper."""
    pts = [(0.06, -0.10), (0.12, -0.24), (0.22, -0.44), (0.34, -0.58), (0.37, -0.64),
           (0.42, -0.57), (0.56, -0.52), (0.70, -0.54), (0.85, -0.61), (1.0, -0.70)]
    fingers = [(1.0, -0.70), (0.80, -0.16), (0.55, -0.01), (0.30, 0.08), (0.10, 0.12)]
    for p0, p1 in zip(fingers, fingers[1:]):
        pts += _qarc(p0, p1, 0.13)
    pts.append((0.05, 0.10))
    wing = Polygon(pts).buffer(0)
    body = unary_union([
        ellipse(0, -0.02, 0.10, 0.20),
        circle(0, -0.26, 0.10, 24),
        Polygon([(0.0, -0.30), (0.09, -0.50), (0.10, -0.24)]),
        Polygon([(0.0, -0.30), (-0.09, -0.50), (-0.10, -0.24)]),
    ])
    g = unary_union([wing, mirror_x(wing), body])
    g = affinity.scale(g, span / 2, span / 2, origin=(0, 0))
    g = round_convex(round_concave(g, span * 0.006), span * 0.003)
    g = unary_union([Polygon(p.exterior) for p in polys(g)])   # Zwickel schliessen
    g = affinity.rotate(g, rot, origin=(0, 0))
    return affinity.translate(g, cx, cy)


def pumpkin_shape(w, cx=0.0, cy=0.0, stem=True):
    """Kuerbis; (cx, cy) = Mitte des Koerpers. Hoehe Koerper ~ 0.78 w."""
    h = 0.78 * w
    lobes = [ellipse(0, 0, 0.26 * w, h / 2)]
    for s in (-1, 1):
        lobes.append(ellipse(s * 0.17 * w, 0.01 * h, 0.27 * w, 0.485 * h))
        lobes.append(ellipse(s * 0.30 * w, 0.03 * h, 0.20 * w, 0.44 * h))
    g = unary_union(lobes)
    if stem:
        st = Polygon([(-0.05 * w, -0.40 * h), (-0.045 * w, -0.58 * h), (0.0, -0.66 * h),
                      (0.06 * w, -0.70 * h), (0.07 * w, -0.64 * h), (0.035 * w, -0.57 * h),
                      (0.05 * w, -0.40 * h)])
        g = unary_union([g, st])
    g = round_concave(g, w * 0.015)
    return affinity.translate(g, cx, cy)


def pumpkin_ribs(w, cx=0.0, cy=0.0):
    h = 0.78 * w
    out = []
    for s, k in [(-1, 0.13), (1, 0.13), (-1, 0.33), (1, 0.33)]:
        pts = [(s * k * w * math.sin(math.pi * t) ** 0.7 * 0.9 + s * k * w * 0.1,
                -0.40 * h + 0.80 * h * t) for t in [i / 24 for i in range(25)]]
        out.append(affinity.translate(LineString(pts), cx, cy))
    return out


def jack_face(w, cx=0.0, cy=0.0, style=0):
    """Gesicht eines Kuerbisses (Flaechen, zum Ausschneiden/Gravieren)."""
    h = 0.78 * w
    eye_y = -0.10 * h
    def grin(y0, y1, curve, x):
        """Mund zwischen zwei Boegen, x = halbe Breite."""
        top = [(t, y0 + curve * (1 - (t / x) ** 2)) for t in
               [-x + 2 * x * i / 30 for i in range(31)]]
        bot = [(t, y1 + curve * 1.6 * (1 - (t / x) ** 2)) for t in
               [x - 2 * x * i / 30 for i in range(31)]]
        return Polygon(top + bot)

    if style == 0:      # klassisch: Dreiecke, Grinsen mit Zaehnen
        eyes = [Polygon([(s * 0.10 * w, eye_y + 0.08 * h), (s * 0.30 * w, eye_y + 0.08 * h),
                         (s * 0.20 * w, eye_y - 0.12 * h)]) for s in (-1, 1)]
        nose = Polygon([(-0.05 * w, 0.07 * h), (0.05 * w, 0.07 * h), (0, -0.02 * h)])
        mouth = grin(0.12 * h, 0.20 * h, 0.08 * h, 0.34 * w)
        teeth = [box(-0.14 * w, 0.0, -0.06 * w, 0.255 * h),
                 box(0.07 * w, 0.29 * h, 0.15 * w, 0.45 * h)]
        mouth = mouth.difference(unary_union(teeth))
    elif style == 1:    # froehlich: Halbmond-Augen, breites Grinsen
        eyes = [ellipse(s * 0.19 * w, eye_y, 0.09 * w, 0.10 * h).difference(
            ellipse(s * 0.19 * w, eye_y + 0.07 * h, 0.11 * w, 0.09 * h)) for s in (-1, 1)]
        nose = Polygon([(-0.04 * w, 0.06 * h), (0.04 * w, 0.06 * h), (0, 0.0)])
        mouth = grin(0.11 * h, 0.17 * h, 0.12 * h, 0.32 * w)
        mouth = mouth.difference(box(-0.08 * w, 0.0, -0.035 * w, 0.40 * h)).difference(
            box(0.045 * w, 0.0, 0.09 * w, 0.40 * h))
    else:               # boese: schraege Augen, Spitzzaehne
        eyes = [Polygon([(s * 0.07 * w, eye_y + 0.02 * h), (s * 0.32 * w, eye_y - 0.10 * h),
                         (s * 0.27 * w, eye_y + 0.09 * h), (s * 0.12 * w, eye_y + 0.10 * h)])
                for s in (-1, 1)]
        nose = Polygon([(-0.06 * w, 0.07 * h), (0, -0.01 * h), (0.06 * w, 0.07 * h),
                        (0, 0.04 * h)])
        mouth = grin(0.12 * h, 0.19 * h, 0.09 * h, 0.36 * w)
        teeth = []
        for k, x in enumerate([-0.20, 0.0, 0.20]):
            teeth.append(Polygon([((x - 0.05) * w, 0.10 * h), ((x + 0.05) * w, 0.10 * h),
                                  (x * w, 0.28 * h)]))
        for x in [-0.10, 0.10]:
            teeth.append(Polygon([((x - 0.05) * w, 0.40 * h), ((x + 0.05) * w, 0.40 * h),
                                  (x * w, 0.27 * h)]))
        mouth = mouth.difference(unary_union(teeth))
        mouth = unary_union([p for p in polys(mouth) if p.area > 0.002 * w * w])
    g = round_convex(unary_union(eyes + [nose, mouth.buffer(0)]), w * 0.006)
    return affinity.translate(g, cx, cy)


def ghost_shape(w, h, cx=0.0, cy=0.0, flat=False):
    """Gespenst; (cx, cy) = Mittelpunkt des Kopfes. Wellensaum unten (3 Zipfel)."""
    r = w / 2
    yb = h - r          # tiefster Punkt der Zipfel
    a = 0.16 * w        # Tiefe der Zipfel
    pts = [(-r - 0.04 * w * math.sin(t * math.pi), t * (yb - a)) for t in
           [i / 12 for i in range(13)]]
    for i in range(1, 60):
        t = i / 60
        pts.append((-r + w * t, yb - a * (1 - abs(math.sin(3 * math.pi * t)))))
    pts += [(r + 0.04 * w * math.sin(t * math.pi), t * (yb - a)) for t in
            [1 - i / 12 for i in range(13)]]
    g = unary_union([circle(0, 0, r, 64), Polygon(pts).buffer(0)])
    if flat:
        g = g.intersection(box(-w, -w, w, yb - 0.04 * w))
    g = round_convex(round_concave(g, w * 0.02), w * 0.01)
    return affinity.translate(g, cx, cy)


def ghost_face(w, cx=0.0, cy=0.0, style=0):
    eyes = [ellipse(s * 0.17 * w, 0.02 * w, 0.075 * w, 0.115 * w) for s in (-1, 1)]
    if style == 0:
        mouth = ellipse(0, 0.25 * w, 0.075 * w, 0.10 * w)
    elif style == 1:
        mouth = ellipse(0, 0.20 * w, 0.20 * w, 0.12 * w).difference(
            ellipse(0, 0.13 * w, 0.24 * w, 0.11 * w))
    else:
        mouth = ellipse(0, 0.24 * w, 0.14 * w, 0.055 * w)
        eyes = [e.difference(ellipse(s * 0.17 * w, -0.08 * w, 0.12 * w, 0.07 * w))
                for e, s in zip(eyes, (-1, 1))]
    return affinity.translate(unary_union(eyes + [mouth]), cx, cy)


def cat_shape(h, cx=0.0, by=0.0):
    """Sitzende Katze; (cx, by) = Mitte der Standflaeche, Hoehe h."""
    k = h / 100
    body = unary_union([ellipse(0, -26, 21, 30), ellipse(0, -9, 27, 13),
                        Polygon([(-10, -60), (10, -60), (17, -40), (-17, -40)])])
    head = ellipse(0, -70, 15, 13.5)
    ears = [Polygon([(-14, -72), (-13, -96), (-2, -81)]),
            Polygon([(14, -72), (13, -96), (2, -81)])]
    tail_pts = [(20, -3)] + [(30 + 14 * math.sin(t * 2.6), -5 - 40 * t)
                             for t in [i / 20 for i in range(1, 21)]]
    tail = stroke(tail_pts, 7)
    g = unary_union([body, head, *ears, tail]).intersection(box(-60, -120, 60, 0))
    g = round_convex(round_concave(g, 2.0), 1.0)
    g = affinity.scale(g, k, k, origin=(0, 0))
    return affinity.translate(g, cx, by)


def cat_eyes(h, cx=0.0, by=0.0):
    k = h / 100
    eyes = []
    for s in (-1, 1):
        e = ellipse(s * 6.2, -71, 3.6, 3.4).intersection(ellipse(s * 6.2, -71, 6.5, 2.6)
                                                           .buffer(0))
        eyes.append(affinity.rotate(e, s * 18, origin=(s * 6.2, -71)))
    nose = Polygon([(-1.6, -64.5), (1.6, -64.5), (0, -62.5)])
    g = unary_union(eyes + [nose])
    g = affinity.scale(g, k, k, origin=(0, 0))
    return affinity.translate(g, cx, by)


def tombstone(w, h, cx=0.0, by=0.0, kind=0):
    """Grabstein; (cx, by) = Mitte der Standflaeche."""
    if kind == 0:       # rund
        g = unary_union([box(-w / 2, -(h - w / 2), w / 2, 0), circle(0, -(h - w / 2), w / 2, 64)])
    elif kind == 1:     # Kreuz oben
        bh = h * 0.70
        arm = w * 0.17
        g = unary_union([box(-w / 2, -bh, w / 2, 0),
                         Polygon([(-w / 2, -bh), (-w * 0.30, -bh - w * 0.10),
                                  (w * 0.30, -bh - w * 0.10), (w / 2, -bh)]),
                         box(-arm / 2, -h, arm / 2, -bh), box(-w * 0.34, -h + h * 0.09,
                                                             w * 0.34, -h + h * 0.09 + arm)])
    else:               # Spitzbogen mit Schultern
        sh = h * 0.72
        g = unary_union([box(-w / 2, -sh, w / 2, 0),
                         Polygon([(-w / 2, -sh), (-w * 0.34, -sh - h * 0.06),
                                  (-w * 0.20, -sh - h * 0.06), (0, -h),
                                  (w * 0.20, -sh - h * 0.06), (w * 0.34, -sh - h * 0.06),
                                  (w / 2, -sh)])])
    g = round_concave(round_convex(g, 1.6), 1.2)
    return affinity.translate(g, cx, by)


def web(r, spokes=8, rings=6, w=2.2, start=-90, span=360, seed=1, sag=0.18):
    """Spinnennetz aus Strichen (Speichen + durchhaengende Faeden)."""
    rnd = random.Random(seed)
    closed = span >= 360
    n = spokes if closed else spokes + 1
    angs = [start + span * i / (spokes if closed else spokes) for i in range(n)]
    lens = [r * rnd.uniform(0.92, 1.0) for _ in angs]
    g = [stroke([(0, 0), polar(L, a)], w) for a, L in zip(angs, lens)]
    for k in range(1, rings + 1):
        rr = r * k / (rings + 0.6)
        for i in range(len(angs) - (0 if closed else 1)):
            a0, a1 = angs[i], angs[(i + 1) % len(angs)]
            if a1 < a0:
                a1 += 360
            p0, p1 = polar(rr, a0), polar(rr, a1)
            pts = []
            for t in [j / 12 for j in range(13)]:
                x = p0[0] + (p1[0] - p0[0]) * t
                y = p0[1] + (p1[1] - p0[1]) * t
                d = math.hypot(x, y) or 1
                s = 1 - sag * math.sin(math.pi * t)
                pts.append((x * s, y * s))
            g.append(stroke(pts, w * 0.8))
    return unary_union(g)


def spider(size, cx=0.0, cy=0.0, w=None):
    w = w or size * 0.07
    body = unary_union([ellipse(0, size * 0.10, size * 0.16, size * 0.20),
                        circle(0, -size * 0.13, size * 0.10, 24)])
    legs = []
    for s in (-1, 1):
        for i, a in enumerate([-50, -20, 10, 40]):
            p0 = (s * size * 0.08, size * (-0.05 + 0.06 * i))
            p1 = (s * size * 0.38, p0[1] + size * (a / 100) - size * 0.12)
            p2 = (s * size * 0.50, p1[1] + size * 0.30)
            legs.append(stroke([p0, p1, p2], w))
    return affinity.translate(unary_union([body] + legs), cx, cy)


def crescent(r, cx=0.0, cy=0.0, rot=0):
    g = circle(0, 0, r, 64).difference(circle(r * 0.45, -r * 0.2, r * 0.85, 64))
    return affinity.translate(affinity.rotate(g, rot, origin=(0, 0)), cx, cy)


def rrect(x0, y0, x1, y1, r):
    return round_convex(box(x0, y0, x1, y1), r)


# =========================================================== Laser 1: Candy-Bar-Schild
SIGN_W, SIGN_H = 280.0, 130.0
FOOT_L, FOOT_H = 70.0, 22.0


def foot(name="Standfuss"):
    """Standfuss mit Schlitz von oben (Kreuzverbindung mit einem Schlitz von unten)."""
    L, H = FOOT_L, FOOT_H
    g = Polygon([(-L / 2, 0), (-L / 2, -6), (-L * 0.30, -H * 0.62), (-10, -H), (10, -H),
                 (L * 0.30, -H * 0.62), (L / 2, -6), (L / 2, 0)])
    g = round_convex(g, 2.0)
    g = g.difference(box(-SLOT / 2, -H - 1, SLOT / 2, -H / 2))
    g = g.difference(box(-L * 0.28, -2.0, L * 0.28, 1))    # zwei Auflagen statt Flaeche
    return Part(name, round_concave(g, 0.4))


def bottom_slot(x):
    return box(x - SLOT / 2, -FOOT_H / 2, x + SLOT / 2, 1)


def candybar_sign():
    W, H = SIGN_W, SIGN_H
    # Brett mit Wellen-Oberkante, Ursprung: Mitte der Unterkante
    top = [(-W / 2, -H + 12)]
    for i in range(41):
        x = -W / 2 + W * i / 40
        top.append((x, -H + 4 * math.sin(x / 18) - 3))
    top.append((W / 2, -H + 12))
    board = unary_union([rrect(-W / 2, -H + 8, W / 2, 0, 8), Polygon(top).buffer(0)])
    board = round_convex(board, 6)
    pk_w = 74
    pk_c = (-W / 2 + 22, -31)
    pk = pumpkin_shape(pk_w, *pk_c)
    b1 = bat(72, W / 2 - 40, -H - 6, rot=6)
    b2 = bat(46, W / 2 - 100, -H - 6, rot=-8)
    g = round_concave(unary_union([board, pk, b1, b2]), 2.0)
    # Ausschnitte: Kuerbisgesicht, Aufhaengeloecher, Fusschlitze
    face = jack_face(pk_w, *pk_c, 0)
    holes = [circle(-W / 2 + 60, -H + 6, 2.6), circle(W / 2 - 60, -H + 6, 2.6)]
    slots = [bottom_slot(-75), bottom_slot(75)]
    g = g.difference(unary_union([face, *holes, *slots]))
    eng = unary_union([
        text("Candy Bar", SPOOKY, cx=14, cy=-H * 0.56, width=170),
        text("Süßes oder Saures", DECO, cx=14, cy=-H * 0.24, width=120),
        bat(20, 14 - 78, -H * 0.25), bat(20, 14 + 78, -H * 0.25),
    ])
    sc = [rrect(-W / 2 + 7, -H + 13, W / 2 - 7, -7, 5).exterior]
    sc = [s.difference(pk.buffer(3)).difference(unary_union(slots).buffer(3))
          .difference(unary_union(holes).buffer(3)) for s in sc]
    sc += pumpkin_ribs(pk_w, *pk_c)
    sc = [s.difference(face.buffer(1.5)) for s in sc]
    sign = Part("Schild Candy Bar", g, eng, sc, hang=(0, -H)).clean()
    return [sign, foot("Standfuss 1"), foot("Standfuss 2")]


# =========================================================== Laser 2: Halloween-Laterne
LX, LY, LZ = 90.0, 90.0, 110.0


def _wall(width, side, holes, eng=None, score=None, name=""):
    T, H = MAT, LZ
    g = box(0, 0, width, H)
    cuts = []
    for i, (a, b) in enumerate(_fingers(H, 5)):
        gap = (i % 2 == 1) if not side else (i % 2 == 0)
        if gap:
            cuts += [box(0, a, T, b), box(width - T, a, width, b)]
    for i, (a, b) in enumerate(_fingers(width, 5)):
        if i % 2 == 0:
            cuts.append(box(a, H - T, b, H))
    g = g.difference(unary_union(cuts)).difference(holes)
    return Part(name, g, eng, score or [])


def _front():
    W = LX
    pw, pcx, pcy = 70, W / 2, 56
    face = jack_face(pw, pcx, pcy, 2)
    outline = pumpkin_shape(pw, pcx, pcy)
    sc = [LineString(outline.exterior.coords)] + pumpkin_ribs(pw, pcx, pcy)
    sc = [s.difference(face.buffer(1.6)) for s in sc]
    eng = unary_union([text("Süßes oder Saures", DECO, cx=W / 2, cy=LZ - 11, width=W - 24),
                       bat(14, 14, 13, rot=-15), bat(11, W - 15, 18, rot=12)])
    return _wall(W, False, face, eng, sc, "Vorderwand Kuerbis")


def _graveyard(W):
    """Fensterausschnitt Friedhof: Bogenfenster minus Silhouette (Huegel, Steine, Baum)."""
    x0, x1, yt, yb = 12, W - 12, 30, LZ - 16 - MAT
    rad = (x1 - x0) / 2
    win = unary_union([circle(W / 2, yt + rad, rad, 64).intersection(box(0, 0, W, yt + rad)),
                       box(x0, yt + rad, x1, yb)])
    sil = []
    pts = [(x0 - 2, yb + 2)] + [(x, yb - 8 - 3 * math.sin(x / 10 + 1)) for x in
                                [x0 - 2 + (x1 - x0 + 4) * i / 30 for i in range(31)]]
    pts.append((x1 + 2, yb + 2))
    sil.append(Polygon(pts))
    sil.append(tombstone(12, 17, W / 2 + 4, yb - 7, 0))
    sil.append(tombstone(10, 20, W / 2 + 20, yb - 6, 1))
    sil.append(tombstone(8, 11, W / 2 - 9, yb - 8, 0))
    # kahler Baum links, Ast reicht bis an den Rahmen
    tx, ty = x0 + 10, yb - 8
    tr = [stroke([(tx, ty + 2), (tx + 1, ty - 22), (tx - 1, ty - 36)], 3.4),
          stroke([(tx + 1, ty - 20), (tx + 10, ty - 30), (tx + 13, ty - 40)], 2.0),
          stroke([(tx - 1, ty - 30), (x0 - 4, ty - 42)], 2.2),
          stroke([(tx + 6, ty - 26), (tx + 18, ty - 27)], 1.6),
          stroke([(tx, ty - 35), (tx + 4, ty - 46)], 1.6)]
    sil += tr
    sil = round_convex(unary_union(sil), 0.4).intersection(win.buffer(3))
    hole = round_concave(win.difference(sil), 0.5)
    hole = unary_union([p for p in polys(hole) if p.area > 2.0])
    bats = unary_union([bat(15, W / 2 - 18, 15, -10), bat(12, W / 2 + 4, 11, 8),
                        bat(15, W / 2 + 24, 17, 14)])
    return unary_union([hole, bats])


def _night_sky(W):
    g = [crescent(16, W / 2 - 6, 34, -20)]
    g += [bat(20, W / 2 + 14, 66, 10), bat(15, W / 2 - 18, 78, -12), bat(12, W / 2 + 16, 88, 6)]
    for x, y, r in [(17, 18, 3.2), (W - 18, 26, 3.6), (W - 22, 52, 2.6), (19, 56, 2.8),
                    (W / 2 + 20, 16, 2.4)]:
        g.append(round_convex(star(x, y, r, r * 0.45), 0.25))
    return unary_union(g)


def lantern():
    parts = [_front(),
             _wall(LX, False, _night_sky(LX), name="Rueckwand Nachthimmel"),
             _wall(LY, True, _graveyard(LY), name="Seitenwand Friedhof 1"),
             _wall(LY, True, affinity.translate(mirror_x(_graveyard(LY)), LY, 0),
                   name="Seitenwand Friedhof 2")]
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
    eng = unary_union([bat(13, LX / 2 + 26 * math.cos(math.radians(a)),
                           LY / 2 + 26 * math.sin(math.radians(a)), a + 90)
                       for a in range(0, 360, 60)])
    parts.append(Part("Boden", g, eng))
    return [p.clean() for p in parts]


# =========================================================== Laser 3: Glas-Anhaenger
def _tag_pumpkin(name, style):
    w = 64
    hole = (0, -0.29 * w)
    g = pumpkin_shape(w, 0, 0).difference(circle(*hole, 2.4))
    eng = unary_union([text(name, SPOOKY, cx=0, cy=4, width=w * 0.70, max_h=11),
                       jack_face(30, 0, -10, style).intersection(box(-30, -18, 30, -6))])
    sc = [LineString(pumpkin_shape(w, 0, 0, stem=False).buffer(-3).exterior.coords)
          .difference(circle(*hole, 5.5))]
    return Part(f"Anhaenger Kuerbis {name}", g, eng, sc, hang=hole)


def _tag_ghost(name):
    g = ghost_shape(50, 74, 0, 0).difference(circle(0, -18, 2.2))
    eng = unary_union([ghost_face(50, 0, -8, 0).intersection(box(-30, -20, 30, 8)),
                       text(name, SPOOKY, cx=0, cy=22, width=40, max_h=10)])
    return Part(f"Anhaenger Geist {name}", g, eng, [], hang=(0, -18))


def _tag_stone(name):
    g = tombstone(50, 70, 0, 35, 0).difference(circle(0, -26, 2.2))
    eng = unary_union([text("R.I.P.", DECO, cx=0, cy=-10, width=24),
                       text(name, SPOOKY, cx=0, cy=10, width=40, max_h=10)])
    sc = [tombstone(42, 62, 0, 31, 0).exterior.difference(circle(0, -26, 5)),
          LineString([(-14, 0), (14, 0)]),
          LineString([(14, 34), (11, 26), (15, 21), (12, 15)])]
    return Part(f"Anhaenger Grabstein {name}", g, eng, sc, hang=(0, -26))


def _tag_cauldron(name):
    body = unary_union([ellipse(0, 4, 31, 24), rrect(-29, -20, 29, -14, 3),
                        box(-20, 20, -14, 30), box(14, 20, 20, 30)])
    bubbles = unary_union([circle(-12, -22, 6), circle(1, -26, 8), circle(13, -21, 5),
                           ellipse(0, -18, 22, 5)])
    g = round_concave(unary_union([body, bubbles]), 1.2).difference(circle(1, -27, 2.4))
    eng = text(name, SPOOKY, cx=0, cy=6, width=46, max_h=10)
    sc = [LineString([(-27, -12), (27, -12)]),
          LineString([(x, 16 + 3 * math.sin(x / 4)) for x in [-24 + i for i in range(49)]])]
    return Part(f"Anhaenger Kessel {name}", g, eng, sc, hang=(1, -27))


def _tag_bat(name):
    g = unary_union([circle(0, 0, 29, 64), circle(0, -31, 5)])
    g = round_concave(g, 1.2).difference(circle(0, -31, 2.2))
    eng = unary_union([bat(34, 0, -13), text(name, SPOOKY, cx=0, cy=7, width=44, max_h=10)])
    sc = [circle(0, 0, 25.5, 64).exterior.difference(circle(0, -31, 7)),
          LineString([(-14, 16), (14, 16)])]
    return Part(f"Anhaenger Fledermaus {name}", g, eng, sc, hang=(0, -31))


def jar_tags():
    parts = [_tag_pumpkin("Hexenküsse", 0), _tag_ghost("Geisterspucke"),
             _tag_stone("Zombiefinger"), _tag_cauldron("Gummiwürmer"),
             _tag_bat("Fledermäuse"), _tag_pumpkin("Monsteraugen", 1)]
    return [p.clean() for p in parts]


# =========================================================== Laser 4: Steckfiguren
def _with_slot(g):
    return g.difference(bottom_slot(0))


def figures():
    gh = ghost_shape(84, 128, 0, -128 + 42, flat=True)
    gb = gh.bounds
    gh = affinity.translate(gh, 0, -gb[3])
    gface = ghost_face(84, 0, gh.bounds[1] + 42, 1)
    ghost = Part("Gespenst", _with_slot(gh).difference(gface),
                 text("Buh!", SPOOKY, cx=16, cy=-30, width=30), hang=(0, gh.bounds[1]))

    pw = 120
    pk = pumpkin_shape(pw, 0, -0.39 * pw).intersection(box(-pw, -pw * 2, pw, -2))
    pk = round_convex(pk.union(box(-pw * 0.30, -10, pw * 0.30, 0)), 2)
    pface = jack_face(pw, 0, -0.39 * pw, 0)
    psc = [s.difference(pface.buffer(2)).difference(bottom_slot(0).buffer(3))
           for s in pumpkin_ribs(pw, 0, -0.39 * pw)]
    pumpkin = Part("Kuerbis", _with_slot(pk).difference(pface), None, psc)

    ct = cat_shape(135, 0, 0)
    cat = Part("Katze", _with_slot(ct).difference(cat_eyes(135, 0, 0)),
               None, [LineString([(-14, -6), (-10, -30)]), LineString([(14, -6), (12, -28)])])
    parts = [ghost.clean(), pumpkin.clean(), cat.clean()]
    return parts + [foot(f"Standfuss {n}") for n in ("Gespenst", "Kuerbis", "Katze")]


# =========================================================== Laser 5: Grabsteine
def tombstones():
    specs = [(80, 120, 0, ["R.I.P."], ["der letzte", "Lolli"]),
             (74, 132, 1, ["Hier ruht"], ["Graf", "Karies"]),
             (84, 112, 2, ["Achtung!"], ["Nimm nur", "zwei!"])]
    parts = []
    for i, (w, h, kind, head, lines) in enumerate(specs):
        g = tombstone(w, h, 0, 0, kind)
        top = g.bounds[1]
        body_top = -h * (0.70 if kind == 1 else 0.72 if kind == 2 else 1.0) + (
            w / 2 if kind == 0 else 0)
        ty = (top + w * 0.36) if kind == 0 else body_top + 16
        eng = [text(head[0], SPOOKY, cx=0, cy=ty, width=w * 0.62, max_h=16)]
        for k, ln in enumerate(lines):
            eng.append(text(ln, DECO, cx=0, cy=ty + 20 + k * 14, width=w * 0.70, max_h=11))
        if kind == 2:
            eng.append(bat(22, 0, top + 18))
        sc = [tombstone(w - 9, h - 9, 0, -4.5, kind).exterior]
        rnd = random.Random(i + 3)
        cx0 = rnd.choice([-1, 1]) * w * 0.32
        crack = [(cx0, top + h * 0.45)]
        for _ in range(4):
            crack.append((crack[-1][0] + rnd.uniform(-4, 4), crack[-1][1] + rnd.uniform(5, 8)))
        sc.append(LineString(crack))
        sc.append(LineString([(-w * 0.42, -12), (-w * 0.28, -16), (-w * 0.12, -13),
                              (w * 0.05, -17), (w * 0.22, -13), (w * 0.40, -16)]))
        sc = [s.difference(bottom_slot(0).buffer(3)) for s in sc]
        g = _with_slot(g)
        name = ["Grabstein Lolli", "Grabstein Karies", "Grabstein Nimm zwei"][i]
        parts.append(Part(name, g, unary_union(eng), sc).clean())
    return parts + [foot(f"Standfuss {k + 1}") for k in range(3)]


# =========================================================== Laser 6: Fledermaus-Girlande + Netz
def garland():
    parts = []
    for i, span in enumerate([96, 96, 80, 80, 80, 64, 64, 64]):
        g = bat(span, 0, 0)
        for s in (-1, 1):
            g = g.difference(circle(s * span * 0.24, -span * 0.11, 1.8))
        eye = unary_union([circle(s * span * 0.018, -span * 0.105, span * 0.009)
                           for s in (-1, 1)])
        parts.append(Part(f"Fledermaus {i + 1}", g.difference(eye), hang=(0, -span * 0.11)))
    r = 72
    w = web(r, spokes=10, rings=6, w=2.6, seed=4)
    w = unary_union([w, circle(0, 0, 9), circle(0, -r - 4, 6.5)])
    sp = spider(30, 0, r + 30)
    thread = stroke([(0, r - 4), (0, r + 26)], 2.4)
    g = round_concave(unary_union([w, sp, thread]), 0.5)
    g = Polygon(g.exterior, [i for i in g.interiors if Polygon(i).area > 8])
    netz = Part("Spinnennetz", g.difference(circle(0, -r - 4, 2.6)), hang=(0, -r - 4))
    return [p.clean() for p in parts] + [netz.clean()]


# =========================================================== Schneideplotter
PLOT_W = 290.0   # nutzbare Breite einer 12"-Schneidematte (305 mm) mit Rand


def plot_sweet_or_sour():
    a = text("Süßes oder", SPOOKY, cx=0, cy=0, width=PLOT_W)
    b = text("Saures!", SPOOKY, cx=0, cy=0, width=PLOT_W * 0.72)
    ha = a.bounds[3] - a.bounds[1]
    b = affinity.translate(b, 0, ha / 2 + 10 + (b.bounds[3] - b.bounds[1]) / 2)
    xb = (b.bounds[2] - b.bounds[0]) / 2 + 22
    yb = (b.bounds[1] + b.bounds[3]) / 2
    bats = [bat(34, xb, yb - 6, 14), bat(30, -xb, yb + 4, -12)]
    return [unary_union([a, b]), *bats]


def plot_candybar():
    t = text("Candy Bar", SPOOKY, cx=0, cy=0, width=PLOT_W)
    b = t.bounds
    bats = [bat(60, b[2] - 40, b[1] - 34, 12), bat(40, b[2] - 100, b[1] - 46, -8),
            bat(30, b[0] + 30, b[1] - 30, -16)]
    return [t, *bats]


def plot_bats():
    rnd = random.Random(8)
    out = []
    sizes = [110, 95, 90, 80, 75, 70, 65, 60, 55, 50, 50, 45, 40, 40, 35, 35, 30, 30, 25, 25]
    placed = []
    for s in sizes:
        for _ in range(4000):
            x, y = rnd.uniform(s / 2, PLOT_W - s / 2), rnd.uniform(s / 2, PLOT_W - s / 2)
            g = bat(s, x, y, rnd.uniform(-20, 20))
            if all(g.distance(p) > 4 for p in placed):
                placed.append(g)
                break
    out += placed
    return out


def plot_web_corner():
    r = 270
    w = web(r, spokes=6, rings=7, w=3.0, start=0, span=90, seed=11, sag=0.14)
    w = w.intersection(box(-2, -2, r + 5, r + 5))
    hang_x = r * 0.42
    thread = stroke([(hang_x, r * 0.40), (hang_x, r * 0.78)], 1.6)
    sp = spider(46, hang_x, r * 0.78 + 26, w=3.0)
    return [unary_union([w, thread, sp])]


def plot_jar_faces():
    out = []
    for i in range(3):
        out.append(jack_face(90, 0, 0, i))
    for i in range(3):
        out.append(ghost_face(90, 0, 0, i))
    return out


def plot_jar_names():
    names = ["Hexenküsse", "Geisterspucke", "Zombiefinger", "Gummiwürmer",
             "Fledermäuse", "Monsteraugen"]
    return [text(n, SPOOKY, width=125, max_h=34) for n in names]


PLOTTER = [
    ("01_suesses-oder-saures", "Schriftzug „Süßes oder Saures!“", plot_sweet_or_sour, False),
    ("02_candy-bar", "Schriftzug „Candy Bar“", plot_candybar, False),
    ("03_fledermausschwarm", "Fledermausschwarm (20 Stück)", plot_bats, False),
    ("04_spinnennetz-ecke", "Spinnennetz-Ecke mit Spinne", plot_web_corner, False),
    ("05_glas-gesichter", "Gesichter für Bonbongläser", plot_jar_faces, True),
    ("06_glas-schriftzuege", "Namen für Bonbongläser", plot_jar_names, True),
]
