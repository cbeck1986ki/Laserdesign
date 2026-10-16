"""Gelayerte Weltkarte mit 5 Schichten (rechteckiger Rahmen) fuer den Laser.

Aufruf: python3 tools/weltkarte.py

Schicht 1 = Grundplatte (tiefster Ozean) ... Schicht 5 = Kontinente + Rahmen.
Die Meeres-Schichten 2-4 sind organische "Tiefenlinien" rund um die Kuesten:
Abstand zur Kueste + weiches Rauschen, als Hoehenlinien geschnitten.
Kartendaten: Natural Earth 1:50m (Public Domain), Projektion Robinson.
"""
import json
import sys
from pathlib import Path

import cairosvg
import numpy as np
import shapely
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from pyproj import Transformer
from scipy import ndimage
from shapely import affinity
from shapely.geometry import LineString, Polygon, box, shape
from shapely.ops import unary_union
from skimage import measure

sys.path.insert(0, str(Path(__file__).parent))
import render as R  # noqa: E402
from lasergeo import Part, lines, polys, write_svg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).parent / "data"
OUT = ROOT / "entwuerfe" / "06_weltkarte-layered"

# ------------------------------------------------------------------ Parameter
MAT = 3.0            # Materialstaerke (mm) - fuer den Staender-Schlitz
W_OUT = 400.0        # Aussenbreite der Karte (mm); Hoehe ergibt sich aus der Projektion
FRAME = 12.0         # Rahmenbreite (mm)
CORNER = 6.0         # Eckenradius aussen (mm)
LON0 = 10.0          # Mittelmeridian -> Schnitt bei 170 W (Beringstrasse)
LAT_MIN, LAT_MAX = -57.0, 84.0   # ohne Antarktis
LAND_GROW = 0.7      # Land minimal verdicken, damit Landengen (Panama...) halten
GAP = 0.4            # Mindestspalt zwischen getrennten Landmassen
MIN_ISLAND = 5.0     # kleinere Inseln (mm^2) entfallen in Schicht 5
LEVELS = [17.0, 9.5, 3.8]   # Tiefenlinien-Abstand zur Kueste fuer Schicht 2, 3, 4 (mm)
NOISE = 4.0          # Amplitude der organischen Wellung (mm)
RES = 0.2            # Raster fuer die Tiefenlinien (mm/px)
SEED = 7

STAND_SLOT = 5 * MAT + 0.3   # Schlitz im Aufsteller fuer den 5-Schicht-Stapel
STAND_TILT = 8.0             # Neigung nach hinten (Grad)


# ------------------------------------------------------------------ Geodaten
def _features(name):
    return [shape(f["geometry"]) for f in
            json.loads((DATA / f"{name}.geojson").read_text())["features"]]


def _shift(g):
    """Laengen um LON0 verschieben und am neuen Gegenmeridian teilen."""
    g = affinity.translate(g, -LON0)
    a = g.intersection(box(-180, LAT_MIN - 2, 180, 90))
    b = affinity.translate(g.intersection(box(-540, LAT_MIN - 2, -180, 90)), 360)
    return unary_union([a, b])


class Proj:
    def __init__(self):
        self.t = Transformer.from_crs("EPSG:4326", "+proj=robin +lon_0=0", always_xy=True)
        xr, _ = self.t.transform(180, 0)
        _, yt = self.t.transform(0, LAT_MAX)
        _, yb = self.t.transform(0, LAT_MIN)
        self.k = (W_OUT - 2 * FRAME) / (2 * xr)
        self.xr, self.yt = xr, yt
        self.h_out = (yt - yb) * self.k + 2 * FRAME

    def __call__(self, g):
        g = shapely.segmentize(g, 0.5)

        def f(c):
            x, y = self.t.transform(c[:, 0], c[:, 1])
            return np.column_stack([FRAME + (np.asarray(x) + self.xr) * self.k,
                                    FRAME + (self.yt - np.asarray(y)) * self.k])
        return shapely.transform(g, f)


