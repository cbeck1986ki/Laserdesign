"""Serie 3: Versicherung fuer Gewerbe & Landwirtschaft (einfarbig, Plotter).
Aufruf: python3 tools/serie3_versicherung.py [slug-praefix ...]"""
import math
import sys
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box

sys.path.insert(0, str(Path(__file__).parent))
from vinyl import (ALFA, OSWALD, PACIFICO, RYE, banner, bar, build, circle,  # noqa: E402
                   circle_text_bottom, circle_text_top, frame, hline_rule, knock, leaf, polyline, ring, rrect,
                   stack, star, svgpath, text, union, arch)

OUT = Path(__file__).resolve().parent.parent / "tshirt-plotter" / "serie3_versicherung"


def place(g, dx=0, dy=0, s=1.0, rot=0):
    if rot:
        g = affinity.rotate(g, rot, origin=(0, 0))
    if s != 1:
        g = affinity.scale(g, s, s, origin=(0, 0))
    return affinity.translate(g, dx, dy)


# ================================================================== Illustrationen
def tyre(cx, cy, r, t, lugs, lug_h, hub):
    g = ring(cx, cy, r, t)
    for i in range(lugs):
        a = 2 * math.pi * i / lugs
        w = 2 * math.pi * r / lugs * 0.45
        lug = Polygon([(-w / 2, 0), (w / 2, 0), (w * 0.35, -lug_h), (-w * 0.35, -lug_h)])
        lug = affinity.rotate(affinity.translate(lug, 0, -r + 0.5), math.degrees(a), origin=(0, 0))
        g = g.union(affinity.translate(lug, cx, cy))
    rim = ring(cx, cy, r - t - 3.2, 3.4)
    spokes = union([bar((cx, cy), (cx + (r - t - 4) * math.cos(a), cy + (r - t - 4) * math.sin(a)), 3.4)
                    for a in np.linspace(0, 2 * math.pi, 7)[:-1]])
    return union(g, rim, spokes, circle(cx, cy, hub))


def tractor():
    rear = tyre(38, 0, 44, 11, 22, 4.5, 9)
    front = tyre(-70, 16, 27, 8, 16, 3.5, 6)
    hood = svgpath("M -98 -46 L -6 -46 L -6 -8 L -92 -8 C -98 -8 -100 -12 -100 -16 L -100 -42 "
                   "C -100 -45 -99 -46 -98 -46 Z")
    grille = union([bar((-92, -40 + i * 7), (-80, -40 + i * 7), 2.6, "flat") for i in range(4)])
    hood = knock(hood, grille)
    cab = svgpath("M -8 -126 L 76 -126 L 76 -118 L 70 -118 L 70 -44 L -8 -44 Z")
    window = svgpath("M 2 -112 L 60 -112 L 60 -58 L 10 -58 C 5 -58 2 -61 2 -66 Z")
    cab = knock(cab, window)
    seat = svgpath("M 30 -60 L 46 -60 L 46 -82 L 52 -82 L 52 -56 L 30 -56 Z")
    fender = ring(38, 0, 58, 9).intersection(box(-30, -80, 110, -6))
    exhaust = union(bar((-58, -46), (-58, -80), 6, "flat"), rrect(-62, -86, -54, -78, 1.5))
    body = union(hood, cab, seat, exhaust, fender)
    body = knock(body, circle(38, 0, 58 - 9 - 2.4), circle(-70, 16, 27 + 4.5 + 2.4))
    body = knock(body, ring(38, 0, 58.0 + 0.01, 0.01))
    hitch = union(bar((-6, -14), (6, -14), 8, "flat"), bar((-100, -10), (-108, -10), 4, "flat"))
    return union(body, rear, front, hitch)


def d_traktor():
    tr = place(tractor(), 0, -24)
    ground = union([bar((x0, 36), (x1, 36), 3.2, "round") for x0, x1 in ((-128, -60), (-46, 128))])
    tufts = union([polyline([(x - 6, 30), (x - 2, 36)], 2.4) for x in (-120, -24, 112)] +
                  [polyline([(x + 5, 29), (x + 1, 36)], 2.4) for x in (-120, -24, 112)])
    t1 = text("ACKERN.", ALFA, 30, 0, 90, tracking=0.02, width=250)
    t2 = text("ABSICHERN.", ALFA, 30, 0, 130, tracking=0.02, width=250)
    t3 = text("ANPACKEN.", ALFA, 30, 0, 170, tracking=0.02, width=250)
    return union(tr, ground, tufts, t1, t2, t3)


