"""Luxus-Sportwagen-Serie: zehn Entwuerfe rund um Supersportwagen, GT und Klassiker (generisch, ohne Marken)."""
import math

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from autos import (SANS, SPORT, _wheel, arc_band, car, ctext, finger_box, gauge_clock, rrect,
                   scene_window, single, speedlines, spline, steck_car)
from designs import MAT, SLOT
from lasergeo import Part, circle, polar, polys, round_concave, round_convex, star, stroke, text


def checker(region, cell=4.0, x0=None, y0=None):
    """Schachbrettmuster (jedes zweite Feld) auf eine Flaeche zugeschnitten."""
    b = region.bounds
    x0 = b[0] if x0 is None else x0
    y0 = b[1] if y0 is None else y0
    sq = []
    i = 0
    y = y0
    while y < b[3]:
        x = x0
        j = 0
        while x < b[2]:
            if (i + j) % 2 == 0:
                sq.append(box(x, y, x + cell, y + cell))
            x += cell
            j += 1
        y += cell
        i += 1
    return unary_union(sq).intersection(region)


def flag(x, y, w=40, h=28, pole=60, wave=4.0):
    """Wehende Zielflagge an einer Stange; (x, y) = Fuss der Stange."""
    top = y - pole
    pts_top = [(x + w * t, top + wave * math.sin(t * 2 * math.pi)) for t in [i / 20 for i in range(21)]]
    pts_bot = [(x + w * t, top + h + wave * math.sin(t * 2 * math.pi)) for t in [i / 20 for i in range(21)]]
    cloth = Polygon(pts_top + pts_bot[::-1])
    g = unary_union([cloth, stroke([(x, y), (x, top - 3)], 2.6), circle(x, top - 3.5, 2.4)])
    eng = checker(cloth.buffer(-1.2), cell=h / 6, x0=x, y0=top - wave)
    return g, eng


# ====================================================================== 1 Wandschild Supersportwagen
def supercar_sign():
    W, BAR = 380.0, 26.0
    cg, ce, cs = car("midengine", 230, 34, 0, wheels="cut")
    # geschwungene "Rennstrecken"-Linie hinter dem Auto
    up = spline([(0, -12), (90, -40), (190, -62), (290, -66), (380, -50)], 12)
    lo = spline([(380, -36), (290, -52), (190, -48), (90, -26), (0, -2)], 12)
    swoosh = Polygon(up + lo).buffer(0)
    fg, fe = flag(326, 0, 44, 30, 92)
    bar = rrect(0, -4, W, BAR, 5)
    bg = unary_union([swoosh, fg]).difference(cg.buffer(2.2))
    bg = unary_union([q for q in polys(bg) if q.intersects(bar)])
    g = unary_union([bg, bar, cg]).difference(unary_union([circle(10, 13, 2.6), circle(W - 10, 13, 2.6)]))
    eng = [ce, fe, ctext("PURE PERFORMANCE", SPORT, W / 2, 12, size=15, max_w=230)]
    eng.append(speedlines(4, 30, -20, n=4, gap=4.2, w=1.5).intersection(g.buffer(-1)).difference(cg.buffer(2)))
    sc = list(cs) + [LineString(spline([(0, -7), (90, -33), (190, -55), (290, -59), (380, -43)], 12))
                     .difference(cg.buffer(3)).difference(fg.buffer(2))]
    return [single(Part("Wandschild Supersportwagen", g, unary_union(eng).intersection(g), sc))]


# ====================================================================== 2 Tacho-Uhr
def speedo_clock():
    odo = rrect(-27, -60, 27, -46, 2)
    digits = unary_union([ctext(d, SANS, -21 + i * 10.5, -53, size=8) for i, d in enumerate("02026")])
    cells = unary_union([box(-26 + i * 10.5, -59, -16.5 + i * 10.5, -47) for i in range(5)])
    extra = unary_union([cells.difference(digits),
                         ctext("km/h", SANS, 0, -32, size=8)])
    p = gauge_clock([str(20 * i) for i in range(1, 13)], "GRAN TURISMO", "HANDGEFERTIGT · SEIT 2026", 11,
                    extra=extra)
    p.name = "Wanduhr Tacho"
    p.score.append(odo.exterior)
    return [p]


# ====================================================================== 3 Untersetzer Rennsport
def _race_coaster(num, title, sub):
    R = 47.5
    g = circle(0, 0, R, 96)
    roundel = circle(0, -6, 23, 64)
    stripes = unary_union([box(-15, -R, -7, R), box(7, -R, 15, R)]).intersection(circle(0, 0, R - 6))
    eng = unary_union([stripes.difference(roundel.buffer(2.2)),
                       roundel.exterior.buffer(0.7),
                       ctext(str(num), SPORT, 0, -6, size=30, max_w=36, max_h=24),
                       ctext(title, SPORT, 0, 27, size=8.5, max_w=58),
                       ctext(sub, SANS, 0, 36.5, size=4.2, max_w=40)])
    eng = eng.difference(box(-30, 22, 30, 40).difference(unary_union([
        ctext(title, SPORT, 0, 27, size=8.5, max_w=58), ctext(sub, SANS, 0, 36.5, size=4.2, max_w=40)])))
    return single(Part(f"Untersetzer {title}", g, eng, [circle(0, 0, R - 4, 96).exterior]))


