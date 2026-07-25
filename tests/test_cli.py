from article_crawler.cli import parse_args, read_url_file


def test_read_url_file_skips_blank_lines_and_comments(tmp_path):
    url_file = tmp_path / "urls.txt"
    url_file.write_text(
        "\n".join(
            [
                "https://example.com/one",
                "",
                "# a comment",
                "https://example.com/two  ",
                "   ",
            ]
        )
    )

    assert read_url_file(url_file) == [
        "https://example.com/one",
        "https://example.com/two",
    ]


def test_parse_args_combines_positional_urls_and_url_file(tmp_path):
    url_file = tmp_path / "urls.txt"
    url_file.write_text("https://example.com/from-file\n")

    args = parse_args(
        ["https://example.com/direct", "--url-file", str(url_file), "-o", "book.epub"]
    )

    assert args.urls == ["https://example.com/direct"]
    assert args.url_file == url_file