def barn_scene():
    """Hof mit Scheune, Silo, Sonne und Ackerfurchen; Horizont bei y=0."""
    barn = svgpath("M -40 0 L -40 -46 L -30 -72 L 0 -88 L 30 -72 L 40 -46 L 40 0 Z")
    roof = svgpath("M -47 -42 L -35 -76 L 0 -96 L 35 -76 L 47 -42 L 40 -42 L 30 -70 L 0 -87 L -30 -70 "
                   "L -40 -42 Z")
    barn = knock(barn, roof.buffer(2.4))
    door = rrect(-17, -36, 17, 0, 1)
    barn = knock(barn, door)
    door_fr = union(frame(-15, -34, 15, 2, 0, 3), polyline([(-15, -34), (15, 0)], 3), polyline([(15, -34), (-15, 0)], 3))
    door_fr = door_fr.intersection(box(-15, -34, 15, 0))
    loft = rrect(-9, -66, 9, -50, 1)
    barn = knock(barn, loft)
    silo = svgpath("M 52 0 L 52 -84 C 52 -98 76 -98 76 -84 L 76 0 Z")
    silo = knock(silo, union([box(50, y, 80, y + 2.6) for y in (-80, -60, -40, -20)]))
    sun = circle(-62, -66, 15)
    rays = union([bar((-62 + 21 * math.cos(a), -66 + 21 * math.sin(a)),
                      (-62 + 28 * math.cos(a), -66 + 28 * math.sin(a)), 3.4)
                  for a in np.radians(np.arange(0, 360, 30))])
    sunall = knock(union(sun, rays), barn.buffer(4).union(roof.buffer(4)))
    return union(barn, roof, door_fr, silo, sunall)


def d_hof_badge():
    R = 128
    outer = ring(0, 0, R, 6)
    inner = ring(0, 0, 90, 3)
    top = circle_text_top("HOF · ERNTE · TIER", ALFA, 15, 0, 0, 101, tracking=0.08)
    bot = circle_text_bottom("GUT ABGESICHERT", ALFA, 15, 0, 0, 116, tracking=0.1)
    stars = [star(-108, 0, 7), star(108, 0, 7)]
    scene = place(barn_scene(), 0, 22, 0.86)
    # Ackerfurchen unterhalb des Horizonts, auf den Innenkreis begrenzt
    clipc = circle(0, 0, 84)
    furrows = []
    for i in range(-8, 9):
        x0, x1 = i * 22 - 7, i * 22 + 7
        furrows.append(Polygon([(i * 5 - 1.5, 26), (i * 5 + 1.5, 26), (x1, 90), (x0, 90)]))
    field = union(furrows).intersection(clipc).difference(box(-100, -100, 100, 27.5))
    horizon = bar((-84, 24), (84, 24), 2.6, "flat").intersection(clipc)
    return union(outer, inner, top, bot, stars, scene, field, horizon)


def wheat_ear(length=70, grains=7, gw=7.5, gl=15, stalk=2.4, awns=True):
    """Aehre nach oben (-y), Fuss bei (0,0)."""
    g = [bar((0, 0), (0, -length), stalk)]
    top = -length
    for i in range(grains):
        y = top + 10 + i * gl * 0.62
        for s in (-1, 1):
            g.append(leaf(s * gw * 0.55, y, gl, gw, -90 + s * 24))
    g.append(leaf(0, top + 3, gl * 0.95, gw * 0.95, -90))
    if awns:
        for s in (-1, 1):
            g.append(polyline([(s * 2, top + 4), (s * 7, top - 16)], 1.8))
    return union(g)


def d_ernte():
    ears = []
    for ang, L in ((-34, 120), (-20, 128), (-7, 134), (7, 134), (20, 128), (34, 120)):
        e = wheat_ear(length=L * 0.66, grains=7, gw=9, gl=17, stalk=2.8, awns=True)
        stalk = bar((0, 0), (0, 70), 2.6, "flat")
        ears.append(affinity.rotate(union(e, stalk), ang, origin=(0, 52)))
    sheaf = union(ears)
    sheaf = affinity.translate(sheaf, 0, -40)
    band = rrect(-21, -4, 21, 10, 3)
    sheaf = knock(sheaf, band.buffer(2.4)).union(band)
    t1 = arch(text("ERNTE GUT,", ALFA, 32, 0, -162, tracking=0.03), 330, 0, -162)
    t2 = text("alles gut.", PACIFICO, 44, 0, 78)
    return union(sheaf, t1, t2)


