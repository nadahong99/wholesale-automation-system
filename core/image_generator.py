# core/image_generator.py
"""Product image processing: background removal, overlays, thumbnails."""
import io
import os
import requests
from pathlib import Path
from typing import Optional, Tuple
from utils.logger import get_logger

logger = get_logger("image_generator")

TMP_DIR = Path("data/images")
TMP_DIR.mkdir(parents=True, exist_ok=True)


def download_image(url: str) -> Optional[bytes]:
    """Download an image from *url* and return its bytes."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.content
    except Exception as exc:
        logger.warning(f"download_image failed for {url}: {exc}")
        return None


def make_white_background(image_bytes: bytes) -> Optional[bytes]:
    """Paste the image onto a white background (removes transparent areas)."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        background.paste(img, mask=img.split()[3])
        result = background.convert("RGB")
        out = io.BytesIO()
        result.save(out, format="JPEG", quality=90)
        return out.getvalue()
    except Exception as exc:
        logger.warning(f"make_white_background failed: {exc}")
        return image_bytes


def add_price_overlay(
    image_bytes: bytes,
    selling_price: int,
    margin_percent: float,
    size: Tuple[int, int] = (800, 800),
) -> Optional[bytes]:
    """Resize image to *size*, add price + margin overlay text."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(size, Image.LANCZOS)
        draw = ImageDraw.Draw(img)

        # Semi-transparent price banner at bottom
        banner_h = 80
        banner = Image.new("RGBA", (size[0], banner_h), (0, 0, 0, 160))
        img.paste(banner, (0, size[1] - banner_h), mask=banner.split()[3])

        draw = ImageDraw.Draw(img)
        price_text = f"₩{selling_price:,}  |  마진 {margin_percent:.1f}%"
        draw.text((20, size[1] - banner_h + 25), price_text, fill=(255, 255, 255))

        out = io.BytesIO()
        img.save(out, format="JPEG", quality=90)
        return out.getvalue()
    except Exception as exc:
        logger.warning(f"add_price_overlay failed: {exc}")
        return image_bytes


def make_thumbnail(image_bytes: bytes, size: Tuple[int, int] = (200, 200)) -> Optional[bytes]:
    """Generate a thumbnail."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail(size, Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
        return out.getvalue()
    except Exception as exc:
        logger.warning(f"make_thumbnail failed: {exc}")
        return None


def process_product_image(
    image_url: str,
    selling_price: int,
    margin_percent: float,
) -> Tuple[Optional[bytes], Optional[bytes]]:
    """
    Full pipeline: download → white BG → price overlay → thumbnail.
    Returns (main_image_bytes, thumbnail_bytes).
    """
    raw = download_image(image_url)
    if not raw:
        return None, None

    processed = make_white_background(raw)
    with_overlay = add_price_overlay(processed, selling_price, margin_percent)
    thumb = make_thumbnail(processed)
    return with_overlay, thumb


def upload_processed_image(
    image_url: str,
    selling_price: int,
    margin_percent: float,
    product_id: int,
) -> Optional[str]:
    """
    Process the product image and upload to GCS.
    Returns the public GCS URL of the processed image.
    """
    from integrations.gcs_upload import upload_bytes

    main_bytes, _ = process_product_image(image_url, selling_price, margin_percent)
    if not main_bytes:
        return None

    filename = f"products/processed/{product_id}.jpg"
    return upload_bytes(main_bytes, filename=filename)
