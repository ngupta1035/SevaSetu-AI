import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

ALLOWED = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_BYTES = 8 * 1024 * 1024


async def validate_image_bytes(file: UploadFile) -> tuple[bytes, str]:
    """Check type, size and that the bytes are a real image. Returns (data, suffix)."""
    if file.content_type not in ALLOWED:
        raise HTTPException(415, "Only JPEG, PNG or WEBP images are allowed")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image too large (max 8 MB)")
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "File is not a valid image")
    return data, ALLOWED[file.content_type]


async def save_image(file: UploadFile) -> tuple[str, str]:
    """Validate and store an upload. Returns (public_url, disk_path)."""
    data, suffix = await validate_image_bytes(file)
    folder = Path(settings.UPLOAD_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{suffix}"
    path = folder / name
    path.write_bytes(data)
    return f"/uploads/{name}", str(path)