def cloud(cx, cy, w):
    k = w / 100
    c = union(circle(-26, 0, 22), circle(2, -14, 28), circle(30, -2, 20), rrect(-48, -6, 50, 20, 10))
    c = c.intersection(box(-60, -60, 60, 20))
    return place(c, cx, cy, k)


def umbrella(cx, cy, r):
    canopy = circle(0, 0, r).intersection(box(-r, -r, r, 0))
    scal = union([circle(x, 0, r / 6) for x in np.linspace(-r * 5 / 6, r * 5 / 6, 6)])
    canopy = canopy.difference(scal.difference(box(-r, -r, r, -r * 0.03)))
    ribs = union([polyline([(0, -r), (x, 0)], 2.4) for x in np.linspace(-r / 2, r / 2, 3)])
    canopy = knock(canopy, ribs.difference(box(-r, -r - 1, r, -r + 8)))
    tip = bar((0, -r), (0, -r - 9), 3.2)
    shaft = bar((0, -2), (0, r), 4.2, "flat")
    return place(union(canopy, tip, shaft), cx, cy)


def d_hagel():
    cl = cloud(-6, -128, 150)
    rng = np.random.default_rng(7)
    hail = []
    pts = [(-70, -84), (-46, -66), (-88, -56), (-28, -88), (14, -82), (40, -90), (62, -70), (84, -84),
           (-74, -36), (78, -44), (100, -62), (-102, -24), (-12, -64), (104, -20), (-56, -12), (60, -16),
           (24, -60)]
    for x, y in pts:
        hail.append(circle(x, y, 3.8 + rng.random() * 2.2))
    um = umbrella(0, -14, 64)
    hail = union([h for h in hail if not h.intersects(um.buffer(4)) and not h.intersects(cl.buffer(3))])
    ears = union([place(wheat_ear(L, 6, 7, 14, 2.4), x, 50, rot=a)
                  for x, L, a in ((-44, 58, -10), (-24, 66, -4), (24, 66, 4), (44, 58, 10))])
    ears = knock(ears, um.buffer(3.2))
    ground = bar((-110, 52), (110, 52), 3.4)
    t1 = text("HAGEL?", ALFA, 34, 0, 112, tracking=0.03, width=230)
    t2 = text("KANN KOMMEN.", ALFA, 22, 0, 146, tracking=0.06, width=230)
    return union(cl, hail, um, ears, ground, t1, t2)


def cow():
    head = svgpath("M -38 -64 C -18 -74 18 -74 38 -64 C 46 -36 44 -6 36 18 L -36 18 C -44 -6 -46 -36 -38 -64 Z")
    muzzle = svgpath("M -42 24 C -42 6 -26 0 0 0 C 26 0 42 6 42 24 C 42 44 26 56 0 56 C -26 56 -42 44 -42 24 Z")
    nostrils = union(place(affinity.scale(circle(0, 0, 7), 0.8, 1.15), -15, 28, rot=-20),
                     place(affinity.scale(circle(0, 0, 7), 0.8, 1.15), 15, 28, rot=20))
    muzzle = knock(muzzle, nostrils)
    head = knock(head, muzzle.buffer(2.6))
    ear_l = leaf(-64, -46, 46, 22, 14)
    ear_r = leaf(64, -46, 46, 22, -14)
    ears = knock(union(ear_l, ear_r), head.buffer(2.6))
    ears = knock(ears, union(leaf(-66, -46, 28, 10, 14), leaf(66, -46, 28, 10, -14)))
    horn_l = svgpath("M -32 -62 C -46 -64 -58 -72 -62 -94 C -50 -86 -40 -80 -24 -72 Z")
    horn_r = affinity.scale(horn_l, -1, 1, origin=(0, 0))
    horns = knock(union(horn_l, horn_r), head.buffer(2.4))
    tuft = union([circle(x, -66, 7) for x in (-12, 0, 12)])
    head = union(head, tuft)
    # Sonnenbrille
    lens_l = svgpath("M -44 -40 L -6 -40 C -6 -24 -10 -14 -24 -14 C -38 -14 -44 -24 -44 -40 Z")
    lens_r = affinity.scale(lens_l, -1, 1, origin=(0, 0))
    bridge = bar((-6, -36), (6, -36), 4, "flat")
    arms = union(bar((-44, -38), (-52, -40), 3.6, "flat"), bar((44, -38), (52, -40), 3.6, "flat"))
    glasses = union(lens_l, lens_r, bridge)
    shine = union(polyline([(-36, -34), (-28, -24)], 2.4), polyline([(14, -34), (22, -24)], 2.4))
    head = knock(head, glasses.buffer(2.4))
    glasses = knock(glasses, shine)
    spot = svgpath("M 4 -8 C 12 -16 26 -12 26 -2 C 26 6 16 8 10 4 C 4 2 0 -4 4 -8 Z")
    head = knock(head, spot)
    return union(head, muzzle, ears, horns, glasses, arms)


