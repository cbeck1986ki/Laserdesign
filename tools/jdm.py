"""JDM-Serie: zehn Entwuerfe fuer die japanische Tuning- und Drift-Szene (generisch, ohne Marken)."""
import math

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from autos import (JP, SANS, SPORT, arc_band, car, ctext, ellipse, finger_box, gauge_clock,
                   rrect, scene_window, single, speedlines, spline, steck_car, vtext)
from designs import MAT, SLOT
from lasergeo import Part, circle, polar, polys, round_concave, round_convex, star, stroke, text


# ---------------------------------------------------------------- Motive
def seigaiha(region, r=6.0, rings=3, w=0.45):
    """Japanisches Wellenmuster (Seigaiha) als Linien, auf eine Flaeche zugeschnitten."""
    b = region.bounds
    # Spaetere Reihen verdecken fruehere: von unten nach oben ausschneiden
    out = []
    row = 0
    y = b[1] - r
    rows = []
    while y < b[3] + r:
        xs = []
        x = b[0] - r + (r if row % 2 else 0)
        while x < b[2] + r:
            xs.append(x)
            x += 2 * r
        rows.append((y, xs))
        y += r / 2
        row += 1
    for i, (y, xs) in enumerate(rows):
        later = unary_union([Point(x, yy).buffer(r * 0.999) for yy, xx in rows[i + 1:i + 3] for x in xx]) \
            if i + 1 < len(rows) else None
        for x in xs:
            for k in range(rings):
                rr = r * (1 - k / rings)
                ln = LineString([polar(rr, a, x, y) for a in range(180, 361, 10)])
                if later is not None:
                    ln = ln.difference(later)
                ln = ln.intersection(region)
                if not ln.is_empty:
                    out.append(ln.buffer(w / 2))
    return unary_union(out)


def turbo(cx, cy, s=1.0):
    """Turbolader (Schneckengehaeuse) -> (Flaeche, Aussparungen fuer Gravur, Linien)."""
    pts = [polar(10 * s + 7 * s * t / (2 * math.pi), math.degrees(t) - 90, cx, cy)
           for t in [i * 2 * math.pi / 60 for i in range(61)]]
    housing = Polygon(pts + [(cx + 17 * s, cy - 2 * s)]).buffer(0)
    housing = unary_union([housing, circle(cx, cy, 13 * s),
                           box(cx - 1 * s, cy - 17 * s, cx + 24 * s, cy - 6 * s),
                           box(cx + 22 * s, cy - 19 * s, cx + 26 * s, cy - 4 * s)])
    wheel = circle(cx, cy, 8.4 * s)
    blades = unary_union([stroke([polar(2.5 * s, a, cx, cy), polar(8 * s, a + 28, cx, cy)], 1.2 * s)
                          for a in range(0, 360, 45)])
    lines = [LineString(pts[10:])]
    return housing, wheel.difference(blades.union(circle(cx, cy, 2.2 * s))), lines


def piston(cx, cy, s=1.0):
    head = rrect(cx - 13 * s, cy - 22 * s, cx + 13 * s, cy, 2 * s)
    grooves = unary_union([box(cx - 13 * s, cy + y * s - 0.6 * s, cx + 13 * s, cy + y * s + 0.6 * s)
                           for y in (-18, -14.5, -11)])
    rod = Polygon([(cx - 5 * s, cy - 6 * s), (cx + 5 * s, cy - 6 * s), (cx + 3.4 * s, cy + 22 * s),
                   (cx - 3.4 * s, cy + 22 * s)])
    big = circle(cx, cy + 25 * s, 7.5 * s)
    g = unary_union([head, rod, big])
    return g, unary_union([grooves, circle(cx, cy - 6 * s, 3 * s)]), circle(cx, cy + 25 * s, 3.6 * s)


