"""Wiederverwendbare Produkt-Vorlagen fuer die Geschenk- und Themenserien (mm, y nach unten)."""
import math

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from autos import finger_box, scene_window, single
from designs import DECO, MAT, SCRIPT, SLOT
from lasergeo import Part, circle, polar, polys, round_concave, round_convex, star, stroke, text
from motive import engraved, heart_poly, icon, ring, rr

SANS = "Inter-Bold.otf"
SPORT = "InterDisplay-BlackItalic.otf"


# ---------------------------------------------------------------- Text-Helfer
def T(s, font, cx, cy, size=10, max_w=None, max_h=None):
    """Text zentriert, optional auf Breite/Hoehe begrenzt."""
    g = text(s, font, size=size, cx=cx, cy=cy)
    b = g.bounds
    k = 1.0
    if max_w and b[2] - b[0] > max_w:
        k = max_w / (b[2] - b[0])
    if max_h and (b[3] - b[1]) * k > max_h:
        k = max_h / (b[3] - b[1])
    if k != 1.0:
        g = affinity.scale(g, k, k, origin=(cx, cy))
    return g


def texts(items):
    """items: (text, font, cx, cy, size[, max_w])"""
    out = []
    for it in items:
        s, f, cx, cy, size = it[:5]
        mw = it[5] if len(it) > 5 else None
        out.append(T(s, f, cx, cy, size, mw))
    return unary_union(out)


def icons(items):
    """items: (name, cx, cy, h[, rot])"""
    return unary_union([engraved(*it) for it in items])


def keep_connected(g, anchor):
    return unary_union([q for q in polys(g) if q.intersects(anchor)])


# ---------------------------------------------------------------- Umrissformen
def outline(shape, W, H, r=8):
    if shape == "rect":
        return rr(0, 0, W, H, r)
    if shape == "arch":
        R = min(W / 2, H * 0.32)                       # flacher Bogen oben
        top = affinity.translate(affinity.scale(circle(0, 0, 1, 96), W / 2, R, origin=(0, 0)), W / 2, R)
        return unary_union([box(0, R, W, H - r), rr(0, R, W, H, r), top])
    if shape == "heart":
        h = heart_poly(0, 0, 1.0)
        b = h.bounds
        h = affinity.scale(h, W / (b[2] - b[0]), H / (b[3] - b[1]), origin=(0, 0))
        b = h.bounds
        return affinity.translate(h, -b[0], -b[1])
    if shape == "oval":
        return affinity.translate(affinity.scale(circle(0, 0, 1, 96), W / 2, H / 2, origin=(0, 0)), W / 2, H / 2)
    if shape == "banner":
        n = 6
        return Polygon([(0, 0), (W, 0), (W - n * 2, H / 2), (W, H), (0, H), (n * 2, H / 2)])
    if shape == "cloud":
        g = [rr(10, H * 0.35, W - 10, H, 10)]
        for i, (fx, fr) in enumerate([(0.2, 0.28), (0.42, 0.36), (0.66, 0.3), (0.84, 0.22)]):
            g.append(circle(W * fx, H * 0.38, H * fr))
        return unary_union(g).intersection(box(0, 0, W, H))
    raise ValueError(shape)


# ====================================================================== Wandschild
def plaque(name, W, H, shape="rect", txt=(), ico=(), holes=2, border=True, extra_eng=None, extra_score=()):
    g = outline(shape, W, H)
    if isinstance(holes, (list, tuple)):
        g = g.difference(unary_union([circle(x, y, 2.6) for x, y in holes]))
    elif holes == 2:
        g = g.difference(unary_union([circle(12, 12, 2.6), circle(W - 12, 12, 2.6)]))
    elif holes == 1:
        g = g.difference(circle(W / 2, 10, 2.6))
    eng = [texts(txt), icons(ico)]
    if extra_eng is not None:
        eng.append(extra_eng)
    sc = list(extra_score)
    if border:
        sc.append(outline(shape, W, H).buffer(-5).exterior)
    return single(Part(name, g, unary_union(eng), sc))


# ====================================================================== Wanduhr
def clock(name, R=130.0, numbers="arabic", font=DECO, labels=None, ico=(), txt=(), ticks=True, rim_icons=None):
    g = circle(0, 0, R, 128).difference(circle(0, 0, 4.0))
    eng = []
    roman = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    for i in range(12):
        a = -90 + 30 * i
        if labels and labels[i]:
            lab = labels[i]
            x, y = polar(R - 30, a)
            eng.append(T(lab, font, x, y, 13, max_w=34, max_h=14))
        elif rim_icons and rim_icons.get(i):
            x, y = polar(R - 30, a)
            eng.append(engraved(rim_icons[i], x, y, 24))
        elif numbers == "arabic":
            x, y = polar(R - 30, a)
            eng.append(T(str(12 if i == 0 else i), font, x, y, 22, max_h=17))
        elif numbers == "roman":
            x, y = polar(R - 30, a)
            eng.append(T(roman[i], font, x, y, 16, max_h=14))
        if ticks:
            for k in range(1, 5):
                eng.append(circle(*polar(R - 11, a + 6 * k), 1.0))
            eng.append(circle(*polar(R - 11, a), 2.4))
    eng += [texts(txt), icons(ico)]
    sc = [circle(0, 0, R - 4, 128).exterior]
    return single(Part(name, g, unary_union(eng), sc))


