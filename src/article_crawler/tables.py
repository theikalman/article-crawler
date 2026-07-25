"""Rasterize HTML <table> elements in extracted article content into PNG
images, since EPUB readers render tables inconsistently (overflowing
columns, unreadable borders on small screens).
"""

from bs4 import BeautifulSoup
import sys

from article_crawler.images import ImageAsset

TABLE_PAGE_TEMPLATE = """<html><head><style>
  body {{ margin: 0; padding: 12px; background: white;
          font-family: -apple-system, Helvetica, Arial, sans-serif; }}
  table {{ border-collapse: collapse; }}
  td, th {{ border: 1px solid #333; padding: 6px 10px; text-align: left;
            font-size: 16px; white-space: nowrap; }}
  th {{ background: #eee; }}
</style></head><body>{table_html}</body></html>"""


def _normalize_table_elements(soup: BeautifulSoup) -> None:
    """trafilatura's HTML output represents table rows/cells as non-standard
    <row>/<cell> tags rather than <tr>/<td>/<th>. Browsers treat unknown tags
    as plain inline elements with no box, so a table built from them has zero
    size and never becomes "visible" - rewrite them to real table markup.
    """
    for row in soup.find_all("row"):
        row.name = "tr"
    for cell in soup.find_all("cell"):
        cell.name = "th" if cell.get("role") == "head" else "td"


def render_tables(html: str, prefix: str = "img") -> tuple[str, list[ImageAsset]]:
    soup = BeautifulSoup(html, "html.parser")
    _normalize_table_elements(soup)

    # Only render top-level tables - a nested <table> is already captured as
    # part of its ancestor's screenshot.
    tables = [table for table in soup.find_all("table") if table.find_parent("table") is None]
    if not tables:
        return html, []

    print(f"Rendering {len(tables)} table(s)...", file=sys.stderr)
    print(TABLE_PAGE_TEMPLATE.format(table_html=str(tables[0])), file=sys.stderr)
    print("...", file=sys.stderr)

    images: list[ImageAsset] = []
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(device_scale_factor=2)
            for index, table in enumerate(tables, start=1):
                page.set_content(TABLE_PAGE_TEMPLATE.format(table_html=str(table)))
                element = page.query_selector("table")
                screenshot = element.screenshot()

                file_name = f"images/{prefix}_table_{index:03d}.png"
                images.append(
                    ImageAsset(file_name=file_name, media_type="image/png", content=screenshot)
                )

                img_tag = soup.new_tag("img", src=file_name, alt="Table")
                table.replace_with(img_tag)
        finally:
            browser.close()

    return str(soup), images