def d_kuh():
    c = place(cow(), 0, -60, 1.25)
    t1 = text("KUHL BLEIBEN.", ALFA, 30, 0, 50, tracking=0.03, width=250)
    t2 = text("DER HOF IST ABGESICHERT.", OSWALD, 13, 0, 78, tracking=0.14, width=250)
    return union(c, t1, t2)


def shield(w, h):
    return svgpath(f"M {-w / 2} {-h / 2} L {w / 2} {-h / 2} L {w / 2} {h * 0.05} "
                   f"C {w / 2} {h * 0.3} {w * 0.25} {h * 0.42} 0 {h / 2} "
                   f"C {-w * 0.25} {h * 0.42} {-w / 2} {h * 0.3} {-w / 2} {h * 0.05} Z")


def d_risiko():
    sh = shield(54, 64)
    sh = knock(sh, shield(54, 64).buffer(-5).difference(shield(54, 64).buffer(-7.4)))
    sh = knock(sh, polyline([(-12, 0), (-3, 10), (14, -10)], 6.5))
    t1 = text("RISIKO", ALFA, 46, tracking=0.03, width=210)
    t2 = text("IST MEIN HOBBY.", OSWALD, 16, tracking=0.2, width=210)
    rule = hline_rule(0, 0, 250, t=2.4, diamond=5)
    t3 = text("ABSICHERN", ALFA, 38, tracking=0.03, width=250)
    t4 = text("IST MEIN BERUF.", OSWALD, 16, tracking=0.2, width=250)
    return stack([sh, t1, t2, rule, t3, t4], [12, 7, 12, 12, 7])


def hammer():
    handle = rrect(-4.2, -8, 4.2, 74, 4.2)
    grip = rrect(-6.5, 40, 6.5, 76, 6.5)
    head = svgpath("M -28 -19 L 12 -19 C 20 -19 27 -22 32 -29 C 35 -14 26 -1 12 -1 L -28 -1 Z")
    face = rrect(-38, -23, -25, 3, 2.5)
    return union(handle, grip, head, face)


def wrench():
    shaft = rrect(-4.2, -44, 4.2, 44, 4.2)
    jaw = circle(0, -52, 15).difference(rrect(-6.5, -76, 6.5, -50, 1.5))
    ring_end = ring(0, 52, 13, 6.4)
    return union(shaft, jaw, ring_end)


def d_handwerk():
    inner = shield(170, 196).buffer(-6)
    h = place(affinity.translate(hammer(), 0, -28), 0, 0, 1.1, rot=-40)
    w = place(wrench(), 0, 0, 1.15, rot=40)
    h = knock(h, w.buffer(3))
    tools = union(h, w)
    tools = place(tools, 0, -10)
    # Werkzeuge stehen als Aussparung im Schild -> invertieren
    shield_fill = inner.buffer(-3.2)
    body = union(knock(shield(170, 196), inner), knock(shield_fill, tools.buffer(0)))
    ban = banner(0, 66, 236, 40, tail=26, drop=10, notch=9, gap=2.0, label="HANDWERK", font=ALFA, cap=20,
                 tracking=0.1, bend=500)
    body = knock(body, ban.buffer(3))
    top = arch(text("RÜCKENDECKUNG FÜRS", OSWALD, 16, 0, -116, tracking=0.16), 300, 0, -116)
    return union(body, ban, top)


