# article-crawler

Fetch articles from the web and turn them into EPUB files you can read on any e-reader.

## How it works

1. `fetcher.py` downloads the HTML for a URL. By default it renders the page
   in a real headless browser (Playwright/Chromium) and scrolls it in steps so
   viewport-triggered lazy loaders fire before the HTML is captured; pass
   `--no-render` to skip the browser and do a plain, faster HTTP request
   instead.
2. `extractor.py` uses [trafilatura](https://trafilatura.readthedocs.io/) to
   pull out the article's title, author, date, and main content, stripping ads,
   nav bars, and other clutter.
3. `images.py` downloads every image referenced in the extracted content
   (including lazy-loaded and base64-inlined images) and rewrites each `<img>`
   src to a local file, keeping images in their original position relative to
   the surrounding text. Images that fail to download are dropped rather than
   left as broken links.
4. `epub_builder.py` uses [ebooklib](https://github.com/aerkalov/ebooklib) to
   package one or more extracted articles, plus their downloaded images, into a
   single EPUB file, with each article as its own chapter and a table of
   contents linking to every one of them.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

## Usage

```bash
article-crawler https://example.com/some-article -o my-article.epub
```

By default every URL is fetched through a headless browser that scrolls the
page first, so lazy-loaded images (common on course platforms, SPAs, etc.)
actually appear in the HTML before extraction. This is slower than a plain
HTTP fetch; pass `--no-render` to opt out for sites that don't need it:

```bash
article-crawler --no-render https://example.com/plain-static-article -o my-article.epub
```

`--settle-time` (default `3.0` seconds) controls how long to wait after
scrolling for lazy-loaded content to finish loading; raise it for slower
sites (ignored with `--no-render`).

Fetch multiple articles into one EPUB, with a table of contents linking to
each one:

```bash
article-crawler https://example.com/article-1 https://example.com/article-2 \
  -o collection.epub -t "My Reading List"
```

Or read the URLs from a file instead (one URL per line; blank lines and lines
starting with `#` are ignored):

```bash
article-crawler --url-file urls.txt -o collection.epub -t "My Reading List"
```

`--url-file` can be combined with URLs passed directly on the command line.

## Development

Run tests:

```bash
pytest
```