def shift_pattern(cx, cy, s=1.0, w=2.2, gears=6):
    xs = [-15, -5, 5, 15] if gears == 6 else [-10, 0, 10]
    g = [stroke([(cx + xs[0] * s, cy), (cx + xs[-1] * s, cy)], w * s)]
    labels = ["1", "2", "3", "4", "5", "6", "R"] if gears == 6 else ["1", "2", "3", "4", "5", "R"]
    li = 0
    for i, x in enumerate(xs):
        if i < len(xs) - 1 or gears == 5:
            g.append(stroke([(cx + x * s, cy - 13 * s), (cx + x * s, cy + 13 * s)], w * s))
        else:
            g.append(stroke([(cx + x * s, cy - 13 * s), (cx + x * s, cy)], w * s))
    nums = []
    for i, x in enumerate(xs):
        for yy in (-19, 19):
            if li >= len(labels):
                break
            if i == len(xs) - 1 and yy > 0 and gears == 6:
                continue
            nums.append(ctext(labels[li], SPORT, cx + x * s, cy + yy * s, size=8 * s))
            li += 1
    if gears == 6:
        nums.append(ctext("R", SPORT, cx + xs[-1] * s, cy - 19 * s, size=8 * s))
    return unary_union(g + nums)


# ====================================================================== 1 Wandschild Touge
def touge_sign():
    W, BAR = 360.0, 28.0
    mt = Polygon([(0, 0), (0, -26), (30, -46), (58, -34), (100, -74), (132, -52), (176, -92),
                  (214, -60), (246, -80), (282, -48), (318, -66), (360, -40), (360, 0)])
    sun = circle(290, -74, 46, 96)
    cg, ce, cs = car("coupe", 150, 26, 0, wheels="cut")
    # Luftspalt zwischen Auto und Bergen, damit die Silhouette frei steht
    bar = rrect(0, -4, W, BAR, 5)
    bg = unary_union([mt, sun]).difference(cg.buffer(2.2))
    bg = unary_union([q for q in polys(bg) if q.intersects(bar)])     # eingeschlossene Reste entfernen
    g = unary_union([bg, bar, cg])
    g = g.difference(unary_union([circle(10, 14, 2.6), circle(W - 10, 14, 2.6)]))
    eng = [ce]
    # Sonnenstreifen (Retro-Sunset) im sichtbaren Teil der Sonne
    vis = sun.difference(mt.buffer(1.5))
    for k, y in enumerate(range(-66, -26, 7)):
        eng.append(box(240, y, 340, y + 2 + k * 0.6).intersection(vis))
    # Schneekappen
    for px, py in [(100, -74), (176, -92), (246, -80)]:
        cap = Polygon([(px - 14, py + 13), (px, py), (px + 13, py + 12), (px + 6, py + 9), (px, py + 13),
                       (px - 6, py + 9)])
        eng.append(cap.intersection(mt))
    # Passstrasse in Serpentinen
    road = spline([(186, -4), (238, -16), (196, -28), (246, -40), (206, -52), (236, -62), (214, -74)], 10)
    eng.append(LineString(road).buffer(2.4).intersection(mt.buffer(-1.5)).difference(cg.buffer(2)))
    eng.append(speedlines(0, 30, -34, n=4, gap=4.5, w=1.6).intersection(g.buffer(-1)).difference(cg.buffer(2)))
    eng.append(ctext("TOUGE", SPORT, 205, 13, size=22, max_w=150))
    eng.append(ctext("峠", JP, 104, 13, size=20))
    sc = list(cs) + [LineString(road)]
    return [single(Part("Wandschild Touge", g, unary_union(eng).intersection(g), sc))]


# ====================================================================== 2 Drehzahlmesser-Uhr
def rpm_clock():
    extra = unary_union([ctext("×1000 r/min", SANS, 0, -38, size=7.5),
                         ctext("REDLINE", SPORT, 70, 26, size=6.5),
                         ctext("走り屋", JP, 0, -56, size=9)])
    p = gauge_clock([str(i) for i in range(1, 13)], "TURBO", "SEIT 1990 · NUR FÜR DIE GARAGE", 10,
                    extra=extra)
    p.name = "Wanduhr Drehzahlmesser"
    return [p]


