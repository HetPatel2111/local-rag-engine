import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests


LOGGER = logging.getLogger("step2")


_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]+")


def slugify(value: str, max_len: int = 80) -> str:
    value = value.strip()
    value = _NON_ALNUM.sub("_", value).strip("_")
    if not value:
        value = "page"
    return value[:max_len].rstrip("_") or "page"


def filename_for_url(url: str, index: int) -> str:
    parsed = urlparse(url)
    netloc = slugify(parsed.netloc)
    path = slugify(parsed.path or "root")
    return f"{index:03d}_{netloc}_{path}.html"


def fetch_with_retries(
    session: requests.Session,
    url: str,
    *,
    timeout_sec: int,
    max_retries: int,
) -> requests.Response:
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=timeout_sec)
            if resp.status_code >= 400:
                resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < max_retries:
                backoff = min(2** (attempt - 1), 8)
                LOGGER.warning(
                    "Fetch failed (attempt %d/%d) %s: %s; retrying in %ss",
                    attempt,
                    max_retries,
                    url,
                    exc,
                    backoff,
                )
                time.sleep(backoff)
            else:
                break
    assert last_exc is not None
    raise last_exc


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    input_path = Path("data/urls/urls.json")
    output_dir = Path("data/html")
    metadata_path = output_dir / "metadata.json"

    timeout_sec = 10
    max_retries = 3

    urls = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(urls, list) or not all(isinstance(u, str) for u in urls):
        raise ValueError(f"Invalid URL list in {input_path.as_posix()}")

    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "RAG-Step2/1.0 (+https://example.invalid)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )

    total = len(urls)
    metadata: list[dict[str, str]] = []

    for idx, url in enumerate(urls, start=1):
        filename = filename_for_url(url, idx)
        file_path = output_dir / filename

        print(f"[{idx}/{total}] Fetching: {url}")
        try:
            resp = fetch_with_retries(
                session,
                url,
                timeout_sec=timeout_sec,
                max_retries=max_retries,
            )
            file_path.write_bytes(resp.content)
            metadata.append({"url": url, "filename": filename})
            print(f"[{idx}/{total}] Saved: {filename} (status {resp.status_code})")
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Failed to fetch %s: %s", url, exc)
            print(f"[{idx}/{total}] FAILED: {url}")

    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    LOGGER.info("Wrote metadata: %s (%d entries)", metadata_path.as_posix(), len(metadata))


if __name__ == "__main__":
    main()

