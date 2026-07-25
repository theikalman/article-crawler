"""Extract the main article content from raw HTML."""

from dataclasses import dataclass, field

import lxml.html
import trafilatura
from bs4 import BeautifulSoup
from trafilatura.metadata import extract_title as _extract_title_from_tree

from article_crawler.images import ImageAsset, download_images
from article_crawler.tables import render_tables


@dataclass
class Article:
    url: str
    title: str
    author: str | None
    date: str | None
    content_html: str
    images: list[ImageAsset] = field(default_factory=list)


def _normalize_code_elements(html: str) -> str:
    """Fix trafilatura's HTML output, which represents both inline code
    (<code>) and code blocks (<pre><code>) as <pre>, causing every inline
    snippet to render on its own line in EPUB readers.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Collapse the <pre><pre>...</pre></pre> wrapping trafilatura emits for
    # what was originally a <pre><code> block.
    for pre in soup.find_all("pre"):
        inner = pre.find("pre", recursive=False)
        if inner is not None and len(pre.contents) == 1:
            inner.unwrap()

    # Anything left without an internal newline was inline <code>, not a
    # <pre> block - convert it back so it stays inline in the flow of text.
    for pre in soup.find_all("pre"):
        if "\n" not in pre.get_text():
            pre.name = "code"

    return str(soup)


def _resolve_title(html: str, metadata) -> str | None:
    """Pick the article title.

    trafilatura.extract_metadata() prefers og:title/twitter:title over the
    page's own <h1>/<title>, but some sites set those social-preview tags to
    the site name instead of the article title. The page's <h1>/<title> is
    what a reader actually sees, so prefer it and only fall back to the
    metadata-derived title when no h1/title tag is present.
    """
    tree_title = _extract_title_from_tree(lxml.html.fromstring(html))
    if tree_title:
        return tree_title
    return metadata.title if metadata else None


def extract_article(html: str, url: str, image_prefix: str = "img") -> Article:
    metadata = trafilatura.extract_metadata(html, default_url=url)
    content_html = trafilatura.extract(
        html,
        url=url,
        output_format="html",
        include_images=True,
        include_links=False,
    )

    if not content_html:
        raise ValueError(f"Could not extract article content from {url}")

    content_html = _normalize_code_elements(content_html)
    content_html, images = download_images(content_html, base_url=url, prefix=image_prefix)
    content_html, table_images = render_tables(content_html, prefix=image_prefix)
    images += table_images

    return Article(
        url=url,
        title=_resolve_title(html, metadata) or url,
        author=metadata.author if metadata else None,
        date=metadata.date if metadata else None,
        content_html=content_html,
        images=images,
    )
