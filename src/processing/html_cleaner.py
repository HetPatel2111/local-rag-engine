"""Convert HTML pages into clean Markdown knowledge-base documents."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from src.utils.text import clean_title, normalize_whitespace

REMOVE_TAGS = {"script", "style", "header", "nav", "footer", "button", "form", "svg", "noscript"}
NOISE_TERMS = (
    "banner",
    "marketing",
    "promo",
    "testimonial",
    "testimonials",
    "announcement",
    "announcements",
    "replay",
    "replays",
    "conference",
    "signup",
    "newsletter",
    "cookie",
    "sponsor",
    "sponsored",
    "advert",
)
BLOCK_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "ul", "ol", "blockquote"}

_HEADING_RE = re.compile(r"^h([1-6])$")


@dataclass(frozen=True)
class MarkdownPage:
    """A markdown page ready for knowledge-base storage."""

    url: str
    title: str
    created_at: str
    markdown: str
    category: str
    slug: str


def _is_noise_tag(tag: Tag) -> bool:
    """Return True if the element looks like site chrome or marketing content."""
    if getattr(tag, "attrs", None) is None:
        return False

    haystack = " ".join(
        [
            tag.get("id", ""),
            " ".join(tag.get("class", [])) if isinstance(tag.get("class", []), list) else str(tag.get("class", "")),
        ]
    ).lower()
    return any(term in haystack for term in NOISE_TERMS)


def _remove_noise_nodes(soup: BeautifulSoup) -> None:
    """Remove tags that do not belong in the knowledge base."""
    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in list(soup.find_all(True)):
        if getattr(tag, "attrs", None) is None:
            continue
        if _is_noise_tag(tag):
            tag.decompose()


def _choose_root(soup: BeautifulSoup) -> Tag:
    """Pick the most relevant content container."""
    return (
        soup.find("article")
        or soup.find("main")
        or soup.find("body")
        or soup
    )


def _slug_from_url(url: str) -> str:
    """Build a deterministic file slug from the URL path."""
    parsed = urlparse(url)
    path = parsed.path.strip("/") or "index"
    slug = path.replace("/", "__")
    slug = re.sub(r"[^a-zA-Z0-9_\-\.]+", "_", slug)
    return slug.strip("_") or "index"


def _category_from_url(url: str) -> str:
    """Map URLs into the knowledge-base folder structure."""
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        return "index"
    first = parts[0].lower()
    if first in {"guide", "config", "api", "index"}:
        return first
    if first == "blog":
        return "skip"
    return "index"


def _heading_level(tag_name: str) -> int | None:
    match = _HEADING_RE.match(tag_name)
    return int(match.group(1)) if match else None


def _normalize_code_block(text: str) -> str:
    """Keep code block structure while stripping noisy whitespace."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line.strip())


def _markdown_list(tag: Tag) -> list[str]:
    """Render a list tag to markdown lines."""
    lines: list[str] = []
    ordered = tag.name == "ol"
    items = tag.find_all("li", recursive=False)
    for index, item in enumerate(items, start=1):
        text = normalize_whitespace(item.get_text(" ", strip=True))
        if not text:
            continue
        prefix = f"{index}. " if ordered else "- "
        lines.append(f"{prefix}{text}")
    return lines


def _should_keep_text(text: str) -> bool:
    """Reject obvious UI and marketing text."""
    lowered = text.lower()
    if len(text) < 20:
        return False
    return not any(term in lowered for term in NOISE_TERMS)


def html_to_markdown(html_text: str, url: str, created_at: str | None = None) -> MarkdownPage:
    """Convert a raw HTML document to a structured Markdown page."""
    soup = BeautifulSoup(html_text, "html.parser")
    _remove_noise_nodes(soup)

    root = _choose_root(soup)
    title = clean_title(soup.title.get_text(" ", strip=True) if soup.title else "")
    if not title:
        h1 = root.find("h1")
        title = clean_title(h1.get_text(" ", strip=True) if h1 else "")

    if not title:
        title = clean_title(Path(urlparse(url).path).name or "index")

    markdown_lines: list[str] = []
    seen_heading: set[tuple[int, str]] = set()

    for node in root.find_all(BLOCK_TAGS, recursive=True):
        if not isinstance(node, Tag):
            continue
        if _is_noise_tag(node):
            continue
        if any(parent.name in REMOVE_TAGS for parent in node.parents if isinstance(parent, Tag)):
            continue

        heading_level = _heading_level(node.name)
        if heading_level:
            text = normalize_whitespace(node.get_text(" ", strip=True))
            if not text or not _should_keep_text(text):
                continue
            key = (heading_level, text.lower())
            if key in seen_heading:
                continue
            seen_heading.add(key)
            markdown_lines.append(f"{'#' * heading_level} {text}")
            markdown_lines.append("")
            continue

        if node.name == "p":
            text = normalize_whitespace(node.get_text(" ", strip=True))
            if _should_keep_text(text):
                markdown_lines.append(text)
                markdown_lines.append("")
            continue

        if node.name in {"ul", "ol"}:
            list_lines = _markdown_list(node)
            if list_lines:
                markdown_lines.extend(list_lines)
                markdown_lines.append("")
            continue

        if node.name == "blockquote":
            text = normalize_whitespace(node.get_text(" ", strip=True))
            if _should_keep_text(text):
                markdown_lines.append(f"> {text}")
                markdown_lines.append("")
            continue

        if node.name == "pre":
            code_text = _normalize_code_block(node.get_text(" ", strip=True))
            if code_text:
                markdown_lines.append("```")
                markdown_lines.append(code_text)
                markdown_lines.append("```")
                markdown_lines.append("")

    markdown = "\n".join(line.rstrip() for line in markdown_lines).strip()
    if title and (not markdown.startswith("#")):
        markdown = f"# {title}\n\n{markdown}" if markdown else f"# {title}"

    category = _category_from_url(url)
    if created_at is None:
        created_at = datetime.now(timezone.utc).isoformat()
    slug = _slug_from_url(url)

    return MarkdownPage(
        url=url,
        title=title,
        created_at=created_at,
        markdown=markdown,
        category=category,
        slug=slug,
    )


def save_markdown_page(page: MarkdownPage, knowledge_base_dir: Path) -> Path:
    """Persist a markdown page with frontmatter."""
    if page.category == "skip":
        raise ValueError("Skip pages are not saved to the knowledge base")

    target_dir = knowledge_base_dir / page.category
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{page.slug}.md"

    frontmatter = [
        "---",
        f'url: "{page.url}"',
        f'title: "{page.title}"',
        f'created_at: "{page.created_at}"',
        "---",
        "",
    ]
    output_path.write_text("\n".join(frontmatter) + page.markdown + "\n", encoding="utf-8")
    return output_path
