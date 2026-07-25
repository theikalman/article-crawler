"""Download images referenced inside extracted article HTML.

Rewrites each <img> src to a local path so the bytes can be embedded directly
into the EPUB, keeping every image in its original position in the text.
"""

import base64
import binascii
import mimetypes
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from article_crawler.fetcher import DEFAULT_HEADERS

DEFAULT_EXTENSION = ".jpg"
DEFAULT_MEDIA_TYPE = "image/jpeg"

# Lazy-loading libraries stash the real image behind these before "src".
_SOURCE_ATTRS = ("data-src", "data-lazy-src", "data-original", "src")


@dataclass
class ImageAsset:
    file_name: str
    media_type: str
    content: bytes


def _resolve_source(img) -> str | None:
    for attr in _SOURCE_ATTRS:
        value = img.get(attr)
        if value and not value.startswith("data:image/svg"):
            return value

    for attr in ("srcset", "data-srcset"):
        srcset = img.get(attr)
        if srcset:
            candidates = [c.strip().split(" ")[0] for c in srcset.split(",") if c.strip()]
            if candidates:
                return candidates[-1]

    return None


def _guess_extension(url: str, media_type: str | None) -> str:
    if media_type:
        ext = mimetypes.guess_extension(media_type.split(";")[0].strip())
        if ext:
            return ".jpg" if ext == ".jpe" else ext

    ext = mimetypes.guess_type(urlparse(url).path)[0]
    if ext:
        guessed = mimetypes.guess_extension(ext)
        if guessed:
            return ".jpg" if guessed == ".jpe" else guessed

    return DEFAULT_EXTENSION


def download_images(
    html: str, base_url: str, prefix: str = "img"
) -> tuple[str, list[ImageAsset]]:
    soup = BeautifulSoup(html, "html.parser")
    images: list[ImageAsset] = []

    # trafilatura's HTML output represents images as <graphic src="...">
    # rather than standard <img>; normalize to <img> either way.
    for index, img in enumerate(soup.find_all(["img", "graphic"]), start=1):
        source = _resolve_source(img)
        if not source:
            img.decompose()
            continue

        if source.startswith("data:"):
            header, _, encoded = source.partition(",")
            if not encoded:
                img.decompose()
                continue
            media_type = header.removeprefix("data:").split(";")[0] or DEFAULT_MEDIA_TYPE
            try:
                content = base64.b64decode(encoded)
            except (ValueError, binascii.Error):
                img.decompose()
                continue
            ext = _guess_extension(source, media_type)
        else:
            absolute_url = urljoin(base_url, source)
            try:
                response = requests.get(absolute_url, headers=DEFAULT_HEADERS, timeout=15)
                response.raise_for_status()
            except requests.RequestException:
                img.decompose()
                continue
            content = response.content
            media_type = response.headers.get("Content-Type", DEFAULT_MEDIA_TYPE).split(";")[0].strip()
            ext = _guess_extension(absolute_url, media_type)

        file_name = f"images/{prefix}_{index:03d}{ext}"
        images.append(ImageAsset(file_name=file_name, media_type=media_type or DEFAULT_MEDIA_TYPE, content=content))

        for attr in list(img.attrs):
            if attr not in ("alt", "title"):
                del img[attr]
        img["src"] = file_name
        img.name = "img"

    return str(soup), images
