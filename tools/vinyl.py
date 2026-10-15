"""Werkzeugkasten fuer einfarbige Plotter-Motive (Flex-/Flockfolie): Schrift mit Kerning, Bogentext,
Schriftbaender, Lorbeer, SVG-Pfade als Flaechen, Export (SVG/DXF/PNG) und Shirt-Mockups.
Einheiten: mm, y nach unten."""
import io
import math
from functools import lru_cache
from pathlib import Path

import cairosvg
import numpy as np
import pathops
import shapely
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from svgelements import Path as SvgPath

FONT_DIR = Path(__file__).parent / "fonts"

ALFA = "AlfaSlabOne-Regular.ttf"
ARCHIVO = "ArchivoBlack-Regular.ttf"
BEBAS = "BebasNeue-Regular.ttf"
BUNGEE = "Bungee-Regular.ttf"
KANIT = "Kanit-ExtraBold.ttf"
MONO = "JetBrainsMono-ExtraBold.ttf"
ORBITRON = "Orbitron-Black.ttf"
OSWALD = "Oswald-Bold.ttf"
PACIFICO = "Pacifico-Regular.ttf"
PIXEL = "PressStart2P-Regular.ttf"
RYE = "Rye-Regular.ttf"

EMPTY = Polygon()


# ================================================================== Schrift
class _FlatPen(BasePen):
    def __init__(self, glyphset=None, steps=12):
        super().__init__(glyphset)
        self.contours, self.cur, self.steps = [], None, steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                             u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                             u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if self.cur and len(self.cur) >= 3:
            self.contours.append(self.cur)
        self.cur = None

    _endPath = _closePath


@lru_cache(None)
def _tt(font):
    return TTFont(str(FONT_DIR / font))


@lru_cache(None)
def _hb(font):
    blob = hb.Blob.from_file_path(str(FONT_DIR / font))
    return hb.Font(hb.Face(blob))


@lru_cache(None)
def _glyph(font, gid):
    """Glyphe als Flaeche in Font-Einheiten (y nach oben); Ueberlappungen per pathops aufgeloest."""
    f = _tt(font)
    gs = f.getGlyphSet()
    name = f.getGlyphOrder()[gid]
    p = pathops.Path()
    gs[name].draw(pathops.PathPen(p, gs))
    p.simplify(fix_winding=True)
    pen = _FlatPen(steps=14)
    p.draw(pen)
    g = EMPTY
    for c in pen.contours:
        r = Polygon(c).buffer(0)
        if not r.is_empty:
            g = g.symmetric_difference(r)
    return g


def line(s, font, size, tracking=0.0):
    """Textzeile mit Kerning (HarfBuzz). Links x=0, Grundlinie y=0. Liefert (Geometrie, Breite)."""
    f = _hb(font)
    upm = _tt(font)["head"].unitsPerEm
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(f, buf, {"kern": True, "liga": True})
    x, shapes = 0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        g = _glyph(font, info.codepoint)
        if not g.is_empty:
            shapes.append(affinity.translate(g, x + pos.x_offset, pos.y_offset))
        x += pos.x_advance + tracking * upm
    k = size / upm
    g = unary_union(shapes) if shapes else EMPTY
    return affinity.scale(g, k, -k, origin=(0, 0)), (x - tracking * upm) * k


def cap_height(font):
    f = _tt(font)
    os2 = f["OS/2"]
    ch = getattr(os2, "sCapHeight", 0) or 0.7 * f["head"].unitsPerEm
    return ch / f["head"].unitsPerEm


def text(s, font, cap=None, cx=0.0, base=0.0, tracking=0.0, width=None, size=None, align="center"):
    """Zeile platzieren. Groesse ueber Versalhoehe `cap` (mm), Em-Groesse `size` oder Breite `width`.
    align: center (cx = Mitte), left (cx = linker Rand), right (cx = rechter Rand)."""
    if size is None:
        size = (cap / cap_height(font)) if cap else 10
    g, adv = line(s, font, size, tracking)
    if width:
        b = g.bounds
        k = width / (b[2] - b[0])
        g = affinity.scale(g, k, k, origin=(0, 0))
    b = g.bounds
    dx = {"center": cx - (b[0] + b[2]) / 2, "left": cx - b[0], "right": cx - b[2]}[align]
    return affinity.translate(g, dx, base)


