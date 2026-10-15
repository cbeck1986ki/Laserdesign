"""Serie 2: IT- & KI-Motive (einfarbig, Plotter).   Aufruf: python3 tools/serie2_it_ki.py"""
import math
import sys
from pathlib import Path

import numpy as np

from shapely import affinity
from shapely.geometry import Polygon, box

sys.path.insert(0, str(Path(__file__).parent))
from vinyl import (ALFA, ARCHIVO, BEBAS, KANIT, MONO, ORBITRON, OSWALD, PACIFICO, PIXEL, banner,  # noqa
                   bar, build, circle, circle_text_bottom, circle_text_top, frame, hline_rule, knock, laurel,
                   polyline, ring, rrect, sparkle, star, svgpath, text, union)

OUT = Path(__file__).resolve().parent.parent / "tshirt-plotter" / "serie2_it-ki"


# ------------------------------------------------------------------ 1  404 – Schlaf nicht gefunden
def d_404():
    big = text("404", KANIT, 118, 0, 0, tracking=0.02)
    # Glitch: Zahl in Streifen schneiden und einzelne Streifen seitlich versetzen
    bands = [(-125, -86, 0), (-86, -72, -12), (-72, -34, 0), (-34, -25, 10), (-25, 5, 0)]
    pieces = []
    for y0, y1, dx in bands:
        s = big.intersection(box(-200, y0 + 0.9, 200, y1 - 0.9))
        pieces.append(affinity.translate(s, dx, 0))
    scan = [box(-134, -80 - 2, -116, -80 + 2), box(116, -29.5 - 2, 134, -29.5 + 2)]
    head = union(pieces, scan)
    sub = text("SCHLAF NICHT GEFUNDEN", BEBAS, 26, 0, 40, tracking=0.06, width=250)
    rule = hline_rule(0, 56, 250, t=2.2, diamond=4.5)
    err = text("> kaffee.exe läuft seit 72 h", MONO, 10, 0, 82)
    return union(head, sub, rule, err)


# ------------------------------------------------------------------ 2  Certified Prompt Engineer (Abzeichen)
def d_prompt_badge():
    R = 128
    outer = ring(0, 0, R, 5.5)
    inner = ring(0, 0, 88, 2.6)
    top = circle_text_top("CERTIFIED PROMPT ENGINEER", OSWALD, 15.5, 0, 0, 98, tracking=0.07)
    bot = circle_text_bottom("SPRICHT FLIESSEND KI", OSWALD, 15.5, 0, 0, 114, tracking=0.09)
    stars = [star(-106, 0, 7.5), star(106, 0, 7.5)]
    # Sprechblase mit KI-Funkeln
    bub = rrect(-52, -58, 52, 14, 18).union(Polygon([(-30, 8), (-44, 34), (-8, 12)]))
    bub = knock(bub, sparkle(-6, -22, 27), sparkle(26, -40, 10), sparkle(28, -4, 7))
    since = text("SEIT 2023", BEBAS, 12, 0, 56, tracking=0.12)
    rules = [bar((-70, 50), (-40, 50), 2.2, "flat"), bar((40, 50), (70, 50), 2.2, "flat")]
    return union(outer, inner, top, bot, stars, bub, since, rules)


# ------------------------------------------------------------------ 3  STRG + ALT + Kaffee (Tastenkappen)
def cup_icon(cx, cy, s):
    """Kaffeetasse mit Dampf, Groesse s ~ Breite."""
    k = s / 40
    body = svgpath("M -16 -4 L 16 -4 L 13 18 C 12.5 21 10.5 23 7.5 23 L -7.5 23 C -10.5 23 -12.5 21 -13 18 Z")
    handle = ring(16.5, 6, 7.5, 3.6).difference(box(0, -20, 15.5, 30))
    steam = union([polyline([(x + 3 * math.sin(t / 3), -8 - t) for t in [i * 0.5 for i in range(25)]], 2.8)
                   for x in (-8, 0, 8)])
    g = union(body, handle, steam)
    return affinity.translate(affinity.scale(g, k, k, origin=(0, 0)), cx, cy)


def keycap(cx, cy, w, h, label=None, icon=None):
    skirt = rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 10)
    face = rrect(cx - w / 2 + 7, cy - h / 2 + 4, cx + w / 2 - 7, cy + h / 2 - 13, 8)
    g = knock(skirt, face.buffer(2.2)).union(face)
    if label:
        g = knock(g, text(label, OSWALD, 15, cx, cy - 4.5 + 7.5, tracking=0.04))
    if icon is not None:
        g = knock(g, icon)
    return g


