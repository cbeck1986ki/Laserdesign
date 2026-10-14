"""Fotorealistische(re) Mockups aus der Laser-Geometrie: Holzoptik, Brandkanten, Schatten."""
import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from lasergeo import FONT_DIR, polys

SS = 3  # Supersampling


def _mask(geom, bounds, scale, pad):
    x0, y0 = bounds[0] - pad, bounds[1] - pad
    w = int((bounds[2] - bounds[0] + 2 * pad) * scale)
    h = int((bounds[3] - bounds[1] + 2 * pad) * scale)
    im = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(im)
    t = lambda c: [((x - x0) * scale * SS, (y - y0) * scale * SS) for x, y in c]
    for p in polys(geom):
        d.polygon(t(p.exterior.coords), fill=255)
        for i in p.interiors:
            d.polygon(t(i.coords), fill=0)
    return im.resize((w, h), Image.LANCZOS)


def _noise(w, h, cell, rng):
    n = rng.random((max(2, h // cell + 2), max(2, w // cell + 2)))
    return np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize(
        (w, h), Image.BICUBIC), dtype=np.float32) / 255


def wood(w, h, seed=0, base=(226, 192, 146)):
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    warp = _noise(w, h, 90, rng)
    grain = np.sin((x / 26.0 + warp * 1.8 + y * 0.003) * 2 * math.pi)
    fib = np.asarray(Image.fromarray((rng.random((max(2, h // 50), w)) * 255)
                                     .astype(np.uint8)).resize((w, h), Image.BILINEAR),
                     dtype=np.float32) / 255
    blot = _noise(w, h, 160, rng)
    shade = 0.92 + 0.045 * grain + 0.05 * (fib - 0.5) + 0.06 * (blot - 0.5)
    img = np.stack([np.clip(shade * c, 0, 255) for c in base], -1)
    return img.astype(np.float32)


def render_part(part, scale, seed=0, base=(226, 192, 146), pad=4):
    """RGBA-Bild eines gelaserten Holzteils + Funktion mm->px."""
    b = part.solid.bounds
    m = _mask(part.solid, b, scale, pad)
    w, h = m.size
    tex = wood(w, h, seed, base)
    a = np.asarray(m, dtype=np.float32) / 255
    if part.engrave is not None and not part.engrave.is_empty:
        e = np.asarray(_mask(part.engrave, b, scale, pad), dtype=np.float32)[..., None] / 255
        tex = tex * (1 - e) + tex * np.array([0.40, 0.28, 0.19]) * e
    if part.score:
        lm = Image.new("L", (w * SS, h * SS), 0)
        d = ImageDraw.Draw(lm)
        x0, y0 = b[0] - pad, b[1] - pad
        for l in part.score:
            d.line([((x - x0) * scale * SS, (y - y0) * scale * SS) for x, y in l.coords],
                   fill=255, width=max(2, int(0.32 * scale * SS)), joint="curve")
        e = np.asarray(lm.resize((w, h), Image.LANCZOS), dtype=np.float32)[..., None] / 255
        tex = tex * (1 - e) + tex * np.array([0.45, 0.32, 0.22]) * e
    # Brandkante: dunkler Rand, Innenbereich leicht aufgehellt (Kantenlicht)
    er1 = np.asarray(m.filter(ImageFilter.MinFilter(3)), dtype=np.float32) / 255
    er2 = np.asarray(m.filter(ImageFilter.MinFilter(7)), dtype=np.float32) / 255
    edge = np.clip(a - er1, 0, 1)[..., None]
    soft = np.clip(er1 - er2, 0, 1)[..., None]
    tex = tex * (1 - edge) + np.array([62, 38, 22]) * edge
    tex = tex * (1 - soft * 0.18) + np.array([120, 80, 45]) * soft * 0.18
    rgba = np.dstack([np.clip(tex, 0, 255), a * 255]).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    to_px = lambda x, y: ((x - b[0] + pad) * scale, (y - b[1] + pad) * scale)
    return img, to_px


# ---------------------------------------------------------------- Szene
def background(w, h, seed=1, c1=(24, 52, 40), c2=(6, 16, 13), bokeh=60, table=None):
    rng = random.Random(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((x - w * 0.5) / w) ** 2 + ((y - h * 0.38) / h) ** 2)
    t = np.clip(r * 1.5, 0, 1)[..., None]
    img = np.array(c1) * (1 - t) + np.array(c2) * t
    bg = Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cols = [(255, 196, 110), (255, 226, 170), (255, 170, 80), (220, 60, 50), (255, 240, 210)]
    for _ in range(bokeh):
        cx, cy = rng.uniform(0, w), rng.uniform(0, h * (0.75 if table else 1))
        rr = rng.uniform(8, 55)
        c = rng.choice(cols)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c + (rng.randint(25, 85),),
                  outline=c + (rng.randint(60, 120),), width=2)
    bg = Image.alpha_composite(bg, layer.filter(ImageFilter.GaussianBlur(5)))
    if table:
        ty = int(h * table)
        tw = wood(w, h - ty, seed + 5, base=(118, 74, 44))
        grad = np.linspace(0.55, 1.0, h - ty)[:, None, None]
        tim = Image.fromarray(np.clip(tw * grad, 0, 255).astype(np.uint8), "RGB")
        tim = tim.filter(ImageFilter.GaussianBlur(2))
        bg.paste(tim, (0, ty))
        hl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(hl).rectangle([0, ty, w, ty + 3], fill=(255, 220, 170, 60))
        bg = Image.alpha_composite(bg, hl)
    # Vignette
    v = np.clip(1.15 - r * 0.9, 0.35, 1)[..., None]
    arr = np.asarray(bg, dtype=np.float32)
    arr[..., :3] *= v
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def snow(img, n=160, seed=3):
    rng = random.Random(seed)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y, r = rng.uniform(0, img.width), rng.uniform(0, img.height), rng.uniform(1, 3.4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rng.randint(70, 190)))
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(0.8)))


def shadow(canvas, piece, pos, offset=(14, 18), blur=12, alpha=0.55):
    a = piece.split()[3].point(lambda v: int(v * alpha))
    sh = Image.new("RGBA", piece.size, (0, 0, 0, 255))
    sh.putalpha(a)
    pad = blur * 3
    big = Image.new("RGBA", (piece.width + 2 * pad, piece.height + 2 * pad), (0, 0, 0, 0))
    big.paste(sh, (pad, pad))
    big = big.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(big, (int(pos[0] + offset[0] - pad), int(pos[1] + offset[1] - pad)))


def ribbon(canvas, top, end, color=(178, 28, 36), width=5):
    d = ImageDraw.Draw(canvas)
    d.line([top, end], fill=tuple(int(c * 0.6) for c in color), width=width + 2)
    d.line([top, end], fill=color, width=width)
    d.line([(top[0] - 1, top[1]), (end[0] - 1, end[1])],
           fill=tuple(min(255, c + 60) for c in color), width=1)
    ex, ey = end
    d.ellipse([ex - width, ey - width * 0.8, ex + width, ey + width * 0.8], fill=color)


def label(canvas, title, sub):
    d = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(str(FONT_DIR / "BerkshireSwash-Regular.ttf"), 52)
    try:
        f2 = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 24)
    except OSError:
        f2 = ImageFont.load_default()
    x, y = 48, canvas.height - 118
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle([x - 22, y - 16, x + max(d.textlength(title, f1),
                                                  d.textlength(sub, f2)) + 26, y + 98],
                         18, fill=(0, 0, 0, 120))
    canvas.alpha_composite(ov)
    d.text((x, y), title, font=f1, fill=(255, 241, 220))
    d.text((x + 2, y + 66), sub, font=f2, fill=(232, 205, 160))


def glow_layer(size, center, radius, color=(255, 170, 70), strength=1.0):
    w, h = size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2) / radius
    a = np.clip(1 - r, 0, 1) ** 2 * 255 * strength
    arr = np.zeros((h, w, 4), np.float32)
    arr[..., :3] = color
    arr[..., 3] = np.clip(a, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def shade(img, k):
    r, g, b, a = img.split()
    rgb = Image.merge("RGB", (r, g, b)).point(lambda v: int(v * k))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def skew_side(img, sx, k):
    """Seitenflaeche: horizontal stauchen und nach hinten oben scheren."""
    w, h = img.size
    wo = int(w * sx)
    ho = int(h + k * wo)
    return img.transform((wo, ho), Image.AFFINE, (1 / sx, 0, 0, k, 1, -k * wo),
                         resample=Image.BICUBIC), wo, int(k * wo)


def joint_strips(w, h, t, seed, base=(226, 192, 146), k=0.62):
    """Holzstreifen, die die Zinkenluecken an Seiten- und Unterkante fuellen (Nachbarwand)."""
    tex = wood(w, h, seed, base) * k
    a = np.zeros((h, w), np.float32)
    a[:, :t] = a[:, w - t:] = 255
    a[h - t:, :] = 255
    return Image.fromarray(np.dstack([np.clip(tex, 0, 255), a]).astype(np.uint8), "RGBA")
