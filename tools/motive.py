"""Motiv-Bibliothek: einfache Icons als Flaechen (mm, y nach unten).

icon(name, cx, cy, h) liefert (shape, detail):
  shape  = gefuellte Umrissflaeche
  detail = Aussparungen (Fenster, Linien), die beim Gravieren hell bleiben
Graviertes Motiv = shape - detail.
"""
import math

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from lasergeo import circle, polar, round_concave, round_convex, star, stroke, text


def ell(x, y, rx, ry, rot=0):
    e = affinity.scale(circle(0, 0, 1, 32), rx, ry, origin=(0, 0))
    return affinity.translate(affinity.rotate(e, rot, origin=(0, 0)), x, y)


def rr(x0, y0, x1, y1, r):
    r = min(r, (x1 - x0) / 2 - 0.01, (y1 - y0) / 2 - 0.01)
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=10)


def ring(x, y, r, w):
    return circle(x, y, r + w / 2).difference(circle(x, y, r - w / 2))


def heart_poly(cx=0, cy=0, s=1.0, n=80):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s / 16 * 10, cy + (y + 2.5) * s / 16 * 10))
    return Polygon(pts).buffer(0)


E = Polygon()   # leere Geometrie


# ---------------------------------------------------------------- Icons (ca. 20 mm hoch, Mitte 0/0)
def _heart():
    return heart_poly(0, 0, 1.1), E


def _flower():
    petals = unary_union([ell(*polar(5.5, a), 4.6, 3.0, a) for a in range(-90, 270, 72)])
    shape = unary_union([petals, circle(0, 0, 3.4)])
    return shape, ring(0, 0, 3.9, 0.9)


def _flower_stem():
    head, det = _flower()
    head = affinity.translate(affinity.scale(head, 0.62, 0.62, origin=(0, 0)), 0, -4.5)
    det = affinity.translate(affinity.scale(det, 0.62, 0.62, origin=(0, 0)), 0, -4.5)
    stem = stroke([(0, -2), (0.6, 4), (0, 10)], 1.4)
    leaf = ell(3.4, 4.5, 3.2, 1.5, -30)
    return unary_union([head, stem, leaf]), det


def _leaf():
    v = circle(-4, 0, 9).intersection(circle(4, 0, 9))
    v = affinity.rotate(v, 35, origin=(0, 0))
    return v, LineString([(-4.5, 6.5), (4.5, -6.5)]).buffer(0.45)


def _hammer():
    head = rr(-8, -11, 8, -5, 1.2)
    handle = rr(-1.8, -5.5, 1.8, 11, 1.4)
    g = affinity.rotate(unary_union([head, handle]), -30, origin=(0, 0))
    return g, E


def _wrench():
    h = stroke([(-7, 7), (7, -7)], 3.6)
    jaw1 = circle(-8.4, 8.4, 4.6).difference(affinity.rotate(box(-9.6, 7.2, -6, 15), 45, origin=(-8.4, 8.4)))
    jaw2 = circle(8.4, -8.4, 4.6)
    return unary_union([h, jaw1, jaw2]), unary_union([circle(8.4, -8.4, 2.2)])


def _tools():
    a = affinity.rotate(unary_union([rr(-8, -12, 8, -6, 1.2), rr(-1.8, -6.5, 1.8, 12, 1.4)]), 40, origin=(0, 0))
    b, bd = _wrench()
    return unary_union([a, b]).buffer(0), bd.difference(a)


def _beer():
    body = rr(-7, -7, 5, 10, 1.5)
    handle = ring(6.5, 1.5, 4.0, 2.2).difference(box(-10, -10, 4.5, 12))
    foam = unary_union([circle(x, -7.5, r) for x, r in ((-5.5, 2.6), (-1.5, 3.1), (2.6, 2.7), (5.4, 2.0))])
    det = unary_union([box(x - 0.55, -3.5, x + 0.55, 7.5) for x in (-3.5, -0.8, 1.9)])
    return unary_union([body, handle, foam]), det


