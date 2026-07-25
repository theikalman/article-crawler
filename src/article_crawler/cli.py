"""Command-line entry point: fetch article URLs and write an EPUB."""

import argparse
import sys
from pathlib import Path

from article_crawler.epub_builder import build_epub
from article_crawler.extractor import extract_article
from article_crawler.fetcher import fetch_html, fetch_rendered_html


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch one or more article URLs and bundle them into an EPUB."
    )
    parser.add_argument("urls", nargs="*", default=[], help="Article URL(s) to fetch")
    parser.add_argument(
        "-f",
        "--url-file",
        type=Path,
        help=(
            "Path to a text file with one article URL per line. Blank lines and "
            "lines starting with # are ignored. Can be combined with URLs given "
            "directly on the command line."
        ),
    )
    parser.add_argument(
        "-o", "--output", default="output.epub", type=Path, help="Path to the output EPUB file"
    )
    parser.add_argument(
        "-t", "--title", default="Article Collection", help="Title for the generated EPUB"
    )
    parser.add_argument(
        "--no-render",
        dest="render",
        action="store_false",
        default=True,
        help=(
            "Skip the headless browser and fetch with a plain HTTP request instead. "
            "Faster, but misses images/content that a site lazy-loads with JavaScript."
        ),
    )
    parser.add_argument(
        "--settle-time",
        type=float,
        default=3.0,
        help="Seconds to wait after scrolling for lazy-loaded content to finish loading (ignored with --no-render)",
    )
    return parser.parse_args(argv)


def read_url_file(path: Path) -> list[str]:
    urls = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    urls = list(args.urls)
    if args.url_file:
        urls.extend(read_url_file(args.url_file))

    if not urls:
        print("No URLs given. Pass URLs directly or with --url-file.", file=sys.stderr)
        return 1

    articles = []
    for index, url in enumerate(urls, start=1):
        print(f"Fetching {url}...", file=sys.stderr)
        if args.render:
            html = fetch_rendered_html(url, settle_time=args.settle_time)
        else:
            html = fetch_html(url)
        articles.append(extract_article(html, url, image_prefix=f"a{index}"))

    build_epub(articles, args.output, book_title=args.title)
    print(f"Wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