def d_kleingedrucktes():
    page = frame(-80, -100, 60, 70, 4, 4.4)
    page = knock(page, box(26, -104, 64, -66))
    page = union(page, polyline([(30, -100), (60, -70)], 4.4), polyline([(30, -100), (30, -70), (60, -70)], 4.4,
                                                                          cap="flat", join="mitre"))
    lines = []
    for i, y in enumerate(range(-84, 60, 11)):
        x1 = 46 if y > -66 else 18
        if i % 4 == 3:
            x1 -= 40
        lines.append(bar((-66, y), (x1, y), 3.2, "flat"))
    lines = union(lines)
    lens_c, lens_r = (18, 10), 50
    lens = ring(*lens_c, lens_r, 9)
    handle = bar((lens_c[0] + 0.7 * (lens_r + 4), lens_c[1] + 0.7 * (lens_r + 4)),
                 (lens_c[0] + 0.7 * (lens_r + 54), lens_c[1] + 0.7 * (lens_r + 54)), 17, "round")
    neck = bar((lens_c[0] + 0.7 * (lens_r - 2), lens_c[1] + 0.7 * (lens_r - 2)),
               (lens_c[0] + 0.7 * (lens_r + 10), lens_c[1] + 0.7 * (lens_r + 10)), 11, "flat")
    mag = union(lens, handle, neck)
    para = text("§", ALFA, 46, lens_c[0], lens_c[1] + 23)
    inside = circle(*lens_c, lens_r - 9 - 2.6)
    page = knock(union(page, lines), circle(*lens_c, lens_r + 2.6), handle.buffer(2.6), neck.buffer(2.6))
    g = union(page, mag, para.intersection(inside))
    g = place(g, 6, -40)
    t1 = text("ICH LESE DAS", ALFA, 20, 0, 108, tracking=0.06, width=250)
    t2 = text("KLEINGEDRUCKTE.", ALFA, 20, 0, 138, tracking=0.03, width=250)
    t3 = text("freiwillig.", PACIFICO, 26, 60, 184)
    return union(g, t1, t2, t3)


def rooster():
    d = ("M -54 -71 L -41 -78 C -42 -86 -42 -93 -38 -96 C -34 -100 -30 -97 -30 -93 C -28 -101 -21 -101 -20 -94 "
         "C -17 -100 -9 -98 -11 -90 C -6 -90 -5 -83 -12 -79 C -12 -70 -8 -60 0 -55 C 10 -50 22 -54 30 -62 "
         "C 36 -86 54 -104 76 -100 C 62 -92 54 -78 56 -62 C 66 -76 78 -82 90 -78 C 76 -68 70 -54 68 -40 "
         "C 74 -48 82 -50 90 -48 C 76 -36 64 -22 48 -17 C 38 -13 28 -11 20 -11 C 4 -11 -12 -18 -21 -30 "
         "C -28 -40 -31 -52 -32 -61 C -36 -58 -44 -56 -44 -63 L -41 -68 Z")
    body = svgpath(d)
    body = knock(body, circle(-30, -81, 2.6))
    wing = svgpath("M -6 -40 C 6 -50 26 -48 36 -36 C 26 -38 14 -36 6 -26 C 0 -30 -4 -34 -6 -40 Z")
    body = knock(body, wing.buffer(2.0).difference(wing))
    legs = union(polyline([(4, -13), (0, 0)], 4), polyline([(18, -12), (20, 0)], 4),
                 bar((-8, 0), (8, 0), 3.2), bar((12, 0), (28, 0), 3.2))
    return union(body, legs)


def d_wetterhahn():
    r = place(rooster(), 0, -36, 1.3)
    pole = bar((10, -36), (10, 70), 5, "flat")
    arrow_shaft = bar((-104, -24), (100, -24), 4.4, "flat")
    head = Polygon([(-122, -24), (-98, -38), (-102, -24), (-98, -10)])
    tail = union([Polygon([(x, -24), (x + 14, -38), (x + 24, -38), (x + 10, -24), (x + 24, -10), (x + 14, -10)])
                  for x in (84, 100)])
    vane = union(arrow_shaft, head, tail)
    vane = knock(vane, r.buffer(2.4)).union(r)
    cross = union(bar((-58, 34), (78, 34), 3.6, "flat"), circle(10, 34, 6))
    letters = union(text("W", ALFA, 14, -70, 41), text("O", ALFA, 14, 90, 41))
    g = union(vane, pole, cross, letters)
    g = place(g, -6, 0)
    top = arch(text("BAUERNREGEL", RYE, 22, 0, -172, tracking=0.08, width=210), 520, 0, -172)
    l1 = text("KRÄHT DER HAHN FRÜH AUF DEM MIST,", OSWALD, 12.5, 0, 82, tracking=0.06, width=256)
    l2 = text("GUT, WENN DER HOF VERSICHERT IST.", OSWALD, 12.5, 0, 106, tracking=0.06, width=256)
    return union(g, top, l1, l2)