def d_keycaps():
    w = 72
    k1 = keycap(-92, 0, w, w, "STRG")
    k2 = keycap(0, 0, w, w, "ALT")
    k3 = keycap(92, 0, w, w, icon=cup_icon(92, -2, 30))
    plus = [union(bar((x - 6.5, 0), (x + 6.5, 0), 4.4, "flat"), bar((x, -6.5), (x, 6.5), 4.4, "flat"))
            for x in (-46, 46)]
    head = text("NEUSTART", ARCHIVO, 34, 0, 92, tracking=0.03, width=256)
    sub = text("ERST KAFFEE, DANN CODE.", OSWALD, 12, 0, 118, tracking=0.16, width=256)
    top = text("DER WICHTIGSTE SHORTCUT DES TAGES", OSWALD, 9.5, 0, -48, tracking=0.12, width=256)
    return union(k1, k2, k3, plus, head, sub, top)


# ------------------------------------------------------------------ 4  Powered by KI (Chip)
def d_chip():
    S = 46
    body = rrect(-S, -S, S, S, 7)
    body = knock(body, frame(-S + 6, -S + 6, S - 6, S - 6, 4, 2.0))
    body = knock(body, text("KI", ORBITRON, 30, 0, 15, tracking=0.04))
    pins, traces = [], []
    offs = [-33, -20, -7, 7, 20, 33]
    for o in offs:
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if dx:
                pins.append(box(dx * S - (0 if dx > 0 else 10), o - 3, dx * S + (10 if dx > 0 else 0), o + 3))
            else:
                pins.append(box(o - 3, dy * S - (0 if dy > 0 else 10), o + 3, dy * S + (10 if dy > 0 else 0)))
    pad_r, tw = 5.2, 2.6

    def trace(pts):
        end = pts[-1]
        return union(polyline(pts, tw, cap="flat", join="mitre"), ring(end[0], end[1], pad_r, 2.6))

    for sx in (1, -1):
        traces += [trace([(sx * 56, -33), (sx * 70, -33), (sx * 86, -49), (sx * 112, -49)]),
                   trace([(sx * 56, -20), (sx * 92, -20), (sx * 100, -28)]),
                   trace([(sx * 56, 7), (sx * 124, 7)]),
                   trace([(sx * 56, 20), (sx * 78, 20), (sx * 96, 38), (sx * 108, 38)]),
                   trace([(sx * 56, 33), (sx * 66, 33), (sx * 80, 47), (sx * 80, 60)])]
    for sy in (1, -1):
        traces += [trace([(-20, sy * 56), (-20, sy * 66), (-30, sy * 76)]),
                   trace([(7, sy * 56), (7, sy * 70)]),
                   trace([(33, sy * 56), (33, sy * 64), (42, sy * 73)])]
    top = text("POWERED BY", ARCHIVO, 21, 0, -94, tracking=0.08, width=200)
    bot1 = text("KAFFEE & KÜNSTLICHE", OSWALD, 15, 0, 106, tracking=0.06, width=250)
    bot2 = text("INTELLIGENZ", ARCHIVO, 25, 0, 140, tracking=0.08, width=250)
    return union(body, pins, traces, top, bot1, bot2)


# ------------------------------------------------------------------ 5  Kein Bug, ein Feature (Pixel-Kaefer)
BUG = """
..X.......X..
...X.....X...
....XXXXX....
...XXXXXXX...
X..X.XXX.X..X
.X.XXXXXXX.X.
..XXXXXXXXX..
X.XXXX.XXXX.X
.XXXXX.XXXXX.
..XXXX.XXXX..
.XXXXX.XXXXX.
X..XXX.XXX..X
....XX.XX....
"""


def pixels(art, px):
    rows = art.strip().splitlines()
    on = {(i, j) for j, r in enumerate(rows) for i, c in enumerate(r) if c == "X"}
    cells = [box(i * px, j * px, (i + 1) * px, (j + 1) * px) for i, j in on]
    # Diagonal-Nachbarn mit kleinem Steg verbinden (sonst nur Eckpunkt-Kontakt)
    s = px * 0.28
    for i, j in on:
        for di in (1, -1):
            if (i + di, j + 1) in on and (i + di, j) not in on and (i, j + 1) not in on:
                x, y = (i + (1 if di > 0 else 0)) * px, (j + 1) * px
                cells.append(Polygon([(x - s, y), (x, y - s), (x + s, y), (x, y + s)]))
    g = union(cells)
    b = g.bounds
    return affinity.translate(g, -(b[0] + b[2]) / 2, -b[1])