# ====================================================================== 3 Untersetzer Garage
def _coaster(title, kana, motif, sc=()):
    R = 47.5
    g = circle(0, 0, R, 96)
    eng = unary_union([motif, ctext(title, SPORT, 0, 23, size=11, max_w=62),
                       ctext(kana, JP, 0, 34.5, size=6.5, max_w=40)])
    return single(Part(f"Untersetzer {title}", g, eng, [circle(0, 0, R - 4, 96).exterior] + list(sc)))


def garage_coasters():
    out = []
    h, w, ln = turbo(-4, -8, 1.05)
    out.append(_coaster("BOOST", "ターボ", h.difference(w.buffer(0.01).symmetric_difference(w)).difference(
        circle(-4, -8, 9).difference(w)), ln))
    from autos import _wheel
    d, e, _ = _wheel(0, -8, 22, "eng")
    out.append(_coaster("STANCE", "ホイール", e))
    out.append(_coaster("SHIFT", "シフト", shift_pattern(0, -8, 1.15)))
    pg, pe, ph = piston(0, -14, 0.82)
    out.append(_coaster("BUILT", "エンジン", pg.difference(pe).difference(ph)))
    return out


# ====================================================================== 4 Schluesselanhaenger
def keytags():
    out = []
    # a) japanisches Kennzeichen
    g = rrect(-36, -18, 36, 18, 3.5).difference(unary_union([circle(-26, -12.5, 2.6), circle(26, -12.5, 2.6)]))
    eng = unary_union([ctext("東京 300", JP, 0, -10.5, size=7.5, max_w=30),
                       ctext("な", JP, -26, 5.5, size=9),
                       ctext("20-26", SANS, 7, 5, size=20, max_w=50, max_h=14)])
    out.append(single(Part("Anhaenger Kennzeichen", g, eng, [rrect(-33.6, -15.6, 33.6, 15.6, 2).exterior],
                           hang=(-26, -12.5))))
    # b) Turbolader
    hsg, wh, ln = turbo(0, 0, 1.25)
    g = round_concave(hsg, 1.0).difference(circle(30.5, -14.4, 2.6))
    out.append(single(Part("Anhaenger Turbo", g, unary_union([circle(0, 0, 10.5).difference(wh)]), ln,
                           hang=(30.5, -14.4))))
    # c) Kolben
    pg, pe, ph = piston(0, 0, 1.0)
    out.append(single(Part("Anhaenger Kolben", pg.difference(ph), pe, [], hang=(0, 25))))
    # d) Schaltknauf mit Schaltschema
    g = unary_union([circle(0, 0, 19, 64), rrect(-6, 14, 6, 30, 2)]).difference(circle(0, 25, 2.6))
    out.append(single(Part("Anhaenger Schaltknauf", round_concave(g, 2), shift_pattern(0, -1, 0.68, 2.0),
                           [circle(0, 0, 17, 64).exterior], hang=(0, 25))))
    # e) Felge (Speichenfenster = Oese)
    from autos import _wheel
    d, e, holes = _wheel(0, 0, 20, "cut")
    g = d.difference(unary_union(holes))
    out.append(single(Part("Anhaenger Felge", g, e, [], hang=polar(12, -90 + 36))))
    # f) Keil-Coupe
    cg, ce, cs = car("wedge", 78, -39, 10, wheels="eng")
    cg = cg.difference(circle(-31, -5, 2.4))
    out.append(single(Part("Anhaenger Coupe", cg, ce, cs, hang=(-31, -5))))
    return out


