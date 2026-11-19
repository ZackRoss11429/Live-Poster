from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from epaper_dithering import DitherMode, DitherOptions, Palette, dither_image
from constants import WIDTH, HEIGHT

BASE_DIR = Path(__file__).resolve().parent
PALETTE_PATH = BASE_DIR / "spectra_7_3_6color_v2.json"

palette = Palette.load(str(PALETTE_PATH))


def _extract_palette_inks(pal: Palette) -> frozenset[tuple[int, int, int]]:
    nominal_inks = np.array(
        [
            [0, 0, 0],        # Black
            [255, 255, 255],  # White
            [255, 255, 0],    # Yellow
            [255, 0, 0],      # Red
            [0, 0, 255],      # Blue
            [0, 255, 0],      # Green
        ],
        dtype=np.uint8,
    ).reshape(1, 6, 3)
    probe = Image.fromarray(nominal_inks, mode="RGB")
    mapped = dither_image(probe, pal, DitherOptions(mode=DitherMode.NONE)).convert("RGB")
    pixels = np.asarray(mapped, dtype=np.uint8).reshape(-1, 3)
    return frozenset(tuple(int(c) for c in row) for row in pixels)


ALLOWED_SIX_INKS: frozenset[tuple[int, int, int]] = _extract_palette_inks(palette)

# Nominal inks: use these on the canvas *before* dithering.
INK_WHITE = (255, 255, 255)
INK_BLACK = (0, 0, 0)


def _panel_rgb(nominal: tuple[int, int, int]) -> tuple[int, int, int]:
    probe = Image.new("RGB", (1, 1), nominal)
    return dither_image(probe, palette, DitherOptions(mode=DitherMode.NONE)).convert("RGB").getpixel((0, 0))


# Measured inks: use these when drawing on the image *after* dithering.
PANEL_WHITE = _panel_rgb(INK_WHITE)
PANEL_BLACK = _panel_rgb(INK_BLACK)

TIMESTAMP_FONT = ImageFont.load_default(size=28)


@dataclass(frozen=True)
class PosterSettings:
    fit_mode: Literal["cover", "contain"] = "cover"
    show_timestamp: bool = False
    use_dbs: bool = False


def render_image_poster(
    source_image: Image.Image,
    settings: PosterSettings,
    now: datetime,
) -> Image.Image:
    width = WIDTH
    height = HEIGHT

    # --- STEP 1: Normalise EXIF rotation & convert to RGB ---
    img = ImageOps.exif_transpose(source_image).convert("RGB")

    # --- STEP 2: Resize to fit the poster dimensions ---
    if settings.fit_mode == "cover":
        canvas = ImageOps.fit(img, (width, height), method=Image.Resampling.LANCZOS)
    else:
        canvas = ImageOps.pad(
            img,
            (width, height),
            method=Image.Resampling.LANCZOS,
            color=INK_WHITE,
        )

    # Smooth, don't sharpen: dithering adds its own texture, and sharpening turns source grain into speckle.
    canvas = canvas.filter(ImageFilter.GaussianBlur(radius=0.8))

    # --- STEP 3: Reduce to the 6 panel inks ---
    options = DitherOptions(
        # Atkinson: no lattice pattern on flat areas (Floyd-Steinberg makes a visible grid on skies).
        mode=DitherMode.ATKINSON,
        serpentine=True,
        # The measured palette is dark and narrow; squeeze the source into it before matching.
        tone=0.5,
        gamut=0.5,
        shadows=0.3,
        dbs=settings.use_dbs,
    )
    dithered = dither_image(canvas, palette, options).convert("RGB")

    # --- STEP 4: Optionally add a timestamp (after dithering, so text stays crisp and exact-ink) ---
    if settings.show_timestamp:
        draw = ImageDraw.Draw(dithered)
        draw.fontmode = "1"  # no anti-aliasing: every pixel stays one of the six inks
        timestamp_str = now.strftime("%Y-%m-%d %H:%M UTC")
        left, top, right, bottom = draw.textbbox((0, 0), timestamp_str, font=TIMESTAMP_FONT)
        pad = 10
        x0, y1 = 16, height - 16
        y0 = y1 - (bottom - top) - 2 * pad
        draw.rectangle([x0, y0, x0 + (right - left) + 2 * pad, y1], fill=PANEL_WHITE)
        draw.text((x0 + pad - left, y0 + pad - top), timestamp_str, fill=PANEL_BLACK, font=TIMESTAMP_FONT)

    return dithered