# ====================================================================== Untersetzer
def coaster(title, sub, ic, font=DECO, R=47.5, frame="ring"):
    g = circle(0, 0, R, 96)
    eng = unary_union([engraved(ic, 0, -11, 36),
                       T(title, font, 0, 20, 11, max_w=64, max_h=11),
                       T(sub, SANS, 0, 31.5, 4.4, max_w=46)])
    sc = [circle(0, 0, R - 4, 96).exterior]
    if frame == "double":
        sc.append(circle(0, 0, R - 6, 96).exterior)
    return single(Part(f"Untersetzer {title}", g, eng, sc))


# ====================================================================== Anhaenger
def tag_icon(name, ic, h=40, txt=None, font=DECO):
    """Anhaenger in Form des Motivs (Rand 2 mm) mit Oese oben."""
    s, d = icon(ic, 0, 0, h)
    body = round_convex(s.buffer(2.2, join_style="round"), 0.5)
    b = body.bounds
    top = (0, b[1] - 1.5)
    # Oese am hoechsten Punkt nahe der Mitte
    eye = circle(top[0], top[1] + 1.5, 4.8)
    g = round_concave(unary_union([body, eye]), 1.0).difference(circle(top[0], top[1] + 1.5, 2.3))
    eng = s.difference(d) if not d.is_empty else s
    eng = eng.difference(circle(top[0], top[1] + 1.5, 5.6))
    return single(Part(name, g, eng, [], hang=(top[0], top[1] + 1.5)))


def tag_heart(name, line1, line2=None, W=46, font=SCRIPT, ic=None):
    H = W * 0.92
    g = outline("heart", W, H)
    g = affinity.translate(g, -W / 2, -H / 2)
    hy = -H / 2 + H * 0.22
    g = g.difference(circle(0, hy, 2.3))
    eng = []
    if ic:
        eng.append(engraved(ic, 0, -1, W * 0.3))
        eng.append(T(line1, font, 0, H * 0.18, 9, max_w=W * 0.55, max_h=W * 0.16))
    elif line2:
        eng.append(T(line1, font, 0, -1, 9, max_w=W * 0.62, max_h=W * 0.2))
        eng.append(T(line2, SANS, 0, H * 0.16, 4.2, max_w=W * 0.46))
    else:
        eng.append(T(line1, font, 0, 1, 9, max_w=W * 0.66, max_h=W * 0.26))
    sc = [g.buffer(-2.6).exterior]
    return single(Part(name, g, unary_union(eng), sc, hang=(0, hy)))


def tag_rect(name, ic, line1, line2=None, W=66, H=30, font=DECO):
    body = rr(-W / 2, -H / 2, W / 2, H / 2, 4)
    tab = unary_union([circle(-W / 2 - 3, 0, 6.5), box(-W / 2 - 3, -6.5, -W / 2 + 4, 6.5)])
    g = round_concave(unary_union([body, tab]), 1.2).difference(circle(-W / 2 - 4, 0, 2.5))
    tx = 8
    eng = [engraved(ic, -W / 2 + 12, 0, H - 10)]
    if line2:
        eng += [T(line1, font, tx, -3.5, 9, max_w=W - 30, max_h=10), T(line2, SANS, tx, 7.5, 3.8, max_w=W - 30)]
    else:
        eng.append(T(line1, font, tx, 0, 10, max_w=W - 30, max_h=13))
    return single(Part(name, g, unary_union(eng), [rr(-W / 2 + 2.5, -H / 2 + 2.5, W / 2 - 2.5, H / 2 - 2.5, 2.5).exterior],
                       hang=(-W / 2 - 4, 0)))


def tag_round(name, ic, line1, R=22, font=DECO):
    g = unary_union([circle(0, 0, R, 64), circle(0, -R - 2, 5)]).difference(circle(0, -R - 2, 2.3))
    g = round_concave(g, 1.0)
    eng = unary_union([engraved(ic, 0, -4.5, R * 0.95), T(line1, font, 0, R * 0.55, 6, max_w=R * 1.4, max_h=6.5)])
    return single(Part(name, g, eng, [circle(0, 0, R - 2.4, 64).exterior], hang=(0, -R - 2)))