def _grill():
    bowl = Polygon([polar(9, a, 0, -1) for a in range(0, 181, 10)]).buffer(0)
    lid = Polygon([polar(9, a, 0, -2.2) for a in range(180, 361, 10)]).buffer(0)
    knob = circle(0, -12, 1.6)
    legs = unary_union([stroke([(-4, 6), (-7, 11)], 1.3), stroke([(4, 6), (7, 11)], 1.3),
                        stroke([(0, 7), (0, 11)], 1.3)])
    smoke = unary_union([LineString([(x + 1.4 * math.sin(t / 2), -14 - t) for t in range(0, 7)]).buffer(0.55)
                         for x in (-4, 0, 4)])
    g = unary_union([bowl, lid, knob, legs, smoke])
    return g, box(-9.5, -2.2, 9.5, -1).union(unary_union([circle(x, -6, 0.9) for x in (-4, 0, 4)]))


def _fish():
    body = ell(-1.5, 0, 9, 5)
    tail = Polygon([(6, 0), (11, -5), (10, 0), (11, 5)])
    fin = Polygon([(-3, -4.6), (1, -7.5), (2, -4.5)])
    g = unary_union([body, tail, fin])
    det = unary_union([circle(-6.5, -1.2, 1.1), LineString([(-3.6, -3.4), (-2.2, 0), (-3.6, 3.4)]).buffer(0.4)])
    return g, det


def _tie():
    knot = Polygon([(-3, -10), (3, -10), (2, -6), (-2, -6)])
    blade = Polygon([(-2, -6), (2, -6), (4.4, 7), (0, 11), (-4.4, 7)])
    det = unary_union([LineString([(-3, -2), (3, 1)]).buffer(0.45), LineString([(-3.6, 3), (3.8, 6.3)]).buffer(0.45)])
    return unary_union([knot, blade]).buffer(0.3), det.intersection(blade)


def _mustache():
    half = Polygon(spline_pts([(0, -1.5), (-4, -3.5), (-9, -2.5), (-12, -4.5), (-13, -7), (-11.5, -5.6),
                               (-12, -1), (-8, 1.8), (-3, 1.6), (0, 0.4)]))
    g = unary_union([half.buffer(0), affinity.scale(half, -1, 1, origin=(0, 0)).buffer(0)])
    return g, E


def _trophy():
    cup = Polygon([(-7, -10), (7, -10), (6.4, -3), (3, 1.5), (-3, 1.5), (-6.4, -3)])
    handles = unary_union([ring(-7.5, -6, 3.2, 1.6), ring(7.5, -6, 3.2, 1.6)]).difference(box(-6.8, -12, 6.8, 2))
    stem = box(-1.4, 1, 1.4, 6)
    base = rr(-6, 6, 6, 10, 1)
    det = star(0, -4.5, 3.2, 1.4)
    return unary_union([cup, handles, stem, base]), det


def _crown():
    pts = [(-10, 6), (-11, -6), (-5.5, -1), (0, -9), (5.5, -1), (11, -6), (10, 6)]
    g = unary_union([Polygon(pts), circle(-11, -7, 1.6), circle(0, -10, 1.8), circle(11, -7, 1.6)])
    return g, unary_union([circle(-5, 3, 1.1), circle(0, 3, 1.1), circle(5, 3, 1.1)])


def _coffee():
    cup = Polygon([(-7, -3), (7, -3), (6, 5), (4, 7), (-4, 7), (-6, 5)])
    handle = ring(7.5, 1.4, 2.8, 1.6).difference(box(-8, -5, 6.6, 9))
    saucer = ell(0, 8, 10, 1.8)
    steam = unary_union([LineString([(x + 1.3 * math.sin(t / 1.5), -5 - t) for t in [i * 0.5 for i in range(14)]])
                         .buffer(0.6) for x in (-3, 0.5, 4)])
    return unary_union([cup, handle, saucer, steam]), box(-7.5, 6.8, 7.5, 7.4).union(box(-6, -1.6, 6, -1))