def frame_geo(h):
    outer = box(CORNER, CORNER, W_OUT - CORNER, h - CORNER).buffer(CORNER, quad_segs=16)
    inner = box(FRAME, FRAME, W_OUT - FRAME, h - FRAME)
    return outer, inner


def land_pieces(P, inner):
    """Kontinente/Inseln als getrennte, laserfeste Teile (groesste zuerst)."""
    raw = []
    for g in _features("ne_50m_land"):
        for p in polys(P(_shift(g))):
            p = p.intersection(inner.buffer(-GAP))
            raw += [q for q in polys(p) if q.area > 0.3]
    raw.sort(key=lambda p: -p.area)
    pieces, taken = [], []
    for p in raw:
        q = p.buffer(LAND_GROW, quad_segs=6)
        q = q.buffer(-0.35).buffer(0.35)          # Haarfeine Zacken weg
        if taken:
            near = unary_union([t for t in taken if t.intersects(q.buffer(GAP))])
            if not near.is_empty:
                q = q.difference(near.buffer(GAP))
        q = q.buffer(-0.45).buffer(0.45)          # Splitter nach dem Freistellen weg
        for s in polys(q):
            if s.area >= MIN_ISLAND:
                s = Polygon(s.exterior, [i for i in s.interiors
                                         if Polygon(i).area > 6]).simplify(0.03)
                pieces.append(s)
                taken.append(s)
    return pieces


def lakes(P, pieces):
    land = unary_union(pieces)
    out = []
    for g in _features("ne_50m_lakes"):
        g = P(_shift(g)).buffer(0.25).intersection(land.buffer(-1.0))
        out += [p for p in polys(g) if p.area > 2.5]
    return unary_union(out)


def borders(P, pieces):
    land = unary_union(pieces).buffer(-0.9)
    out = []
    for g in _features("ne_50m_admin_0_boundary_lines_land"):
        g = P(_shift(g)).simplify(0.05)
        out += [l for l in lines(g.intersection(land)) if l.length > 1.0]
    return out


# ------------------------------------------------------------------ Tiefenlinien
def _smooth_noise(shape_, sigma, rng):
    n = ndimage.gaussian_filter(rng.standard_normal(shape_), sigma, mode="wrap")
    return n / n.std()


def sea_layers(land, h):
    """Schicht 2..4: Bereiche, die naeher als LEVELS[i] (+ Rauschen) an der Kueste liegen."""
    nx, ny = int(np.ceil(W_OUT / RES)), int(np.ceil(h / RES))
    im = Image.new("L", (nx, ny), 0)
    d = ImageDraw.Draw(im)
    for p in polys(land):
        d.polygon([(x / RES, y / RES) for x, y in p.exterior.coords], fill=255)
        for i in p.interiors:
            d.polygon([(x / RES, y / RES) for x, y in i.coords], fill=0)
    mask = np.asarray(im) > 127
    dist = ndimage.distance_transform_edt(~mask) * RES
    rng = np.random.default_rng(SEED)
    noise = (0.8 * _smooth_noise(mask.shape, 20 / RES, rng)
             + 0.45 * _smooth_noise(mask.shape, 6 / RES, rng))
    field = dist + NOISE * noise * np.clip(dist / 6.0, 0, 1)
    field = ndimage.gaussian_filter(field, 0.6 / RES)
    big = field.max() + 100
    padded = np.pad(field, 1, constant_values=big)
    out = []
    for lv in LEVELS:
        rings = [Polygon((c[:, ::-1] - 1 + 0.5) * RES).buffer(0)
                 for c in measure.find_contours(padded, lv) if len(c) > 3]
        rings.sort(key=lambda r: -r.area)
        g = Polygon()
        for r in rings:                   # gerade-ungerade-Regel: Inseln & Loecher
            g = g.symmetric_difference(r)
        out.append(g.simplify(0.06))
    return out