# ====================================================================== 5 Omamori-Rueckspiegelanhaenger
def _omamori(kanji, sub, motif=None):
    g = Polygon([(-23, 16), (-15, 8), (15, 8), (23, 16), (23, 82), (-23, 82)])
    g = round_convex(g, 2.5)
    knot = unary_union([circle(0, 5, 6.2), circle(-6.5, 9, 3.6), circle(6.5, 9, 3.6)])
    g = round_concave(unary_union([g, knot]), 1.2).difference(circle(0, 4.4, 2.5))
    sc = [Polygon([(-20, 17.5), (-14, 11.5), (14, 11.5), (20, 17.5), (20, 79), (-20, 79)]).exterior]
    size = 10.5 if len(kanji) < 4 else 9.2
    eng = [vtext(kanji, JP, 0, 21 + len(kanji) * size * 0.56, size)]
    band = box(-20, 64, 20, 79)
    eng.append(seigaiha(band.buffer(-0.8), r=3.4, rings=2, w=0.5))
    eng.append(box(-20, 63.2, 20, 64.2))
    eng.append(ctext(sub, SPORT, 0, 70.5 if motif is None else 70.5, size=4.6, max_w=32))
    if motif is not None:
        eng.append(motif)
    eng = unary_union(eng)
    eng = eng.difference(box(-17, 67.2, 17, 73.8).difference(ctext(sub, SPORT, 0, 70.5, size=4.6, max_w=32)))
    return single(Part(f"Omamori {kanji}", g, eng, sc, hang=(0, 4.4)))


def omamori():
    return [_omamori("交通安全", "SAFE DRIVE"), _omamori("必勝", "WIN THE RACE"),
            _omamori("開運", "GOOD LUCK")]


# ====================================================================== 6 Rundbild Drift
def drift_round():
    R = 120.0
    g = circle(0, 0, R, 128).difference(circle(0, -R + 9, 3.2))
    eng = []
    eng.append(circle(-48, -44, 40, 96))
    sea = circle(0, 0, R - 8, 128).intersection(box(-R, 52, R, R))
    eng.append(seigaiha(sea, r=10, rings=3, w=1.1))
    eng.append(box(-R, 49, R, 51.2).intersection(circle(0, 0, R - 8)))
    cg, ce, cs = car("coupe", 150, -88, 46, wheels="eng")
    car_eng = cg.difference(ce.buffer(0.01))
    car_eng = affinity.rotate(car_eng, -5, origin=(0, 46))
    cs = [affinity.rotate(s, -5, origin=(0, 46)) for s in cs]
    eng.append(car_eng)
    # Rauchwolken als Spiralen hinter dem Heck
    smoke = []
    for cx, cy, r in [(-98, 26, 10), (-82, 12, 8), (-102, 2, 7), (-70, 30, 6)]:
        pts = [polar(r * (1 - t / 12.0) ** 0.9, t * 40 + 180, cx, cy) for t in range(0, 12)]
        smoke.append(LineString(pts).buffer(0.9))
        smoke.append(LineString([polar(r, a, cx, cy) for a in range(90, 300, 10)]).buffer(0.9))
    eng.append(unary_union(smoke).difference(car_eng.buffer(2)))
    eng.append(vtext("ドリフト", JP, 86, -38, 17))
    eng.append(ctext("DRIFT", SPORT, 28, -82, size=16))
    eng = unary_union(eng).difference(circle(0, 0, R).exterior.buffer(9))
    sc = [circle(0, 0, R - 5, 128).exterior.difference(circle(0, -R + 9, 6))]
    return [single(Part("Rundbild Drift", g, eng.intersection(g), sc + cs))]


# ====================================================================== 7 3D-Steckauto
def jdm_steck():
    from autos import CARS
    L = 180
    k = L / 100
    dx = sum(CARS["coupe"]["door"]) / 2 * k
    roundel = circle(dx, -13.5 * k, 9.5).difference(ctext("86", SPORT, dx, -13.5 * k, size=11))
    return steck_car("coupe", L, 66, "Steckauto Coupe", eng_extra=roundel)


# ====================================================================== 8 Handyhalter
ANG = 68.0     # Neigung der Rueckwand


