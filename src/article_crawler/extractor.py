"""Extract the main article content from raw HTML."""

from dataclasses import dataclass, field

import trafilatura

from article_crawler.images import ImageAsset, download_images


@dataclass
class Article:
    url: str
    title: str
    author: str | None
    date: str | None
    content_html: str
    images: list[ImageAsset] = field(default_factory=list)


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

    content_html, images = download_images(content_html, base_url=url, prefix=image_prefix)

    return Article(
        url=url,
        title=(metadata.title if metadata else None) or url,
        author=metadata.author if metadata else None,
        date=metadata.date if metadata else None,
        content_html=content_html,
        images=images,
    )
