import asyncio
import base64
import hashlib
import io
import os

import flet as ft
import requests
from PIL import Image as PILImage

from config import PRIMARY, SURFACE_COLOR, TIMEOUT

IMAGE_CACHE_LIMIT = 160

# (url, max_width) -> base64 data URI, kept for the life of the process
_image_cache = {}

# Pages with a batched image update already scheduled
_pending_updates = set()

# Transparent 1x1 GIF used as the src of a photo that is still downloading, so
# the control paints nothing instead of a broken-image icon (which is what made
# the grid look like it was blinking while it filled in).
_BLANK_PIXEL = (
    "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)

# Disk cache directory — same folder Flet already uses for product images
_DISK_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    ".flet", "storage", "cache", "product-images",
)
os.makedirs(_DISK_CACHE_DIR, exist_ok=True)


def _disk_cache_path(url: str, max_width) -> str:
    """Return the file path for the cached image of *url* at *max_width*.

    The width is part of the key so a card thumbnail (360) never reuses the
    full-size copy downloaded for the detail sheet (720) — smaller payloads to
    the client and no over-sized data URI in transit.
    """
    key = hashlib.sha256(f"{url}|{max_width}".encode()).hexdigest()
    return os.path.join(_DISK_CACHE_DIR, f"{key}.jpg")


def _remember(key, data_uri):
    if len(_image_cache) >= IMAGE_CACHE_LIMIT:
        _image_cache.pop(next(iter(_image_cache)))
    _image_cache[key] = data_uri


def _disk_data_uri(url, max_width):
    """Return the cached data URI for *url* from disk, or None.

    Reading a cached thumbnail is a local file read (well under a millisecond),
    so the image can be handed to the client with its final source on the very
    first frame. That avoids the visible flash that came from starting with a
    placeholder/direct URL and swapping the src after paint.
    """
    if not url or not max_width:
        return None
    try:
        with open(_disk_cache_path(url, max_width), "rb") as f:
            payload = f.read()
    except OSError:
        return None
    if not payload:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(payload).decode()


def _schedule_update(page):
    """Refresh the client once for a burst of finished image loads.

    Each downloaded image used to call page.update() on its own, so a grid of
    twenty cards sent twenty separate updates while it filled in.
    """
    if id(page) in _pending_updates:
        return
    _pending_updates.add(id(page))

    async def run():
        await asyncio.sleep(0.05)
        _pending_updates.discard(id(page))
        try:
            page.update()
        except Exception:
            pass

    page.run_task(run)

STATUS_LABELS = {
    "pending": ("Menunggu Bayar", ft.Colors.ORANGE_700),
    "paid": ("Menunggu Konfirmasi", ft.Colors.BLUE_600),
    "success": ("Selesai", ft.Colors.GREEN_600),
    "canceled": ("Dibatalkan", ft.Colors.RED_500),
    "expired": ("Kedaluwarsa", ft.Colors.GREY_500),
}

PAYMENT_LABELS = {
    "bank": "Transfer Bank (Midtrans)",
    "qris": "QRIS (Midtrans)",
    "muamalat": "Virtual Account Muamalat",
}

STATUS_GROUP = {
    "Menunggu": ["pending", "paid"],
    "Selesai": ["success"],
    "Lainnya": ["canceled", "expired"],
}


def status_text(status, size=13, weight=None):
    label, color = STATUS_LABELS.get(status, (status, ft.Colors.GREY))
    return ft.Text(
        label,
        size=size,
        color=color,
        weight=weight or ft.FontWeight.W_700,
    )


