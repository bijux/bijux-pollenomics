from __future__ import annotations

import json
import os
import ssl
import time
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

INSECURE_TLS_ENV_VAR = "BIJUX_POLLENOMICS_ALLOW_INSECURE_TLS"
HTTP_REQUEST_RETRIES = 3
ALLOWED_URL_SCHEMES = frozenset({"http", "https"})


def allow_insecure_tls_fallback() -> bool:
    """Return whether network fetches may retry with TLS verification disabled."""
    return os.getenv(INSECURE_TLS_ENV_VAR, "").strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }


def should_retry_insecure_tls(error: URLError) -> bool:
    """Return whether a failed request should retry with an unverified TLS context."""
    return isinstance(error.reason, ssl.SSLCertVerificationError)


def should_retry_transient_network_error(error: Exception) -> bool:
    """Return whether one transport failure is likely to succeed on a later attempt."""
    return isinstance(error, (TimeoutError, URLError))


def validate_http_url(url: str) -> None:
    """Reject unexpected URL schemes before handing a request to urllib."""
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_URL_SCHEMES or not parsed.netloc:
        raise ValueError(f"Unsupported URL for network fetch: {url}")


def build_ssl_context(*, insecure: bool) -> ssl.SSLContext | None:
    """Create an SSL context only when an insecure TLS retry is explicitly enabled."""
    if not insecure:
        return None
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def fetch_json(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
    timeout: float | None = None,
) -> object:
    """Fetch and decode a JSON payload."""
    return json.loads(
        fetch_text(
            url, params=params, headers=headers, insecure=insecure, timeout=timeout
        )
    )


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
    validate_http_url(url)
    request = Request(url, headers=headers or {})
    return fetch_url_bytes(request, insecure=insecure, timeout=timeout).decode("utf-8")


def fetch_binary(
    url: str,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
) -> bytes:
    """Fetch binary content with optional TLS fallback."""
    validate_http_url(url)
    request = Request(url, headers=headers or {})
    context = build_ssl_context(insecure=insecure)
    try:
        with urlopen(request, context=context) as response:  # nosec B310
            return cast(bytes, response.read())
    except HTTPError as error:
        if error.code != 403:
            raise
        fallback_headers = dict(headers or {})
        fallback_headers.setdefault("User-Agent", "Mozilla/5.0")
        with urlopen(
            Request(url, headers=fallback_headers),
            context=build_ssl_context(insecure=True),
        ) as response:  # nosec B310
            return cast(bytes, response.read())
    except (TimeoutError, URLError):
        return fetch_url_bytes(request, insecure=insecure, timeout=None)


def fetch_url_bytes(
    request: Request,
    *,
    insecure: bool,
    timeout: float | None,
) -> bytes:
    """Fetch one HTTP payload with TLS fallback and bounded retries for transient failures."""
    validate_http_url(request.full_url)
    context = build_ssl_context(insecure=insecure)
    last_error: TimeoutError | URLError | None = None
    for attempt in range(HTTP_REQUEST_RETRIES):
        try:
            with urlopen(request, context=context, timeout=timeout) as response:  # nosec B310
                return cast(bytes, response.read())
        except URLError as error:
            last_error = error
            if (
                not insecure
                and allow_insecure_tls_fallback()
                and should_retry_insecure_tls(error)
            ):
                context = build_ssl_context(insecure=True)
                insecure = True
                continue
            if (
                not should_retry_transient_network_error(error)
                or attempt + 1 >= HTTP_REQUEST_RETRIES
            ):
                raise
        except TimeoutError as error:
            last_error = error
            if (
                not should_retry_transient_network_error(error)
                or attempt + 1 >= HTTP_REQUEST_RETRIES
            ):
                raise
        time.sleep(float(attempt + 1))
    if last_error is not None:
        raise last_error
    raise RuntimeError("HTTP request completed without returning bytes")
