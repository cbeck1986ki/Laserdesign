"""Gemeinsame Bausteine fuer die Auto-Serien (JDM und Luxus-Sportwagen).

Alle Fahrzeuge sind frei gezeichnete, generische Silhouetten ohne Marken, Logos oder Modellnamen.
Einheiten mm, y nach unten, Fahrbahn bei y = 0.
"""
import math

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from designs import MAT, SLOT, _fingers
from lasergeo import Part, circle, polar, polys, round_concave, round_convex, stroke, text

SANS = "Inter-Bold.otf"
SPORT = "InterDisplay-BlackItalic.otf"
JP = "ipag.ttf"


# ---------------------------------------------------------------- Helfer
def ellipse(x, y, rx, ry, rot=0):
    e = affinity.scale(circle(0, 0, 1, 32), rx, ry, origin=(0, 0))
    return affinity.translate(affinity.rotate(e, rot, origin=(0, 0)), x, y)


def rrect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=12)


def single(part):
    n = len(polys(part.solid))
    assert n == 1, f"{part.name}: {n} getrennte Stuecke"
    return part.clean()


def ctext(s, font, cx, cy, size=None, width=None, max_h=None, max_w=None):
    """Text zentriert; optional auf max. Breite begrenzt."""
    g = text(s, font, size=size or 10, cx=cx, cy=cy, width=width, max_h=max_h)
    b = g.bounds
    if max_w and b[2] - b[0] > max_w:
        k = max_w / (b[2] - b[0])
        g = affinity.scale(g, k, k, origin=(cx, cy))
    return g


def vtext(s, font, cx, cy, size, gap=1.12):
    """Japanisch senkrecht: Zeichen untereinander, (cx, cy) = Mitte."""
    n = len(s)
    y0 = cy - (n - 1) * size * gap / 2
    return unary_union([text(ch, font, size=size, cx=cx, cy=y0 + i * size * gap)
                        for i, ch in enumerate(s)])


def spline(pts, n=10, closed=False):
    """Catmull-Rom-Kurve (offen oder geschlossen)."""
    pts = list(pts)
    if closed:
        p = [pts[-1]] + pts + pts[:2]
        segs = len(pts)
    else:
        p = [pts[0]] + pts + [pts[-1]]
        segs = len(pts) - 1
    out = []
    for i in range(1, segs + 1):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t
                                    + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3)
                             for j in range(2)))
    if not closed:
        out.append(pts[-1])
    return out


def arc_band(r0, r1, a0, a1, cx=0, cy=0, n=60):
    """Ringsegment zwischen den Winkeln a0..a1 (Grad, 0 = rechts, im Uhrzeigersinn)."""
    outer = [polar(r1, a0 + (a1 - a0) * i / n, cx, cy) for i in range(n + 1)]
    inner = [polar(r0, a1 - (a1 - a0) * i / n, cx, cy) for i in range(n + 1)]
    return Polygon(outer + inner)


def speedlines(x0, x1, y, n=4, gap=3.2, w=1.6, stagger=8):
    return unary_union([stroke([(x0 + (k % 2) * stagger + k * 3, y + k * gap),
                                (x1 - k * 6, y + k * gap)], w) for k in range(n)])