def phone_stand(title="JDM", kanji="走", kind="coupe"):
    a = math.radians(ANG)
    d = (math.cos(a), -math.sin(a))          # Richtung der Rueckwand (nach oben/hinten)
    P0 = (44.0, 0.0)
    A_LEN, A_W, NOTCH = 116.0, 84.0, 38.0
    # Teil A: Rueckwand mit Schlitz von unten
    ga = rrect(-A_W / 2, 0, A_W / 2, A_LEN, 6)
    ga = ga.difference(box(-SLOT / 2, A_LEN - NOTCH, SLOT / 2, A_LEN + 1))
    cg, ce, cs = car(kind, 66, -33, 30, wheels="eng")
    eng_a = unary_union([cg.difference(ce.buffer(0.01)),
                         ctext(title, SPORT, 0, 46, size=17, max_w=60),
                         ctext(kanji, JP, 0, 64, size=12),
                         speedlines(-36, -6, 14, n=3, gap=4, w=1.3)])
    eng_a = eng_a.difference(box(-SLOT / 2 - 4, A_LEN - NOTCH - 2, SLOT / 2 + 4, A_LEN))
    pa = Part("Handyhalter Rueckwand", ga, eng_a, cs + [rrect(-A_W / 2 + 4, 4, A_W / 2 - 4, A_LEN - NOTCH - 6, 4).exterior])
    # Teil B: Standfuss (Seitenansicht), y nach unten = Boden bei y = 0
    top_len = 72.0
    Q = (P0[0] + d[0] * top_len, P0[1] + d[1] * top_len)
    n = (math.sin(a), math.cos(a))           # Normale (nach hinten/unten)
    strip = Polygon([(P0[0] - n[0] * 8, P0[1]), (Q[0] - n[0] * 8, Q[1] - n[1] * 8),
                     (Q[0] + n[0] * 8, Q[1] + n[1] * 8), (P0[0] + 14, 0)])
    rear = Polygon([(Q[0], Q[1]), (118, 0), (40, 0)])
    base = box(22, -6, 118, 0)
    lip = box(22, -14, 29, 0)
    gb = round_convex(unary_union([strip, rear, base, lip]), 2.0)
    gb = round_concave(gb, 2.0)
    # Schlitz von oben entlang der Rueckwand (Laenge = Ueberlappung - Kerbe in A)
    over = top_len + 3
    sl_len = over - NOTCH
    S0 = (P0[0] + d[0] * (over - sl_len), P0[1] + d[1] * (over - sl_len))
    S1 = (P0[0] + d[0] * (over + 5), P0[1] + d[1] * (over + 5))
    slot = LineString([S0, S1]).buffer(SLOT / 2, cap_style="flat")
    gb = gb.difference(slot)
    # Gewichtsersparnis + Deko: Fenster im Fuss
    win = Polygon([(60, -8), (100, -8), (Q[0] + 10, Q[1] + 22)]).buffer(-1).buffer(1)
    gb = gb.difference(round_convex(win, 3))
    pb = Part("Handyhalter Fuss", gb, None, [])
    return [single(pa), single(pb)]


# ====================================================================== 9 Kennzeichen-Wandschild
def plate_sign():
    W, H = 330.0, 165.0
    g = rrect(0, 0, W, H, 12).difference(unary_union([circle(58, 20, 3.5), circle(W - 58, 20, 3.5)]))
    eng = unary_union([ctext("東京", JP, 128, 40, size=28),
                       ctext("300", SANS, 212, 40, size=30, max_h=21),
                       ctext("な", JP, 42, 108, size=36),
                       ctext("20-26", SANS, 192, 106, size=90, max_w=232, max_h=72)])
    sc = [rrect(6, 6, W - 6, H - 6, 8).exterior, rrect(9.5, 9.5, W - 9.5, H - 9.5, 6).exterior]
    return [single(Part("Kennzeichen-Schild", g, eng, sc))]


# ====================================================================== 10 Laterne Tokyo Night
LX, LY, LZ = 90.0, 90.0, 110.0
GROUND = LZ - 18 - MAT