def _cake():
    slice_ = Polygon([(-10, 8), (10, 8), (10, -2), (-10, 2)])
    top = Polygon([(-10, 2), (10, -2), (10, -4), (-10, 0.2)])
    cream = unary_union([circle(x, -3 + (x + 10) * -0.1 + 1, 1.6) for x in (-7, -2, 3, 8)])
    cherry = unary_union([circle(1, -8, 2.4), stroke([(1, -10), (3.5, -13)], 0.7)])
    det = unary_union([box(-10, 4.2, 10, 5.0), LineString([(-10, 1.2), (10, -2.8)]).buffer(0.4)])
    return unary_union([slice_, top, cream, cherry]), det


def _rolling_pin():
    g = unary_union([rr(-8, -3, 8, 3, 1.5), rr(-14, -1.4, -8, 1.4, 0.7), rr(8, -1.4, 14, 1.4, 0.7),
                     circle(-14.5, 0, 1.8), circle(14.5, 0, 1.8)])
    g = affinity.rotate(g, -25, origin=(0, 0))
    return g, E


def _whisk():
    handle = rr(-1.5, 2, 1.5, 11, 1.2)
    wires = unary_union([ell(0, -5, w, 7.5).exterior.buffer(0.45) for w in (1.2, 3.2, 5.2)])
    return unary_union([handle, wires, box(-1.8, 1, 1.8, 2.6)]), E


def _yarn():
    ball = circle(-1, 1, 8.5)
    lines = unary_union([LineString([polar(9, a, -1, 1), polar(9, a + 120, -1, 1)]).buffer(0.5)
                         for a in (10, 40, 70, 200, 230)])
    needles = unary_union([stroke([(-6, -12), (11, 9)], 1.1), stroke([(6, -12), (-3, 12)], 1.1),
                           circle(-6.4, -12.4, 1.4), circle(6.4, -12.4, 1.4)])
    thread = LineString([(6, 5), (10, 8), (12, 7)]).buffer(0.5)
    return unary_union([ball, needles, thread]), lines.intersection(ball.buffer(-0.6))


def _glasses():
    g = unary_union([ring(-6, 0, 4.4, 1.6), ring(6, 0, 4.4, 1.6),
                     LineString([(-1.8, -0.6), (0, -1.6), (1.8, -0.6)]).buffer(0.8),
                     stroke([(-10.3, -1), (-13, -3)], 1.2), stroke([(10.3, -1), (13, -3)], 1.2)])
    return g, E


def _hat():
    brim = ell(0, 4, 13, 2.6)
    crown = Polygon(spline_pts([(-8, 4), (-7, -4), (-3, -6), (0, -4.6), (3, -6), (7, -4), (8, 4)]))
    return unary_union([brim, crown.buffer(0)]), box(-7.6, 0.4, 7.6, 2.2)


def _knight():
    pts = [(-7, 10), (7, 10), (6, 6), (3.5, 5), (5, 0), (6, -6), (3, -10), (-1, -11), (-2.5, -9),
           (-7, -6.5), (-8.5, -3.5), (-7.4, -1.6), (-4, -2.6), (-3, -1), (-6, 4), (-6, 6)]
    g = Polygon(spline_pts(pts, 4)).buffer(0)
    return unary_union([g, rr(-8, 8, 8, 12, 1)]), circle(-2.4, -6.2, 1.0)


def _house():
    roof = Polygon([(-11, -1), (0, -11), (11, -1)])
    body = box(-8, -2, 8, 10)
    chim = box(4.5, -10, 7, -4)
    det = unary_union([box(-2, 3, 2, 10), box(-6.4, 1, -3.6, 4.4), box(3.6, 1, 6.4, 4.4)])
    return unary_union([roof, body, chim]), det