# ====================================================================== Bilderrahmen 10x15
def photo_frame(name, title, sub=None, ico=(), font=SCRIPT, photo=(100, 150)):
    pw, ph = photo
    W, H = pw + 40, ph + 62
    win = rr(20, 20, 20 + pw - 6, 20 + ph - 6, 2)       # 3 mm Auflage pro Seite
    win = affinity.translate(win, 3, 3)
    front = rr(0, 0, W, H, 8).difference(win)
    ty = 20 + ph + 20
    eng = [T(title, font, W / 2, ty, 16, max_w=W - 30, max_h=18)]
    if sub:
        eng.append(T(sub, SANS, W / 2, ty + 15, 4.6, max_w=W - 50))
    eng.append(icons(ico))
    sc = [rr(5, 5, W - 5, H - 5, 5).exterior, win.buffer(3).exterior]
    p_front = single(Part(f"{name} Front", front, unary_union(eng), sc))
    # Rueckwand mit Schlitz fuer den Aufsteller und Griffmulde
    SL = 26.0
    back = rr(0, 0, W, H, 8).difference(box(W / 2 - SL / 2, H * 0.42, W / 2 + SL / 2, H * 0.42 + SLOT))
    back = back.difference(circle(W / 2, H - 14, 5))
    p_back = single(Part(f"{name} Rueckwand", back, T("Foto 10 x 15", SANS, W / 2, 24, 5)))
    # Aufsteller: Zunge passt in den Schlitz, Bein spreizt nach hinten
    leg = Polygon([(-SL / 2 + 0.2, 0), (SL / 2 - 0.2, 0), (SL / 2 - 0.2, 8), (17, 14), (13, H * 0.5), (-13, H * 0.5),
                   (-17, 14), (-SL / 2 + 0.2, 8)])
    leg = round_convex(leg, 1.5)
    p_leg = single(Part(f"{name} Aufsteller", leg, None))
    return [p_front, p_back, p_leg]


# ====================================================================== Medaille
def medal(name, top, ic, bottom, R=36.0, font=DECO):
    disc = circle(0, 0, R, 96)
    lug = rr(-18, -R - 12, 18, -R + 6, 5)
    g = round_concave(unary_union([disc, lug]), 2).difference(rr(-13, -R - 7.5, 13, -R - 3.5, 1.5))
    rays = unary_union([Polygon([polar(R - 3, a - 4), polar(R - 7.5, a), polar(R - 3, a + 4)])
                        for a in range(0, 360, 15)])
    eng = unary_union([rays, T(top, SANS, 0, -R * 0.55, 5.2, max_w=R * 1.2), engraved(ic, 0, -2, R * 0.66),
                       T(bottom, font, 0, R * 0.52, 9, max_w=R * 1.3, max_h=9)])
    return single(Part(name, g, eng, [circle(0, 0, R - 9, 96).exterior], hang=(0, -R - 5.5)))


# ====================================================================== 3D-Pokal (Kreuzsteckung)
def trophy3d(name, line1, line2, font=DECO):
    H = 150.0
    prof = [(0, 0), (34, 0), (34, 8), (16, 12), (10, 22), (7, 48), (14, 56), (36, 70), (44, 110), (44, 128),
            (40, 132), (32, 128), (30, 112), (22, 100)]
    right = Polygon([(x, -y) for x, y in prof] + [(0, -100)])
    cup = unary_union([right, affinity.scale(right, -1, 1, origin=(0, 0))]).buffer(0)
    handles = unary_union([ring(46, -100, 10, 4), ring(-46, -100, 10, 4)]).difference(box(-44, -140, 44, 0))
    g = round_concave(round_convex(unary_union([cup, handles]), 1.0), 1.5)
    mid = -66
    a = g.difference(box(-SLOT / 2, -H, SLOT / 2, mid))               # Schlitz von oben
    b = g.difference(box(-SLOT / 2, mid, SLOT / 2, 1))                 # Schlitz von unten
    eng_a = unary_union([T(line1, font, -22, -108, 9, max_w=30), T(line2, SANS, 22, -108, 5, max_w=30),
                         engraved("stern", 0, -24, 10)]).difference(box(-SLOT / 2 - 3, -H, SLOT / 2 + 3, mid + 2))
    eng_b = unary_union([engraved("stern", -22, -110, 12), engraved("stern", 22, -110, 12)])
    sc = [LineString([(-30, -125), (30, -125)]).difference(box(-SLOT / 2 - 2, -H, SLOT / 2 + 2, 0))]
    return [single(Part(f"{name} A", a, eng_a, sc)), single(Part(f"{name} B", b, eng_b, sc))]