def race_coasters():
    return [_race_coaster(1, "GRAND PRIX", "POLE POSITION"), _race_coaster(24, "ENDURANCE", "24 STUNDEN"),
            _race_coaster(7, "HILLCLIMB", "BERGRENNEN"), _race_coaster(99, "RALLYE", "HISTORIC")]


# ====================================================================== 4 Schluesselanhaenger
def keytags():
    out = []
    # a) Lenkrad
    rim = circle(0, 0, 20, 64).difference(circle(0, 0, 15.5, 64))
    spokes = unary_union([stroke([(0, 0), polar(17, a)], 5) for a in (0, 180, 90)])
    hub = circle(0, 0, 7)
    g = round_concave(unary_union([rim, spokes, hub]), 1.0)
    eng = unary_union([circle(0, 0, 5), arc_band(15.5, 20, -102, -78)])
    out.append(single(Part("Anhaenger Lenkrad", g, eng.intersection(g), [circle(0, 0, 18).exterior],
                           hang=polar(10, -45))))
    # b) offene Schaltkulisse
    g = rrect(-26, -17, 26, 17, 4)
    xs = [-14, -4.7, 4.7, 14]
    gate = [stroke([(xs[0], 0), (xs[-1], 0)], 2.6)]
    for x in xs[:3]:
        gate.append(stroke([(x, -10), (x, 10)], 2.6))
    gate.append(stroke([(xs[-1], -10), (xs[-1], 0)], 2.6))
    gate += [circle(x, y, 2.4) for x in xs[:3] for y in (-10, 10)] + [circle(xs[-1], -10, 2.4)]
    gate = unary_union(gate)
    tab = unary_union([circle(-29, 0, 6.5), box(-29, -6.5, -24, 6.5)])
    g = round_concave(unary_union([g, tab]), 1.2).difference(unary_union([gate, circle(-30, 0, 2.6)]))
    nums = unary_union([ctext(n, SPORT, x, y, size=4.4) for n, x, y in
                        [("1", xs[0], -14.6), ("2", xs[0], 14.6), ("3", xs[1], -14.6), ("4", xs[1], 14.6),
                         ("5", xs[2], -14.6), ("6", xs[2], 14.6), ("R", xs[3], -14.6)]])
    out.append(single(Part("Anhaenger Schaltkulisse", g, nums, [], hang=(-30, 0))))
    # c) Zielflagge
    fg, fe = flag(0, 30, 40, 26, 44, 3.2)
    fg = round_concave(fg.union(circle(0, -16.5, 3.6)), 0.8).difference(circle(0, -16.5, 1.9))
    out.append(single(Part("Anhaenger Zielflagge", fg, fe, [], hang=(0, -16.5))))
    # d) Schluessel-Fob mit Monogramm
    g = unary_union([rrect(-16, -26, 16, 26, 14), circle(0, -29, 5.2)]).difference(circle(0, -29, 2.4))
    eng = unary_union([ctext("GT", SPORT, 0, -8, size=15),
                       circle(0, 9, 4.2).exterior.buffer(0.5), circle(0, 19, 4.2).exterior.buffer(0.5),
                       Polygon([(-1.8, 10.6), (1.8, 10.6), (0, 7.4)]), Polygon([(-1.8, 17.4), (1.8, 17.4), (0, 20.6)])])
    out.append(single(Part("Anhaenger Fob", round_concave(g, 1.2), eng,
                           [rrect(-13.5, -23.5, 13.5, 23.5, 11.5).exterior], hang=(0, -29))))
    # e) Leistungs-Plakette
    shield = Polygon([(-19, -22), (19, -22), (19, 2)] + [polar(19, a, 0, 2) for a in range(0, 181, 15)] +
                     [(-19, 2)]).buffer(0)
    g = round_convex(shield, 2.5).difference(circle(0, -16.5, 2.5))
    eng = unary_union([ctext("V12", SPORT, 0, -2, size=13, max_w=30), ctext("750 PS", SANS, 0, 12, size=5.5)])
    out.append(single(Part("Anhaenger V12", g, eng, [round_convex(shield, 2.5).buffer(-2.4).exterior],
                           hang=(0, -16.5))))
    # f) Hypercar
    cg, ce, cs = car("hyper", 80, -40, 10, wheels="eng")
    cg = cg.difference(circle(-25, -3.4, 2.3))
    out.append(single(Part("Anhaenger Hypercar", cg, ce, cs, hang=(-25, -3.4))))
    return out