# ---------------------------------------------------------------- Fahrzeuge
# Normiert auf Laenge 100, Front rechts (x = 100), Heck links, Fahrbahn y = 0.
# body: Umriss (ohne Unterkante), glass: Fensterflaeche, wheels: (x, r), extra: Zusatzteile
CARS = {
    # 90er-Fastback-Coupe mit Heckfluegel
    "coupe": dict(
        body=[(1.5, -5), (0, -9), (0.3, -16), (2, -18.5), (12, -19.8), (27, -21.4), (36, -25.4),
              (46, -27.8), (55, -27.6), (63, -23.2), (72, -18.4), (86, -16.2), (95.5, -14.2),
              (99.6, -11.2), (100, -7), (98.6, -4.6)],
        glass=[(36.8, -24.6), (46, -26.8), (54.6, -26.6), (62, -22.6), (47, -21.8), (35.5, -22.2)],
        pillar=48.5, wheels=[(18.5, 8.6), (80.5, 8.6)], wing=True, popup=False,
        door=(46.5, 63.5), light=[(95, -13.6), (99.2, -11), (93.5, -12.1)]),
    # kompakter Fronttriebler-Hatchback
    "hatch": dict(
        body=[(1.2, -5), (0, -10), (0.6, -18.6), (4, -25.4), (11, -29), (38, -30), (52, -28.6),
              (67, -21.4), (86, -18.6), (96.5, -16.2), (99.8, -12.6), (100, -7), (98.4, -4.6)],
        glass=[(5.4, -25.4), (11.4, -28), (37.5, -28.8), (50.8, -27.6), (64.5, -21.6), (3.4, -21.6)],
        pillar=30, wheels=[(17, 9.6), (81.5, 9.6)], wing=False, popup=False,
        door=(31, 64), light=[(95.5, -15.6), (99.5, -12.5), (93.5, -13.8)]),
    # kantige Sportlimousine (Drift-Klassiker)
    "sedan": dict(
        body=[(1.2, -5), (0, -11), (0.3, -17.4), (3.4, -19.6), (17, -20.2), (26, -21.4), (33.5, -28.6),
              (60, -29.2), (68.5, -21.6), (90, -19.6), (98.6, -17.6), (100, -13), (100, -7), (98.4, -4.6)],
        glass=[(27.5, -21.6), (34.4, -27.6), (59.4, -28.1), (66.5, -21.6)],
        pillar=46.5, wheels=[(17.5, 8.8), (81, 8.8)], wing=False, popup=False,
        door=(33, 47, 66), light=[(96, -17.3), (99.8, -15.2), (94, -15.6)]),
    # leichter Roadster mit Klappscheinwerfern
    "roadster": dict(
        body=[(1.2, -5), (0, -10), (0.6, -15.8), (6, -17.4), (28, -18), (31.5, -21.8), (37, -22.4),
              (40, -18.6), (50.5, -18.4), (55, -25.6), (60.6, -25.6), (63.5, -18.2), (84, -16),
              (96.5, -13.2), (100, -9.2), (99, -4.6)],
        glass=[(55.8, -24.4), (59.8, -24.4), (61.8, -19.2), (53, -19.2)],
        pillar=None, wheels=[(18, 8.4), (80.5, 8.4)], wing=False, popup=True,
        door=(41, 60), light=[(91, -14.6), (96, -13.4), (91, -13.6)]),
    # flache Keilform (Kreiskolben-Coupe-Stil)
    "wedge": dict(
        body=[(1.2, -5), (0, -10), (0.4, -16.6), (3, -19.2), (15, -20.4), (26, -21.8), (38, -26.8),
              (50, -27.2), (60, -22.4), (72, -17), (88, -14.4), (97, -12), (100, -8.8), (99, -4.6)],
        glass=[(38.8, -26), (49.6, -26.3), (58.6, -22), (46, -21), (33, -22)],
        pillar=None, wheels=[(19, 8.4), (80, 8.4)], wing=False, popup=False,
        door=(44, 61), light=[(94, -12.8), (99, -10.4), (92.5, -11.6)]),
    # Mittelmotor-Supersportwagen
    "midengine": dict(
        body=[(1.2, -5), (0, -10), (0.6, -16.8), (3.8, -18.6), (16, -19.4), (30, -21.4), (40, -24.6),
              (52, -24.8), (62, -21), (72, -15), (90, -12), (97.5, -9.8), (100, -7.2), (99, -4.4)],
        glass=[(40.6, -23.8), (51.6, -23.9), (60.8, -20.6), (52, -19.6), (37.6, -20.6)],
        pillar=None, wheels=[(17, 8.8), (79.5, 8.8)], wing=False, popup=False, intake=True,
        door=(42, 62), light=[(93, -10.5), (98.6, -8.4), (91, -9.4)]),
    # Gran Turismo mit langer Motorhaube
    "gt": dict(
        body=[(1.2, -5), (0, -11), (0.8, -17), (5, -19), (18, -21), (30, -25.4), (40, -27),
              (48, -26.6), (56, -22.2), (66, -19), (88, -16.6), (97, -14), (100, -10.6), (99.6, -6),
              (98, -4.6)],
        glass=[(30.8, -24.6), (40, -26.2), (47.6, -25.8), (54.4, -21.8), (40, -21.2), (28.6, -22)],
        pillar=None, wheels=[(16.5, 9.0), (80, 9.0)], wing=False, popup=False,
        door=(39, 57), light=[(94, -14.2), (99.4, -11.4), (92.5, -12.6)]),
    # klassisches 60er-Jahre-Coupe mit Speichenraedern
    "classic": dict(
        body=[(1.2, -6), (0, -11), (1.6, -15.8), (9, -18.4), (21, -19), (31, -23.8), (41, -25.6),
              (49.6, -24.6), (56, -19.6), (70, -17.2), (80, -17.8), (91.5, -15.6), (98, -12),
              (100, -8.8), (98.8, -5.8)],
        glass=[(32, -23), (41, -24.7), (49, -23.8), (54.4, -19.8), (29.6, -20.2)],
        pillar=42.5, wheels=[(15.5, 8.2), (82, 8.2)], wing=False, popup=False, spokes=True,
        door=(40, 57), light=[(95.6, -14.6), (99, -11.6), (96.6, -11)]),
    # Hypercar mit Haifischflosse und Fluegel
    "hyper": dict(
        body=[(1.2, -4.4), (0, -8.6), (0.5, -14.6), (4, -16.4), (14, -17.4), (26, -19.4), (38, -23.6),
              (50, -23.8), (60, -20), (70, -14.6), (90, -12), (97.5, -10), (100, -7.2), (99, -4.2)],
        glass=[(38.6, -22.8), (49.6, -23), (58.8, -19.8), (50, -19), (35.6, -19.6)],
        pillar=None, wheels=[(17, 8.8), (78, 8.6)], wing=True, popup=False, intake=True, fin=True,
        door=(40, 60), light=[(92, -9.4), (98.6, -7.6), (90, -8.4)]),
}


