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


MISLEADING_OG_TITLE_HTML = """
<html>
<head>
<title>Actual Article Title</title>
<meta property="og:title" content="My Blog" />
<meta name="twitter:title" content="My Blog" />
</head>
<body>
<article>
<h1>Actual Article Title</h1>
<p>This is a sample paragraph with enough content to be recognized as an article body by the extraction library.</p>
<p>Here is a second paragraph to add more substance to the text.</p>
</article>
</body>
</html>
"""


def test_extract_article_prefers_page_title_over_misleading_og_title():
    article = extract_article(MISLEADING_OG_TITLE_HTML, "https://example.com/sample")

    assert article.title == "Actual Article Title"
