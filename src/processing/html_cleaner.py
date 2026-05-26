"""Extract clean text from HTML using BeautifulSoup."""

from __future__ import annotations

from bs4 import BeautifulSoup

from src.utils.text import clean_title, normalize_whitespace

REMOVE_TAGS = ("script", "style", "header", "nav", "footer")
KEEP_TAGS = ("article", "h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "code")


def extract_title_and_content(html_text: str) -> tuple[str, str]:
    """Extract a cleaned title and content body from an HTML document."""
    soup = BeautifulSoup(html_text, "html.parser")

    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    raw_title = soup.title.get_text(" ", strip=True) if soup.title else ""
    title = clean_title(raw_title)

    blocks: list[str] = []
    for tag in soup.find_all(KEEP_TAGS):
        text = normalize_whitespace(tag.get_text(" ", strip=True))
        if text:
            blocks.append(text)

    content = "\n".join(blocks).strip()
    return title, content