def _image_data_uri(url, max_width):
    """Return a base64 data URI for *url*, using disk + memory cache.

    Load order:
      1. In-memory cache  (fastest, same session)
      2. Disk cache       (fast, survives restarts)
      3. Network download (slow, then written to disk + memory)

    A data URI is used so the Flet web client can render images served from
    a host that doesn't send CORS headers.
    """
    key = (url, max_width)
    cached = _image_cache.get(key)
    if cached is not None:
        return cached

    cached = _disk_data_uri(url, max_width)
    if cached is not None:
        _remember(key, cached)
        return cached

    # Network download
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return None

    payload = response.content
    mime = "image/jpeg"
    try:
        picture = PILImage.open(io.BytesIO(payload))
        picture.load()
        mime = PILImage.MIME.get(picture.format or "", "image/jpeg")
        if max_width and picture.width > max_width:
            if picture.mode in ("RGBA", "LA", "P"):
                picture = picture.convert("RGBA")
                flattened = PILImage.new("RGB", picture.size, (255, 255, 255))
                flattened.paste(picture, mask=picture.split()[-1])
                picture = flattened
            height = max(1, round(picture.height * max_width / picture.width))
            buffer = io.BytesIO()
            picture.convert("RGB").resize(
                (max_width, height), PILImage.Resampling.LANCZOS
            ).save(buffer, format="JPEG", quality=82)
            payload = buffer.getvalue()
            mime = "image/jpeg"
    except Exception:
        pass  # fall back to the original bytes

    # Write to disk cache (best-effort)
    try:
        with open(_disk_cache_path(url, max_width), "wb") as f:
            f.write(payload)
    except OSError:
        pass

    data_uri = f"data:{mime};base64," + base64.b64encode(payload).decode()
    _remember(key, data_uri)
    return data_uri


def _image(max_width, src, **kwargs) -> ft.Image:
    """Image with the anti-flicker settings Flet documents for swapping src.

    gapless_playback keeps the previous frame on screen while a new source
    decodes (Flet: with it False "the image area can briefly be empty, causing
    a flicker/blink effect"), and the fade-in softens the final swap. Without
    these the grid visibly blinked every time a batch of cards was added.
    """
    return ft.Image(
        src=src,
        gapless_playback=True,
        cache_width=max_width,
        placeholder_src=_BLANK_PIXEL,
        fade_in_animation=ft.Animation(
            duration=ft.Duration(milliseconds=180),
            curve=ft.AnimationCurve.EASE_OUT,
        ),
        **kwargs,
    )


def product_image(
    page: ft.Page, url, max_width=480, fallback_width=None, **kwargs
) -> ft.Image:
    """Product photo that renders in every client, including Flet web mode.

    Product images live on the API host, whose static `/storage/*` files send no
    CORS header, so a browser refuses to load them for a Flet web client. The
    bytes are downloaded here (downscaled and cached) and handed to the control.

    The src is either final on the first frame (memory or disk cache) or left
    empty until the download finishes. It is never set to a filesystem path or
    to the remote URL, because both blink: the file path is unloadable in web
    mode and the remote URL is blocked by CORS, so each card showed the broken
    placeholder before the real bytes arrived.
    """
    if not url:
        return _image(max_width, _BLANK_PIXEL, **kwargs)

    key = (url, max_width)

    # 1. Already in memory — use it directly, no async needed
    cached = _image_cache.get(key)
    if cached is not None:
        return _image(max_width, cached, **kwargs)

    # 2. Already on disk — read the thumbnail now so the first paint has it
    cached = _disk_data_uri(url, max_width)
    if cached is not None:
        _remember(key, cached)
        return _image(max_width, cached, **kwargs)

    # 3. Cold at this size — show the smaller copy we already have (the grid
    # thumbnail, typically) instead of a blank box while the larger one loads.
    # Without this the detail sheet re-downloaded its own 720px copy and stayed
    # empty for as long as that took, even though the photo was already cached.
    placeholder = _BLANK_PIXEL
    if fallback_width:
        placeholder = (
            _image_cache.get((url, fallback_width))
            or _disk_data_uri(url, fallback_width)
            or _BLANK_PIXEL
        )

    image = _image(max_width, placeholder, **kwargs)

    async def load():
        data_uri = await asyncio.to_thread(_image_data_uri, url, max_width)
        if data_uri and image.src != data_uri:
            image.src = data_uri
            _schedule_update(page)

    page.run_task(load)
    return image


def status_badge(status, size=12):
    label, color = STATUS_LABELS.get(status, (status, ft.Colors.GREY))
    return ft.Container(
        bgcolor=ft.Colors.with_opacity(0.12, color),
        border_radius=20,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        content=ft.Row(
            [
                ft.Container(
                    width=5,
                    height=5,
                    border_radius=3,
                    bgcolor=color,
                ),
                ft.Text(
                    label,
                    size=size,
                    color=color,
                    weight=ft.FontWeight.W_700,
                ),
            ],
            spacing=5,
            tight=True,
        ),
    )
