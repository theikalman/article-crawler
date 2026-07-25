from article_crawler import images as images_module
from article_crawler.images import download_images

FAKE_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-image-data"

HTML_WITH_IMAGE = """
<p>Some text before the image.</p>
<img src="/static/diagram.png" alt="A diagram">
<p>Some text after the image.</p>
"""


class FakeResponse:
    content = FAKE_PNG_BYTES
    headers = {"Content-Type": "image/png"}

    def raise_for_status(self):
        pass


def test_download_images_rewrites_src_and_keeps_position(monkeypatch):
    calls = []

    def fake_get(url, headers=None, timeout=None):
        calls.append(url)
        return FakeResponse()

    monkeypatch.setattr(images_module.requests, "get", fake_get)

    rewritten_html, assets = download_images(
        HTML_WITH_IMAGE, base_url="https://example.com/article", prefix="a1"
    )

    assert calls == ["https://example.com/static/diagram.png"]
    assert len(assets) == 1
    assert assets[0].content == FAKE_PNG_BYTES
    assert assets[0].media_type == "image/png"
    assert assets[0].file_name == "images/a1_001.png"

    before_index = rewritten_html.index("before the image")
    img_index = rewritten_html.index("images/a1_001.png")
    after_index = rewritten_html.index("after the image")
    assert before_index < img_index < after_index


HTML_WITH_GRAPHIC_TAG = """
<p>Some text before the image.</p>
<graphic src="/static/diagram.png"/>
<p>Some text after the image.</p>
"""


def test_download_images_normalizes_graphic_tag_to_img(monkeypatch):
    monkeypatch.setattr(
        images_module.requests, "get", lambda url, headers=None, timeout=None: FakeResponse()
    )

    rewritten_html, assets = download_images(
        HTML_WITH_GRAPHIC_TAG, base_url="https://example.com/article"
    )

    assert len(assets) == 1
    assert "<graphic" not in rewritten_html
    assert '<img src="images/img_001.png"' in rewritten_html


def test_download_images_drops_image_on_failure(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        raise images_module.requests.RequestException("boom")

    monkeypatch.setattr(images_module.requests, "get", fake_get)

    rewritten_html, assets = download_images(
        HTML_WITH_IMAGE, base_url="https://example.com/article"
    )

    assert assets == []
    assert "<img" not in rewritten_html
