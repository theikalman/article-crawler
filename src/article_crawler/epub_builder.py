"""Build an EPUB file from one or more extracted articles."""

import base64
import re
from datetime import datetime
from html import escape
from pathlib import Path

import ebooklib
from ebooklib import epub

from article_crawler.extractor import Article

# Explicit placeholder in the cover SVG, e.g. `{{DATE_HERE}}`.
_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*DATE_HERE\s*\}\}")
# Matches the SVG viewBox to size the rasterized cover.
_VIEWBOX_PATTERN = re.compile(r'viewBox="0\s+0\s+(\d+)\s+(\d+)"')


def _cover_date_string(when: datetime | None = None) -> str:
    """Return today's date formatted with a leading-zero day, e.g. "25 July 2026"."""
    when = when or datetime.now()
    return f"{when:%d %B %Y}"


def _subst_cover_date(svg_content: str, date_string: str, svg_path: Path) -> str:
    """Replace the `{{DATE_HERE}}` placeholder in ``svg_content`` with ``date_string``."""
    if not _PLACEHOLDER_PATTERN.search(svg_content):
        raise ValueError(
            f"Cover SVG {svg_path} has no date placeholder; "
            "expected a footer like '{{DATE_HERE}}'."
        )
    return _PLACEHOLDER_PATTERN.sub(date_string, svg_content, count=1)


def _rasterize_svg(svg_content: bytes) -> bytes:
    """Render an SVG to PNG bytes using the already-installed Playwright/Chromium.

    Most e-readers won't display an SVG cover, so we rasterize to PNG for the
    embedded ``cover-image``. Falls back to returning the raw SVG if Chromium
    can't be launched.
    """
    match = _VIEWBOX_PATTERN.search(svg_content.decode("utf-8", errors="replace"))
    width, height = (int(match.group(1)), int(match.group(2))) if match else (1600, 2560)

    from playwright.sync_api import Error as PlaywrightError, sync_playwright

    data_url = "data:image/svg+xml;base64," + base64.b64encode(svg_content).decode("ascii")
    html = (
        f"<!doctype html><html><head><style>"
        f"html,body{{margin:0;padding:0;background:transparent;overflow:hidden;}}"
        f"img{{display:block;width:{width}px;height:{height}px;}}"
        f"</style></head><body><img src='{data_url}'/></body></html>"
    )

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.set_content(html, wait_until="load")
                return page.screenshot(type="png", omit_background=False, scale="device")
            finally:
                browser.close()
    except PlaywrightError:
        return svg_content


def build_epub(
    articles: list[Article],
    output_path: Path,
    book_title: str = "Article Collection",
    cover_path: Path | None = None,
    cover_date: str | None = None,
) -> None:
    book = epub.EpubBook()
    book.set_identifier(f"article-crawler-{abs(hash(book_title))}")
    book.set_title(book_title)
    book.set_language("en")

    if cover_path is not None:
        date_string = cover_date or _cover_date_string()
        svg_content = _subst_cover_date(
            cover_path.read_text(encoding="utf-8"), date_string, cover_path
        ).encode("utf-8")
        cover_png = _rasterize_svg(svg_content)
        is_png = cover_png[:8] == b"\x89PNG\r\n\x1a\n"
        cover_file_name = "cover.png" if is_png else cover_path.name
        cover_media_type = "image/png" if is_png else "image/svg+xml"
        book.set_cover(cover_file_name, cover_png, create_page=True)
        # ebooklib assumes JPEG for covers; force the real media type.
        for item in book.get_items_of_type(ebooklib.ITEM_COVER):
            if item.file_name == cover_file_name:
                item.media_type = cover_media_type
                break

    chapters = []
    for index, article in enumerate(articles, start=1):
        chapter = epub.EpubHtml(
            title=article.title,
            file_name=f"chap_{index:03d}.xhtml",
            lang="en",
        )
        byline = f"<p><em>{article.author}</em></p>" if article.author else ""
        source_link = f'<p><a href="{escape(article.url)}">{escape(article.url)}</a></p>'
        chapter.content = f"<h1>{article.title}</h1>{byline}{article.content_html}{source_link}"
        book.add_item(chapter)
        chapters.append(chapter)

        for image in article.images:
            book.add_item(
                epub.EpubItem(
                    uid=image.file_name,
                    file_name=image.file_name,
                    media_type=image.media_type,
                    content=image.content,
                )
            )

    book.toc = chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    spine = []
    if cover_path is not None:
        spine.append("cover")
    spine.append("nav")
    spine.extend(chapters)
    book.spine = spine

    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book)
