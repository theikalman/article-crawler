from article_crawler.extractor import extract_article

SAMPLE_HTML = """
<html>
<head><title>Sample Article</title></head>
<body>
<article>
<h1>Sample Article</h1>
<p>This is a sample paragraph with enough content to be recognized as an article body by the extraction library.</p>
<p>Here is a second paragraph to add more substance to the text.</p>
</article>
</body>
</html>
"""


def test_extract_article_returns_content():
    article = extract_article(SAMPLE_HTML, "https://example.com/sample")

    assert article.url == "https://example.com/sample"
    assert article.content_html
    assert "sample paragraph" in article.content_html
