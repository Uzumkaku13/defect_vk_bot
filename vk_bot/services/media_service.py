from __future__ import annotations

import mimetypes
import uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageOps

from config import MEDIA_DIR

MAX_IMAGE_SIDE = 1800
JPEG_QUALITY = 68


def _guess_extension(url: str, content_type: str | None) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
        return suffix
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed:
            return guessed
    return ".jpg"


def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in {"RGB", "L"}:
        return image.convert("RGB")
    background = Image.new("RGB", image.size, (255, 255, 255))
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    background.paste(image, mask=image.split()[-1])
    return background


def _compress_image(raw_bytes: bytes) -> bytes:
    with Image.open(BytesIO(raw_bytes)) as img:
        img = ImageOps.exif_transpose(img)
        img = _flatten_to_rgb(img)
        img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
        out = BytesIO()
        img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        return out.getvalue()


def download_image(url: str, prefix: str = "defect") -> str:
    response = requests.get(url, timeout=120)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type")
    _guess_extension(url, content_type)
    filename = f"{prefix}_{uuid.uuid4().hex}.jpg"
    target = MEDIA_DIR / filename

    try:
        compressed = _compress_image(response.content)
        target.write_bytes(compressed)
    except Exception:
        target.write_bytes(response.content)
    return str(target)