# ====================================================================== 5 3D-Steckauto Mittelmotor
def lux_steck():
    return steck_car("midengine", 190, 70, "Steckauto Supersportwagen")


# ====================================================================== 6 Rennstrecken-Wandbild
TRACK = [(40, 150), (60, 104), (54, 72), (86, 48), (140, 44), (162, 64), (196, 54), (238, 40), (268, 62),
         (258, 98), (222, 108), (200, 130), (226, 152), (196, 172), (120, 170), (80, 178)]


def circuit_map():
    W, H = 300.0, 215.0
    g = rrect(0, 0, W, H, 8).difference(unary_union([circle(14, 10, 2.6), circle(W - 14, 10, 2.6)]))
    path = spline(TRACK, 14, closed=True)
    ring = LineString(path + [path[0]])
    eng = [ring.buffer(3.4)]
    # Start/Ziel: Schachbrett quer zur Strecke
    p0, p1 = ring.coords[3], ring.coords[4]
    ang = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    sf = checker(box(-1.6, -5, 1.6, 5), cell=1.6, x0=-1.6, y0=-5)
    sf = affinity.translate(affinity.rotate(sf, ang, origin=(0, 0)), *p0)
    eng[0] = eng[0].difference(affinity.translate(affinity.rotate(box(-2.4, -6, 2.4, 6), ang, origin=(0, 0)), *p0))
    eng.append(sf)
    # Boxengasse
    pit = LineString(spline([(46, 158), (62, 118), (64, 100)], 10))
    eng.append(pit.buffer(0.8))
    # Kurvennummern
    corners = [(1, 2), (2, 3), (3, 5), (4, 6), (5, 7), (6, 8), (7, 9), (8, 10), (9, 11), (10, 12), (11, 13),
               (12, 14), (13, 15)]
    for n, idx in corners:
        x, y = TRACK[idx]
        # Nummer nach aussen versetzen
        cx, cy = 155, 110
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy)
        px, py = x + dx / L * 13, y + dy / L * 13
        eng.append(circle(px, py, 5).difference(ctext(str(n), SANS, px, py, size=5.4)))
    eng.append(ctext("GRAND PRIX CIRCUIT", SPORT, W / 2, 24, size=17, max_w=230))
    eng.append(ctext("5,2 KM · 13 KURVEN · RUNDENREKORD 1:41,07", SANS, W / 2, 196, size=6.2, max_w=210))
    eng.append(ctext("START / ZIEL", SANS, p0[0] - 20, p0[1] + 2, size=4.6))
    sc = [rrect(6, 6, W - 6, H - 6, 4).exterior, LineString([(20, 186), (W - 20, 186)])]
    return [single(Part("Rennstrecke", g, unary_union(eng).intersection(g.buffer(-3)), sc))]


# ====================================================================== 7 Schluesselbox
def key_box():
    BW, BD, BH = 150.0, 80.0, 56.0
    cg, ce, cs = car("midengine", 92, BW / 2 - 46, 34, wheels="eng")
    front_eng = unary_union([cg.difference(ce.buffer(0.01)), ctext("KEYS", SPORT, BW / 2, 45, size=10),
                             speedlines(14, 34, 22, n=3, gap=3.4, w=1.2)])
    back_eng = ctext("GARAGE COLLECTION", SPORT, BW / 2, 26, size=10, max_w=110)
    side_eng = checker(box(14, 14, BD - 14, 34), cell=5, x0=14, y0=14)
    faces = {"front": (None, front_eng, []), "back": (None, back_eng, []),
             "left": (None, side_eng, []), "right": (None, side_eng, [])}
    return finger_box(BW, BD, BH, faces, name="Schluesselbox",
                      bottom_eng=ctext("SINCE 2026", SANS, BW / 2, BD / 2, size=7))


