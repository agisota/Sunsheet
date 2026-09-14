#!/usr/bin/env python3
"""Render a controlled Sunsheet/Berkeley Mono raster comparison.

The Berkeley font is supplied at runtime and is never copied into the output
directory. Both faces use Pillow's FreeType renderer with the same nominal
size, origin, baseline, text, and disabled ligature settings.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1800
HEIGHT = 1040
SCALE = 2
FONT_SIZE = 54
TEXT = (
    "0O 1Il a g Q @ $ &  {} [] () <>\n"
    "0123456789  != == ===  -> => >= <=\n"
    "Sphinx of black quartz, judge my vow."
)


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size, layout_engine=ImageFont.Layout.BASIC)


def render_mask(
    font: ImageFont.FreeTypeFont,
    origin: tuple[int, int],
    spacing: int,
) -> Image.Image:
    mask = Image.new("L", (WIDTH * SCALE, HEIGHT * SCALE), 0)
    draw = ImageDraw.Draw(mask)
    draw.multiline_text(
        (origin[0] * SCALE, origin[1] * SCALE),
        TEXT,
        font=font,
        fill=255,
        spacing=spacing * SCALE,
        anchor="ls",
    )
    return mask


def tint(mask: Image.Image, colour: tuple[int, int, int]) -> Image.Image:
    layer = Image.new("RGBA", mask.size, colour + (0,))
    layer.putalpha(mask)
    return layer


def panel(
    image: Image.Image,
    mask: Image.Image,
    crop: tuple[int, int, int, int],
    destination: tuple[int, int],
    colour: tuple[int, int, int],
) -> None:
    region = mask.crop(tuple(value * SCALE for value in crop))
    layer = tint(region, colour)
    image.alpha_composite(layer, tuple(value * SCALE for value in destination))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sunsheet-font", required=True, type=Path)
    parser.add_argument("--berkeley-font", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    for path in (args.sunsheet_font, args.berkeley_font):
        if not path.is_file():
            parser.error(f"font not found: {path}")

    overlay_size = FONT_SIZE * SCALE
    reference_size = 30 * SCALE
    sunsheet = load_font(args.sunsheet_font, overlay_size)
    berkeley = load_font(args.berkeley_font, overlay_size)
    sunsheet_reference = load_font(args.sunsheet_font, reference_size)
    berkeley_reference = load_font(args.berkeley_font, reference_size)
    origin = (70, 120)
    sunsheet_mask = render_mask(sunsheet, origin, spacing=30)
    berkeley_mask = render_mask(berkeley, origin, spacing=30)
    sunsheet_reference_mask = render_mask(sunsheet_reference, origin, spacing=18)
    berkeley_reference_mask = render_mask(berkeley_reference, origin, spacing=18)

    canvas = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE), (12, 14, 18, 255))
    draw = ImageDraw.Draw(canvas)
    label_font = ImageFont.load_default(size=18 * SCALE)

    draw.text((70 * SCALE, 28 * SCALE), "SUNSHEET", fill=(255, 93, 165), font=label_font)
    draw.text((930 * SCALE, 28 * SCALE), "BERKELEY MONO TRIAL", fill=(70, 218, 255), font=label_font)
    panel(canvas, sunsheet_reference_mask, (0, 0, 860, 390), (0, 0), (255, 93, 165))
    panel(canvas, berkeley_reference_mask, (0, 0, 860, 390), (860, 0), (70, 218, 255))

    draw.line(
        ((70 * SCALE, 430 * SCALE), (1730 * SCALE, 430 * SCALE)),
        fill=(58, 62, 72),
        width=2 * SCALE,
    )
    draw.text(
        (70 * SCALE, 462 * SCALE),
        "PIXEL OVERLAY  /  magenta = Sunsheet  /  cyan = Berkeley  /  pale = overlap",
        fill=(225, 228, 235),
        font=label_font,
    )
    panel(canvas, sunsheet_mask, (0, 0, WIDTH, 390), (0, 500), (255, 93, 165))
    panel(canvas, berkeley_mask, (0, 0, WIDTH, 390), (0, 500), (70, 218, 255))

    draw.text(
        (70 * SCALE, 950 * SCALE),
        "Pillow FreeType | 54 px at 2x | same text, origin and nominal size | ligatures disabled",
        fill=(155, 161, 174),
        font=label_font,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).convert("RGB").save(
        args.output,
        optimize=True,
    )


if __name__ == "__main__":
    main()
