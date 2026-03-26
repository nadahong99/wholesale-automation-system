import io
import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

PLATFORM_SIZES: dict = {
    "naver": (1000, 1000),
    "coupang": (1000, 1000),
    "thumbnail": (300, 300),
}

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


class ImageGenerator:
    """Generates product listing images using Pillow."""

    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _try_get_font(self, size: int) -> ImageFont.ImageFont:
        """Try to load a CJK-capable font, fall back to default."""
        font_paths = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/AppleGothic.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def generate_product_image(
        self,
        product_name: str,
        price: int,
        image_url: Optional[str] = None,
        width: int = 1000,
        height: int = 1000,
    ) -> Image.Image:
        """Generate a product listing image with name and price overlay."""
        img = self.create_transparent_background(width, height)
        # Fill with white background
        bg = Image.new("RGB", (width, height), color=(255, 255, 255))
        bg.paste(img, (0, 0), mask=img.split()[3] if img.mode == "RGBA" else None)
        img = bg

        # Draw gradient band at bottom
        draw = ImageDraw.Draw(img)
        band_height = int(height * 0.20)
        for y in range(band_height):
            alpha = int(200 * y / band_height)
            draw.rectangle(
                [(0, height - band_height + y), (width, height - band_height + y)],
                fill=(30, 30, 30, alpha),
            )

        img = self.add_price_overlay(img, price)
        title_font = self._try_get_font(36)
        draw = ImageDraw.Draw(img)
        truncated = product_name[:30] + ("…" if len(product_name) > 30 else "")
        draw.text((40, 40), truncated, fill=(50, 50, 50), font=title_font)
        logger.info(f"Generated image for '{product_name}' price={price}")
        return img

    def create_transparent_background(self, width: int, height: int) -> Image.Image:
        """Create a transparent RGBA image."""
        return Image.new("RGBA", (width, height), (255, 255, 255, 0))

    def add_price_overlay(self, image: Image.Image, price: int) -> Image.Image:
        """Add a price label in Korean Won to the bottom of the image."""
        img = image.convert("RGB")
        draw = ImageDraw.Draw(img)
        font = self._try_get_font(48)
        price_text = f"{price:,}원"
        w, h = img.size
        # Draw semi-transparent rectangle
        draw.rectangle([(0, h - 80), (w, h)], fill=(30, 30, 30))
        draw.text((30, h - 68), price_text, fill=(255, 215, 0), font=font)
        return img

    def add_watermark(self, image: Image.Image, text: str = "wholesale") -> Image.Image:
        """Add a diagonal watermark to the image."""
        img = image.convert("RGBA")
        watermark = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        font = self._try_get_font(60)
        w, h = img.size
        draw.text(
            (w // 4, h // 2),
            text,
            fill=(200, 200, 200, 80),
            font=font,
        )
        combined = Image.alpha_composite(img, watermark)
        return combined.convert("RGB")

    def resize_for_platform(self, image: Image.Image, platform: str) -> Image.Image:
        """Resize image to the required platform dimensions."""
        size = PLATFORM_SIZES.get(platform.lower(), (1000, 1000))
        return image.resize(size, Image.LANCZOS)

    def save_image(self, image: Image.Image, filename: str) -> str:
        """Save image to the output directory and return the path."""
        from utils.helpers import sanitize_filename
        safe_name = sanitize_filename(filename)
        if not safe_name.lower().endswith((".jpg", ".jpeg", ".png")):
            safe_name += ".jpg"
        path = self.output_dir / safe_name
        image.convert("RGB").save(str(path), "JPEG", quality=90)
        logger.info(f"Image saved: {path}")
        return str(path)

    def batch_generate(self, products_list: List[dict]) -> List[str]:
        """Generate and save images for a list of products."""
        paths = []
        for product in products_list:
            name = product.get("name", "Unknown Product")
            price = product.get("selling_price", product.get("price", 0))
            image_url = product.get("image_url")
            img = self.generate_product_image(name, price, image_url)
            filename = f"{name[:40]}_{price}.jpg"
            path = self.save_image(img, filename)
            paths.append(path)
        logger.info(f"Batch generated {len(paths)} images")
        return paths

    def get_image_bytes(self, image: Image.Image, fmt: str = "JPEG") -> bytes:
        """Return image as bytes (for uploading without saving to disk)."""
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format=fmt, quality=90)
        return buf.getvalue()
