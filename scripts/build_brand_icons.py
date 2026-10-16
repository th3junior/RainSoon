#!/usr/bin/env python3
"""Build RainSoon brand PNGs for Home Assistant (brand/ folder)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "rainsoon"
BRAND = INTEGRATION / "brand"
ROOT_ICON = ROOT / "icon.png"

# RainSoon palette
BG_TOP = (18, 52, 120)
BG_BOTTOM = (41, 128, 210)
CLOUD = (248, 252, 255)
CLOUD_SHADE = (210, 225, 240)
DROP = (0, 210, 255)
DROP_CORE = (120, 235, 255)
DROP_TAIL = (0, 140, 210)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _rounded_square_bg(size: int, radius: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad = Image.new("RGBA", (size, size))
    px = grad.load()
    for y in range(size):
        t = y / max(size - 1, 1)
        for x in range(size):
            px[x, y] = (
                _lerp(BG_TOP[0], BG_BOTTOM[0], t),
                _lerp(BG_TOP[1], BG_BOTTOM[1], t),
                _lerp(BG_TOP[2], BG_BOTTOM[2], t),
                255,
            )
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    img.paste(grad, (0, 0), mask)
    return img


def _draw_cloud(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float) -> None:
    s = scale
    blobs = [
        (cx - 52 * s, cy - 8 * s, cx + 8 * s, cy + 24 * s),
        (cx - 22 * s, cy - 34 * s, cx + 38 * s, cy + 20 * s),
        (cx + 8 * s, cy - 24 * s, cx + 58 * s, cy + 28 * s),
    ]
    for box in blobs:
        draw.ellipse(box, fill=CLOUD_SHADE)
    for box in blobs:
        x0, y0, x1, y1 = box
        draw.ellipse((x0, y0 - 2 * s, x1, y1 - 2 * s), fill=CLOUD)


def _draw_drop(
    draw: ImageDraw.ImageDraw, x: float, y: float, scale: float
) -> None:
    s = scale
    w, h = 11 * s, 15 * s
    draw.ellipse((x - w / 2, y - h * 0.35, x + w / 2, y + h * 0.45), fill=DROP_TAIL)
    draw.ellipse((x - w * 0.38, y - h * 0.42, x + w * 0.38, y + h * 0.32), fill=DROP)
    draw.ellipse((x - w * 0.18, y - h * 0.28, x + w * 0.12, y - h * 0.05), fill=DROP_CORE)


def build_icon(size: int = 256) -> Image.Image:
    radius = max(16, size // 8)
    base = _rounded_square_bg(size, radius)
    draw = ImageDraw.Draw(base)
    scale = size / 256
    cx, cy = size // 2, int(size * 0.42)
    _draw_cloud(draw, cx, cy, 1.35 * scale)
    _draw_drop(draw, cx - 18 * scale, cy + 42 * scale, 1.1 * scale)
    _draw_drop(draw, cx, cy + 52 * scale, 1.25 * scale)
    _draw_drop(draw, cx + 20 * scale, cy + 44 * scale, 1.0 * scale)
    # Subtle vignette
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(
        (0, 0, size - 1, size - 1),
        radius=radius,
        outline=(255, 255, 255, 40),
        width=max(1, size // 128),
    )
    base = Image.alpha_composite(base, overlay)
    return base.convert("RGB")


def build_logo(w: int = 512, h: int = 256) -> Image.Image:
    icon = build_icon(h - 32).resize((h - 32, h - 32), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(icon, (16, 16))
    draw = ImageDraw.Draw(canvas)
    try:
        from PIL import ImageFont

        font_title = ImageFont.truetype("arial.ttf", 42)
        font_sub = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        font_title = font_sub = ImageFont.load_default()
    draw.text((h + 8, h // 2 - 36), "RainSoon", fill=(255, 255, 255), font=font_title)
    draw.text((h + 8, h // 2 + 8), "Rain alerts", fill=(180, 220, 255), font=font_sub)
    return canvas


def main() -> None:
    BRAND.mkdir(parents=True, exist_ok=True)
    INTEGRATION.mkdir(parents=True, exist_ok=True)

    for size, name in ((256, "icon.png"), (512, "icon@2x.png")):
        img = build_icon(size)
        img.save(BRAND / name, format="PNG", optimize=True)
        if size == 256:
            img.save(INTEGRATION / "icon.png", format="PNG", optimize=True)
            img.save(ROOT_ICON, format="PNG", optimize=True)

    for dims, name in (((512, 256), "logo.png"), ((1024, 512), "logo@2x.png")):
        build_logo(*dims).save(BRAND / name, format="PNG", optimize=True)

    legacy = build_icon(256)
    legacy.save(INTEGRATION / "logo.png", format="PNG", optimize=True)
    print("RainSoon PNG brand assets OK:", BRAND)


if __name__ == "__main__":
    main()