# ================================================================== Verformen
def dense(g, step=0.6):
    return shapely.segmentize(g, step)


def arch(g, R, cx=0.0, base=0.0):
    """Bogen nach oben (Regenbogen): Grundlinie y=base wird Kreisbogen mit Radius R um (cx, base+R)."""
    g = dense(g)

    def f(c):
        x, y = c[:, 0] - cx, c[:, 1] - base
        a, rad = x / R, R - y
        return np.column_stack([cx + rad * np.sin(a), base + R - rad * np.cos(a)])
    return shapely.transform(g, f)


def smile(g, R, cx=0.0, base=0.0):
    """Bogen nach unten (Laecheln), Buchstaben bleiben aufrecht, Koepfe zeigen zum Kreismittelpunkt."""
    g = dense(g)

    def f(c):
        x, y = c[:, 0] - cx, c[:, 1] - base
        a, rad = x / R, R + y
        return np.column_stack([cx + rad * np.sin(a), base - R + rad * np.cos(a)])
    return shapely.transform(g, f)


def circle_text_top(s, font, cap, cx, cy, r, tracking=0.0):
    """Text oben auf einem Kreis (Grundlinie auf Radius r, Buchstaben nach aussen)."""
    g = text(s, font, cap, 0, 0, tracking)
    return arch(affinity.translate(g, cx, cy - r), r, cx, cy - r)


def circle_text_bottom(s, font, cap, cx, cy, r, tracking=0.0):
    """Text unten auf einem Kreis, lesbar von links nach rechts; Versalien reichen von r nach innen."""
    g = text(s, font, cap, 0, 0, tracking)
    return smile(affinity.translate(g, cx, cy + r), r, cx, cy + r)


def skew(g, deg):
    return affinity.skew(g, xs=-deg, origin=(0, 0))


# ================================================================== Formen
def circle(x, y, r):
    return Point(x, y).buffer(r, quad_segs=64)


def ring(x, y, r, t):
    return circle(x, y, r).difference(circle(x, y, r - t))


def rrect(x0, y0, x1, y1, r):
    if r <= 0:
        return box(x0, y0, x1, y1)
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=24)


def frame(x0, y0, x1, y1, r, t):
    return rrect(x0, y0, x1, y1, r).difference(rrect(x0 + t, y0 + t, x1 - t, y1 - t, max(r - t, 0)))


def bar(p, q, w, cap="round"):
    return LineString([p, q]).buffer(w / 2, cap_style=cap, join_style="round")


def polyline(pts, w, cap="round", join="round"):
    return LineString(pts).buffer(w / 2, cap_style=cap, join_style=join)


def star(cx, cy, ro, ri=None, n=5, rot=-90):
    ri = ri if ri is not None else ro * 0.42
    pts = []
    for i in range(2 * n):
        r = ro if i % 2 == 0 else ri
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return Polygon(pts)


def sparkle(cx, cy, r, waist=0.16):
    """Vierzackiges Funkeln mit nach innen gewoelbten Flanken (KI-Symbol)."""
    pts = []
    for i in range(4):
        a0 = math.radians(-90 + i * 90)
        a1 = math.radians(-90 + (i + 1) * 90)
        p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
        p2 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        am = (a0 + a1) / 2
        p1 = (cx + waist * r * math.cos(am), cy + waist * r * math.sin(am))
        for t in np.linspace(0, 1, 30, endpoint=False):
            u = 1 - t
            pts.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                        u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return Polygon(pts)


def leaf(cx, cy, length, width, angle):
    """Spitzes Blatt (Schnittmenge zweier Kreise), Mitte (cx, cy), Laengsachse unter `angle` Grad."""
    L, W = length / 2, width / 2
    R = (L * L + W * W) / (2 * W)
    a = circle(0, R - W, R).intersection(circle(0, -(R - W), R))
    return affinity.translate(affinity.rotate(a, angle, origin=(0, 0)), cx, cy)