def d_bug():
    bug = affinity.translate(pixels(BUG, 11), 0, -158)
    t1 = text("KEIN BUG.", PIXEL, 20, 0, 18, width=240)
    t2 = text("EIN FEATURE.", PIXEL, 20, 0, 52, width=240)
    return union(bug, t1, t2)


# ------------------------------------------------------------------ 6  Ich bin kein Roboter
def robot_head(cx, cy, s):
    k = s / 50
    head = rrect(-22, -16, 22, 18, 8)
    head = knock(head, circle(-9, -1, 5), circle(9, -1, 5), bar((-8, 9), (8, 9), 3.2))
    ant = union(bar((0, -16), (0, -25), 3), circle(0, -27, 4))
    ears = union(rrect(-28, -6, -24, 8, 1.5), rrect(24, -6, 28, 8, 1.5))
    drop = svgpath("M 27 -26 C 27 -26 33 -18 33 -14 C 33 -10.5 30.3 -8 27 -8 C 23.7 -8 21 -10.5 21 -14 "
                   "C 21 -18 27 -26 27 -26 Z")
    g = union(head, ant, ears, drop)
    return affinity.translate(affinity.scale(g, k, k, origin=(0, 0)), cx, cy)


def d_captcha():
    W, H = 268, 96
    fr = frame(-W / 2, -H / 2, W / 2, H / 2, 10, 3.6)
    cb = frame(-W / 2 + 18, -22, -W / 2 + 62, 22, 5, 4.2)
    check = polyline([(-W / 2 + 25, -2), (-W / 2 + 37, 12), (-W / 2 + 70, -30)], 8.5, cap="round")
    cbx = knock(cb, check, gap=2.2).union(check)
    t = text("Ich bin kein Roboter", KANIT, 17, -W / 2 + 78, 8.5, align="left", width=146)
    bot = robot_head(W / 2 - 22, -2, 28)
    script = text("...glaube ich.", PACIFICO, 24, 30, 98)
    return union(fr, cbx, t, bot, script)


# ------------------------------------------------------------------ 7  Läuft bei mir. (Stempel)
def d_stamp():
    W, H = 250, 140
    outer = frame(-W / 2, -H / 2, W / 2, H / 2, 12, 5.5)
    inner = frame(-W / 2 + 9, -H / 2 + 9, W / 2 - 9, H / 2 - 9, 6, 2.2)
    t = text("LÄUFT BEI MIR.", ALFA, 30, 0, 18, width=206)
    top = text("GEPRÜFT AUF LOCALHOST", OSWALD, 10.5, 0, -30, tracking=0.14)
    bot = text("AUF DEINEM RECHNER? KEIN SUPPORT.", OSWALD, 9, 0, 46, tracking=0.08, width=206)
    stars = [star(x, -35.2, 5.2) for x in (-96, 96)]
    g = union(outer, inner, t, top, bot, stars)
    return affinity.rotate(g, -6, origin=(0, 0))


# ------------------------------------------------------------------ 8  Ich committe mich. (Git-Graph)
def d_git():
    rows = 30
    msgs = [(0, "init"), (0, "README.md"), (1, "feature: kaffee"), (1, "fix"), (1, "fix fix"), (1, "final"),
            (1, "final_v2"), (0, "FINAL_wirklich_jetzt")]
    bx = 34
    g = []
    main = polyline([(0, 0), (0, rows * 7)], 4.2)

    def bez(p0, p1, p2, p3, n=40):
        return [((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0],
                 (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1])
                for t in np.linspace(0, 1, n)]
    pts = (bez((0, rows), (0, rows * 1.6), (bx, rows * 1.4), (bx, rows * 2)) +
           bez((bx, rows * 6), (bx, rows * 6.6), (0, rows * 6.4), (0, rows * 7)))
    branch = polyline(pts, 4.2)
    g += [main, branch]
    nodes = []
    for k, (lane, msg) in enumerate(msgs):
        x, y = lane * bx, k * rows
        nodes.append((x, y))
        g.append(text(msg, MONO, 9.6, 66, y + 4.8, align="left"))
    lines = union(g)
    for x, y in nodes:
        lines = knock(lines, circle(x, y, 10.5))
        lines = lines.union(ring(x, y, 8.6, 3.6))
    head = text("$ git log --graph", MONO, 9.6, -6, -26, align="left")
    title = text("ICH COMMITTE MICH.", ARCHIVO, 22, 108, rows * 7 + 52, width=262)
    return union(lines, head, title)


