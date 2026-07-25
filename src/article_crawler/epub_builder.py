"""Build an EPUB file from one or more extracted articles."""

from pathlib import Path

from ebooklib import epub

from article_crawler.extractor import Article


def build_epub(articles: list[Article], output_path: Path, book_title: str = "Article Collection") -> None:
    book = epub.EpubBook()
    book.set_identifier(f"article-crawler-{abs(hash(book_title))}")
    book.set_title(book_title)
    book.set_language("en")

    chapters = []
    for index, article in enumerate(articles, start=1):
        chapter = epub.EpubHtml(
            title=article.title,
            file_name=f"chap_{index:03d}.xhtml",
            lang="en",
        )
        byline = f"<p><em>{article.author}</em></p>" if article.author else ""
        chapter.content = f"<h1>{article.title}</h1>{byline}{article.content_html}"
        book.add_item(chapter)
        chapters.append(chapter)

        for image in article.images:
            book.add_item(
                epub.EpubItem(
                    uid=image.file_name,
                    file_name=image.file_name,
                    media_type=image.media_type,
                    content=image.content,
                )
            )

    book.toc = chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", *chapters]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book)