def _car_light():
    from autos import CARS
    k = 26 / 100
    glass = Polygon([(x * k - 13, y * k + 7) for x, y in CARS["hatch"]["glass"]]).buffer(0)
    rims = unary_union([circle(wx * k - 13, -wr * k + 7, wr * k * 0.55) for wx, wr in CARS["hatch"]["wheels"]])
    gaps = unary_union([ring(wx * k - 13, -wr * k + 7, wr * k + 0.35, 0.7) for wx, wr in CARS["hatch"]["wheels"]])
    return unary_union([glass.buffer(-0.2), rims, gaps])


def _umbrella():
    canopy = Polygon([polar(11, a, 0, -1) for a in range(180, 361, 6)] +
                     [(11 - 22 * t, -1 + 1.6 * abs(math.sin(t * 4 * math.pi))) for t in [i / 40 for i in range(41)]]).buffer(0)
    shaft = stroke([(0, -12.5), (0, 8)], 1.2)
    hook = LineString([(0, 8)] + [polar(2.4, a, -2.4, 8) for a in range(0, 181, 15)]).buffer(0.6)
    det = unary_union([LineString([(0, -12), (x, -1)]).buffer(0.4) for x in (-5.5, 5.5)])
    return unary_union([canopy, shaft, hook]), det.intersection(canopy.buffer(-0.5))


def _shield():
    g = Polygon([(-9, -10), (0, -12.5), (9, -10), (9, 0), (6.5, 6), (0, 12), (-6.5, 6), (-9, 0)])
    g = Polygon(spline_pts(list(g.exterior.coords)[:-1], 4)).buffer(0)
    tick = LineString([(-4.5, 0), (-1, 4), (5.5, -4.5)]).buffer(1.3, cap_style="round", join_style="round")
    return g, tick


def _family():
    figs, det = [], []
    for x, h in ((-7, 1.0), (7, 0.94), (0, 0.66)):
        top = 10 - 12 * h
        body = Polygon(spline_pts([(x - 4.4 * h, 10), (x - 4 * h, top + 3 * h), (x, top),
                                   (x + 4 * h, top + 3 * h), (x + 4.4 * h, 10)], 4)).buffer(0)
        head = circle(x, top - 1.2 - 3.2 * h, 3.2 * h)
        figs += [body, head]
    child = figs[4]
    det = child.buffer(0.8).difference(child).intersection(unary_union(figs[:4]))
    return unary_union(figs), det


def _pulse():
    h = heart_poly(0, 0, 1.1)
    line = LineString([(-14, 0), (-6, 0), (-4, -5), (-1, 6), (2, -8), (4, 1), (6, 0), (14, 0)]).buffer(0.9)
    return h, line.intersection(h)


def _key():
    head = circle(-7, 0, 5.5)
    shaft = box(-2, -1.5, 11, 1.5)
    teeth = unary_union([box(6, 1.4, 8, 4.5), box(9.2, 1.4, 11, 3.6)])
    return unary_union([head, shaft, teeth]), circle(-7, 0, 2.4)


def _coin():
    c = circle(0, 0, 10, 64)
    det = unary_union([ring(0, 0, 8.4, 0.7), text("€", "Inter-Bold.otf", size=13, cx=0, cy=0)])
    return c, det


def _coins():
    g, d = [], []
    for k in range(4):
        y = 7 - k * 3.6
        g.append(unary_union([ell(-2, y, 8, 2.6), box(-10, y - 1.2, 6, y)]))
        d.append(LineString([(-10, y - 1.2), (6, y - 1.2)]).buffer(0.35))
    big = circle(6, -3, 6.6)
    g.append(big)
    d.append(text("€", "Inter-Bold.otf", size=8.5, cx=6, cy=-3))
    d.append(ring(6, -3, 5.4, 0.6))
    return unary_union(g), unary_union(d)


def _piggy():
    body = ell(0, 0, 11, 8)
    snout = rr(9, -3, 14, 3, 1.6)
    ear = Polygon([(3, -6), (6, -11), (8, -5)])
    legs = unary_union([rr(x - 1.8, 4, x + 1.8, 10, 0.8) for x in (-6, 5)])
    tail = LineString([polar(1.6, a, -12, -2) for a in range(0, 330, 30)]).buffer(0.5)
    g = unary_union([body, snout, ear, legs, tail])
    det = unary_union([circle(5.5, -2.5, 1.0), circle(12, -0.8, 0.6), circle(12, 0.9, 0.6),
                       rr(-3, -7.2, 3, -5.8, 0.6)])
    return g, det


