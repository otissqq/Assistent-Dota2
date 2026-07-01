"""
Generates simple placeholder hero portraits locally since the sandbox has
no network access to the real Dota 2 / Steam CDN art assets.

Drop real hero portrait PNGs (named exactly '<HeroName>.png', e.g.
'Anti-Mage.png') into assets/heroes/ to instantly replace these placeholders
-- the UI loads whatever file is present, real art included.
"""
import os
import sys
import hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.heroes_data import HEROES, ATTR_COLORS

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "heroes")
os.makedirs(OUT_DIR, exist_ok=True)

SIZE = 256


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in range(0, 6, 2))


def shade(rgb, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in rgb)


def initials(name):
    parts = [p for p in name.replace("-", " ").split(" ") if p]
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def make_portrait(hero):
    base = hex_to_rgb(ATTR_COLORS.get(hero["attr"], "#6c5ce7"))
    dark = shade(base, 0.35)
    light = shade(base, 1.25)

    img = Image.new("RGB", (SIZE, SIZE), dark)
    draw = ImageDraw.Draw(img)

    # diagonal gradient-ish bands for a bit of texture
    for y in range(SIZE):
        t = y / SIZE
        r = int(dark[0] + (light[0] - dark[0]) * t * 0.6)
        g = int(dark[1] + (light[1] - dark[1]) * t * 0.6)
        b = int(dark[2] + (light[2] - dark[2]) * t * 0.6)
        draw.line([(0, y), (SIZE, y)], fill=(r, g, b))

    # subtle hashed seed pattern per-hero so portraits look distinct
    seed = int(hashlib.md5(hero["name"].encode()).hexdigest(), 16)
    import random
    rng = random.Random(seed)
    for _ in range(14):
        cx, cy = rng.randint(0, SIZE), rng.randint(0, SIZE)
        r = rng.randint(20, 70)
        alpha_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        ad = ImageDraw.Draw(alpha_layer)
        ad.ellipse([cx - r, cy - r, cx + r, cy + r], fill=light + (28,))
        img = Image.alpha_composite(img.convert("RGBA"), alpha_layer).convert("RGB")
        draw = ImageDraw.Draw(img)

    img = img.filter(ImageFilter.GaussianBlur(0.6))
    draw = ImageDraw.Draw(img)

    # vignette
    vignette = Image.new("L", (SIZE, SIZE), 0)
    vd = ImageDraw.Draw(vignette)
    vd.ellipse([-SIZE * 0.3, -SIZE * 0.3, SIZE * 1.3, SIZE * 1.3], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(40))
    black = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    img = Image.composite(img, black, vignette)
    draw = ImageDraw.Draw(img)

    # initials
    text = initials(hero["name"])
    font = None
    for fp in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",):
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, 92)
            break
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((SIZE - tw) / 2 - bbox[0], (SIZE - th) / 2 - bbox[1] - 6), text,
               font=font, fill=(255, 255, 255, 235))

    # border frame
    draw.rectangle([2, 2, SIZE - 3, SIZE - 3], outline=shade(light, 1.1), width=4)

    img.save(os.path.join(OUT_DIR, f"{hero['name']}.png"))


if __name__ == "__main__":
    for h in HEROES:
        make_portrait(h)
    print(f"Generated {len(HEROES)} placeholder portraits -> {OUT_DIR}")
