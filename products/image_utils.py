"""
Image processing helpers for product photos.

Goal: every product image — regardless of what size/shape/format a seller
uploads — ends up as a consistently-sized, compressed JPEG. That means:
  - the product grid never jitters or reflows while images load (fixed
    aspect ratio, capped file size)
  - large phone-camera photos (often 4-8MB) get shrunk to a sane size
    so pages load fast instead of lagging
"""
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.base import ContentFile

# Every processed image is resized to fit within this box (aspect ratio kept,
# never upscaled) and re-saved as an optimized JPEG at this quality.
MAX_DIMENSION = (1000, 1000)
JPEG_QUALITY = 82


def optimize_image_field(image_field, filename_hint="image.jpg", max_dimension=None):
    """
    Given a Django ImageFieldFile (already saved to storage), re-process it
    in place: fix orientation, flatten transparency onto white, downscale to
    fit max_dimension (defaults to MAX_DIMENSION), and re-save as an
    optimized JPEG.

    Returns True if it processed successfully, False if it skipped (e.g. the
    file couldn't be read as an image) — callers should not treat False as
    fatal, since the original upload is still on disk either way.
    """
    if not image_field:
        return False

    max_dimension = max_dimension or MAX_DIMENSION

    try:
        image_field.open()
        img = Image.open(image_field)
        img.load()
    except Exception:
        return False

    # Respect EXIF orientation from phone cameras before anything else
    img = ImageOps.exif_transpose(img)

    # Flatten transparency (PNGs, etc.) onto a white background so JPEG
    # conversion doesn't turn transparent areas black
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        rgba = img.convert("RGBA")
        background.paste(rgba, mask=rgba.split()[-1])
        img = background
    else:
        img = img.convert("RGB")

    # Downscale to fit within max_dimension; thumbnail() never upscales
    img.thumbnail(max_dimension, Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    buffer.seek(0)

    base_name = filename_hint.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    new_name = f"{base_name}.jpg"

    # save(..., save=False) writes the new file content but we call the
    # model's own .save() afterward to avoid infinite recursion
    image_field.save(new_name, ContentFile(buffer.read()), save=False)
    return True