# ====================================================================== Steckfigur mit Beinen (z. B. Sparschwein)
def steck_figure(name, side, legs_x, leg_h, leg_w=56.0, eng=None, score=()):
    """side: Seitenprofil (Fuesse bei y=0); legs_x: x-Positionen der Beinpaare; leg_h: Beinhoehe."""
    slots = unary_union([box(x - SLOT / 2, -leg_h - 6, x + SLOT / 2, 1) for x in legs_x])
    s = side.difference(slots)
    e = eng.difference(slots.buffer(1.5)) if eng is not None else None
    parts = [single(Part(f"{name} Koerper", s, e, list(score)))]
    for i, x in enumerate(legs_x):
        top = LineString([(x, 0.5), (x, -300)]).intersection(side).bounds[1]
        hh = min(-top - 4, leg_h + 14)
        cross = unary_union([rr(-leg_w / 2, -hh, leg_w / 2, -leg_h + 2, 4),
                             rr(-leg_w / 2, -leg_h - 2, -leg_w / 2 + 10, 0, 3),
                             rr(leg_w / 2 - 10, -leg_h - 2, leg_w / 2, 0, 3)])
        cross = round_concave(cross, 1.5).difference(box(-SLOT / 2, -hh - 1, SLOT / 2, -leg_h - 6))
        parts.append(single(Part(f"{name} Beine {i + 1}", cross, None)))
    return parts


# ====================================================================== Staender (Handy / Tablet / Rezepte)
def stand(name, A_W=84.0, A_LEN=116.0, NOTCH=38.0, eng_a=None, ang=68.0, scale=1.0, sc_a=()):
    a = math.radians(ang)
    d = (math.cos(a), -math.sin(a))
    s = scale
    P0 = (44.0 * s, 0.0)
    ga = rr(-A_W / 2, 0, A_W / 2, A_LEN, 6).difference(box(-SLOT / 2, A_LEN - NOTCH, SLOT / 2, A_LEN + 1))
    if eng_a is not None:
        eng_a = eng_a.difference(box(-SLOT / 2 - 4, A_LEN - NOTCH - 2, SLOT / 2 + 4, A_LEN))
    pa = Part(f"{name} Rueckwand", ga, eng_a, list(sc_a))
    top_len = 72.0 * s
    Q = (P0[0] + d[0] * top_len, P0[1] + d[1] * top_len)
    n = (math.sin(a), math.cos(a))
    w = 8 * s
    strip = Polygon([(P0[0] - n[0] * w, P0[1]), (Q[0] - n[0] * w, Q[1] - n[1] * w),
                     (Q[0] + n[0] * w, Q[1] + n[1] * w), (P0[0] + 14 * s, 0)])
    rear = Polygon([(Q[0], Q[1]), (118 * s, 0), (40 * s, 0)])
    base = box(22 * s, -6, 118 * s, 0)
    lip = box(22 * s, -14 * s, 29 * s, 0)
    gb = round_concave(round_convex(unary_union([strip, rear, base, lip]), 2.0), 2.0)
    over = top_len + 3
    sl_len = over - NOTCH
    S0 = (P0[0] + d[0] * (over - sl_len), P0[1] + d[1] * (over - sl_len))
    S1 = (P0[0] + d[0] * (over + 5), P0[1] + d[1] * (over + 5))
    gb = gb.difference(LineString([S0, S1]).buffer(SLOT / 2, cap_style="flat"))
    win = Polygon([(60 * s, -8), (100 * s, -8), (Q[0] + 10 * s, Q[1] + 22 * s)]).buffer(-1).buffer(1)
    gb = gb.difference(round_convex(win, 3))
    return [single(pa), single(Part(f"{name} Fuss", gb, None))]


# ====================================================================== Tischschild mit Fuss
def desk_sign(name, W, H, eng, sc=(), base_d=50.0):
    TAB, TX = 24.0, W / 2 - 30
    plate = unary_union([rr(-W / 2, -H, W / 2, 0, 6), box(-W / 2, -8, W / 2, 0)])
    plate = unary_union([plate] + [box(x - TAB / 2, -0.01, x + TAB / 2, MAT) for x in (-TX, TX)])
    p1 = single(Part(f"{name} Schild", plate, eng, [rr(-W / 2 + 4, -H + 4, W / 2 - 4, -4, 3).exterior] + list(sc)))
    base = rr(-W / 2 - 4, -base_d / 2, W / 2 + 4, base_d / 2, 6)
    base = base.difference(unary_union([box(x - TAB / 2 - 0.1, -SLOT / 2, x + TAB / 2 + 0.1, SLOT / 2) for x in (-TX, TX)]))
    p2 = single(Part(f"{name} Fuss", base, None, [rr(-W / 2, -base_d / 2 + 4, W / 2, base_d / 2 - 4, 4).exterior]))
    return [p1, p2]