def _wheel(cx, cy, r, style="eng", spokes=False):
    """Rad: liefert (Flaeche, Gravur, Ausschnitte)."""
    disc = circle(cx, cy, r, 48)
    rim_r = r * 0.66
    tire = disc.difference(circle(cx, cy, rim_r, 48))
    eng, holes = [tire], []
    if spokes:      # Speichenrad: feine Linien statt Loecher
        eng.append(circle(cx, cy, rim_r * 0.93).exterior.buffer(0.25))
        eng.append(circle(cx, cy, rim_r * 0.28))
        return disc, unary_union(eng), [LineString([polar(rim_r * 0.3, a, cx, cy),
                                                     polar(rim_r * 0.9, a + 12, cx, cy)])
                                         for a in range(0, 360, 30)]
    n = 5
    for k in range(n):
        a0 = -90 + 360 * k / n + 13
        a1 = a0 + 360 / n - 26
        win = arc_band(rim_r * 0.36, rim_r * 0.84, a0, a1, cx, cy, 12)
        win = round_convex(win, min(0.6, r * 0.06))
        (holes if style == "cut" else eng).append(win)
    eng.append(circle(cx, cy, rim_r * 0.18))
    return disc, unary_union(eng), holes


def car(kind, L=100.0, x=0.0, y=0.0, facing="right", wheels="eng", details=True, drop=0.0):
    """Fahrzeug-Silhouette. (x, y) = linke Kante auf der Fahrbahn. Liefert (solid, engrave, score)."""
    c = CARS[kind]
    k = L / 100.0
    T = lambda pts: [(px * k, py * k) for px, py in pts]
    body = Polygon(spline(T(c["body"]), 8)).buffer(0)    # Unterkante = gerade Verbindung
    solid, eng, score, holes = [], [], [], []
    for wx, wr in c["wheels"]:
        wx, wr = wx * k, wr * k
        wy = -wr
        arch = circle(wx, wy + 1.15 * k - drop * k, wr * 1.05)
        body = body.difference(arch)
        d, e, h = _wheel(wx, wy, wr, wheels, c.get("spokes", False))
        solid.append(d)
        if isinstance(e, list):
            score += e
        else:
            eng.append(e)
        if isinstance(h, list) and h and isinstance(h[0], LineString):
            score += h
        else:
            holes += h
        # Radlaufkante
        eng.append(arch.exterior.buffer(0.35 * k).intersection(body.buffer(0.01)))
    if c.get("wing"):
        if kind == "hyper":
            solid += [Polygon(T([(-2.5, -23.6), (12, -24.6), (12.5, -22.6), (-2, -21.8)])),
                      stroke(T([(6, -16.6), (5, -23)]), 1.6 * k)]
        else:
            solid += [Polygon(T([(-1.6, -25.8), (13.4, -25.2), (13.4, -23.6), (-1.4, -23.8)])),
                      stroke(T([(3, -18.8), (3.4, -24.4)]), 1.5 * k),
                      stroke(T([(10, -19.4), (10.4, -24.4)]), 1.5 * k)]
    if c.get("fin"):
        solid.append(Polygon(T([(5, -16), (12, -21.4), (38, -23.9), (38, -21.6), (14, -17)])))
    solid.append(body)
    g = unary_union([s_.buffer(0) for s_ in solid])
    if details:
        glass = Polygon(T(c["glass"])).buffer(0)
        glass = round_convex(glass, 0.8 * k)
        eng.append(glass)
        if c.get("pillar"):
            eng_cut = box(c["pillar"] * k - 1.0 * k, -40 * k, c["pillar"] * k + 1.0 * k, 0)
            eng[-1] = glass.difference(eng_cut)
        lt = Polygon(T(c["light"])).buffer(0.3 * k)
        eng.append(lt)
        eng.append(Polygon(T([(0.4, -15.6), (2.4, -15.8), (2.4, -13), (0.4, -13)])))   # Heckleuchte
        dr = c["door"]
        for dx in dr:
            score.append(LineString(T([(dx, -21.5 if kind != "hatch" else -22.4), (dx + 0.6, -7.2)])))
        score.append(LineString(T([(c["wheels"][0][0] + c["wheels"][0][1] * 1.2, -6.4),
                                   (c["wheels"][1][0] - c["wheels"][1][1] * 1.2, -6.4)])))
        if c.get("intake"):
            eng.append(Polygon(T([(25, -15.5), (35, -16.5), (36.5, -9.5), (30, -9)])))
        if c.get("popup"):
            score.append(LineString(T([(89, -15.2), (95, -13.6)])))
        # Spiegel
        mx = (c["glass"][-2][0] if kind != "sedan" else 66) * k
        g = unary_union([g, ellipse(mx + 1.2 * k, -20.2 * k, 1.8 * k, 1.1 * k)])
    g = g.difference(unary_union(holes)) if holes else g
    eng = unary_union(eng).intersection(g)
    out = [g, eng, score]
    if facing == "left":
        out = [affinity.scale(o, -1, 1, origin=(L / 2, 0)) if not isinstance(o, list)
               else [affinity.scale(s, -1, 1, origin=(L / 2, 0)) for s in o] for o in out]
    return [affinity.translate(o, x, y) if not isinstance(o, list)
            else [affinity.translate(s, x, y) for s in o] for o in out]