def _city(W):
    g = [box(0, GROUND - 7, W, LZ)]
    holes = []
    blds = [(14, 12, 40), (24, 9, 30), (34, 11, 52), (50, 8, 34), (60, 12, 46), (72, 10, 30)]
    for x, w, h in blds:
        b = box(x - w / 2, GROUND - 6 - h, x + w / 2, GROUND)
        g.append(b)
        for yy in range(int(GROUND - h), int(GROUND - 12), 6):
            for xx in (x - w / 4, x + w / 4):
                if w > 9:
                    holes.append(box(xx - 1.2, yy, xx + 1.2, yy + 2.6))
    # Sendeturm
    tx = 44.0
    g.append(Polygon([(tx - 6, GROUND - 6), (tx - 1.3, GROUND - 74), (tx + 1.3, GROUND - 74), (tx + 6, GROUND - 6)]))
    g.append(box(tx - 4.5, GROUND - 46, tx + 4.5, GROUND - 42))
    g.append(stroke([(tx, GROUND - 74), (tx, GROUND - 82)], 1.4))
    cg, ce, cs = car("coupe", 50, W / 2 - 25, GROUND - 1, wheels="cut")
    return unary_union(g + [cg]), unary_union(holes).difference(cg.buffer(1))


def _pass(W):
    mt = Polygon([(0, GROUND - 10), (14, GROUND - 46), (26, GROUND - 32), (44, GROUND - 66), (62, GROUND - 36),
                  (76, GROUND - 50), (W, GROUND - 22), (W, LZ), (0, LZ)])
    cg, ce, cs = car("roadster", 52, 18, GROUND - 1, wheels="cut", facing="left")
    return unary_union([mt, box(0, GROUND - 4, W, LZ), cg])


def _torii(W):
    x = W / 2
    fuji = Polygon([(4, GROUND - 6), (32, GROUND - 52), (38, GROUND - 56), (52, GROUND - 56), (58, GROUND - 52),
                    (W - 4, GROUND - 6)])
    ti = [box(x - 22, GROUND - 40, x + 22, GROUND - 36),
          Polygon([(x - 26, GROUND - 44), (x + 26, GROUND - 44), (x + 23, GROUND - 40), (x - 23, GROUND - 40)]),
          box(x - 18, GROUND - 33, x + 18, GROUND - 30),
          box(x - 16, GROUND - 40, x - 12, GROUND), box(x + 12, GROUND - 40, x + 16, GROUND)]
    torii = affinity.scale(unary_union(ti), 0.7, 0.7, origin=(x, GROUND))
    cap = Polygon([(30, GROUND - 47), (38, GROUND - 54), (52, GROUND - 54), (60, GROUND - 47), (52, GROUND - 49),
                   (45, GROUND - 46), (38, GROUND - 49)])
    fuji = fuji.difference(torii.buffer(1.6)).difference(cap)
    return unary_union([box(0, GROUND - 6, W, LZ), torii, fuji])


def tokyo_lantern():
    W = LX
    city, win_holes = _city(W)
    front_hole = unary_union([scene_window(W, LZ, city), win_holes])
    back_hole = scene_window(W, LZ, _pass(W))
    side_hole = scene_window(LY, LZ, _torii(LY))
    t_front = ctext("TOKYO NIGHTS", SPORT, W / 2, LZ - 10.5, size=9, max_w=W - 26)
    t_back = unary_union([ctext("峠", JP, W / 2 - 18, LZ - 10.5, size=9),
                          ctext("TOUGE", SPORT, W / 2 + 6, LZ - 10.5, size=9, max_w=40)])
    t_side = ctext("夜", JP, LY / 2, LZ - 10.5, size=9)
    stars_g = unary_union([round_convex(star(sx, 9, 3.6, 1.6), 0.3) for sx in (7, W - 7)])
    faces = {"front": (unary_union([front_hole, stars_g]), t_front, []),
             "back": (unary_union([back_hole, stars_g]), t_back, []),
             "left": (side_hole, t_side, []), "right": (side_hole, t_side, [])}
    parts = finger_box(LX, LY, LZ, faces, bottom_hole=circle(LX / 2, LY / 2, 11),
                       bottom_eng=ctext("JDM", SPORT, LX / 2, LY / 2 + 22, size=12), name="Laterne")
    return parts
