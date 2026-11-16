"""Finite HTTP transfers with explicit TLS and retry policies."""

from __future__ import annotations

from http.client import HTTPResponse, IncompleteRead
import json
import math
import os
import ssl
import time
from typing import BinaryIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

INSECURE_TLS_ENV_VAR = "BIJUX_POLLENOMICS_ALLOW_INSECURE_TLS"
HTTP_REQUEST_RETRIES = 3
BINARY_MAX_BYTES = 32 * 1024 * 1024
BINARY_SOCKET_TIMEOUT = 30.0
TEXT_MAX_BYTES = 32 * 1024 * 1024
TEXT_SOCKET_TIMEOUT = 30.0
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
    *,
    max_bytes: int = TEXT_MAX_BYTES,
) -> object:
    """Decode JSON only after a finite byte transfer and socket timeout."""
    return json.loads(
        fetch_text(
            url,
            params=params,
            headers=headers,
            insecure=insecure,
            timeout=timeout,
            max_bytes=max_bytes,
        )
    )


def fetch_text(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
    timeout: float | None = None,
    *,
    max_bytes: int = TEXT_MAX_BYTES,
) -> str:
    """Decode UTF-8 after a bounded transfer; None uses a finite socket timeout."""
    if params:
        query = urlencode(params)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"
    validate_http_url(url)
    request = Request(url, headers=headers or {})
    return fetch_url_bytes(
        request, insecure=insecure, timeout=timeout, max_bytes=max_bytes
    ).decode("utf-8")


def fetch_binary(
    url: str,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
    *,
    max_bytes: int = BINARY_MAX_BYTES,
    timeout: float = BINARY_SOCKET_TIMEOUT,
) -> bytes:
    """Fetch bounded bytes with at most three attempts and a socket timeout.

    The timeout applies to socket operations, not the complete download. Larger
    sources require an explicit byte limit. Browser and authorized certificate
    retries share the same attempt budget as transient network failures.
    """
    validate_http_url(url)
    if type(insecure) is not bool:
        raise ValueError("insecure must be a boolean")
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ValueError("timeout must be positive and finite")
    try:
        socket_timeout = float(timeout)
    except (ValueError, OverflowError) as error:
        raise ValueError("timeout must be positive and finite") from error
    if not math.isfinite(socket_timeout) or socket_timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    request = Request(url, headers=headers or {})
    context = build_ssl_context(insecure=insecure)
    browser_retry = False
    for attempt in range(HTTP_REQUEST_RETRIES):
        try:
            manager = urlopen(request, context=context, timeout=socket_timeout)  # nosec B310
            response = manager.__enter__()
            try:
                payload = _read_binary(response, max_bytes=max_bytes)
            except BaseException as primary:
                try:
                    manager.__exit__(type(primary), primary, primary.__traceback__)
                except BaseException as close_error:
                    primary.add_note(f"HTTP response close failed: {close_error}")
                raise
        except HTTPError as error:
            try:
                error.close()
            except Exception as close_error:
                error.add_note(f"HTTP error response close failed: {close_error}")
            if (
                error.code != 403
                or browser_retry
                or attempt + 1 >= HTTP_REQUEST_RETRIES
            ):
                raise
            fallback_headers = dict(request.header_items())
            fallback_headers.setdefault("User-agent", "Mozilla/5.0")
            request = Request(url, headers=fallback_headers)
            browser_retry = True
        except URLError as error:
            if should_retry_insecure_tls(error):
                if (
                    insecure
                    or not allow_insecure_tls_fallback()
                    or attempt + 1 >= HTTP_REQUEST_RETRIES
                ):
                    raise
                context = build_ssl_context(insecure=True)
                insecure = True
                continue
            if attempt + 1 >= HTTP_REQUEST_RETRIES:
                raise
            time.sleep(float(attempt + 1))
        except TimeoutError:
            if attempt + 1 >= HTTP_REQUEST_RETRIES:
                raise
            time.sleep(float(attempt + 1))
        else:
            manager.__exit__(None, None, None)
            return payload
    raise RuntimeError("HTTP binary request completed without returning bytes")


def _read_binary(response: BinaryIO, *, max_bytes: int) -> bytes:
    """Check declared size and observe only the limit plus an overflow sentinel."""
    declared = getattr(response, "headers", {}).get("Content-Length")
    if isinstance(response, HTTPResponse):
        # Native length accounts for chunked and bodyless HTTP responses.
        declared = response.length
    declared_size = None
    if declared is not None:
        digits = str(declared).strip()
        if digits.isascii() and digits.isdecimal():
            declared_size = 0
            for digit in digits:
                declared_size = declared_size * 10 + ord(digit) - ord("0")
                if declared_size > max_bytes:
                    raise ValueError("HTTP binary payload exceeds byte limit")
    payload = bytearray()
    while block := response.read(min(64 * 1024, max_bytes - len(payload) + 1)):
        if len(block) > max_bytes - len(payload):
            raise ValueError("HTTP binary payload exceeds byte limit")
        payload.extend(block)
    if declared_size is not None and len(payload) < declared_size:
        raise IncompleteRead(bytes(payload), declared_size - len(payload))
    return bytes(payload)


def fetch_url_bytes(
    request: Request,
    *,
    insecure: bool,
    timeout: float | None,
    max_bytes: int = TEXT_MAX_BYTES,
) -> bytes:
    """Bound each response while retaining the existing TLS and retry behavior."""
    validate_http_url(request.full_url)
    if type(insecure) is not bool:
        raise ValueError("insecure must be a boolean")
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer")
    if timeout is None:
        timeout = TEXT_SOCKET_TIMEOUT
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ValueError("timeout must be positive and finite")
    try:
        socket_timeout = float(timeout)
    except (ValueError, OverflowError) as error:
        raise ValueError("timeout must be positive and finite") from error
    if not math.isfinite(socket_timeout) or socket_timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    context = build_ssl_context(insecure=insecure)
    last_error: TimeoutError | URLError | None = None
    for attempt in range(HTTP_REQUEST_RETRIES):
        try:
            manager = urlopen(request, context=context, timeout=socket_timeout)  # nosec B310
            response = manager.__enter__()
            try:
                payload = _read_binary(response, max_bytes=max_bytes)
            except BaseException as primary:
                try:
                    manager.__exit__(type(primary), primary, primary.__traceback__)
                except BaseException as close_error:
                    primary.add_note(f"HTTP response close failed: {close_error}")
                raise
        except URLError as error:
            last_error = error
            if isinstance(error, HTTPError):
                try:
                    error.close()
                except Exception as close_error:
                    error.add_note(f"HTTP error response close failed: {close_error}")
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
        else:
            manager.__exit__(None, None, None)
            return payload
        time.sleep(float(attempt + 1))
    if last_error is not None:
        raise last_error
    raise RuntimeError("HTTP request completed without returning bytes")