def car_height(kind, L=100.0):
    return -min(p[1] for p in CARS[kind]["body"]) * L / 100


# ---------------------------------------------------------------- Uhr
def gauge_clock(labels, title, sub, red_from, font=SPORT, R=130.0, extra=None):
    """Instrumenten-Wanduhr: 12 Beschriftungen, Teilstriche, roter Bereich ab Stunde red_from."""
    g = circle(0, 0, R, 128).difference(circle(0, 0, 4.0))    # Ø 8 mm fuer das Quarzwerk
    eng = [circle(0, 0, R - 3.5, 128).difference(circle(0, 0, R - 6.5, 128))]
    for i in range(60):
        a = -90 + 6 * i
        if i % 5 == 0:
            eng.append(stroke([polar(R - 26, a), polar(R - 10, a)], 3.2))
        else:
            eng.append(stroke([polar(R - 18, a), polar(R - 10, a)], 1.2))
    for i in range(1, 13):
        if i >= red_from:
            eng.append(arc_band(R - 30, R - 26, -90 + 30 * (i - 1) + 2, -90 + 30 * i - 2))
    eng.append(arc_band(R - 26, R - 10, -90 + 30 * (red_from - 1), 270).difference(
        unary_union([stroke([polar(R - 27, -90 + 6 * i), polar(R - 9, -90 + 6 * i)], 3.2 + 1.6)
                     for i in range(60)])))
    for i, lab in enumerate(labels):
        a = -90 + 30 * (i + 1)
        x, y = polar(R - 45, a)
        eng.append(ctext(lab, font, x, y, size=17 if len(lab) < 3 else 13, max_w=30))
    eng.append(ctext(title, font, 0, 50, size=14, max_w=88))
    eng.append(ctext(sub, SANS, 0, 64, size=5.6, max_w=84))
    if extra is not None:
        eng.append(extra)
    eng.append(circle(0, 0, 13).exterior.buffer(0.6))
    return single(Part("Wanduhr", g, unary_union(eng), [circle(0, 0, R - 1.6, 128).exterior]))