# ------------------------------------------------------------------ 9  KI-Flüsterer (Lorbeer-Emblem)
def d_whisperer():
    lr = laurel(0, 6, 104, spread=112, n=9, leaf_len=27, leaf_w=9.5, stem=2.8)
    # Roboterkopf
    head = rrect(-46, -36, 46, 34, 20)
    face = rrect(-35, -24, 35, 22, 12)
    eyes = union(circle(-16, -4, 8.5), circle(16, -4, 8.5))
    mouth = svgpath("M -14 8 C -8 15 8 15 14 8 L 11 6 C 6 11 -6 11 -11 6 Z")
    head = union(knock(head, face), eyes, mouth)
    ears = union(rrect(-56, -12, -46, 14, 3), rrect(46, -12, 56, 14, 3))
    ant = union(bar((0, -36), (0, -52), 4), circle(0, -56, 7))
    robot = affinity.translate(union(head, ears, ant), 0, -4)
    sp = [sparkle(-74, -86, 7), sparkle(74, -86, 7)]
    ban = banner(0, 96, 206, 40, tail=30, drop=10, notch=9, gap=2.0, label="KI-FLÜSTERER", font=ALFA,
                 cap=15, tracking=0.05, bend=420)
    lr = knock(lr, ban.buffer(3.2))
    top = circle_text_top("ZERTIFIZIERTER", OSWALD, 12, 0, 6, 104, tracking=0.2)
    return union(lr, robot, sp, ban, top)


# ------------------------------------------------------------------ 10 Kaffee rein, Code raus (Tasse)
def d_mug():
    body = svgpath("M -52 -50 L 52 -50 L 48 46 C 47 58 38 66 26 66 L -26 66 C -38 66 -47 58 -48 46 Z")
    body = knock(body, text("</>", MONO, 30, -2, 22))
    handle = svgpath("M 50 -30 C 92 -34 94 30 46 36 L 47 22 C 76 18 74 -16 51 -16 Z")
    rim = rrect(-58, -58, 58, -48, 4)
    saucer = svgpath("M -84 74 L 84 74 C 80 84 66 88 50 88 L -50 88 C -66 88 -80 84 -84 74 Z")
    steam = [polyline([(x + 7 * math.sin(t / 7 + ph), -66 - t) for t in np.linspace(0, 52, 60)], 5.2)
             for x, ph in ((-26, 0), (0, 2.2), (26, 4.4))]
    top = circle_text_top("KAFFEE REIN", ALFA, 24, 0, 10, 148, tracking=0.04)
    bot = circle_text_bottom("CODE RAUS", ALFA, 24, 0, -16, 146, tracking=0.06)
    dots = [star(-112, 20, 6.5, n=4, ri=2.2, rot=-90), star(112, 20, 6.5, n=4, ri=2.2, rot=-90)]
    return union(body, handle, rim, saucer, steam, top, bot, dots)


DESIGNS = [
    ("01_404-schlaf", "404 – Schlaf nicht gefunden", d_404, (24, 24, 27), (255, 255, 255)),
    ("02_prompt-engineer", "Certified Prompt Engineer", d_prompt_badge, (20, 34, 66), (244, 236, 214)),
    ("03_strg-alt-kaffee", "STRG + ALT + Kaffee", d_keycaps, (236, 233, 226), (24, 24, 28)),
    ("04_powered-by-ki", "Powered by KI", d_chip, (14, 42, 38), (122, 240, 190)),
    ("05_kein-bug", "Kein Bug. Ein Feature.", d_bug, (60, 64, 72), (255, 214, 64)),
    ("06_kein-roboter", "Ich bin kein Roboter …glaube ich.", d_captcha, (250, 250, 248), (30, 64, 160)),
    ("07_laeuft-bei-mir", "Läuft bei mir. (Stempel)", d_stamp, (190, 196, 202), (170, 24, 36)),
    ("08_ich-committe-mich", "Ich committe mich.", d_git, (28, 30, 34), (255, 140, 60)),
    ("09_ki-fluesterer", "KI-Flüsterer", d_whisperer, (118, 30, 44), (245, 230, 200)),
    ("10_kaffee-rein-code-raus", "Kaffee rein – Code raus", d_mug, (92, 64, 48), (250, 240, 225)),
]

if __name__ == "__main__":
    only = sys.argv[1:]
    build([d for d in DESIGNS if not only or any(d[0].startswith(o) for o in only)], OUT)
