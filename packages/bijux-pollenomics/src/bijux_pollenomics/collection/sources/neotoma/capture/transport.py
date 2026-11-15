"""Verified HTTPS metadata transport with explicit request headers and raw entities."""

from __future__ import annotations

from dataclasses import dataclass
from http.client import HTTPSConnection, IncompleteRead
import ssl
from urllib.parse import urlsplit

_HEADERS = (
    ("Host", "api.neotomadb.org"),
    ("Accept", "application/json"),
    ("Accept-Encoding", "identity"),
    ("User-Agent", "bijux-pollenomics"),
    ("Connection", "close"),
)


@dataclass(frozen=True)
class NeotomaHttpResponse:
    """An authenticated source HTTP entity before metadata or numerical decoding."""

    final_url: str
    http_status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes
    body_complete: bool = True


def _fetch_response(url: str, *, timeout: float, max_bytes: int) -> NeotomaHttpResponse:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "api.neotomadb.org":
        raise ValueError("Neotoma metadata requires its official HTTPS origin")
    target = parts.path + ("?" + parts.query if parts.query else "")
    connection = HTTPSConnection(
        parts.netloc, timeout=timeout, context=ssl.create_default_context()
    )
    try:
        connection.putrequest("GET", target, skip_host=True, skip_accept_encoding=True)
        for name, value in _HEADERS:
            connection.putheader(name, value)
        connection.endheaders()
        response = connection.getresponse()
        complete = True
        try:
            body = response.read(max_bytes + 1)
        except IncompleteRead as error:
            body, complete = error.partial, False
        headers = tuple(response.getheaders())
        for name, value in headers:
            if name.lower() == "content-length":
                try:
                    complete = complete and int(value) == len(body)
                except ValueError:
                    complete = False
        return NeotomaHttpResponse(
            final_url=url,
            http_status=response.status,
            headers=headers,
            body=body,
            body_complete=complete and len(body) <= max_bytes,
        )
    finally:
        connection.close()
