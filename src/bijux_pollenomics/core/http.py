from __future__ import annotations

import json
import os
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


INSECURE_TLS_ENV_VAR = "BIJUX_POLLENOMICS_ALLOW_INSECURE_TLS"


def allow_insecure_tls_fallback() -> bool:
    """Return whether network fetches may retry with TLS verification disabled."""
    return os.getenv(INSECURE_TLS_ENV_VAR, "").strip().casefold() in {"1", "true", "yes", "on"}


def should_retry_insecure_tls(error: URLError) -> bool:
    """Return whether a failed request should retry with an unverified TLS context."""
    return isinstance(error.reason, ssl.SSLCertVerificationError)


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
    try:
        with urlopen(request, context=context, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except URLError as error:
        if insecure or not allow_insecure_tls_fallback() or not should_retry_insecure_tls(error):
            raise
        with urlopen(request, context=ssl._create_unverified_context(), timeout=timeout) as response:
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
    except URLError as error:
        if insecure or not allow_insecure_tls_fallback() or not should_retry_insecure_tls(error):
            raise
        with urlopen(request, context=ssl._create_unverified_context()) as response:
            return response.read()