def clean(g, r=1.0, min_hole=25.0, min_piece=12.0):
    """Morphologisch glaetten: keine Stege/Loecher schmaler als ~2 r."""
    g = g.buffer(r).buffer(-r)                # schmale Buchten/Spalte schliessen
    g = g.buffer(-r).buffer(r)                # schmale Stege entfernen
    res = []
    for p in polys(g):
        if p.area < min_piece:
            continue
        res.append(Polygon(p.exterior, [i for i in p.interiors if Polygon(i).area >= min_hole]))
    return unary_union(res)


# ------------------------------------------------------------------ Staender
def stand_foot():
    w, hgt, top = 120.0, 42.0, 56.0
    body = Polygon([(0, hgt), (w, hgt), (w / 2 + top / 2, 0), (w / 2 - top / 2, 0)])
    body = body.buffer(-5).buffer(5, quad_segs=12)
    slot = box(-STAND_SLOT / 2, -20, STAND_SLOT / 2, 18)
    slot = affinity.rotate(slot, -STAND_TILT, origin=(0, 18))
    slot = affinity.translate(slot, w / 2, 0)
    return body.difference(slot)


# ------------------------------------------------------------------ Aufbau
LAYER_NAMES = ["Grundplatte (tiefes Meer)", "Meer tief", "Meer mittel", "Meer flach",
               "Kontinente + Rahmen"]


def build():
    P = Proj()
    h = P.h_out
    outer, inner = frame_geo(h)
    ring = outer.difference(inner)
    pieces = land_pieces(P, inner)
    land = unary_union(pieces)
    sea = sea_layers(land, h)

    layers = [Part("Schicht 1", outer)]
    upper = land
    stack = []
    for g in reversed(sea):               # von oben (flach) nach unten (tief)
        g = clean(g.intersection(inner))
        g = unary_union([g, upper.buffer(0.8)]).intersection(inner)
        stack.append(g)
        upper = g
    for g in reversed(stack):
        layers.append(Part(f"Schicht {len(layers) + 1}", unary_union([ring, g])))
    top = Part("Schicht 5", unary_union([ring] + [p for p in pieces]))
    top.engrave = lakes(P, pieces)
    top.score = borders(P, pieces)
    # Rahmen und Landteile bleiben getrennte Teile -> einzeln bemalbar
    top.solid = [ring] + pieces
    layers.append(top)
    return layers, (W_OUT, h)


def _part_list(layer):
    if isinstance(layer.solid, list):
        return [Part(layer.name, layer.solid[0], layer.engrave, layer.score)] + \
               [Part(layer.name, p) for p in layer.solid[1:]]
    return [layer]


# ------------------------------------------------------------------ Mockup
PAINT = [(58, 44, 104), (84, 66, 140), (118, 100, 176), (160, 148, 210)]


def _mask(g, w, h, s):
    im = Image.new("L", (w * 2, h * 2), 0)
    for p in polys(g):                    # je Teil einzeln, sonst loescht ein Loch Nachbarn
        t = Image.new("L", im.size, 0)
        d = ImageDraw.Draw(t)
        d.polygon([(x * s * 2, y * s * 2) for x, y in p.exterior.coords], fill=255)
        for i in p.interiors:
            d.polygon([(x * s * 2, y * s * 2) for x, y in i.coords], fill=0)
        im = ImageChops.lighter(im, t)
    return im.resize((w, h), Image.LANCZOS)


