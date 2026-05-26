import json
import logging
from pathlib import Path
from xml.etree import ElementTree as ET

import requests


LOGGER = logging.getLogger("step1")


def extract_urls_from_sitemap(xml_text: str) -> list[str]:
    root = ET.fromstring(xml_text)
    urls: list[str] = []

    for elem in root.iter():
        if elem.tag.endswith("loc") and elem.text:
            url = elem.text.strip()
            if url:
                urls.append(url)

    return urls


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    sitemap_url = "https://vite.dev/sitemap.xml"
    output_path = Path("data/urls/urls.json")
    max_urls = 100

    LOGGER.info("Downloading sitemap: %s", sitemap_url)
    resp = requests.get(sitemap_url, timeout=30)
    resp.raise_for_status()
    LOGGER.info("Downloaded sitemap (%d bytes)", len(resp.content))

    LOGGER.info("Extracting URLs from sitemap XML")
    extracted_urls = extract_urls_from_sitemap(resp.text)
    LOGGER.info("Extracted %d URLs (pre-dedupe)", len(extracted_urls))

    unique_urls = dedupe_preserve_order(extracted_urls)
    LOGGER.info("Deduped to %d unique URLs", len(unique_urls))

    urls_to_save = unique_urls[:max_urls]
    LOGGER.info("Processing first %d URLs (saving %d)", max_urls, len(urls_to_save))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(urls_to_save, indent=2), encoding="utf-8")
    LOGGER.info("Wrote %s", output_path.as_posix())

    print(f"total urls collected: {len(unique_urls)}")


if __name__ == "__main__":
    main()