# ---------------------------------------------------- Gefahren-Icons
def icon_flame():
    outer = svgpath("M 0 -24 C 7 -13 17 -6 15 7 C 13.5 17 7 23 0 23 C -9 23 -16 16 -16 6 C -16 -3 -10 -7 -7 -15 "
                    "C -3 -9 -2 -5 -2 0 C 3 -6 3 -15 0 -24 Z")
    inner = svgpath("M 1 2 C 5 7 8 11 7 16 C 6 19.5 3.5 21 0 21 C -4 21 -7 18.5 -7 15 C -7 11 -4 9 -3 5 "
                    "C -1.5 8 -0.5 9 0 11 C 1.5 8 2 5 1 2 Z")
    return knock(outer, inner)


def icon_storm():
    c = cloud(0, -2, 46)
    bolt = Polygon([(2, -2), (-8, 12), (0, 12), (-5, 26), (10, 6), (2, 6), (8, -2)])
    return union(knock(c, bolt.buffer(2.2)), bolt)


def icon_drop():
    d = svgpath("M 0 -24 C 8 -11 17 -1 17 8 C 17 18 9 24 0 24 C -9 24 -17 18 -17 8 C -17 -1 -8 -11 0 -24 Z")
    hl = ring(0, 8, 10.5, 3).intersection(box(-20, 8, -2, 30))
    return knock(d, hl)


def icon_lock():
    shackle = ring(0, -8, 12, 4.8).intersection(box(-20, -30, 20, -6)).union(
        union(box(-12, -8, -7.2, 0), box(7.2, -8, 12, 0)))
    body = rrect(-17, -2, 17, 24, 3.5)
    hole = union(circle(0, 8, 4), Polygon([(-2.4, 9), (2.4, 9), (3.4, 18), (-3.4, 18)]))
    return union(shackle, knock(body, hole))


def d_police():
    icons = [("FEUER", icon_flame), ("STURM", icon_storm), ("WASSER", icon_drop), ("EINBRUCH", icon_lock)]
    g = []
    for i, (lab, fn) in enumerate(icons):
        cx = -97.5 + i * 65
        g.append(ring(cx, 0, 29, 3.6))
        g.append(place(fn(), cx, 0, 0.85))
        g.append(text(lab, OSWALD, 9.5, cx, 48, tracking=0.12))
    t1 = text("KEINE PANIK.", ALFA, 32, 0, -54, tracking=0.03, width=252)
    rule = hline_rule(0, 70, 252, t=2.4, diamond=5)
    t2 = text("ICH HAB FÜR ALLES", OSWALD, 17, 0, 104, tracking=0.12, width=252)
    t3 = text("'NE POLICE.", ALFA, 30, 0, 144, tracking=0.04, width=252)
    return union(g, t1, rule, t2, t3)


DESIGNS = [
    ("01_ackern-absichern-anpacken", "Ackern. Absichern. Anpacken.", d_traktor, (44, 72, 44), (246, 238, 214)),
    ("02_hof-badge", "Hof · Ernte · Tier – gut abgesichert", d_hof_badge, (226, 214, 186), (66, 44, 30)),
    ("03_hagel-kann-kommen", "Hagel? Kann kommen.", d_hagel, (34, 52, 84), (250, 250, 250)),
    ("04_ernte-gut-alles-gut", "Ernte gut, alles gut.", d_ernte, (120, 84, 50), (250, 222, 140)),
    ("05_kuhl-bleiben", "Kuhl bleiben.", d_kuh, (250, 250, 248), (24, 24, 26)),
    ("06_risiko-hobby", "Risiko ist mein Hobby. Absichern mein Beruf.", d_risiko, (22, 30, 52), (255, 196, 64)),
    ("07_rueckendeckung-handwerk", "Rückendeckung fürs Handwerk", d_handwerk, (64, 66, 70), (250, 140, 40)),
    ("08_kleingedrucktes", "Ich lese das Kleingedruckte. Freiwillig.", d_kleingedrucktes, (180, 200, 214),
     (20, 32, 56)),
    ("09_bauernregel-wetterhahn", "Bauernregel mit Wetterhahn", d_wetterhahn, (150, 40, 34), (250, 240, 220)),
    ("10_fuer-alles-ne-police", "Keine Panik. Ich hab für alles 'ne Police.", d_police, (30, 30, 32),
     (255, 255, 255)),
]

if __name__ == "__main__":
    only = sys.argv[1:]
    build([d for d in DESIGNS if not only or any(d[0].startswith(o) for o in only)], OUT)