def mockup(layers, size, s=3.6):
    W, H = int(size[0] * s), int(size[1] * s)
    ring = layers[4].solid[0]
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    geos = [l.solid for l in layers[:4]] + [unary_union(layers[4].solid)]
    for k, g in enumerate(geos):
        m = _mask(g, W, H, s)
        a = np.asarray(m, np.float32) / 255
        if k < 4:
            # Farbe deckt die Maserung weitgehend ab
            tex = 0.3 * R.wood(W, H, 40 + k, base=PAINT[k]) + 0.7 * np.array(PAINT[k])
            # Rahmen jeder Schicht bleibt Holz
            fm = np.asarray(_mask(ring, W, H, s), np.float32)[..., None] / 255
            tex = tex * (1 - fm) + R.wood(W, H, 50, base=(232, 210, 176)) * fm
        else:
            tex = R.wood(W, H, 60, base=(238, 220, 188))
            e = np.asarray(_mask(layers[4].engrave, W, H, s), np.float32)[..., None] / 255
            tex = tex * (1 - e) + np.array([150, 140, 205]) * e
            lm = Image.new("L", (W * 2, H * 2), 0)
            d = ImageDraw.Draw(lm)
            for l in layers[4].score:
                d.line([(x * s * 2, y * s * 2) for x, y in l.coords], fill=255, width=2)
            e = np.asarray(lm.resize((W, H), Image.LANCZOS), np.float32)[..., None] / 255
            tex = tex * (1 - e * 0.8) + np.array([110, 80, 60]) * e * 0.8
        # Brandkante + Lichtkante
        er = np.asarray(m.filter(ImageFilter.MinFilter(3)), np.float32) / 255
        edge = np.clip(a - er, 0, 1)[..., None]
        tex = tex * (1 - edge) + np.array([60, 40, 34]) * edge
        img = Image.fromarray(np.dstack([np.clip(tex, 0, 255), a * 255]).astype(np.uint8))
        if k:
            R.shadow(canvas, img, (0, 0), (3, 5), 4, 0.6)
        canvas.alpha_composite(img)
    bg = R.background(W + 360, H + 360, 2, c1=(196, 196, 198), c2=(120, 120, 124), bokeh=0)
    R.shadow(bg, canvas, (180, 180), (16, 22), 18, 0.6)
    bg.alpha_composite(canvas, (180, 180))
    R.label(bg, "Weltkarte in 5 Schichten",
            f"{size[0]:.0f} × {size[1]:.0f} mm · 5 × 3 mm Sperrholz · Robinson-Projektion")
    return bg


def explode(layers, size):
    """Alle 5 Schichten einzeln nebeneinander (Laservorschau)."""
    s = 1.6
    w, h = int(size[0] * s), int(size[1] * s)
    o = Image.new("RGB", (w * 3 + 80, h * 2 + 60), (245, 245, 245))
    d = ImageDraw.Draw(o)
    for i, l in enumerate(layers):
        g = unary_union(l.solid) if isinstance(l.solid, list) else l.solid
        col = (PAINT + [(226, 200, 160)])[i]
        m = _mask(g, w, h, s)
        x, y = 20 + (i % 3) * (w + 20), 20 + (i // 3) * (h + 20)
        o.paste(Image.new("RGB", (w, h), col), (x, y), m)
        d.text((x + 6, y + h - 16), f"{i + 1}: {LAYER_NAMES[i]}", fill=(20, 20, 20))
    return o


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    layers, size = build()
    for i, l in enumerate(layers):
        slug = f"06_weltkarte_schicht{i + 1}"
        svg = OUT / f"{slug}.svg"
        write_svg(svg, _part_list(l), size, f"Weltkarte Schicht {i + 1}: {LAYER_NAMES[i]}")
        n = sum(len(polys(p)) for p in (l.solid if isinstance(l.solid, list) else [l.solid]))
        print(f"{slug}: {n} Teile, {size[0]:.0f} x {size[1]:.0f} mm")
    foot = Part("Aufsteller", stand_foot())
    foot2 = foot.moved(130, 0)
    write_svg(OUT / "06_weltkarte_aufsteller.svg", [foot.moved(5, 5), foot2.moved(5, 5)],
              (260, 52), "Weltkarte Aufsteller (2x)")
    cairosvg.svg2png(url=str(OUT / "06_weltkarte_schicht5.svg"),
                     write_to=str(OUT / "06_weltkarte_schicht5_laservorschau.png"),
                     output_width=1600, background_color="white")
    explode(layers, size).save(OUT / "06_weltkarte_schichten.png")
    mockup(layers, size).convert("RGB").save(OUT / "06_weltkarte_mockup.jpg", quality=92)


if __name__ == "__main__":
    main()
