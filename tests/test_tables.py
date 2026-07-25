from article_crawler.tables import render_tables

FAKE_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-table-screenshot"

HTML_WITH_TABLE = """
<p>Some text before the table.</p>
<table><tr><th>Name</th><th>Value</th></tr><tr><td>A</td><td>1</td></tr></table>
<p>Some text after the table.</p>
"""

HTML_WITHOUT_TABLE = "<p>No tables here.</p>"

# trafilatura's actual HTML output represents rows/cells with these
# non-standard tags rather than <tr>/<td>/<th>.
HTML_WITH_TRAFILATURA_TABLE = """
<p>before</p>
<table>
  <row><cell role="head">Name</cell><cell role="head">Value</cell></row>
  <row><cell>Alpha</cell><cell>1</cell></row>
</table>
<p>after</p>
"""


class FakeElement:
    def screenshot(self):
        return FAKE_PNG_BYTES


class FakePage:
    def set_content(self, html):
        self.html = html

    def query_selector(self, selector):
        assert selector == "table"
        return FakeElement()


class FakeBrowser:
    def new_page(self, device_scale_factor=None):
        return FakePage()

    def close(self):
        pass


class FakeChromium:
    def launch(self):
        return FakeBrowser()


class FakePlaywright:
    chromium = FakeChromium()


class FakeSyncPlaywright:
    def __enter__(self):
        return FakePlaywright()

    def __exit__(self, *args):
        pass


def fake_sync_playwright():
    return FakeSyncPlaywright()


def test_render_tables_replaces_table_with_image(monkeypatch):
    import playwright.sync_api

    monkeypatch.setattr(playwright.sync_api, "sync_playwright", fake_sync_playwright)

    rewritten_html, assets = render_tables(HTML_WITH_TABLE, prefix="a1")

    assert len(assets) == 1
    assert assets[0].content == FAKE_PNG_BYTES
    assert assets[0].media_type == "image/png"
    assert assets[0].file_name == "images/a1_table_001.png"

    assert "<table>" not in rewritten_html
    before_index = rewritten_html.index("before the table")
    img_index = rewritten_html.index("images/a1_table_001.png")
    after_index = rewritten_html.index("after the table")
    assert before_index < img_index < after_index


def test_render_tables_noop_without_table():
    rewritten_html, assets = render_tables(HTML_WITHOUT_TABLE)

    assert assets == []
    assert rewritten_html.strip() == HTML_WITHOUT_TABLE.strip() or "No tables here" in rewritten_html


def test_render_tables_normalizes_trafilatura_row_cell_tags(monkeypatch):
    import playwright.sync_api

    captured_html = []

    class CapturingFakePage(FakePage):
        def set_content(self, html):
            super().set_content(html)
            captured_html.append(html)

    class CapturingFakeBrowser(FakeBrowser):
        def new_page(self, device_scale_factor=None):
            return CapturingFakePage()

    class CapturingFakeChromium(FakeChromium):
        def launch(self):
            return CapturingFakeBrowser()

    class CapturingFakePlaywright(FakePlaywright):
        chromium = CapturingFakeChromium()

    class CapturingFakeSyncPlaywright(FakeSyncPlaywright):
        def __enter__(self):
            return CapturingFakePlaywright()

    monkeypatch.setattr(
        playwright.sync_api, "sync_playwright", lambda: CapturingFakeSyncPlaywright()
    )

    rewritten_html, assets = render_tables(HTML_WITH_TRAFILATURA_TABLE, prefix="a1")

    assert len(assets) == 1
    assert "<row" not in captured_html[0]
    assert "<cell" not in captured_html[0]
    assert "<tr>" in captured_html[0]
    assert "<th" in captured_html[0]
    assert "<td>" in captured_html[0]

    before_index = rewritten_html.index("before")
    img_index = rewritten_html.index("images/a1_table_001.png")
    after_index = rewritten_html.index("after")
    assert before_index < img_index < after_index


def test_render_tables_skips_nested_tables(monkeypatch):
    import playwright.sync_api

    monkeypatch.setattr(playwright.sync_api, "sync_playwright", fake_sync_playwright)

    html = "<table><tr><td><table><tr><td>inner</td></tr></table></td></tr></table>"
    rewritten_html, assets = render_tables(html, prefix="a1")

    assert len(assets) == 1
    assert rewritten_html.count("<img") == 1
