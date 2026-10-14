"""Saaletal-Serie: zehn Entwuerfe rund um Hammelburg, Bad Kissingen & die Fraenkische Saale.

Einheiten mm, y nach unten. Alle Gebaeude sind stilisierte Silhouetten, keine Bauplaene.
"""
import math

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from designs import DECO, MAT, SCRIPT, SLOT, _fingers
from lasergeo import (Part, circle, polar, polys, round_concave, round_convex, star,
                      stroke, text)

SANS = "Inter-Bold.otf"


def ellipse(x, y, rx, ry, rot=0):
    e = affinity.scale(circle(0, 0, 1, 32), rx, ry, origin=(0, 0))
    return affinity.translate(affinity.rotate(e, rot, origin=(0, 0)), x, y)


def rrect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=12)


def rot_text(s, font, cx, cy, angle, **kw):
    return affinity.rotate(text(s, font, cx=cx, cy=cy, **kw), angle, origin=(cx, cy))


def single(part):
    """Sicherstellen, dass jedes Teil zusammenhaengt (keine losen Inseln beim Schneiden)."""
    n = len(polys(part.solid))
    assert n == 1, f"{part.name}: {n} getrennte Stuecke"
    return part.clean()


def spline(pts, n=14):
    """Catmull-Rom-Kurve durch alle Punkte."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t
                                    + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3)
                             for j in range(2)))
    out.append(pts[-1])
    return out


def wave(x0, x1, y, amp=1.4, period=9.0):
    n = max(8, int((x1 - x0) / 0.8))
    return LineString([(x0 + (x1 - x0) * i / n,
                        y + amp * math.sin((x1 - x0) * i / n / period * 2 * math.pi))
                       for i in range(n + 1)])


# ====================================================================== Motive
# Jede Silhouette steht mit der Basis auf y=0 und liefert (Flaeche, Fenster).
def _cross(x, y, s):
    w = max(1.2, 1.3 * s)
    return unary_union([stroke([(x, y), (x, y - 6 * s)], w),
                        stroke([(x - 2.2 * s, y - 4 * s), (x + 2.2 * s, y - 4 * s)], w)])


def _arch_win(x, y, w, h):
    """Rundbogenfenster, (x, y) = unten Mitte."""
    return unary_union([box(x - w / 2, y - h + w / 2, x + w / 2, y), circle(x, y - h + w / 2, w / 2)])


def church(x, s=1.0):
    """Pfarrkirche mit Spitzturm (Hammelburg, stilisiert)."""
    nave = Polygon([(x - 4 * s, 0), (x - 4 * s, -16 * s), (x - 1 * s, -23 * s), (x + 17 * s, -23 * s),
                    (x + 20 * s, -16 * s), (x + 20 * s, 0)])
    tower = box(x - 11 * s, -34 * s, x - 3 * s, 0)
    spire = Polygon([(x - 12 * s, -34 * s), (x - 7 * s, -54 * s), (x - 2 * s, -34 * s)])
    g = unary_union([nave, tower, spire, _cross(x - 7 * s, -53 * s, s)])
    win = unary_union([_arch_win(x - 7 * s, -22 * s, 3 * s, 7 * s)] +
                      [_arch_win(x + k * s, -5 * s, 3.4 * s, 9 * s) for k in (3, 9, 15)])
    return g, win


def onion_church(x, s=1.0):
    """Russisch-orthodoxe Kirche mit Zwiebelkuppeln (Bad Kissingen, stilisiert)."""
    def onion(cx, by, k):
        prof = [(0, 0), (5, -1.5), (7, -4), (6.6, -7), (4.2, -10), (1.6, -13), (0.4, -15), (0, -16)]
        pts = [(cx + px * k, by + py * k) for px, py in prof]
        pts += [(cx - px * k, by + py * k) for px, py in reversed(prof[1:-1])]
        return unary_union([Polygon(pts), _cross(cx, by - 15.5 * k, k)])
    body = box(x - 10 * s, -20 * s, x + 10 * s, 0)
    drum = box(x - 4.5 * s, -27 * s, x + 4.5 * s, -19 * s)
    side = [box(x + d * s - 2.4 * s, -24 * s, x + d * s + 2.4 * s, -19 * s) for d in (-7, 7)]
    g = unary_union([body, drum, *side, onion(x, -27 * s, s),
                     onion(x - 7 * s, -24 * s, 0.5 * s), onion(x + 7 * s, -24 * s, 0.5 * s)])
    win = unary_union([_arch_win(x + d * s, -6 * s, 3 * s, 8 * s) for d in (-5.5, 0, 5.5)] +
                      [_arch_win(x, -21 * s, 2.2 * s, 4.5 * s)])
    return g, win


def twin_spires(x, s=1.0):
    """Doppeltuermige neugotische Kirche (Bad Kissingen, stilisiert)."""
    g = [box(x - 13 * s, -24 * s, x + 13 * s, 0),
         Polygon([(x - 13 * s, -24 * s), (x, -32 * s), (x + 13 * s, -24 * s)])]
    win = []
    for d in (-9, 9):
        g.append(box(x + d * s - 4 * s, -44 * s, x + d * s + 4 * s, 0))
        g.append(Polygon([(x + d * s - 4.6 * s, -44 * s), (x + d * s, -66 * s),
                          (x + d * s + 4.6 * s, -44 * s)]))
        g.append(_cross(x + d * s, -65 * s, s * 0.8))
        win.append(_arch_win(x + d * s, -32 * s, 2.6 * s, 7 * s))
    win.append(circle(x, -17 * s, 3.2 * s))
    win.append(_arch_win(x, -2 * s, 5 * s, 9 * s))
    return unary_union(g), unary_union(win)


def arcade(x0, x1, s=1.0, h=18):
    """Langer Kurbau mit Bogengang (Arkadenbau/Wandelhalle, stilisiert)."""
    g = unary_union([box(x0, -h * s, x1, 0),
                     Polygon([(x0 - 1 * s, -h * s), (x0 + 3 * s, -(h + 5) * s),
                              (x1 - 3 * s, -(h + 5) * s), (x1 + 1 * s, -h * s)])])
    n = max(3, int((x1 - x0) / (7 * s)))
    step = (x1 - x0) / n
    win = [_arch_win(x0 + step * (i + 0.5), 0, step * 0.62, 10 * s) for i in range(n)]
    win += [box(x0 + step * (i + 0.5) - 1 * s, -15 * s, x0 + step * (i + 0.5) + 1 * s, -12.5 * s)
            for i in range(n)]
    return g, unary_union(win)


def castle(x, s=1.0):
    """Burg/Schloss mit Bergfried, Palas und Mauer (Schloss Saaleck, stilisiert)."""
    keep = box(x - 6 * s, -36 * s, x + 6 * s, 0)
    merl = [box(x - 6.5 * s + k * 3.25 * s, -40 * s, x - 6.5 * s + k * 3.25 * s + 2.2 * s, -35 * s)
            for k in range(4)]
    palas = box(x + 5 * s, -20 * s, x + 26 * s, 0)
    roof = Polygon([(x + 4 * s, -20 * s), (x + 9 * s, -29 * s), (x + 22 * s, -29 * s), (x + 27 * s, -20 * s)])
    wall = box(x - 22 * s, -11 * s, x - 5 * s, 0)
    wm = [box(x - 22 * s + k * 3.4 * s, -14 * s, x - 22 * s + k * 3.4 * s + 2.2 * s, -10 * s)
          for k in range(5)]
    g = unary_union([keep, *merl, palas, roof, wall, *wm])
    win = unary_union([_arch_win(x, -24 * s, 2.6 * s, 6 * s)] +
                      [box(x + d * s - 1.4 * s, -15 * s, x + d * s + 1.4 * s, -10 * s) for d in (10, 15.5, 21)] +
                      [_arch_win(x - 14 * s, 0, 4.5 * s, 7 * s)])
    return g, win


def ruin(x, s=1.0):
    """Burgruine mit abgebrochenem Turm (Trimburg, stilisiert)."""
    tower = Polygon([(x - 6 * s, 0), (x - 6 * s, -30 * s), (x - 3 * s, -33 * s), (x - 1 * s, -29 * s),
                     (x + 2 * s, -35 * s), (x + 4 * s, -31 * s), (x + 6 * s, -32 * s), (x + 6 * s, 0)])
    wall = Polygon([(x + 5 * s, 0), (x + 5 * s, -14 * s), (x + 9 * s, -17 * s), (x + 12 * s, -12 * s),
                    (x + 16 * s, -15 * s), (x + 19 * s, -9 * s), (x + 22 * s, -10 * s), (x + 23 * s, 0)])
    wall2 = Polygon([(x - 5 * s, 0), (x - 5 * s, -12 * s), (x - 9 * s, -15 * s), (x - 13 * s, -9 * s),
                     (x - 17 * s, -8 * s), (x - 18 * s, 0)])
    g = unary_union([tower, wall, wall2])
    win = unary_union([_arch_win(x, -18 * s, 2.6 * s, 7 * s), _arch_win(x + 13 * s, -2 * s, 3.4 * s, 6 * s)])
    return g, win


def gate_tower(x, s=1.0):
    """Stadttor-Turm mit Zeltdach (Hohntor Bad Neustadt, stilisiert)."""
    t = box(x - 8 * s, -42 * s, x + 8 * s, 0)
    roof = Polygon([(x - 9.5 * s, -42 * s), (x, -58 * s), (x + 9.5 * s, -42 * s)])
    lant = box(x - 1.6 * s, -62 * s, x + 1.6 * s, -56 * s)
    knob = circle(x, -63 * s, 1.6 * max(s, 0.8))
    g = unary_union([t, roof, lant, knob])
    win = unary_union([_arch_win(x, 0, 8 * s, 13 * s)] +
                      [box(x + d * s - 1.4 * s, -33 * s, x + d * s + 1.4 * s, -28 * s) for d in (-4, 4)] +
                      [box(x - 1.4 * s, -22 * s, x + 1.4 * s, -17 * s)])
    return g, win


def house(x, w, h, roof, s=1.0, step=False):
    """Giebelhaus von vorne; step=True: Treppengiebel (Rathaus)."""
    w, h, roof = w * s, h * s, roof * s
    if step:
        pts = [(x - w / 2, 0), (x - w / 2, -h)]
        n = 4
        for k in range(n):
            xa = x - w / 2 + (w / 2) * k / n
            ya = -h - roof * (k + 1) / n
            pts += [(xa, ya), (xa + w / 2 / n, ya)]
        pts += [(2 * x - px, py) for px, py in reversed(pts[2:])]
        pts += [(x + w / 2, 0)]
        g = Polygon(pts).buffer(0)
    else:
        g = Polygon([(x - w / 2, 0), (x - w / 2, -h), (x, -h - roof), (x + w / 2, -h), (x + w / 2, 0)])
    win = []
    rows = max(1, int(h / (7 * s)))
    cols = max(1, int(w / (6 * s)))
    for r in range(rows):
        for c in range(cols):
            wx = x - w / 2 + w * (c + 0.5) / cols
            wy = -h + (r + 0.6) * h / (rows + 0.3)
            win.append(box(wx - 1.3 * s, wy - 1.8 * s, wx + 1.3 * s, wy + 1.8 * s))
    win.append(box(x - 1.2 * s, -h - roof * 0.55, x + 1.2 * s, -h - roof * 0.3))
    return g, unary_union(win).intersection(g.buffer(-0.8 * s))


def tree(x, s=1.0, kind="round"):
    if kind == "poplar":
        return unary_union([ellipse(x, -15 * s, 3.4 * s, 13 * s), box(x - 0.9 * s, -3 * s, x + 0.9 * s, 0)])
    return unary_union([circle(x, -11 * s, 6 * s), circle(x - 3.5 * s, -8 * s, 4.2 * s),
                        circle(x + 3.5 * s, -8 * s, 4.2 * s), box(x - 1.1 * s, -4 * s, x + 1.1 * s, 0)])


def grapes(cx, cy, r=2.4, rows=(4, 3, 3, 2, 1), leaf=True):
    """Weintraube (Mittelpunkt der obersten Beerenreihe = cx, cy)."""
    g = []
    for i, n in enumerate(rows):
        for k in range(n):
            g.append(circle(cx + (k - (n - 1) / 2) * 2.25 * r, cy + i * 1.95 * r, r))
    g.append(stroke([(cx, cy - 1.2 * r), (cx + 0.6 * r, cy - 3.2 * r)], 0.55 * r))
    if leaf:
        lc = (cx + 3.8 * r, cy - 3.0 * r)
        pts = []
        for i in range(60):
            a = 2 * math.pi * i / 60
            rr = 2.6 * r * (0.78 + 0.22 * math.cos(5 * (a + 0.3))) * (0.9 + 0.1 * math.sin(a))
            pts.append(polar(rr, math.degrees(a), *lc))
        g.append(Polygon(pts).buffer(0))
        g.append(stroke([(cx + 0.6 * r, cy - 3.2 * r), lc], 0.45 * r))
    return unary_union(g)


def leaf_veins(cx, cy, r=2.4):
    lc = (cx + 3.8 * r, cy - 3.0 * r)
    return [LineString([lc, polar(2.0 * r, a, *lc)]) for a in (-150, -90, -30, 30, 90)]


def canoe(cx, cy, L=40.0, paddler=True):
    """Kanadier mit Paddler; (cx, cy) = Wasserlinie Mitte."""
    hull = [(cx - L / 2, cy - 4.2)]
    for i in range(1, 30):
        t = i / 30
        hull.append((cx - L / 2 + L * t, cy - 1 + 5.2 * math.sin(math.pi * t) ** 0.7))
    hull += [(cx + L / 2, cy - 4.2), (cx + L / 2 - 3, cy - 2.4), (cx - L / 2 + 3, cy - 2.4)]
    g = [Polygon(hull).buffer(0)]
    if paddler:
        px = cx - L * 0.12
        g += [Polygon([(px - 3.4, cy - 2), (px - 2.4, cy - 11), (px + 2.6, cy - 11), (px + 3.4, cy - 2)]),
              circle(px, cy - 14.4, 3.0),
              stroke([(px + 9, cy - 19), (px - 7, cy + 6)], 1.6),
              ellipse(px - 7.6, cy + 6.6, 1.8, 3.8, rot=-40)]
    return unary_union(g)


def sheep_head(cx, cy, k=1.0):
    return unary_union([ellipse(cx, cy, 10 * k, 7 * k, -25), ellipse(cx - 7 * k, cy - 6 * k, 5 * k, 2.4 * k, 30)])


# ====================================================================== 1 Skyline
SKY_W = 380.0


def _ground(x):
    hill = 30 * math.exp(-((x - 332) / 30) ** 2) + 14 * math.exp(-((x - 172) / 22) ** 2)
    return -4 - hill - 1.5 * math.sin(x / 13)


def skyline_scene(width=SKY_W, s=1.0, with_hills=True):
    """Panorama Saaletal von Bad Neustadt bis Schloss Saaleck. Basis bei y=0."""
    gy = (lambda x: _ground(x * SKY_W / width) * s) if with_hills else (lambda x: 0.0)
    X = lambda v: v * width / SKY_W
    items = []

    def put(fn, x, *a, **kw):
        g, w = fn(X(x), *a, s=s, **kw) if fn not in (tree,) else (fn(X(x), s, *a, **kw), None)
        dy = gy(X(x)) + 1.5 * s
        items.append((affinity.translate(g, 0, dy), affinity.translate(w, 0, dy) if w else None))

    put(tree, 10, kind="poplar")
    put(gate_tower, 30)
    put(house, 50, 14, 16, 9)
    put(tree, 62)
    put(onion_church, 78)
    put(twin_spires, 108)
    g, w = arcade(X(126), X(160), s=s)
    items.append((affinity.translate(g, 0, gy(X(143)) + 1.5 * s), affinity.translate(w, 0, gy(X(143)) + 1.5 * s)))
    put(tree, 166, kind="poplar")
    put(ruin, 180)
    put(tree, 200)
    put(house, 214, 12, 14, 8)
    put(church, 236)
    put(house, 270, 18, 20, 11, step=True)
    put(house, 289, 12, 15, 8)
    put(tree, 301, kind="poplar")
    put(castle, 330)
    put(tree, 366)
    solid = unary_union([g for g, _ in items])
    win = unary_union([w for _, w in items if w is not None])
    # Weinberg-Zeilen am Saaleck-Hang
    vines = []
    if with_hills:
        for k in range(7):
            x0 = X(300 + k * 9)
            vines.append(LineString([(x0, gy(x0) + 4 * s), (x0 + X(7), gy(x0 + X(7)) + 14 * s)]))
    return solid, win, vines, gy


def skyline():
    W, BAR = SKY_W, 26.0
    solid, win, vines, gy = skyline_scene()
    terrain = Polygon([(0, BAR)] + [(x, gy(x)) for x in [W * i / 190 for i in range(191)]] + [(W, BAR)])
    bar = rrect(0, -2, W, BAR, 4)
    g = unary_union([solid, terrain.intersection(box(0, -200, W, BAR)), bar])
    g = round_concave(g, 0.5)
    g = g.difference(unary_union([circle(9, 13, 2.5), circle(W - 9, 13, 2.5)]))
    eng = [win, text("Saaletal", SCRIPT, cx=W / 2, cy=12.5, width=78, max_h=19)]
    for y in (9.5, 15.5):
        eng.append(wave(22, W / 2 - 52, y).buffer(0.7))
        eng.append(wave(W / 2 + 52, W - 22, y).buffer(0.7))
    score = vines + [LineString([(4, 1.5), (W - 4, 1.5)])]
    return [single(Part("Skyline Saaletal", g, unary_union(eng), score))]


# ====================================================================== 2 Flusskarte
TOWNS = [  # Name, Breite, Laenge, Label-Versatz (dx, dy) in mm, Ausrichtung
    ("Quelle", 50.335, 10.590, (0, -7), "c"),
    ("Bad Königshofen", 50.300, 10.468, (0, 8), "c"),
    ("Saal a. d. Saale", 50.318, 10.352, (0, -7), "c"),
    ("Bad Neustadt", 50.322, 10.217, (-12, -7), "c"),
    ("Bad Bocklet", 50.268, 10.078, (5, 0), "l"),
    ("Bad Kissingen", 50.200, 10.077, (5, 0), "l"),
    ("Euerdorf", 50.150, 10.025, (5, 1), "l"),
    ("Elfershausen", 50.143, 9.963, (-6, -7), "c"),
    ("Hammelburg", 50.117, 9.893, (0, 8), "c"),
    ("Gräfendorf", 50.118, 9.745, (0, -7), "c"),
    ("Gemünden", 50.050, 9.705, (5, 2), "l"),
]
# Zwischenpunkte fuer einen natuerlicheren Flusslauf
RIVER = [(50.335, 10.590), (50.318, 10.53), (50.300, 10.468), (50.296, 10.42), (50.318, 10.352),
         (50.330, 10.29), (50.322, 10.217), (50.300, 10.17), (50.285, 10.11), (50.268, 10.078),
         (50.235, 10.090), (50.200, 10.077), (50.172, 10.060), (50.150, 10.025), (50.152, 9.99),
         (50.143, 9.963), (50.128, 9.93), (50.117, 9.893), (50.108, 9.84), (50.122, 9.79),
         (50.118, 9.745), (50.085, 9.72), (50.050, 9.705)]
MAIN = [(49.935, 9.79), (49.99, 9.745), (50.050, 9.705), (50.040, 9.64), (50.010, 9.585)]
MAP_W, MAP_H = 300.0, 215.0


def _proj(lat, lon):
    k = 392.0
    return (14 + (lon - 9.56) * math.cos(math.radians(50.2)) * k, 30 + (50.36 - lat) * k)


def river_map():
    W, H = MAP_W, MAP_H
    g = rrect(0, 0, W, H, 8).difference(unary_union([circle(14, 10, 2.6), circle(W - 14, 10, 2.6)]))
    eng = []
    river = spline([_proj(*p) for p in RIVER], 10)
    # Fluss wird zur Muendung hin breiter
    for i in range(len(river) - 1):
        wdt = 1.4 + 1.6 * i / len(river)
        eng.append(stroke([river[i], river[i + 1]], wdt))
    eng.append(stroke(spline([_proj(*p) for p in MAIN], 10), 3.4))
    eng.append(text("Main", SANS, cx=_proj(49.965, 9.81)[0], cy=_proj(49.965, 9.81)[1], size=6))
    for name, lat, lon, (dx, dy), al in TOWNS:
        x, y = _proj(lat, lon)
        dot = circle(x, y, 2.6) if name != "Quelle" else star(x, y, 3.6, 1.6)
        eng.append(dot)
        t = text(name, SANS, size=5.6)
        b = t.bounds
        tw = b[2] - b[0]
        cx = x + dx + (tw / 2 if al == "l" else 0)
        eng.append(affinity.translate(t, cx - (b[0] + b[2]) / 2, y + dy - (b[1] + b[3]) / 2))
    # Rhoen mit Bergsymbol
    rx, ry = _proj(50.395, 9.99)
    for ddx, hh in ((-7, 8), (0, 12), (8, 9)):
        eng.append(Polygon([(rx + ddx - hh * 0.8, ry + 4), (rx + ddx, ry + 4 - hh),
                            (rx + ddx + hh * 0.8, ry + 4)]))
    eng.append(text("Rhön", SCRIPT, cx=rx + 1, cy=ry + 11, width=20))
    # Weinberge bei Hammelburg
    hx, hy = _proj(50.085, 9.955)
    eng.append(grapes(hx - 2, hy + 4, r=1.5, leaf=False))
    # Titel unten rechts
    eng.append(text("Fränkische Saale", SCRIPT, cx=210, cy=170, width=150))
    eng.append(text("VON DER QUELLE BIS ZUR MÜNDUNG", SANS, cx=210, cy=190, width=110))
    # Kompass
    cx, cy = 34, 44
    for a in range(0, 360, 90):
        eng.append(Polygon([polar(14 if a == 270 else 10, a, cx, cy), polar(2.6, a + 45, cx, cy),
                            (cx, cy), polar(2.6, a - 45, cx, cy)]))
    eng.append(text("N", SANS, cx=cx, cy=cy - 19, size=6))
    score = [rrect(6, 6, W - 6, H - 6, 4).exterior]
    return [single(Part("Flusskarte Fraenkische Saale", g, unary_union(eng), score))]


# ====================================================================== 3 Wanduhr
CLOCK_R = 130.0
CLOCK_TOWNS = ["Bad Königshofen", "Saal a. d. Saale", "Bad Neustadt", "Niederlauer", "Bad Bocklet",
               "Bad Kissingen", "Euerdorf", "Aura a. d. Saale", "Elfershausen", "Hammelburg",
               "Gräfendorf", "Gemünden"]


def wall_clock():
    R = CLOCK_R
    g = circle(0, 0, R, 128).difference(circle(0, 0, 4.0))   # Ø 8 mm fuer das Quarzwerk
    eng = []
    for i, name in enumerate(CLOCK_TOWNS):
        a = -90 + 30 * i
        x, y = polar(98, a)
        ang = a + 90 if -180 <= a <= 0 or a >= 180 else a - 90
        t = text(name, SANS, size=7.0, cx=x, cy=y)
        tw = t.bounds[2] - t.bounds[0]
        if tw > 42:
            t = affinity.scale(t, 42 / tw, 42 / tw, origin=(x, y))
        eng.append(affinity.rotate(t, ang, origin=(x, y)))
        eng.append(circle(*polar(116, a), 3.0 if i % 3 == 0 else 2.0))
    for i in range(60):
        if i % 5:
            a = -90 + 6 * i
            eng.append(stroke([polar(114, a), polar(119, a)], 0.9))
    sky, win, vines, _ = skyline_scene(width=150, s=0.42, with_hills=False)
    sky = affinity.translate(sky.difference(win), -75, -22)
    eng.append(sky)
    eng.append(stroke([(-80, -21.6), (80, -21.6)], 1.2))
    eng.append(text("Saaletal", SCRIPT, cx=0, cy=34, width=86))
    eng.append(text("ZEIT FÜR HEIMAT", SANS, cx=0, cy=55, width=50))
    eng.append(wave(-40, 40, 66, amp=1.2, period=8).buffer(0.6))
    score = [circle(0, 0, R - 5, 128).exterior]
    return [single(Part("Wanduhr Saaletal", g, unary_union(eng), score))]


# ====================================================================== 4 Untersetzer
def _coaster(name, sub, motif, mscore=()):
    R = 47.5
    g = circle(0, 0, R, 96)
    eng = unary_union([motif,
                       text(name, DECO, cx=0, cy=19.5, width=62, max_h=11),
                       text(sub, SANS, cx=0, cy=31, width=46, max_h=3.6)])
    score = [circle(0, 0, R - 4, 96).exterior] + list(mscore)
    return single(Part(f"Untersetzer {name}", g, eng, score))


def coasters():
    out = []
    gr = grapes(-5, -25, r=3.0)
    out.append(_coaster("Hammelburg", "FRANKENS ÄLTESTE WEINSTADT", gr.difference(
        unary_union([l.buffer(0.35) for l in leaf_veins(-5, -25, 3.0)])), ))
    a, wa = onion_church(-11, 0.95)
    b, wb = twin_spires(13, 0.62)
    kis = affinity.translate(unary_union([a.difference(wa), b.difference(wb)]), 0, 3)
    out.append(_coaster("Bad Kissingen", "KURSTADT AN DER SAALE",
                        unary_union([kis, box(-26, 3, 26, 4.4)])))
    c, wc = castle(-3, 0.8)
    hill = Polygon([(-34, 7)] + [(x, -1 - 7 * math.exp(-(x / 18) ** 2)) for x in range(-34, 35, 2)]
                   + [(34, 7)])
    hill = hill.intersection(circle(0, 0, 40))
    sa = unary_union([affinity.translate(c.difference(wc), 0, -7.2), hill])
    rows = [LineString([(x, -1 - 7 * math.exp(-(x / 18) ** 2) + 1.4), (x + 4, 6)])
            for x in range(-28, 30, 5)]
    sa = sa.difference(unary_union([r.buffer(0.45) for r in rows]))
    out.append(_coaster("Schloss Saaleck", "WEINGUT & BURG BEI HAMMELBURG", sa))
    ca = canoe(0, -6, 46)
    waves = unary_union([wave(-32, 32, y, amp=1.3, period=10).buffer(0.75) for y in (-1.5, 3.5)])
    out.append(_coaster("Fränkische Saale", "PADDELN · RADELN · GENIESSEN",
                        unary_union([ca, waves.difference(ca.buffer(1.0))])))
    return out


# ====================================================================== 5 Bocksbeutel-Flaschenanhaenger
def _bocksbeutel(variant):
    belly = circle(0, 0, 30, 64)
    shoulder = Polygon([(-20, -22), (-7.5, -38), (7.5, -38), (20, -22)])
    neck = box(-7.5, -50, 7.5, -36)
    lip = rrect(-9, -55, 9, -48, 1.5)
    ring = circle(0, -76, 23, 64)
    g = round_concave(unary_union([belly, shoulder, neck, lip, ring]), 2.0)
    g = g.difference(circle(0, -76, 17, 64))   # Ø 34 mm passt ueber den Flaschenhals
    sc = [circle(0, 2, 24.5, 64).exterior, LineString([(-7.5, -44), (7.5, -44)])]
    if variant == 0:
        eng = [text("Hammelburg", DECO, cx=0, cy=-3, width=40),
               text("FRANKENS ÄLTESTE", SANS, cx=0, cy=8.5, width=30),
               text("WEINSTADT", SANS, cx=0, cy=14, width=19),
               grapes(-1.5, -19, r=1.6, rows=(3, 2, 1), leaf=False)]
    elif variant == 1:
        eng = [text("Zum Wohl!", SCRIPT, cx=0, cy=-2, width=40),
               text("AUS DEM SAALETAL", SANS, cx=0, cy=10, width=32),
               wave(-14, 14, 16, amp=1.0, period=7).buffer(0.55),
               grapes(-1.5, -19, r=1.6, rows=(3, 2, 1), leaf=False)]
    else:
        c, wc = castle(-2, 0.48)
        eng = [affinity.translate(c.difference(wc), 0, -7),
               box(-18, -7.4, 18, -6.4),
               text("Schloss Saaleck", SCRIPT, cx=0, cy=4, width=38),
               text("HAMMELBURG", SANS, cx=0, cy=14, width=22)]
    return single(Part("Bocksbeutel-Anhaenger", g, unary_union(eng), sc, hang=(0, -76)))


def bottle_tags():
    return [_bocksbeutel(v) for v in range(3)]


# ====================================================================== 6 Schluesselanhaenger
KEY_TOWNS = ["Hammelburg", "Bad Kissingen", "Bad Bocklet", "Euerdorf", "Elfershausen", "Bad Neustadt"]


def _keytag(name):
    body = rrect(-31, -15, 31, 15, 3)
    tab = unary_union([circle(-34, 0, 7), box(-34, -7, -28, 7)])
    g = round_concave(unary_union([body, tab]), 1.5).difference(circle(-35, 0, 2.7))
    eng = unary_union([text(name, SANS, cx=1.5, cy=-2, width=48, max_h=7.2),
                       text("FRÄNKISCHE SAALE", SANS, cx=1.5, cy=8, width=30)])
    sc = [rrect(-27.5, -12, 30.5 - 2, 12, 1.6).exterior]
    return single(Part(f"Ortsschild {name}", g, eng, sc, hang=(-35, 0)))


def keytags():
    return [_keytag(n) for n in KEY_TOWNS]


# ====================================================================== 7 Lesezeichen
BM_W, BM_H = 40.0, 150.0


def _bookmark(name, scene):
    W, H = BM_W, BM_H
    outer = Polygon([(0, 8), (W / 2, 0), (W, 8), (W, H), (0, H)])
    outer = round_convex(outer, 2.0)
    window = rrect(5, 14, W - 5, 66, 3)
    solid = scene.intersection(window.buffer(1.5))
    g = unary_union([outer.difference(window), solid])
    g = round_concave(g, 0.5).difference(circle(W / 2, 7.2, 2.4))
    eng = rot_text(name, SCRIPT if len(name) < 12 else DECO, W / 2, 108, -90, size=20, width=None,
                   max_h=16)
    b = eng.bounds
    if b[3] - b[1] > 70:
        k = 70 / (b[3] - b[1])
        eng = affinity.scale(eng, k, k, origin=(W / 2, 108))
    sc = [LineString([(6, 74), (W - 6, 74)]), LineString([(6, H - 6), (W - 6, H - 6)])]
    return single(Part(f"Lesezeichen {name}", g, eng, sc, hang=(W / 2, 7.2)))


def bookmarks():
    W = BM_W
    # Weinrebe: geschwungene Ranke von unten nach oben mit Trauben und Blaettern
    vine_pts = [(W / 2, 68), (W / 2 + 7, 56), (W / 2 - 6, 42), (W / 2 + 5, 28), (W / 2 - 2, 12)]
    stem = LineString(spline(vine_pts, 10))
    vine = [stem.buffer(1.2)]
    vine.append(grapes(W / 2 + 5.5, 46, r=2.2, rows=(3, 3, 2, 1), leaf=False))
    vine.append(grapes(W / 2 - 8.5, 28, r=1.9, rows=(3, 2, 1), leaf=False))
    for cx, cy, rot in ((W / 2 - 8, 56, 20), (W / 2 + 8, 30, -30), (W / 2 + 6, 18, 10)):
        vine.append(ellipse(cx, cy, 5.5, 4.0, rot))
        near = stem.interpolate(stem.project(Point(cx, cy)))
        vine.append(stroke([(cx, cy), (near.x, near.y)], 1.6))
    vine.append(stroke([(W / 2 - 6, 42), (W / 2 - 8.5, 26)], 1.6))
    vine.append(stroke([(W / 2 + 5, 49), (W / 2 + 5.5, 44)], 1.6))
    bm1 = _bookmark("Hammelburg", unary_union(vine))
    # Arkaden: zweistoeckiger Bogengang
    arc = box(0, 0, W, 80)
    holes = []
    for row, (yb, hh) in enumerate(((64, 18), (40, 14))):
        for k in range(3):
            holes.append(_arch_win(5 + (W - 10) * (k + 0.5) / 3, yb, 6.4, hh))
    holes.append(circle(W / 2, 20, 6.5))
    holes += [affinity.translate(star(0, 0, 3.0, 1.3), W / 2 + d, 20) for d in (-12, 12)]
    bm2 = _bookmark("Bad Kissingen", arc.difference(unary_union(holes)))
    # Saale: Kanu auf Wellen, Weide am Ufer
    water = Polygon([(0, 80), (0, 56)] + [(x, 54 + 1.6 * math.sin(x / 3.2)) for x in
                                          [i * 0.5 for i in range(81)]] + [(W, 80)])
    ca = canoe(W / 2 + 2, 55.5, 28)
    willow = unary_union([stroke([(W - 6, 56), (W - 8, 30)], 2.0)] +
                         [stroke([(W - 8, 30), polar(L, a, W - 8, 30)], 1.5)
                          for L, a in ((12, 200), (13, 160), (11, 120), (9, 80))] +
                         [stroke([polar(L, a, W - 8, 30), (polar(L, a, W - 8, 30)[0], 46)], 1.4)
                          for L, a in ((12, 200), (13, 160))])
    bm3 = _bookmark("Fränkische Saale", unary_union([water, ca, willow]))
    return [bm1, bm2, bm3]


# ====================================================================== 8 Christbaumanhaenger
ORN_R = 40.0


def _ornament(name, scene, extra_score=()):
    R, WR = ORN_R, 31.0
    window = circle(0, -2, WR, 96)
    solid = scene.intersection(window.buffer(1.5))
    g = unary_union([circle(0, 0, R, 96).difference(window), solid,
                     circle(0, -R - 3, 5.5)])
    g = round_concave(g, 0.6).difference(circle(0, -R - 3, 2.4))
    eng = text(name, SCRIPT if len(name) < 12 else DECO, cx=0, cy=19, width=46, max_h=11)
    sc = [circle(0, 0, R - 3, 96).exterior.difference(box(-6, -R - 6, 6, -R + 2))] + list(extra_score)
    return single(Part(f"Anhaenger {name}", g, eng, sc, hang=(0, -R - 3)))


def _hill(y0, peak, h, w):
    return Polygon([(-40, 40), (-40, y0)] + [(x, y0 - h * math.exp(-((x - peak) / w) ** 2))
                                              for x in [i - 40 for i in range(81)]] + [(40, 40), (-40, 40)])


def ornaments():
    s = 0.62
    out = []
    # Hammelburg
    base = 12
    parts = [church(0, s), house(-18, 12, 15, 8, s), house(18, 16, 18, 10, s, step=True)]
    g = unary_union([affinity.translate(p[0], 0, base) for p in parts] + [tree(-28, s), tree(29, s)])
    g = unary_union([g, _hill(base - 1, 0, 0, 10)])
    win = unary_union([affinity.translate(p[1], 0, base) for p in parts])
    out.append(_ornament("Hammelburg", g.difference(win.buffer(-0.1).intersection(g))))
    # Bad Kissingen
    a, wa = onion_church(-11, s * 1.15)
    b, wb = twin_spires(12, s * 0.9)
    g = unary_union([affinity.translate(a, 0, base), affinity.translate(b, 0, base),
                     _hill(base - 1, 0, 0, 10), tree(-27, s), tree(28, s, "poplar")])
    win = affinity.translate(unary_union([wa, wb]), 0, base)
    out.append(_ornament("Bad Kissingen", g.difference(win)))
    # Schloss Saaleck auf dem Weinberg
    hill = _hill(14, 0, 10, 20)
    c, wc = castle(-4, s)
    g = unary_union([hill, affinity.translate(c, 0, 4.5)])
    rows = [LineString([(x, 14 - 10 * math.exp(-(x / 20) ** 2) + 2), (x + 3, 15)])
            for x in range(-26, 27, 4)]
    out.append(_ornament("Schloss Saaleck", g.difference(affinity.translate(wc, 0, 4.5)), rows))
    # Trimburg (Ruine ueber dem Saaletal)
    hill = _hill(15, -4, 9, 16)
    r, wr = ruin(-4, s * 1.1)
    hy = lambda x: 15 - 9 * math.exp(-((x + 4) / 16) ** 2) + 1
    g = unary_union([hill, affinity.translate(r, 0, 7),
                     affinity.translate(tree(18, s, "poplar"), 0, hy(18)),
                     affinity.translate(tree(25, s), 0, hy(25)),
                     affinity.translate(tree(-27, s), 0, hy(-27))])
    out.append(_ornament("Trimburg", g.difference(affinity.translate(wr, 0, 7))))
    return out


# ====================================================================== 9 Steckfigur Rhoenschaf
def sheep():
    # Seitenansicht, Hufe auf y=0, Blick nach rechts
    wool = unary_union([ellipse(0, -52, 41, 20)] +
                       [circle(40 * math.cos(math.radians(a)), -52 + 20 * math.sin(math.radians(a)), 8.5)
                        for a in range(0, 360, 20)])
    head = sheep_head(50, -68, 1.3)
    neck = Polygon([(28, -62), (40, -76), (54, -60), (36, -46)])
    tail = circle(-46, -60, 6)
    T = MAT
    legs = []
    for lx in (-26, 24):
        for dx in (-5, 5):                                # je zwei Beine, dazwischen ein Spalt
            legs.append(rrect(lx + dx - 3.6, -42, lx + dx + 3.6, 0, 1.2).union(
                box(lx + dx - 3.6, -42, lx + dx + 3.6, -3)))
        legs.append(box(lx - 8.6, -6, lx + 8.6, 0))      # Steg ueber dem Zapfen
        legs.append(box(lx - 4, -1, lx + 4, T))          # Steckzapfen in die Bodenplatte
    g = round_concave(unary_union([wool, head, neck, tail, *legs]), 1.2)
    eng = head.difference(circle(53, -71, 2.3)).intersection(g)
    curls = []
    for cx, cy in [(-28, -58), (-16, -64), (-4, -66), (8, -64), (20, -58), (-22, -46), (-10, -50),
                   (2, -52), (14, -48), (26, -46), (-14, -38), (-2, -38), (10, -38)]:
        curls.append(LineString([polar(3.2, a, cx, cy) for a in range(200, 470, 15)]))
    pa = Part("Rhoenschaf", g, eng, curls)
    # Bodenplatte mit Schlitzen
    L, D = 132.0, 58.0
    base = rrect(-L / 2, -D / 2, L / 2, D / 2, D / 2 - 2)
    slots = unary_union([box(lx - 4.1, -8 - SLOT / 2, lx + 4.1, -8 + SLOT / 2) for lx in (-26, 24)])
    gb = base.difference(slots)
    engb = unary_union([text("Grüße aus Hammelburg", SCRIPT, cx=0, cy=12, width=82, max_h=12),
                        grapes(-50, -8, r=1.8, rows=(3, 2, 1), leaf=False), grapes(50, -8, r=1.8, rows=(3, 2, 1), leaf=False)])
    pb = Part("Bodenplatte", gb, engb, [rrect(-L / 2 + 4, -D / 2 + 4, L / 2 - 4, D / 2 - 4, D / 2 - 6).exterior])
    return [single(pa), single(pb)]


# ====================================================================== 10 Laterne Kurstadt
LX, LY, LZ = 90.0, 90.0, 110.0


def _kur_window(W, variant):
    """Fensterbild: Arkaden vorn, Kirchen dahinter (variant 0/1) oder Gradierwerk (2)."""
    wx0, wx1, top, bot = 13.0, W - 13.0, 13.0, LZ - 18.0 - MAT
    if variant == 2:
        win = box(wx0, top + 4, wx1, bot)
        bars = [box(x - 1.3, top, x + 1.3, bot + 2) for x in
                [wx0 + 1.5 + (wx1 - wx0 - 3) * i / 9 for i in range(10)]]
        beams = [box(wx0 - 2, y - 1.5, wx1 + 2, y + 1.5) for y in (top + 4 + 22, top + 4 + 46)]
        solid = unary_union(bars + beams)
        hole = round_concave(win.difference(solid), 0.4)
        eng = text("Gradierbau", SCRIPT, cx=W / 2, cy=LZ - 10.5, width=W - 34, max_h=11)
        return hole, eng
    rad = (wx1 - wx0) / 2
    win = unary_union([circle(W / 2, top + rad, rad, 64), box(wx0, top + rad, wx1, bot)])
    ay = bot - 20       # Oberkante Arkadenbau
    arc = unary_union([box(wx0 - 2, ay, wx1 + 2, bot + 2),
                       Polygon([(wx0 - 2, ay + 1), (wx0 + 4, ay - 4), (wx1 - 4, ay - 4), (wx1 + 2, ay + 1)])])
    arches = [_arch_win(wx0 + (wx1 - wx0) * (i + 0.5) / 5, bot - 1.5, 7.0, 13) for i in range(5)]
    if variant == 0:
        ch, _ = onion_church(W / 2, 1.05)
        ch = affinity.translate(ch, 0, ay - 2)
        side = [affinity.translate(tree(wx0 + 6, 0.7, "poplar"), 0, ay),
                affinity.translate(tree(wx1 - 6, 0.7, "poplar"), 0, ay)]
    else:
        ch, _ = twin_spires(W / 2, 0.85)
        ch = affinity.translate(ch, 0, ay - 2)
        side = [affinity.translate(tree(wx0 + 5, 0.7), 0, ay), affinity.translate(tree(wx1 - 5, 0.7), 0, ay)]
    solid = round_convex(unary_union([arc, ch, *side]), 0.5).intersection(win.buffer(2))
    hole = round_concave(win.difference(solid), 0.5)
    hole = unary_union([hole] + [a.intersection(solid.buffer(-1.2)) for a in arches])
    hole = unary_union([p for p in polys(hole) if p.area > 2.0])
    stars_g = [round_convex(star(sx, 9, 3.6, 1.6), 0.3) for sx in (7, W - 7)]
    words = "Bad Kissingen" if variant == 0 else "Kurstadt"
    eng = text(words, SCRIPT, cx=W / 2, cy=LZ - 10.5, width=W - 30, max_h=12)
    return unary_union([hole] + stars_g), eng


def _kur_wall(width, side, variant):
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
    g = g.difference(unary_union(cuts))
    hole, eng = _kur_window(width, variant)
    return g.difference(hole), eng


def kur_lantern():
    parts = []
    for name, side, var in [("Vorderwand", False, 0), ("Rueckwand", False, 1),
                            ("Seitenwand links", True, 2), ("Seitenwand rechts", True, 2)]:
        w, eng = _kur_wall(LX if not side else LY, side, var)
        parts.append(Part(name, w, eng))
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
    eng = text("Bad Kissingen", SCRIPT, cx=LX / 2, cy=LY / 2 + 22, width=50)
    parts.append(Part("Boden", g, eng))
    return [single(p) for p in parts]
