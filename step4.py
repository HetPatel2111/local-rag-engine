import json
import logging
from pathlib import Path


LOGGER = logging.getLogger("step4")


def load_pages_from_clean_dir(clean_dir: Path) -> list[dict[str, str]]:
    json_files = sorted(p for p in clean_dir.rglob("*.json") if p.is_file())
    if not json_files:
        raise FileNotFoundError(f"No .json files found under {clean_dir.as_posix()}")

    pages: list[dict[str, str]] = []
    for path in json_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            pages.extend(data)
        elif isinstance(data, dict):
            pages.append(data)
        else:
            raise ValueError(f"Unsupported JSON shape in {path.as_posix()}")

    normalized: list[dict[str, str]] = []
    for i, item in enumerate(pages, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid page at index {i}")
        url = str(item.get("url", "")).strip()
        title = str(item.get("title", "")).strip()
        content = str(item.get("content", "")).strip()
        if not url:
            raise ValueError(f"Missing url at index {i}")
        normalized.append({"url": url, "title": title, "content": content})

    return normalized


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except Exception:  # noqa: BLE001
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore[no-redef]
        except Exception:  # noqa: BLE001
            LOGGER.warning(
                "langchain is not installed; using a local RecursiveCharacterTextSplitter-compatible fallback"
            )

            class RecursiveCharacterTextSplitter:  # type: ignore[no-redef]
                def __init__(self, *, chunk_size: int, chunk_overlap: int) -> None:
                    if chunk_size <= 0:
                        raise ValueError("chunk_size must be > 0")
                    if chunk_overlap < 0:
                        raise ValueError("chunk_overlap must be >= 0")
                    if chunk_overlap >= chunk_size:
                        raise ValueError("chunk_overlap must be < chunk_size")
                    self.chunk_size = chunk_size
                    self.chunk_overlap = chunk_overlap
                    self.separators = ["\n\n", "\n", " ", ""]

                def split_text(self, text: str) -> list[str]:
                    text = text or ""
                    text = text.strip()
                    if not text:
                        return []

                    pieces = self._recursive_split(text, self.separators)
                    return self._merge_with_overlap(pieces)

                def _recursive_split(self, text: str, seps: list[str]) -> list[str]:
                    if len(text) <= self.chunk_size:
                        return [text]
                    if not seps:
                        return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

                    sep = seps[0]
                    if sep == "":
                        return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

                    parts = text.split(sep)
                    if len(parts) == 1:
                        return self._recursive_split(text, seps[1:])

                    out: list[str] = []
                    for i, part in enumerate(parts):
                        if not part:
                            continue
                        candidate = part if i == 0 else sep + part
                        if len(candidate) <= self.chunk_size:
                            out.append(candidate)
                        else:
                            out.extend(self._recursive_split(part, seps[1:]))
                    return out

                def _merge_with_overlap(self, pieces: list[str]) -> list[str]:
                    chunks: list[str] = []
                    current = ""
                    for piece in pieces:
                        if not current:
                            current = piece
                            continue
                        if len(current) + len(piece) <= self.chunk_size:
                            current += piece
                            continue
                        chunks.append(current.strip())
                        overlap = current[-self.chunk_overlap :] if self.chunk_overlap else ""
                        current = (overlap + piece).strip()
                    if current:
                        chunks.append(current.strip())
                    return [c for c in chunks if c]

    clean_dir = Path("data/clean")
    fallback_pages_json = Path("data/clean/pages.json")

    chunk_size = 600
    chunk_overlap = 100

    output_dir = Path("data/chunks")
    output_path = output_dir / "chunks.json"

    if clean_dir.exists():
        LOGGER.info("Loading cleaned pages from %s", clean_dir.as_posix())
        pages = load_pages_from_clean_dir(clean_dir)
    else:
        LOGGER.warning(
            "Input dir %s not found; falling back to %s",
            clean_dir.as_posix(),
            fallback_pages_json.as_posix(),
        )
        pages = json.loads(fallback_pages_json.read_text(encoding="utf-8"))
        if not isinstance(pages, list):
            raise ValueError(f"Invalid pages JSON in {fallback_pages_json.as_posix()}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks: list[dict[str, str]] = []
    total_pages = len(pages)

    for page_index, page in enumerate(pages, start=1):
        url = str(page.get("url", "")).strip()
        title = str(page.get("title", "")).strip()
        content = str(page.get("content", "") or "").strip()

        print(f"[{page_index}/{total_pages}] Chunking: {url}")

        if not content:
            continue

        parts = splitter.split_text(content)
        for chunk_index, text in enumerate(parts, start=1):
            chunk_id = f"{page_index:03d}_{chunk_index:04d}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "url": url,
                    "title": title,
                    "text": text,
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    LOGGER.info("Wrote %s (%d chunks)", output_path.as_posix(), len(chunks))


if __name__ == "__main__":
    main()