def _safe():
    body = rr(-10, -10, 10, 9, 1.6)
    feet = unary_union([box(-8, 9, -5, 11), box(5, 9, 8, 11)])
    det = unary_union([rr(-8, -8, 8, 7, 1).exterior.buffer(0.4), ring(-1, -0.5, 3.8, 0.8), circle(-1, -0.5, 1.0),
                       box(5, -3, 6.2, 2)] + [LineString([polar(4.4, a, -1, -0.5), polar(5.6, a, -1, -0.5)]).buffer(0.3)
                                              for a in range(0, 360, 45)])
    return unary_union([body, feet]), det


def _chart():
    bars = unary_union([box(-10 + i * 5.2, 9 - h, -6.4 + i * 5.2, 9) for i, h in enumerate((5, 8, 11.5, 15))])
    arrow = unary_union([LineString([(-11, 0), (-4, -5), (1, -3), (9, -11)]).buffer(1.1, cap_style="round"),
                         Polygon([(10.8, -12.8), (4.6, -11.6), (9.6, -6.6)])])
    base = box(-11, 9, 11, 10.4)
    return unary_union([bars, arrow, base]), arrow.buffer(0.9).difference(arrow).intersection(bars)


def _clover():
    leaves = unary_union([affinity.rotate(heart_poly(0, -5.4, 0.62), a, origin=(0, 0)) for a in (0, 90, 180, 270)])
    stem = LineString([(2, 4), (4, 9), (3, 12)]).buffer(0.8)
    return unary_union([leaves, stem]), circle(0, 0, 0.9)


def _wallet():
    body = rr(-11, -6, 11, 9, 2)
    flap = rr(2, -1, 13, 5, 1.6)
    notes = Polygon([(-9, -6), (-7, -10.5), (8, -9), (7, -6)])
    det = unary_union([flap.exterior.buffer(0.45), circle(9.5, 2, 1.1)])
    return unary_union([body, flap, notes]), det


def _sun():
    c = circle(0, 0, 6)
    rays = unary_union([Polygon([polar(7.5, a - 9), polar(11.5, a), polar(7.5, a + 9)]) for a in range(0, 360, 30)])
    return unary_union([c, rays]), E


def _butterfly():
    w = unary_union([ell(-5, -3.5, 5.2, 4.6, -20), ell(5, -3.5, 5.2, 4.6, 20),
                     ell(-3.8, 4.4, 3.6, 3.2, 25), ell(3.8, 4.4, 3.6, 3.2, -25)])
    body = rr(-1, -6, 1, 8, 1)
    ant = unary_union([LineString([(0, -6), (-3, -10.5)]).buffer(0.4), LineString([(0, -6), (3, -10.5)]).buffer(0.4)])
    det = unary_union([body.buffer(0.7).difference(body), circle(-5.5, -3.5, 1.4), circle(5.5, -3.5, 1.4)])
    return unary_union([w, body, ant]), det.intersection(w)


def _star():
    return star(0, 0, 11, 4.6), E


def _tree():
    crown = unary_union([circle(0, -5, 7), circle(-5, -1, 5), circle(5, -1, 5)])
    trunk = Polygon([(-1.6, 2), (1.6, 2), (2.2, 11), (-2.2, 11)])
    return unary_union([crown, trunk]), E


def _book():
    left = Polygon([(-11, -6), (-1, -8), (0, -7), (0, 8), (-1, 7), (-11, 8)])
    right = affinity.scale(left, -1, 1, origin=(0, 0))
    det = unary_union([LineString([(-9, y), (-2.5, y - 1)]).buffer(0.35) for y in (-3, 0, 3)] +
                      [LineString([(9, y), (2.5, y - 1)]).buffer(0.35) for y in (-3, 0, 3)])
    return unary_union([left, right]), det