# ====================================================================== Visitenkartenhalter
def card_holder(name, eng_back, eng_front=None):
    W = 96.0
    TAB = 18.0
    back = unary_union([rr(-W / 2, -62, W / 2, 0, 5), box(-W / 2, -6, W / 2, 0)] +
                       [box(x - TAB / 2, -0.01, x + TAB / 2, MAT) for x in (-26, 26)])
    front = unary_union([rr(-W / 2, -22, W / 2, 0, 4), box(-W / 2, -5, W / 2, 0)] +
                        [box(x - TAB / 2, -0.01, x + TAB / 2, MAT) for x in (-26, 26)])
    base = rr(-W / 2 - 4, -16, W / 2 + 4, 24, 5)
    slots = unary_union([box(x - TAB / 2 - 0.1, y - SLOT / 2, x + TAB / 2 + 0.1, y + SLOT / 2)
                         for x in (-26, 26) for y in (-8, 16)])
    return [single(Part(f"{name} Rueckwand", back, eng_back)),
            single(Part(f"{name} Front", front, eng_front)),
            single(Part(f"{name} Boden", base.difference(slots), None))]


# ====================================================================== Kiste mit Deckel / Trennwaenden
def box_set(name, W, D, H, faces, lid=None, lid_eng=None, dividers=(), bottom_eng=None):
    parts = finger_box(W, D, H, faces, name=name, bottom_eng=bottom_eng)
    if lid:
        top = rr(0, 0, W + 2, D + 2, 3)
        inner = rr(MAT + 0.3, MAT + 0.3, W + 2 - MAT - 0.3 - 2, D + 2 - MAT - 0.3 - 2, 1)
        inner = affinity.translate(inner, 1, 1)
        if lid == "slot":
            slot = rr((W + 2) / 2 - 22, (D + 2) / 2 - 2.2, (W + 2) / 2 + 22, (D + 2) / 2 + 2.2, 1.5)
            top = top.difference(slot)
            inner = inner.difference(slot)
            if lid_eng is not None:
                lid_eng = lid_eng.difference(slot.buffer(2))
        elif lid == "knob":
            top = top.difference(circle((W + 2) / 2, (D + 2) / 2, 6))
        parts.append(single(Part(f"{name} Deckel", top, lid_eng, [rr(3, 3, W - 1, D - 1, 2).exterior])))
        parts.append(single(Part(f"{name} Deckel innen", inner, None)))
    for i, lab in enumerate(dividers):
        dw = W - 2 * MAT - 0.4
        dh = H - 8
        g = unary_union([rr(0, 0, dw, dh, 2), rr(dw / 2 - 22, -12, dw / 2 + 22, 4, 4)])
        e = T(lab, SANS, dw / 2, -4.6, 6, max_w=40)
        parts.append(single(Part(f"{name} Trennwand {lab}", g, e)))
    return parts


# ====================================================================== Laterne mit Szenen
def lantern(name, front, back, side, t_front, t_back, t_side, bottom_txt=None, font=SCRIPT, size=(90.0, 90.0, 110.0)):
    LX, LY, LZ = size
    stars_g = unary_union([round_convex(star(sx, 9, 3.6, 1.6), 0.3) for sx in (7, LX - 7)])
    tf = lambda s, w: T(s, font, w / 2, LZ - 10.5, 11, max_w=w - 28, max_h=12)
    faces = {"front": (unary_union([scene_window(LX, LZ, front), stars_g]), tf(t_front, LX), []),
             "back": (unary_union([scene_window(LX, LZ, back), stars_g]), tf(t_back, LX), []),
             "left": (scene_window(LY, LZ, side), tf(t_side, LY), []),
             "right": (scene_window(LY, LZ, side), tf(t_side, LY), [])}
    return finger_box(LX, LY, LZ, faces, bottom_hole=circle(LX / 2, LY / 2, 11), name=name,
                      bottom_eng=T(bottom_txt, font, LX / 2, LY / 2 + 24, 10, max_w=60) if bottom_txt else None)


GROUND = 110.0 - 18 - MAT


