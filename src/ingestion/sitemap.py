"""Utilities for downloading and parsing sitemap XML files."""

from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import requests


def download_sitemap(sitemap_url: str, timeout: int = 30) -> str:
    """Download a sitemap XML document."""
    response = requests.get(sitemap_url, timeout=timeout)
    response.raise_for_status()
    return response.text


def extract_urls(xml_text: str) -> list[str]:
    """Extract URL entries from a sitemap XML payload."""
    root = ET.fromstring(xml_text)
    urls: list[str] = []
    for element in root.iter():
        if element.tag.endswith("loc") and element.text:
            value = element.text.strip()
            if value:
                urls.append(value)
    return urls


def dedupe_urls(urls: list[str]) -> list[str]:
    """Preserve order while removing duplicates."""
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        unique.append(url)
    return unique


def save_json(path: Path, payload: object) -> None:
    """Write JSON payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

