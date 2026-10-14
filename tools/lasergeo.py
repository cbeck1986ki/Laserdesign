"""Geometrie-Helfer und SVG-Export fuer Laser-Dateien (Einheiten: mm, y nach unten)."""
import math
from dataclasses import dataclass, field
from functools import reduce
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import (GeometryCollection, LineString, MultiLineString,
                              MultiPolygon, Point, Polygon, box)
from shapely.ops import unary_union

FONT_DIR = Path(__file__).parent / "fonts"

# Farbkonvention fuer xTool Creative Space (XCS): jede Farbe = eigene Ebene
COL_CUT = "#FF0000"      # Schneiden
COL_ENGRAVE = "#0000FF"  # Gravieren (Flaeche)
COL_SCORE = "#000000"    # Linie gravieren (Score)


# ---------------------------------------------------------------- Grundformen
def circle(x, y, r, res=48):
    return Point(x, y).buffer(r, quad_segs=res)


def star(cx, cy, r_out, r_in, n=5, rot=-90):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return Polygon(pts)


def round_convex(g, r):
    """Aeussere Spitzen abrunden."""
    return g.buffer(-r, join_style="round").buffer(r, join_style="round")


def round_concave(g, r):
    """Innenecken abrunden."""
    return g.buffer(r, join_style="round").buffer(-r, join_style="round")


def stroke(line, width):
    return LineString(line).buffer(width / 2, cap_style="round", join_style="round")


def polar(r, deg, cx=0.0, cy=0.0):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def polys(g):
    if g is None or g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    if isinstance(g, (MultiPolygon, GeometryCollection)):
        out = []
        for sub in g.geoms:
            out += polys(sub)
        return out
    return []


def lines(g):
    if g is None or g.is_empty:
        return []
    if isinstance(g, LineString):
        return [g]
    if isinstance(g, (MultiLineString, GeometryCollection)):
        out = []
        for sub in g.geoms:
            out += lines(sub)
        return out
    if isinstance(g, (Polygon, MultiPolygon)):
        out = []
        for p in polys(g):
            out.append(LineString(p.exterior.coords))
            out += [LineString(i.coords) for i in p.interiors]
        return out
    return []


# ---------------------------------------------------------------- Schrift
class _FlatPen(BasePen):
    def __init__(self, glyphset, steps=10):
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
            self.cur.append((
                u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
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


_fonts = {}


def _font(name):
    if name not in _fonts:
        _fonts[name] = TTFont(str(FONT_DIR / name))
    return _fonts[name]


def text(s, font="GreatVibes-Regular.ttf", size=10.0, cx=0.0, cy=0.0, width=None,
         tracking=0.0, max_h=None):
    """Text als Flaechen-Geometrie. size = Em-Groesse in mm; optional auf Breite skaliert.
    (cx, cy) = Mittelpunkt der Text-Boundingbox."""
    f = _font(font)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    upm = f["head"].unitsPerEm
    x = 0
    shapes = []
    for ch in s:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        pen = _FlatPen(gs)
        gs[gname].draw(pen)
        rings = [Polygon([(px + x, py) for px, py in c]).buffer(0) for c in pen.contours]
        rings = [r for r in rings if not r.is_empty]
        if rings:
            shapes.append(reduce(lambda a, b: a.symmetric_difference(b), rings))
        x += f["hmtx"][gname][0] + tracking * upm + (0.12 * upm if ch == " " else 0)
    g = unary_union(shapes)
    g = affinity.scale(g, size / upm, -size / upm, origin=(0, 0))
    if width:
        b = g.bounds
        k = width / (b[2] - b[0])
        g = affinity.scale(g, k, k, origin=(0, 0))
    b = g.bounds
    if max_h and b[3] - b[1] > max_h:
        k = max_h / (b[3] - b[1])
        g = affinity.scale(g, k, k, origin=(0, 0))
        b = g.bounds
    return affinity.translate(g, cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2)


# ---------------------------------------------------------------- Teile & Export
@dataclass
class Part:
    name: str
    solid: object                      # Polygon/MultiPolygon: Umriss + Loecher -> Schneiden
    engrave: object = None             # Flaechen -> Gravieren
    score: list = field(default_factory=list)  # Linien -> Linie gravieren
    hang: tuple = None                 # Aufhaengepunkt (fuer Mockup)

    def clean(self):
        inner = self.solid.buffer(-0.6)
        if self.engrave is not None:
            self.engrave = self.engrave.intersection(inner)
        self.score = [s for l in self.score for s in lines(l.intersection(inner))]
        return self

    def moved(self, dx, dy):
        t = lambda g: affinity.translate(g, dx, dy) if g is not None else None
        return Part(self.name, t(self.solid), t(self.engrave), [t(s) for s in self.score],
                    (self.hang[0] + dx, self.hang[1] + dy) if self.hang else None)

    def bounds(self):
        return self.solid.bounds


def layout(parts, max_w=400, gap=6, margin=5):
    """Teile zeilenweise anordnen; liefert verschobene Teile und Gesamtgroesse."""
    out, x, y, row_h, W = [], margin, margin, 0, 0
    for p in parts:
        b = p.bounds()
        w, h = b[2] - b[0], b[3] - b[1]
        if x + w > max_w and x > margin:
            x, y, row_h = margin, y + row_h + gap, 0
        out.append(p.moved(x - b[0], y - b[1]))
        x += w + gap
        row_h = max(row_h, h)
        W = max(W, x - gap + margin)
    return out, (W, y + row_h + margin)


def _d_rings(g):
    d = []
    for p in polys(g):
        for ring in [p.exterior, *p.interiors]:
            c = list(ring.coords)
            d.append("M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in c[:-1]) + " Z")
    return d


def _d_lines(ls):
    return ["M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in l.coords) for l in ls]


def write_svg(path, parts, size, title=""):
    W, H = size
    out = [f'<?xml version="1.0" encoding="UTF-8"?>',
           f'<!-- {title} | xTool D1 Pro: Rot=Schneiden, Blau=Gravieren (Flaeche), '
           f'Schwarz=Linie gravieren. Einheiten mm. -->',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}mm" height="{H:.2f}mm" '
           f'viewBox="0 0 {W:.3f} {H:.3f}">']
    eng = [d for p in parts for d in _d_rings(p.engrave)]
    if eng:
        out.append(f'<g id="Gravieren" fill="{COL_ENGRAVE}" stroke="none" fill-rule="evenodd">')
        out.append(f'<path d="{" ".join(eng)}"/>')
        out.append("</g>")
    sc = [d for p in parts for d in _d_lines(p.score)]
    if sc:
        out.append(f'<g id="Linie" fill="none" stroke="{COL_SCORE}" stroke-width="0.1">')
        out += [f'<path d="{d}"/>' for d in sc]
        out.append("</g>")
    out.append(f'<g id="Schneiden" fill="none" stroke="{COL_CUT}" stroke-width="0.1">')
    for p in parts:
        # Innenkonturen zuerst, Aussenkontur zuletzt (Teil faellt erst am Ende heraus)
        for poly in polys(p.solid):
            for ring in [*poly.interiors, poly.exterior]:
                c = list(ring.coords)
                out.append(f'<path d="M{" L".join(f"{x:.3f},{y:.3f}" for x, y in c[:-1])} Z"/>')
    out.append("</g>")
    out.append("</svg>")
    Path(path).write_text("\n".join(out), encoding="utf-8")