def laurel_branch(cx, cy, r, a_start, a_end, n=8, leaf_len=17, leaf_w=7, stem=2.2, side=1):
    """Lorbeerzweig auf einem Kreisbogen (Winkel in Grad, 0 = rechts, im Uhrzeigersinn = y-down)."""
    angs = np.linspace(a_start, a_end, 200)
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in angs]
    g = [polyline(pts, stem)]
    direction = 1 if a_end > a_start else -1
    for i, a in enumerate(np.linspace(a_start, a_end, n + 1)[1:]):
        rad = math.radians(a)
        px, py = cx + r * math.cos(rad), cy + r * math.sin(rad)
        tang = math.degrees(rad) + 90 * direction  # Wuchsrichtung entlang des Bogens
        for s in (-1, 1):
            off = 0.5 * leaf_len
            la = tang - s * 28
            lx = px + off * math.cos(math.radians(la)) * 0.85
            ly = py + off * math.sin(math.radians(la)) * 0.85
            k = 1 - 0.25 * (i / n)
            g.append(leaf(lx, ly, leaf_len * k, leaf_w * k, la))
    # Endblatt
    rad = math.radians(a_end)
    px, py = cx + r * math.cos(rad), cy + r * math.sin(rad)
    tang = math.degrees(rad) + 90 * direction
    g.append(leaf(px + 0.4 * leaf_len * math.cos(math.radians(tang)),
                  py + 0.4 * leaf_len * math.sin(math.radians(tang)), leaf_len * 0.8, leaf_w * 0.8, tang))
    return unary_union(g)


def laurel(cx, cy, r, spread=118, n=8, **kw):
    """Zwei Zweige unten zusammen, oben offen (spread = Bogen je Zweig in Grad)."""
    left = laurel_branch(cx, cy, r, 100, 100 + spread, n, **kw)
    right = laurel_branch(cx, cy, r, 80, 80 - spread, n, **kw)
    return unary_union([left, right])


def banner(cx, cy, w, h, tail=24, drop=8, notch=8, gap=1.8, label=None, font=None, cap=None, tracking=0.0,
           bend=None):
    """Schriftband: Mittelteil mit freigestelltem Text, dahinter zwei gekerbte Enden.
    bend = Radius fuer einen nach oben gewoelbten Bogen (None = gerade)."""
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    front = box(x0, y0, x1, y1)
    tl = Polygon([(x0 + 10, y0 + drop), (x0 - tail, y0 + drop), (x0 - tail + notch, y1 + drop - h / 2 + 0),
                  (x0 - tail, y1 + drop), (x0 + 10, y1 + drop)])
    tr = affinity.scale(tl, -1, 1, origin=(cx, cy))
    fold_l = Polygon([(x0, y1), (x0 + 0.01, y1 + drop), (x0 - drop * 0.9, y1 + drop)])  # kleines Umschlag-Dreieck
    fold_r = affinity.scale(fold_l, -1, 1, origin=(cx, cy))
    tails = unary_union([tl, tr]).difference(front.buffer(gap, join_style="mitre"))
    folds = unary_union([fold_l, fold_r]).intersection(unary_union([tl, tr]))
    tails = tails.union(folds.difference(front.buffer(gap, join_style="mitre")))
    g = unary_union([front, tails])
    if label:
        t = text(label, font, cap or h * 0.45, cx, cy + (cap or h * 0.45) / 2, tracking)
        g = g.difference(t)
    if bend:
        g = arch(g, bend, cx, cy)
    return g


def svgpath(d, steps=24):
    """SVG-Pfad (absolut/relativ, alle Befehle) -> Flaeche mit Even-Odd-Regel."""
    p = SvgPath(d)
    g = EMPTY
    for sub in p.as_subpaths():
        pts = []
        for seg in sub:
            name = type(seg).__name__
            if name == "Move":
                continue
            n = 1 if name in ("Line", "Close") else steps
            for t in np.linspace(0, 1, n + 1)[1:]:
                q = seg.point(t)
                pts.append((q.x, q.y))
        if len(pts) >= 3:
            r = Polygon(pts).buffer(0)
            g = g.symmetric_difference(r)
    return g


