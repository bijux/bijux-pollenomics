from __future__ import annotations

from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ..core import http as _http
from ..core.files import write_json, write_text
from ..core.text import clean_optional_text, slugify

ssl = _http.ssl


def fetch_json(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
    timeout: float | None = None,
) -> object:
    """Compatibility wrapper for JSON fetches used by downloader modules and tests."""
    _http.Request = Request
    _http.urlopen = urlopen
    _http.HTTPError = HTTPError
    _http.ssl = ssl
    return _http.fetch_json(url, params=params, headers=headers, insecure=insecure, timeout=timeout)


def fetch_text(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
    timeout: float | None = None,
) -> str:
    """Compatibility wrapper for text fetches used by downloader modules and tests."""
    _http.Request = Request
    _http.urlopen = urlopen
    _http.HTTPError = HTTPError
    _http.ssl = ssl
    return _http.fetch_text(url, params=params, headers=headers, insecure=insecure, timeout=timeout)


def fetch_binary(
    url: str,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
) -> bytes:
    """Compatibility wrapper for binary fetches used by downloader modules and tests."""
    _http.Request = Request
    _http.urlopen = urlopen
    _http.HTTPError = HTTPError
    _http.ssl = ssl
    return _http.fetch_binary(url, headers=headers, insecure=insecure)


__all__ = [
    "HTTPError",
    "Request",
    "clean_optional_text",
    "fetch_binary",
    "fetch_json",
    "fetch_text",
    "slugify",
    "ssl",
    "urlopen",
    "write_json",
    "write_text",
]