def scene(items, ground=GROUND, W=90.0, balloons=()):
    """Silhouetten auf einem Boden; items: (icon, cx, h); balloons: (icon, cx, cy, h) an Schnueren."""
    g = [box(0, ground - 5, W, 110)]
    det = []
    for ic, cx, h in items:
        s, d = icon(ic, cx, 0, h)
        b = s.bounds
        g.append(affinity.translate(s, 0, ground - 3 - b[3]))
        if not d.is_empty:
            det.append(affinity.translate(d, 0, ground - 3 - b[3]).intersection(
                affinity.translate(s, 0, ground - 3 - b[3]).buffer(-1.2)))
    for ic, cx, cy, h in balloons:
        s, _ = icon(ic, cx, cy, h)
        g.append(s)
        g.append(LineString([(cx, cy), (cx, s.bounds[3]), (cx + 3, (s.bounds[3] + ground) / 2), (cx, ground)]).buffer(0.7))
    g = keep_connected(unary_union(g), box(0, ground - 5, W, 110))     # lose Kleinteile (Tropfen o. ae.) weglassen
    # Fenster/Tueren der Motive werden zu Lichtoeffnungen (nur wenn sie ganz innen liegen)
    holes = [q for q in polys(unary_union(det)) if q.area > 1.5] if det else []
    return g.difference(unary_union(holes)) if holes else g


# ====================================================================== Lesezeichen
def bookmark(name, scene_geom, label, font=SCRIPT, W=40.0, H=160.0):
    outer = round_convex(Polygon([(0, 8), (W / 2, 0), (W, 8), (W, H), (0, H)]), 2.0)
    window = rr(5, 14, W - 5, 76, 3)
    solid = scene_geom.intersection(window.buffer(1.5))
    g = round_concave(unary_union([outer.difference(window), solid]), 0.5).difference(circle(W / 2, 7.2, 2.4))
    eng = affinity.rotate(T(label, font, W / 2, 118, 16, max_w=70, max_h=18), -90, origin=(W / 2, 118))
    sc = [LineString([(6, 84), (W - 6, 84)]), LineString([(6, H - 6), (W - 6, H - 6)])]
    return single(Part(f"Lesezeichen {label}", g, eng, sc, hang=(W / 2, 7.2)))


def bm_scene(items, balloons=(), W=40.0, ground=76.0):
    return scene(items, ground=ground + 1.5, W=W, balloons=balloons)


# ====================================================================== Gartenstecker
def garden_stake(name, line1, ic=None, W=90.0, H=55.0, stake=120.0, font=DECO, shape="cloud"):
    sign = outline(shape, W, H) if shape != "rect" else rr(0, 0, W, H, 8)
    spike = Polygon([(W / 2 - 6, H - 2), (W / 2 + 6, H - 2), (W / 2 + 6, H + stake - 14), (W / 2, H + stake),
                     (W / 2 - 6, H + stake - 14)])
    g = round_concave(unary_union([sign, spike]), 2.0)
    b = sign.bounds
    cy = (b[1] + b[3]) / 2 + (6 if shape == "cloud" else 0)
    eng = []
    if ic:
        eng.append(engraved(ic, W * 0.18, cy, H * 0.4))
        eng.append(T(line1, font, W * 0.62, cy, 12, max_w=W * 0.5, max_h=H * 0.34))
    else:
        eng.append(T(line1, font, W / 2, cy, 12, max_w=W * 0.8, max_h=H * 0.45))
    return single(Part(name, g, unary_union(eng), [sign.buffer(-3.2).exterior], hang=None))


# ====================================================================== Herz-Puzzle
def heart_puzzle(name, names, title, W=220.0, font=SCRIPT):
    H = W * 0.92
    heart = affinity.translate(outline("heart", W, H), -W / 2, -H / 2)
    b = heart.bounds

    def edge(p, q, flip):
        (x0, y0), (x1, y1) = p, q
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = -uy * flip, ux * flip
        pts = []
        for t in [i / 40 for i in range(41)]:
            s = t * L
            off = 0
            m = L / 2
            if abs(s - m) < 9:
                u = (s - m) / 9
                off = 7 * math.cos(u * math.pi / 2) ** 2 * (1 + 0.3 * math.cos(u * math.pi))
            pts.append((x0 + ux * s + nx * off, y0 + uy * s + ny * off))
        return pts

    cuts = []
    cols = [b[0] + (b[2] - b[0]) * f for f in (1 / 3, 2 / 3)]
    rows = [b[1] + (b[3] - b[1]) * f for f in (0.42, 0.72)]
    for i, x in enumerate(cols):
        for j, (ya, yb) in enumerate([(b[1] - 5, rows[0]), (rows[0], rows[1]), (rows[1], b[3] + 5)]):
            cuts.append(LineString(edge((x, ya), (x, yb), 1 if (i + j) % 2 else -1)))
    for j, y in enumerate(rows):
        for i, (xa, xb) in enumerate([(b[0] - 5, cols[0]), (cols[0], cols[1]), (cols[1], b[2] + 5)]):
            cuts.append(LineString(edge((xa, y), (xb, y), 1 if (i + j) % 2 else -1)))
    pieces = polys(heart.difference(unary_union(cuts).buffer(0.08)))
    pieces = sorted([p for p in pieces if p.area > 50], key=lambda p: (round(p.centroid.y / 30), p.centroid.x))
    out = []
    for k, p in enumerate(pieces):
        c = p.representative_point()
        lab = names[k] if k < len(names) else ""
        eng = None
        if lab:
            rad = min(26, math.sqrt(p.area) * 0.5)
            eng = T(lab, font, c.x, c.y, 10, max_w=rad * 2.2, max_h=12).intersection(p.buffer(-3))
        out.append(single(Part(f"{name} Teil {k + 1}", p, eng)))
    return out