def hline_rule(cx, y, w, t=2.2, diamond=5.0, gap=4.0):
    """Linie mit Raute in der Mitte."""
    d = Polygon([(cx - diamond, y), (cx, y - diamond), (cx + diamond, y), (cx, y + diamond)])
    l = bar((cx - w / 2, y), (cx - diamond - gap, y), t, "flat")
    r = bar((cx + diamond + gap, y), (cx + w / 2, y), t, "flat")
    return unary_union([d, l, r])


def union(*gs):
    out = []
    for g in gs:
        if isinstance(g, (list, tuple)):
            out.extend(g)
        else:
            out.append(g)
    return unary_union([g for g in out if g is not None and not g.is_empty])


def knock(base, *cut, gap=0.0):
    """Ausstanzen: Aussparung (optional mit Abstand gap) aus der Grundflaeche."""
    c = union(*cut)
    return base.difference(c.buffer(gap, join_style="round") if gap else c)


def outline(g, gap, t):
    """Kontur mit Abstand gap und Staerke t um g herum (Rahmen ohne g)."""
    o = g.buffer(gap + t, join_style="round")
    return o.difference(g.buffer(gap, join_style="round"))


# ================================================================== Pruefung & Aufbereitung
def polys(g):
    if g is None or g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    if hasattr(g, "geoms"):
        out = []
        for s in g.geoms:
            out += polys(s)
        return out
    return []


def finalize(g, target_w=None, target_h=None, margin=6.0, min_hole=2.0, min_island=1.2):
    """Skalieren (Breite oder Hoehe, kleinerer Wert gewinnt), Nullpunkt mit Rand, Mini-Teile entfernen."""
    g = g.buffer(0)
    b = g.bounds
    k = min(target_w / (b[2] - b[0]) if target_w else 1e9, target_h / (b[3] - b[1]) if target_h else 1e9)
    g = affinity.scale(g, k, k, origin=(0, 0))
    b = g.bounds
    g = affinity.translate(g, margin - b[0], margin - b[1])
    out = []
    for p in polys(g):
        if p.area < min_island:
            continue
        holes = [h for h in p.interiors if Polygon(h).area >= min_hole]
        out.append(Polygon(p.exterior, holes).simplify(0.015))
    return unary_union(out)


def thin_share(g, w=1.2):
    thin = g.difference(g.buffer(-w / 2).buffer(w / 2))
    return thin.area / g.area * 100


def narrow_gaps(g, w=0.8):
    """Anteil der Zwischenraeume (Loecher/Spalte) schmaler als w mm -> schwer zu entgittern."""
    neg = g.buffer(w / 2).buffer(-w / 2).difference(g)
    return neg.area


# ================================================================== Export
def rings(g):
    for p in polys(g):
        yield p.exterior
        yield from p.interiors


def path_d(g):
    out = []
    for r in rings(g):
        c = list(r.coords)[:-1]
        out.append("M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in c) + " Z")
    return " ".join(out)


def write_svg(path, g, size, title):
    W, H = size
    Path(path).write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<!-- {title} | Plotterdatei fuer Flex-/Flockfolie. Einheiten mm. VOR DEM SCHNEIDEN SPIEGELN! -->\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}mm" height="{H:.2f}mm" '
        f'viewBox="0 0 {W:.3f} {H:.3f}">\n<title>{title}</title>\n'
        f'<g id="Motiv"><path fill="#000000" fill-rule="evenodd" stroke="none" d="{path_d(g)}"/></g>\n'
        f'<g id="Entgitterrahmen"><rect x="0.5" y="0.5" width="{W - 1:.3f}" height="{H - 1:.3f}" '
        f'fill="none" stroke="#999999" stroke-width="0.25"/></g>\n</svg>\n', encoding="utf-8")