# ---------------------------------------------------------------- 3D-Steckauto
def steck_car(kind, L=180.0, track=64.0, name="Steckauto", eng_extra=None):
    """Seitenteil mit zwei Schlitzen von unten + zwei Achsteile (Front-/Heckansicht) mit Schlitz von oben."""
    c = CARS[kind]
    k = L / 100
    g, e, s = car(kind, L, 0, 0, wheels="cut")
    parts = []
    slots = []
    axle_parts = []
    for wx, wr in c["wheels"]:
        x = wx * k
        r = wr * k
        # Schlitz von unten bis zur Radmitte (Rad bleibt mit der Karosserie verbunden: Schlitz geht durch die Felgenmitte)
        slots.append(box(x - SLOT / 2, -r - 0.5, x + SLOT / 2, 1))
    side = g.difference(unary_union(slots))
    e = e.difference(unary_union(slots).buffer(1.2))
    if eng_extra is not None:
        e = unary_union([e, eng_extra])
    parts.append(Part(f"{name} Seitenteil", side, e, s))
    for i, (wx, wr) in enumerate(c["wheels"]):
        r = wr * k
        top = LineString([(wx * k, 0.5), (wx * k, -200)]).intersection(side).bounds[1]
        h = min(r * 2 + 4, -top - 4)   # Achsteil bleibt 4 mm unter der Karosserie-Oberkante
        w = track + 2 * 9
        body = rrect(-w / 2 + 9, -h, w / 2 - 9, -3, 3)
        tires = [rrect(-w / 2, -2 * r, -w / 2 + 12, 0, 3), rrect(w / 2 - 12, -2 * r, w / 2, 0, 3)]
        ax = unary_union([body] + tires)
        ax = round_concave(ax, 1.5).difference(box(-SLOT / 2, -h - 1, SLOT / 2, -h + (h - r - 0.5)))
        eng_ax = unary_union([rrect(-w / 2 + 2, -2 * r + 2, -w / 2 + 10, -2, 2),
                              rrect(w / 2 - 10, -2 * r + 2, w / 2 - 2, -2, 2)])
        sc = [LineString([(-w / 2 + 14, -r), (-SLOT / 2 - 3, -r)]),
              LineString([(SLOT / 2 + 3, -r), (w / 2 - 14, -r)])]
        axle_parts.append(Part(f"{name} Achse {'hinten' if i == 0 else 'vorn'}", ax, eng_ax, sc))
    return [single(p) for p in parts + axle_parts]


# ---------------------------------------------------------------- Kiste/Laterne mit Fingerzinken
def finger_box(W, D, H, faces, bottom_hole=None, bottom_eng=None, name="Kiste"):
    """Offene Kiste aus 5 Teilen. faces: dict front/back/left/right -> (Loecher, Gravur, Linien)."""
    T = MAT

    def wall(width, side):
        g = box(0, 0, width, H)
        cuts = []
        for i, (a, b) in enumerate(_fingers(H, 5)):
            gap = (i % 2 == 1) if not side else (i % 2 == 0)
            if gap:
                cuts += [box(0, a, T, b), box(width - T, a, width, b)]
        for i, (a, b) in enumerate(_fingers(width, 5)):
            if i % 2 == 0:
                cuts.append(box(a, H - T, b, H))
        return g.difference(unary_union(cuts))

    parts = []
    for key, label, width, side in [("front", "Vorderwand", W, False), ("back", "Rueckwand", W, False),
                                    ("left", "Seitenwand links", D, True),
                                    ("right", "Seitenwand rechts", D, True)]:
        hole, eng, sc = faces.get(key, (None, None, []))
        g = wall(width, side)
        if hole is not None:
            g = g.difference(hole)
        parts.append(Part(f"{name} {label}", g, eng, sc or []))
    g = box(0, 0, W, D)
    cuts = []
    for i, (a, b) in enumerate(_fingers(W, 5)):
        if i % 2 == 1:
            cuts += [box(a, 0, b, T), box(a, D - T, b, D)]
    for i, (a, b) in enumerate(_fingers(D, 5)):
        if i % 2 == 1:
            cuts += [box(0, a, T, b), box(W - T, a, W, b)]
    g = g.difference(unary_union(cuts))
    if bottom_hole is not None:
        g = g.difference(bottom_hole)
    parts.append(Part(f"{name} Boden", g, bottom_eng))
    return [single(p) for p in parts]


def scene_window(W, H, scene, frame=(13, 13, 13, 18 + MAT), arch=True):
    """Fensterausschnitt mit Silhouetten-Szene (Szene = Flaeche, die stehen bleibt)."""
    m, top, side, bot = frame
    wx0, wx1 = side, W - side
    if arch:
        rad = (wx1 - wx0) / 2
        win = unary_union([circle(W / 2, top + rad, rad, 64), box(wx0, top + rad, wx1, H - bot)])
    else:
        win = rrect(wx0, top, wx1, H - bot, 3)
    solid = scene.intersection(win.buffer(2))
    hole = round_concave(win.difference(solid), 0.5)
    hole = unary_union([p for p in polys(hole) if p.area > 2.0])
    return hole