# ====================================================================== Stammbaum
def family_tree(name, title, names, W=300.0, H=260.0, font=SCRIPT):
    cx, cy = W / 2, 132.0
    trunk = Polygon([(cx - 16, H - 40), (cx + 16, H - 40), (cx + 9, cy + 10), (cx - 9, cy + 10)])
    tips = [polar(112, a, cx, cy) for a in (-168, -143, -118, -90, -62, -37, -12)] + \
           [polar(62, a, cx, cy) for a in (-155, -120, -90, -60, -25)]
    branches = [stroke([(cx, cy + 14), t], 6 if i < 7 else 7) for i, t in enumerate(tips)]
    leaves = [heart_poly(x, y, 1.55) for x, y in tips]
    leaf_pos = tips
    base_plate = rr(20, H - 44, W - 20, H, 8)
    g = round_concave(unary_union([trunk, base_plate] + branches + leaves), 2.0)
    g = g.difference(unary_union([circle(34, H - 22, 2.6), circle(W - 34, H - 22, 2.6)]))
    eng = [T(title, font, W / 2, H - 22, 18, max_w=W - 110, max_h=20)]
    for (x, y), nm in zip(leaf_pos, names):
        eng.append(T(nm, font, x, y - 1, 10, max_w=22, max_h=9))
    sc = [h.buffer(-1.8).exterior for h in leaves]
    return [single(Part(name, g, unary_union(eng), sc))]


# ====================================================================== Holzkarte (Schablonenschrift)
def wood_card(name, cut_text, sub, ico=(), W=148.0, H=105.0, font=SCRIPT):
    g = rr(0, 0, W, H, 6)
    word = T(cut_text, font, W / 2, H * 0.44, 30, max_w=W - 30, max_h=34)
    # Schrift wird ausgeschnitten; Innenraeume (Punzen) fallen heraus und bleiben als Loch
    hole = unary_union([Polygon(q.exterior) for q in polys(word)])
    g = g.difference(hole)
    eng = unary_union([T(sub, SANS, W / 2, H - 17, 5, max_w=W - 40), icons(ico)])
    return [single(Part(name, g, eng, [rr(5, 5, W - 5, H - 5, 3).exterior]))]


# ====================================================================== Muehle-Spiel
def muehle(name, title, S=240.0, stones=9, mark_a="herz", mark_b="stern"):
    g = rr(0, 0, S, S, 10)
    c = S / 2
    eng, holes = [], []
    pts = []
    for k, r in enumerate((0.40, 0.27, 0.14)):
        d = S * r
        eng.append(box(c - d, c - d, c + d, c + d).exterior.buffer(1.0))
        for dx in (-d, 0, d):
            for dy in (-d, 0, d):
                if dx or dy:
                    pts.append((c + dx, c + dy))
    for sgn in (-1, 1):
        eng.append(stroke([(c + sgn * S * 0.14, c), (c + sgn * S * 0.40, c)], 2.0))
        eng.append(stroke([(c, c + sgn * S * 0.14), (c, c + sgn * S * 0.40)], 2.0))
    for x, y in pts:
        eng.append(circle(x, y, 5.5))
    eng.append(T(title, SCRIPT, c, S - 12, 12, max_w=S * 0.6, max_h=11))
    board = single(Part(name, g, unary_union(eng), [rr(5, 5, S - 5, S - 5, 6).exterior]))
    out = [board]
    for i in range(2 * stones):
        st = circle(0, 0, 11, 48)
        e = engraved(mark_a if i < stones else mark_b, 0, 0, 12)
        out.append(single(Part(f"Spielstein {i + 1}", st, e, [circle(0, 0, 9, 48).exterior])))
    return out