def write_dxf(path, g, size):
    """DXF R12, geschlossene POLYLINEs, mm, y nach oben (liest auch Silhouette Studio Basic)."""
    W, H = size
    o = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSUNITS", "70", "4",
         "9", "$EXTMIN", "10", "0.0", "20", "0.0", "9", "$EXTMAX", "10", f"{W:.3f}", "20", f"{H:.3f}",
         "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]

    def poly(coords, layer):
        o.extend(["0", "POLYLINE", "8", layer, "66", "1", "70", "1"])
        for x, y in coords:
            o.extend(["0", "VERTEX", "8", layer, "10", f"{x:.3f}", "20", f"{H - y:.3f}"])
        o.extend(["0", "SEQEND", "8", layer])

    for r in rings(g):
        poly(list(r.coords)[:-1], "MOTIV")
    poly([(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)], "ENTGITTERRAHMEN")
    o.extend(["0", "ENDSEC", "0", "EOF"])
    Path(path).write_text("\n".join(o) + "\n", encoding="ascii")


def write_png(path, g, size, dpi=300):
    W, H = size
    px = round(W / 25.4 * dpi)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{px}" height="{round(px * H / W)}" '
           f'viewBox="0 0 {W:.3f} {H:.3f}"><path fill="#000" fill-rule="evenodd" d="{path_d(g)}"/></svg>')
    img = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode())))
    img.save(path, dpi=(dpi, dpi))


# ================================================================== Mockup
# Shirt Gr. L, flach liegend, mm. Halsnaht-Mitte vorne bei (0, 58).
SHIRT = ("M -84 0 C -50 7 50 7 84 0 C 120 12 168 22 206 34 C 262 60 312 100 352 142 L 300 214 "
         "C 280 200 258 192 240 190 C 238 360 240 540 246 728 C 120 738 -120 738 -246 728 "
         "C -240 540 -238 360 -240 190 C -258 192 -280 200 -300 214 L -352 142 "
         "C -312 100 -262 60 -206 34 C -168 22 -120 12 -84 0 Z")
NECK = "M -84 0 C -72 48 -40 64 0 64 C 40 64 72 48 84 0 C 50 7 -50 7 -84 0 Z"
COLLAR = "M -84 0 C -72 48 -40 64 0 64 C 40 64 72 48 84 0"


def rgb(c):
    return "#%02x%02x%02x" % tuple(c)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def mockup(g, shirt_c, vinyl_c, title, sub, top=82):
    """Motiv mittig, Oberkante `top` mm unter der Schulterlinie (~8 cm unter der Halsnaht)."""
    b = g.bounds
    gw = b[2] - b[0]
    tx, ty = -b[0] - gw / 2, top - b[1]
    dark = mix(shirt_c, (0, 0, 0), 0.32)
    light = mix(shirt_c, (255, 255, 255), 0.10)
    inner = mix(shirt_c, (0, 0, 0), 0.55)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1400" viewBox="-400 -70 800 933">
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f1f0ec"/>
  <stop offset="1" stop-color="#dcdad4"/></linearGradient>
 <radialGradient id="body" cx="0.5" cy="0.32" r="0.78"><stop offset="0" stop-color="{rgb(light)}"/>
  <stop offset="0.65" stop-color="{rgb(shirt_c)}"/><stop offset="1" stop-color="{rgb(dark)}"/></radialGradient>
 <linearGradient id="side" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000" stop-opacity="0.13"/>
  <stop offset="0.12" stop-color="#000" stop-opacity="0"/><stop offset="0.88" stop-color="#000" stop-opacity="0"/>
  <stop offset="1" stop-color="#000" stop-opacity="0.13"/></linearGradient>
 <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="9"/></filter>
 <filter id="fold" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="5"/></filter>
 <filter id="vinyl" x="-5%" y="-5%" width="110%" height="110%">
  <feDropShadow dx="0" dy="0.6" stdDeviation="0.5" flood-color="#000" flood-opacity="0.35"/></filter>
 <clipPath id="clip"><path d="{SHIRT}"/></clipPath>
