from __future__ import annotations

import json
import ssl
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch_json(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
    timeout: float | None = None,
) -> object:
    """Fetch and decode a JSON payload."""
    return json.loads(fetch_text(url, params=params, headers=headers, insecure=insecure, timeout=timeout))


def fetch_text(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
    timeout: float | None = None,
) -> str:
    """Fetch a text payload using the standard library."""
    if params:
        query = urlencode(params)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"
    request = Request(url, headers=headers or {})
    context = ssl._create_unverified_context() if insecure else None
    with urlopen(request, context=context, timeout=timeout) as response:
        return response.read().decode("utf-8")


def fetch_binary(
    url: str,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
) -> bytes:
    """Fetch binary content with optional TLS fallback."""
    request = Request(url, headers=headers or {})
    context = ssl._create_unverified_context() if insecure else None
    try:
        with urlopen(request, context=context) as response:
            return response.read()
    except HTTPError as error:
        if error.code != 403:
            raise
        fallback_headers = dict(headers or {})
        fallback_headers.setdefault("User-Agent", "Mozilla/5.0")
        with urlopen(Request(url, headers=fallback_headers), context=ssl._create_unverified_context()) as response:
            return response.read()


def write_json(path: Path, payload: object) -> None:
    """Write JSON with stable formatting."""
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text content."""
    path.write_text(content, encoding="utf-8")


def clean_optional_text(value: object) -> str:
    """Normalize optional text values used in normalized exports."""
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"", "null", "None"} else text


def slugify(value: str) -> str:
    """Convert a label into a stable file slug."""
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")
