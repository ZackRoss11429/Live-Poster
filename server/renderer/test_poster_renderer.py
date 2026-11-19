from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image
from constants import WIDTH, HEIGHT
from poster_renderer import ALLOWED_SIX_INKS, PosterSettings, render_image_poster

BASE_DIR = Path(__file__).resolve().parent
IMG_DIR = BASE_DIR / "test_images"


def _make_full_spectrum_test_image(width: int = WIDTH, height: int = HEIGHT) -> Image.Image:
    """
    Generate a deterministic smooth RGB gradient image in memory (no disk I/O).
    """
    x = np.linspace(0, 255, width, dtype=np.uint8)
    y = np.linspace(0, 255, height, dtype=np.uint8)
    xv, yv = np.meshgrid(x, y)
    rgb = np.stack([xv, yv, np.flipud(xv)], axis=-1)
    return Image.fromarray(rgb, mode="RGB")


def test_imported_image_outputs_only_six_panel_inks() -> None:
    source = _make_full_spectrum_test_image(1920, 1080)
    settings = PosterSettings(fit_mode="cover", show_timestamp=True, use_dbs=False)
    fixed_time = datetime(2026, 11, 19, 0, 59, 0, tzinfo=timezone.utc)

    result = render_image_poster(source, settings, fixed_time)

    # 1. Exact output dimensions
    assert result.size == (WIDTH, HEIGHT)
    assert result.mode == "RGB"

    # 2. Check all pixels belong strictly to the 6-ink set
    pixels = np.asarray(result, dtype=np.uint8).reshape(-1, 3)
    unique_rgb = {tuple(int(c) for c in row) for row in np.unique(pixels, axis=0)}

    unexpected = unique_rgb - ALLOWED_SIX_INKS
    assert not unexpected, f"Unexpected RGB values found: {unexpected}"
    assert len(unique_rgb) == 6, f"Expected 6 unique RGB values, found {len(unique_rgb)}: {unique_rgb}"


if __name__ == "__main__":
    test_imported_image_outputs_only_six_panel_inks()
    print("6-ink validation test passed.")

    with Image.open(IMG_DIR / "template_image_1920x1080.png") as src:
        out = render_image_poster(
            src,
            PosterSettings(fit_mode="cover", show_timestamp=True, use_dbs=False),
            datetime.now(timezone.utc),
        )
        out.save(IMG_DIR / "output_image_1600x1200.png", format="PNG")
        out.show()
