"""Verified HTTPS metadata transport with explicit request headers and raw entities."""

from __future__ import annotations

from http.client import HTTPSConnection, IncompleteRead
import ssl
from urllib.parse import urlsplit

from .models import _HEADERS, NeotomaMetadataResponse


def _fetch_response(
    url: str, *, timeout: float, max_bytes: int
) -> NeotomaMetadataResponse:
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
        return NeotomaMetadataResponse(
            final_url=url,
            http_status=response.status,
            headers=headers,
            body=body,
            body_complete=complete and len(body) <= max_bytes,
        )
    finally:
        connection.close()
