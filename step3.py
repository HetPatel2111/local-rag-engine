import json
import logging
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal


LOGGER = logging.getLogger("step3")


REMOVE_TAGS = {"script", "style", "header", "nav", "footer"}
TEXT_TAGS = {"article", "p", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
CODE_TAGS = {"pre", "code"}


WhitespaceMode = Literal["text", "code"]


@dataclass(frozen=True)
class Chunk:
    mode: WhitespaceMode
    text: str


class CleanTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._remove_depth = 0
        self._title_depth = 0
        self._capture_depth = 0
        self._code_depth = 0

        self.title_parts: list[str] = []
        self.chunks: list[Chunk] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        tag = tag.lower()
        if tag in REMOVE_TAGS:
            self._remove_depth += 1
            return

        if tag == "title":
            self._title_depth += 1
            return

        if tag in TEXT_TAGS:
            self._capture_depth += 1
            return

        if tag in CODE_TAGS:
            self._code_depth += 1
            self._capture_depth += 1
            return

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in REMOVE_TAGS:
            if self._remove_depth > 0:
                self._remove_depth -= 1
            return

        if tag == "title":
            if self._title_depth > 0:
                self._title_depth -= 1
            return

        if tag in CODE_TAGS:
            if self._code_depth > 0:
                self._code_depth -= 1
            if self._capture_depth > 0:
                self._capture_depth -= 1
            return

        if tag in TEXT_TAGS:
            if self._capture_depth > 0:
                self._capture_depth -= 1
            return

    def handle_data(self, data: str) -> None:
        if not data:
            return

        if self._remove_depth > 0:
            return

        if self._title_depth > 0:
            self.title_parts.append(data)
            return

        if self._capture_depth <= 0:
            return

        mode: WhitespaceMode = "code" if self._code_depth > 0 else "text"
        self.chunks.append(Chunk(mode=mode, text=data))


_WS = re.compile(r"\s+")
_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")
_TOKEN_NOISE = re.compile(r"^[A-Za-z0-9]{18,}$")


def normalize_chunks(chunks: list[Chunk]) -> str:
    out_parts: list[str] = []
    for chunk in chunks:
        if chunk.mode == "code":
            text = chunk.text.replace("\r\n", "\n").replace("\r", "\n")
            text = _ZERO_WIDTH.sub("", text)
            text = text.strip("\n")
            if text:
                out_parts.append(text)
        else:
            text = _ZERO_WIDTH.sub("", chunk.text)
            text = _WS.sub(" ", text).strip()
            if text:
                out_parts.append(text)
    return "\n".join(out_parts).strip()


def extract_title(title_parts: list[str]) -> str:
    title = _ZERO_WIDTH.sub("", "".join(title_parts))
    title = _WS.sub(" ", title).strip()
    if not title:
        return ""

    parts = [part for part in re.split(r"\s+", title) if part]
    cleaned_parts: list[str] = []
    seen_words: set[str] = set()

    for part in parts:
        normalized = part.strip(" |-_:/\\")
        if not normalized:
            continue
        if _TOKEN_NOISE.match(normalized):
            continue
        lowered = normalized.lower()
        if lowered in seen_words:
            continue
        seen_words.add(lowered)
        cleaned_parts.append(normalized)

    title = " ".join(cleaned_parts).strip()
    if len(title) > 120:
        title = title[:120].rstrip()
    return title


def extract_from_html(html_text: str) -> tuple[str, str]:
    parser = CleanTextExtractor()
    parser.feed(html_text)
    parser.close()
    title = extract_title(parser.title_parts)
    content = normalize_chunks(parser.chunks)
    return title, content


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    html_dir = Path("data/html")
    metadata_path = html_dir / "metadata.json"
    output_path = Path("data/clean/pages.json")

    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(meta, list):
        raise ValueError(f"Invalid metadata in {metadata_path.as_posix()}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    pages: list[dict[str, str]] = []
    total = len(meta)

    for idx, item in enumerate(meta, start=1):
        if not isinstance(item, dict) or "url" not in item or "filename" not in item:
            raise ValueError(f"Invalid metadata entry at index {idx}")

        url = str(item["url"])
        filename = str(item["filename"])
        file_path = html_dir / filename

        print(f"[{idx}/{total}] Extracting: {filename}")
        html_text = file_path.read_text(encoding="utf-8", errors="replace")
        title, content = extract_from_html(html_text)
        pages.append({"url": url, "title": title, "content": content})

    output_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    LOGGER.info("Wrote %s (%d pages)", output_path.as_posix(), len(pages))


if __name__ == "__main__":
    main()
