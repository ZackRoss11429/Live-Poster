from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter
from epaper_dithering import DbsParams, DitherMode, DitherOptions, Palette, dither_image
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

INK_WHITE = (255, 255, 255)
INK_BLACK = (0, 0, 0)


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

    canvas = canvas.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=3))

    # --- STEP 3: Optionally add a timestamp ---
    if settings.show_timestamp:
        draw = ImageDraw.Draw(canvas)
        box_y0 = height - 45
        box_y1 = height - 15
        draw.rectangle([16, box_y0, 260, box_y1], fill=INK_WHITE)
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        draw.text((24, box_y0 + 8), timestamp_str, fill=INK_BLACK)

    # --- STEP 4: Reduce to the 6 panel inks ---
    options = DitherOptions(
        mode=DitherMode.FLOYD_STEINBERG,
        serpentine=True,
        saturation=1.05,
        dbs=settings.use_dbs,
    )
    dithered = dither_image(canvas, palette)

    return dithered.convert("RGB")