def _watering_can():
    body = rr(-7, -5, 6, 8, 1.5)
    spout = Polygon([(5, 4), (12, -6), (13.5, -5), (7, 7)])
    rose = ell(13.2, -6.6, 1.6, 2.6, 35)
    handle = ring(-1, -5.5, 4.4, 1.6).difference(box(-8, -4.6, 8, 10))
    drops = unary_union([ell(15, y, 0.7, 1.1) for y in (-2, 1.5)])
    return unary_union([body, spout, rose, handle, drops]), E


def _envelope():
    body = rr(-11, -7, 11, 7, 1)
    det = LineString([(-10, -6), (0, 1), (10, -6)]).buffer(0.6)
    return body, det


def _pen():
    g = affinity.rotate(unary_union([rr(-1.8, -10, 1.8, 6, 0.8), Polygon([(-1.8, 6), (1.8, 6), (0, 11)])]), 35,
                        origin=(0, 0))
    return g, E


def _anchor():
    g = unary_union([ring(0, -9, 2.2, 1.2), stroke([(0, -7), (0, 9)], 1.8), stroke([(-5, -4), (5, -4)], 1.6),
                     LineString([polar(9, a, 0, 0) for a in range(20, 161, 10)]).buffer(0.9),
                     Polygon([(-9.6, 1.5), (-7, 5.6), (-11.6, 4.6)]), Polygon([(9.6, 1.5), (7, 5.6), (11.6, 4.6)])])
    return g, E


ICONS = {
    "herz": _heart, "blume": _flower, "blume_stiel": _flower_stem, "blatt": _leaf, "hammer": _hammer,
    "schluessel_werkzeug": _wrench, "werkzeug": _tools, "bier": _beer, "grill": _grill, "fisch": _fish,
    "krawatte": _tie, "bart": _mustache, "pokal": _trophy, "krone": _crown, "kaffee": _coffee,
    "kuchen": _cake, "nudelholz": _rolling_pin, "schneebesen": _whisk, "wolle": _yarn, "brille": _glasses,
    "hut": _hat, "springer": _knight, "haus": _house, "auto": lambda: (_car_shape(), _car_light()),
    "schirm": _umbrella, "schild": _shield, "familie": _family, "puls": _pulse, "schluessel": _key,
    "muenze": _coin, "muenzen": _coins, "sparschwein": _piggy, "tresor": _safe, "chart": _chart,
    "kleeblatt": _clover, "geldboerse": _wallet, "sonne": _sun, "schmetterling": _butterfly, "stern": _star,
    "baum": _tree, "buch": _book, "giesskanne": _watering_can, "brief": _envelope, "stift": _pen,
    "anker": _anchor,
}


def _car_shape():
    from autos import car
    g, _, _ = car("hatch", 26, -13, 7, wheels="eng", details=False)
    return g


def icon(name, cx=0.0, cy=0.0, h=20.0, rot=0.0):
    """Icon in ein Quadrat der Groesse h eingepasst und bei (cx, cy) zentriert -> (shape, detail)."""
    shape, det = ICONS[name]()
    b = shape.bounds
    k = h / max(b[3] - b[1], b[2] - b[0])        # passt in ein Quadrat der Kantenlaenge h
    ox, oy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    T = lambda g: affinity.translate(affinity.rotate(affinity.scale(g, k, k, origin=(ox, oy)), rot, origin=(ox, oy)),
                                     cx - ox, cy - oy) if g is not None and not g.is_empty else Polygon()
    return T(shape), T(det)


def engraved(name, cx=0.0, cy=0.0, h=20.0, rot=0.0):
    s, d = icon(name, cx, cy, h, rot)
    return s.difference(d) if not d.is_empty else s


def spline_pts(pts, n=8):
    """Geschlossene Catmull-Rom-Kurve."""
    p = [pts[-1]] + list(pts) + list(pts[:2])
    out = []
    for i in range(1, len(pts) + 1):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t
                                    + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    return out
