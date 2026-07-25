"""Download HTML for a given article URL, either as a plain HTTP fetch or
rendered through a real browser for sites that lazy-load content with JS."""

import requests

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; article-crawler/0.1; "
        "+https://github.com/theikalman/article-crawler)"
    )
}


def fetch_html(url: str, timeout: int = 15) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def fetch_rendered_html(
    url: str,
    timeout: float = 30.0,
    scroll_pause: float = 1.0,
    settle_time: float = 3.0,
    max_scrolls: int = 60,
) -> str:
    """Render the page in a headless browser, scrolling to the bottom in
    steps so viewport-triggered lazy loaders (images, etc.) fire, then wait
    for things to settle before returning the final HTML.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(user_agent=DEFAULT_HEADERS["User-Agent"])
            try:
                page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
            except Exception:
                page.goto(url, timeout=timeout * 1000, wait_until="load")

            _scroll_to_bottom(page, scroll_pause, max_scrolls)
            page.wait_for_timeout(int(settle_time * 1000))

            return page.content()
        finally:
            browser.close()


def _scroll_to_bottom(page, pause: float, max_scrolls: int) -> None:
    previous_height = 0
    for _ in range(max_scrolls):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(int(pause * 1000))
        current_height = page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            break
        previous_height = current_height
    page.evaluate("window.scrollTo(0, 0)")
