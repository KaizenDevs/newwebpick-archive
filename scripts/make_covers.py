#!/usr/bin/env python3
"""Generate cover thumbnails for issues 01-16 matching the 17-44 design."""

import os
import sys
import colorsys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

COVERS_DIR = os.path.join(os.path.dirname(__file__), "..", "site", "covers")
SIZE = (256, 256)

BOOK_X0, BOOK_Y0, BOOK_X1, BOOK_Y1 = 8, 52, 248, 226
SPINE_W = 4

TARGETS = [f"{i:02d}" for i in range(1, 17)]


# ── Logo extraction ──────────────────────────────────────────────────────────

def extract_logo_mask(cover_path):
    """Return RGBA where only the W-logo shape is opaque (as grayscale tint-ready)."""
    img = Image.open(cover_path).convert("RGBA")
    pixels = img.load()
    w, h = img.size
    inset = 3
    ix0 = 0
    ix1 = BOOK_X1 - inset
    iy0 = BOOK_Y0 + inset
    LOGO_Y_MAX = 150

    for y in range(h):
        for x in range(w):
            if not (ix0 < x < ix1):
                continue
            if y < iy0:
                continue
            r, g, b, a = pixels[x, y]
            if y >= LOGO_Y_MAX:
                pixels[x, y] = (r, g, b, 0)
            else:
                is_gold = (r > 170 and g > 110 and b < 90
                           and r - b > 100 and g / max(r, 1) > 0.62)
                if not is_gold:
                    pixels[x, y] = (r, g, b, 0)
    return img


def tint_logo(logo_mask, target_rgb):
    """Recolor the gold logo to target_rgb, preserving luminance structure."""
    result = logo_mask.copy()
    pixels = result.load()
    w, h = result.size
    tr, tg, tb = target_rgb

    # Convert target to HSV to build a richer tint
    th, ts, tv = colorsys.rgb_to_hsv(tr/255, tg/255, tb/255)

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            # Luminance of original gold pixel
            lum = (0.299*r + 0.587*g + 0.114*b) / 255
            # Reconstruct with target hue/sat, scaled brightness
            nr, ng, nb = colorsys.hsv_to_rgb(th, ts, min(1.0, tv * lum * 1.6))
            # Add a highlight layer for metallic feel
            highlight = max(0, lum - 0.6) * 2.0
            nr = min(1.0, nr + highlight * 0.4)
            ng = min(1.0, ng + highlight * 0.4)
            nb = min(1.0, nb + highlight * 0.4)
            pixels[x, y] = (int(nr*255), int(ng*255), int(nb*255), a)

    return result


# ── Color extraction from screenshot ────────────────────────────────────────