</defs>
<rect x="-400" y="-70" width="800" height="933" fill="url(#bg)"/>
<path d="{SHIRT}" transform="translate(5,9)" fill="#000" opacity="0.28" filter="url(#soft)"/>
<path d="{SHIRT}" fill="url(#body)"/>
<g clip-path="url(#clip)">
 <rect x="-250" y="0" width="500" height="740" fill="url(#side)"/>
 <path d="M -240 200 C -226 300 -230 420 -238 520" stroke="#000" stroke-opacity="0.18" stroke-width="10"
  fill="none" filter="url(#fold)"/>
 <path d="M 240 200 C 226 300 230 420 238 520" stroke="#000" stroke-opacity="0.18" stroke-width="10"
  fill="none" filter="url(#fold)"/>
 <path d="M -206 34 C -222 90 -234 150 -240 190" stroke="#000" stroke-opacity="0.25" stroke-width="1.6"
  fill="none"/>
 <path d="M 206 34 C 222 90 234 150 240 190" stroke="#000" stroke-opacity="0.25" stroke-width="1.6"
  fill="none"/>
 <path d="M -340 158 L -292 204" stroke="#000" stroke-opacity="0.18" stroke-width="1.4" fill="none"/>
 <path d="M 340 158 L 292 204" stroke="#000" stroke-opacity="0.18" stroke-width="1.4" fill="none"/>
 <path d="M -246 712 C -120 722 120 722 246 712" stroke="#000" stroke-opacity="0.2" stroke-width="1.4"
  fill="none" stroke-dasharray="3 2"/>
</g>
<path d="{NECK}" fill="{rgb(inner)}"/>
<path d="{COLLAR}" fill="none" stroke="{rgb(mix(shirt_c, (0, 0, 0), 0.12))}" stroke-width="14"/>
<path d="{COLLAR}" transform="translate(0,7) scale(1.0,1.0)" fill="none" stroke="#000" stroke-opacity="0.18"
 stroke-width="1"/>
<g transform="translate({tx:.2f},{ty:.2f})" filter="url(#vinyl)">
 <path d="{path_d(g)}" fill="{rgb(vinyl_c)}" fill-rule="evenodd"/></g>
</svg>'''
    img = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGB")
    d = ImageDraw.Draw(img)
    try:
        f1 = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 40)
        f2 = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 25)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    d.text((50, 1292), title, font=f1, fill=(30, 30, 30))
    d.text((50, 1344), sub, font=f2, fill=(95, 95, 95))
    return img


def overview(images, cols, path, tw=600, th=700):
    rows = math.ceil(len(images) / cols)
    ov = Image.new("RGB", (tw * cols, th * rows), (236, 235, 231))
    for i, m in enumerate(images):
        ov.paste(m.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    ov.save(path, quality=86)


def build(designs, out_dir, target_w=260, max_h=300, cols=5):
    """designs: Liste (slug, titel, funktion, shirtfarbe, folienfarbe[, breite])."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    thumbs, rows = [], []
    for item in designs:
        slug, title, fn, shirt_c, vinyl_c = item[:5]
        w = item[5] if len(item) > 5 else target_w
        g = finalize(fn(), target_w=w, target_h=max_h)
        b = g.bounds
        size = (b[2] + 6, b[3] + 6)
        d = out_dir / slug
        d.mkdir(exist_ok=True)
        write_svg(d / f"{slug}.svg", g, size, title)
        write_dxf(d / f"{slug}.dxf", g, size)
        write_png(d / f"{slug}_300dpi.png", g, size)
        mw, mh = b[2] - b[0], b[3] - b[1]
        sub = f"Motiv {mw / 10:.1f} × {mh / 10:.1f} cm · einfarbig · Flex-/Flockfolie"
        m = mockup(g, shirt_c, vinyl_c, title, sub)
        m.save(d / f"{slug}_mockup.jpg", quality=88)
        thumbs.append(m)
        n = len(list(rings(g)))
        thin = thin_share(g)
        rows.append((slug, title, mw, mh, n, thin))
        print(f"{slug:30s} {mw:6.1f} x {mh:6.1f} mm  Konturen {n:4d}  <1,2 mm: {thin:4.1f} %", flush=True)
    overview(thumbs, cols, out_dir / "uebersicht.jpg")
    return rows


def stack(geoms, gaps, top=0.0, cx=0.0):
    """Elemente untereinander, horizontal zentriert; gaps[i] = Abstand nach Element i (mm)."""
    out, y = [], top
    for i, g in enumerate(geoms):
        b = g.bounds
        out.append(affinity.translate(g, cx - (b[0] + b[2]) / 2, y - b[1]))
        y += (b[3] - b[1]) + (gaps[i] if i < len(gaps) else 0)
    return unary_union(out)