# ====================================================================== 52-Wochen-Spar-Challenge
def challenge52(name, title="52-Wochen-Spar-Challenge", W=300.0, H=215.0):
    g = rr(0, 0, W, H, 8).difference(unary_union([circle(14, 10, 2.6), circle(W - 14, 10, 2.6)]))
    eng = [T(title, DECO, W / 2, 22, 15, max_w=W - 60)]
    sc = [rr(6, 6, W - 6, H - 6, 4).exterior]
    cw, ch = 21.0, 30.0
    x0, y0 = (W - 13 * cw) / 2, 40
    for i in range(52):
        r, cc = divmod(i, 13)
        x, y = x0 + cc * cw, y0 + r * (ch + 6)
        sc.append(rr(x + 1, y, x + cw - 1, y + ch, 2).exterior)
        eng.append(T(f"{i + 1}", SANS, x + cw / 2, y + 7, 4, max_w=cw - 6))
        eng.append(T(f"{i + 1} €", SANS, x + cw / 2, y + ch - 6, 4.2, max_w=cw - 4))
        sc.append(circle(x + cw / 2, y + ch / 2 + 1, 4.2).exterior)
    eng.append(T("Jede Woche den Betrag sparen und das Feld abhaken · Summe nach einem Jahr: 1.378 €", SANS,
                 W / 2, H - 14, 5, max_w=W - 40))
    eng.append(engraved("sparschwein", 30, 22, 18))
    eng.append(engraved("muenze", W - 30, 22, 16))
    return [single(Part(name, g, unary_union(eng), sc))]


# ====================================================================== Geldbaum
def money_tree(name, title, H=200.0, W=170.0):
    trunk = Polygon([(-10, 0), (10, 0), (6, -102), (-6, -102)])
    br = []
    slits = []
    tips = []
    for ang, L, y in [(-150, 62, -78), (-125, 70, -92), (-100, 60, -100), (-80, 60, -100), (-55, 70, -92),
                      (-30, 62, -78), (-140, 40, -60), (-40, 40, -60)]:
        base = (0, y)
        tip = polar(L, ang, *base)
        br.append(stroke([base, tip], 6))
        tips.append(tip)
    crown = unary_union([circle(x, y, 13) for x, y in tips])
    stand_ = rr(-W / 2 + 25, -6, W / 2 - 25, 0, 2)
    g = round_concave(unary_union([trunk, crown, stand_] + br), 3.0)
    # Schlitze fuer gefaltete Geldscheine
    for x, y in tips:
        slits.append(rr(x - 1.0, y - 7, x + 1.0, y + 7, 1.0))
    g = g.difference(unary_union(slits))
    # Standfuss quer (Kreuzsteckung): Schlitz von unten im Baum, von oben im Fuss
    g = g.difference(box(-SLOT / 2, -20, SLOT / 2, 1))
    foot = round_concave(unary_union([rr(-50, -36, 50, 0, 6)]), 1).difference(box(-SLOT / 2, -37, SLOT / 2, -20))
    eng = T("€", SANS, 0, -40, 9)
    foot_eng = T(title, SCRIPT, 0, -12, 12, max_w=80, max_h=14)
    return [single(Part(f"{name} Baum", g, eng)), single(Part(f"{name} Fuss", foot, foot_eng))]


# ====================================================================== Flaschenanhaenger (Bier)
def bottle_tag(name, line1, line2, ic, ring_d=30.0, font=DECO):
    rr_ = ring_d / 2
    body = rr(-22, 18, 22, 92, 10)
    neck = box(-7, -4, 7, 22)
    ringg = circle(0, -rr_ - 4, rr_ + 7)
    g = round_concave(unary_union([body, neck, ringg]), 3).difference(circle(0, -rr_ - 4, rr_))
    eng = unary_union([engraved(ic, 0, 38, 22), T(line1, font, 0, 62, 10, max_w=38, max_h=11),
                       T(line2, SANS, 0, 76, 4.4, max_w=34)])
    return single(Part(name, g, eng, [rr(-19, 21, 19, 89, 8).exterior], hang=(0, -rr_ - 4)))


# ====================================================================== Brillenstaender
def glasses_stand(name, line1, font=DECO):
    prof = [(0, 0), (62, 0), (62, -8), (44, -14), (42, -40), (50, -52), (52, -58), (46, -62), (52, -66),
            (48, -70), (54, -76), (66, -86), (52, -96), (54, -108), (50, -124), (36, -138), (14, -140),
            (-4, -128), (-8, -100), (0, -70), (4, -40), (0, -20)]
    side = Polygon([(x - 30, y) for x, y in prof]).buffer(0)
    side = round_concave(round_convex(side, 1.5), 1.5)
    base = rr(-40, -26, 40, 26, 10)
    TAB = 20.0
    side = unary_union([side, box(-TAB / 2 - 10, -0.01, TAB / 2 - 10, MAT)])
    base = base.difference(box(-TAB / 2 - 10.1, -SLOT / 2, TAB / 2 - 9.9, SLOT / 2))
    eng_b = T(line1, font, 0, 15, 9, max_w=60)
    eng_s = None
    return [single(Part(f"{name} Kopf", side, eng_s)), single(Part(f"{name} Fuss", base, eng_b))]