def dominant_color(screenshot):
    """Find the most vibrant accent color in the screenshot."""
    w, h = screenshot.size
    region = screenshot.crop((w//5, h//5, 4*w//5, 4*h//5))
    small = region.resize((40, 40), Image.LANCZOS).convert("RGB")

    # Score each pixel: saturation * value (prefer bright + saturated)
    best_rgb = (200, 160, 40)  # fallback gold
    best_score = 0.15

    for py in range(40):
        for px in range(40):
            r, g, b = small.getpixel((px, py))
            hc, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            # Require decent brightness and saturation; score by s*v
            if v > 0.45 and s > 0.35:
                score = s * v
                if score > best_score:
                    best_score = score
                    best_rgb = (r, g, b)

    # Normalize: boost to a usable brightness (value ≥ 0.7)
    hr, sr, vr = colorsys.rgb_to_hsv(best_rgb[0]/255, best_rgb[1]/255, best_rgb[2]/255)
    vr = max(vr, 0.70)
    sr = max(sr, 0.55)
    nr, ng, nb = colorsys.hsv_to_rgb(hr, sr, vr)
    return (int(nr*255), int(ng*255), int(nb*255))


# ── Screenshot preprocessing ─────────────────────────────────────────────────

def crop_flash_chrome(screenshot):
    """Remove Flash navigation chrome (top/bottom bars) from SWF screenshots."""
    w, h = screenshot.size
    # Older Flash magazines have a dark nav bar at top (~11%) and controls at bottom (~8%)
    top = int(h * 0.11)
    bot = int(h * 0.08)
    return screenshot.crop((0, top, w, h - bot))


# ── Book compositing ─────────────────────────────────────────────────────────

def make_book_base(screenshot):
    """Composite screenshot into book shape with depth."""
    canvas = Image.new("RGBA", SIZE, (0, 0, 0, 255))
    draw = ImageDraw.Draw(canvas)

    x0, y0, x1, y1 = BOOK_X0, BOOK_Y0, BOOK_X1, BOOK_Y1

    # Drop shadow
    shadow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle([x0+4, y0+6, x1+4, y1+6], radius=6, fill=(0,0,0,160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    canvas.alpha_composite(shadow)

    # Book back (depth)
    draw.rounded_rectangle([x0+2, y0+2, x1+3, y1+3], radius=5, fill=(20,20,28,255))

    # Spine
    for i in range(SPINE_W):
        brightness = int(15 + i * 5)
        draw.line([(x0+i, y0), (x0+i, y1)], fill=(brightness, brightness, brightness+6, 255))

    # Book face background
    draw.rounded_rectangle([x0+SPINE_W, y0, x1, y1], radius=3, fill=(8,8,8,255))

    # Screenshot into book face
    sc = crop_flash_chrome(screenshot)
    bw = x1 - (x0 + SPINE_W)
    bh = y1 - y0
    sw, sh = sc.size
    ratio = bw / bh
    sr = sw / sh
    if sr > ratio:
        nw = int(sh * ratio)
        off = (sw - nw) // 2
        sc = sc.crop((off, 0, off+nw, sh))
    else:
        nh = int(sw / ratio)
        off = (sh - nh) // 2
        sc = sc.crop((0, off, sw, off+nh))
    sc = sc.resize((bw, bh), Image.LANCZOS)
    # Slightly enhance contrast for magazine feel
    sc = ImageEnhance.Contrast(sc).enhance(1.15)

    face_mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(face_mask).rounded_rectangle([0, 0, bw-1, bh-1], radius=3, fill=255)
    canvas.paste(sc, (x0+SPINE_W, y0), face_mask)

    # Page edges
    for i in range(4):
        draw.line([(x0+SPINE_W+2, y1+1+i), (x1-2, y1+1+i)],
                  fill=(200, 200, 200, max(0, 110 - i*30)))

    # Top reflection
    draw.line([(x0+SPINE_W+1, y0), (x1-1, y0)], fill=(255,255,255,25))

    return canvas


def add_logo_shadow(logo, offset=(3, 6), blur=6):
    """Return new image: blurred dark shadow of logo."""
    shadow = Image.new("RGBA", logo.size, (0,0,0,0))
    _, _, _, a = logo.split()
    shadow_body = Image.new("RGBA", logo.size, (0,0,0,0))
    shadow_body.paste((0, 0, 0, 200), mask=a)
    shadow_body = shadow_body.filter(ImageFilter.GaussianBlur(blur))
    result = Image.new("RGBA", logo.size, (0,0,0,0))
    result.paste(shadow_body, offset)
    return result


# ── Text ─────────────────────────────────────────────────────────────────────

def load_font(size):
    for path in [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/Library/Fonts/Impact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_number(canvas, num, accent_rgb):
    draw = ImageDraw.Draw(canvas)
    label = f"No.{int(num)}"
    font = load_font(44)

    cx = (BOOK_X0 + SPINE_W + BOOK_X1) // 2
    ty = BOOK_Y1 - 52

    # Black drop shadow
    for dx, dy in [(-2,2),(0,3),(2,2),(0,2)]:
        draw.text((cx+dx, ty+dy), label, font=font, fill=(0,0,0,200), anchor="mt")

    # Accent color outline
    ar, ag, ab = accent_rgb
    dark = (max(0,ar-60), max(0,ag-60), max(0,ab-60), 255)
    for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
        draw.text((cx+dx, ty+dy), label, font=font, fill=dark, anchor="mt")

    # Main fill — use accent color, brightened
    h_c, s, v = colorsys.rgb_to_hsv(ar/255, ag/255, ab/255)
    fr, fg, fb = colorsys.hsv_to_rgb(h_c, max(0.6, s), min(1.0, v*1.3 + 0.3))
    draw.text((cx, ty), label, font=font,
              fill=(int(fr*255), int(fg*255), int(fb*255), 255), anchor="mt")


# ── Main ─────────────────────────────────────────────────────────────────────

def make_cover(num, logo_mask_base):
    screenshot_path = os.path.join(COVERS_DIR, f"cover_{num}.png")
    if not os.path.exists(screenshot_path):
        print(f"[SKIP] {num}")
        return

    screenshot = Image.open(screenshot_path).convert("RGBA")
    accent = dominant_color(screenshot.convert("RGB"))

    # Build book with screenshot content
    canvas = make_book_base(screenshot)

    # Tint logo to match accent color
    logo = tint_logo(logo_mask_base, accent)

    # Logo drop shadow onto book
    logo_shadow = add_logo_shadow(logo, offset=(3, 6), blur=5)
    canvas.alpha_composite(logo_shadow)

    # Logo itself
    canvas.alpha_composite(logo)

    # Issue number
    draw_number(canvas, num, accent)

    out = os.path.join(COVERS_DIR, f"cover_{num}.png")
    canvas.convert("RGB").save(out, "PNG")
    print(f"[OK] {num} → accent={accent}")


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else TARGETS
    template = os.path.join(COVERS_DIR, "cover_17.png")
    print("Extracting logo mask from cover_17…")
    logo_mask = extract_logo_mask(template)
    for num in targets:
        make_cover(num, logo_mask)


if __name__ == "__main__":
    main()