# ====================================================================== 8 Modellauto-Display
def model_display():
    W, D, HB = 180.0, 76.0, 86.0
    TAB, TX = 22.0, 56.0
    # Bodenplatte mit Schlitzen hinten
    base = rrect(-W / 2, -D / 2, W / 2, D / 2, 8)
    sy = D / 2 - 9
    slots = unary_union([box(x - TAB / 2 - 0.1, sy - SLOT / 2, x + TAB / 2 + 0.1, sy + SLOT / 2) for x in (-TX, TX)])
    gb = base.difference(slots)
    plate = rrect(-50, 6, 50, 30, 3)
    eng_b = unary_union([ctext("GRAN TURISMO", SPORT, 0, 15, size=8.5, max_w=80),
                         ctext("MASSSTAB 1:43 · NR. 01", SANS, 0, 24.5, size=4.6, max_w=70)])
    pb = Part("Display Bodenplatte", gb, eng_b, [plate.exterior, rrect(-W / 2 + 4, -D / 2 + 4, W / 2 - 4, D / 2 - 4, 5).exterior])
    # Rueckwand mit Zapfen unten (y = 0 = Oberkante Bodenplatte)
    wall = rrect(-W / 2, -HB, W / 2, 0, 8).union(box(-W / 2, -10, W / 2, 0))
    tabs = unary_union([box(x - TAB / 2, -0.01, x + TAB / 2, MAT) for x in (-TX, TX)])
    gw = unary_union([wall, tabs])
    band = box(-W / 2 + 6, -HB + 8, W / 2 - 6, -HB + 20)
    eng_w = unary_union([checker(band, cell=4, x0=-W / 2 + 6, y0=-HB + 8),
                         speedlines(-80, -6, -46, n=4, gap=6, w=1.6),
                         ctext("COLLECTION", SPORT, 44, -52, size=12)])
    pw = Part("Display Rueckwand", gw, eng_w, [rrect(-W / 2 + 4, -HB + 4, W / 2 - 4, -4, 5).exterior])
    return [single(pb), single(pw)]


# ====================================================================== 9 Lesezeichen
BM_W, BM_H = 40.0, 170.0


def _bookmark(kind, name):
    W, H = BM_W, BM_H
    outer = round_convex(Polygon([(0, 8), (W / 2, 0), (W, 8), (W, H), (0, H)]), 2.0)
    window = rrect(5, 14, W - 5, 112, 3)
    L = 94.0
    cg, ce, cs = car(kind, L, 0, 0, wheels="cut", details=False)
    # Auto hochkant: faehrt nach oben, Raeder zeigen nach rechts zur "Strasse"
    cg = affinity.rotate(cg, -90, origin=(0, 0))
    b = cg.bounds
    cg = affinity.translate(cg, (W - 5 - 3.5) - b[2], 112 - 1 - b[3])
    road = box(W - 5 - 4, 10, W, 120)
    scene = unary_union([cg, road])
    solid = scene.intersection(window.buffer(1.5))
    g = unary_union([outer.difference(window), solid])
    g = round_concave(g, 0.5).difference(circle(W / 2, 7.2, 2.4))
    eng = affinity.rotate(ctext(name, SPORT, W / 2, 142, size=12, max_w=50), -90, origin=(W / 2, 142))
    sc = [LineString([(6, 120), (W - 6, 120)]), LineString([(6, H - 6), (W - 6, H - 6)])]
    return single(Part(f"Lesezeichen {name}", g, eng, sc, hang=(W / 2, 7.2)))


def bookmarks():
    return [_bookmark("gt", "GRAN TURISMO"), _bookmark("classic", "CLASSIC"), _bookmark("hyper", "HYPERCAR")]


# ====================================================================== 10 Laterne Garage
LX, LY, LZ = 90.0, 90.0, 110.0
GROUND = LZ - 18 - MAT


def lux_lantern():
    W = LX
    # Vorn: Supersportwagen vor einem Garagentor-Bogen
    cg, ce, cs = car("midengine", 66, W / 2 - 33, GROUND - 1, wheels="eng")
    door_frame = unary_union([box(0, GROUND - 4, W, LZ)] +
                             [box(8, y, W - 8, y + 2.4) for y in range(28, int(GROUND - 34), 9)])
    front_hole = scene_window(W, LZ, unary_union([door_frame, cg]))
    # Hinten: Klassiker
    cg2, _, _ = car("classic", 66, W / 2 - 33, GROUND - 1, wheels="eng", facing="left")
    back_hole = scene_window(W, LZ, unary_union([box(0, GROUND - 4, W, LZ), cg2]))
    # Seiten: Luftschlitze
    side_hole = unary_union([rrect(20, y, LY - 20, y + 3.2, 1.6) for y in range(18, 82, 8)])
    stars_g = unary_union([round_convex(star(sx, 9, 3.6, 1.6), 0.3) for sx in (7, W - 7)])
    faces = {"front": (unary_union([front_hole, stars_g]), ctext("GARAGE", SPORT, W / 2, LZ - 10.5, size=10), []),
             "back": (unary_union([back_hole, stars_g]), ctext("CLASSIC", SPORT, W / 2, LZ - 10.5, size=10), []),
             "left": (side_hole, ctext("V12", SPORT, LY / 2, LZ - 10.5, size=10), []),
             "right": (side_hole, ctext("V12", SPORT, LY / 2, LZ - 10.5, size=10), [])}
    return finger_box(LX, LY, LZ, faces, bottom_hole=circle(LX / 2, LY / 2, 11),
                      bottom_eng=ctext("GRAN TURISMO", SPORT, LX / 2, LY / 2 + 24, size=8), name="Laterne")
