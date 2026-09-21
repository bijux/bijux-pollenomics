"""Read-only, bounded GitHub evidence transport without token-bearing receipts."""

from __future__ import annotations

from http.client import HTTPResponse
import os
import time
from typing import Any, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .contracts import ReferenceRefusal, read_json

MAX_RESPONSE_BYTES = 32 * 1024 * 1024


class EvidenceReader(Protocol):
    """Read bytes from a governed remote evidence route."""

    def read(self, path: str) -> bytes:
        """Return the response body for one evidence route."""
        ...


class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, request: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> Request | None:
        if urlsplit(newurl).scheme != "https":
            raise ReferenceRefusal("Non-HTTPS evidence redirect refused")
        redirected = super().redirect_request(request, fp, code, msg, headers, newurl)
        if redirected is not None and urlsplit(newurl).netloc != "api.github.com":
            redirected.remove_header("Authorization")
        return redirected


class GitHubReader:
    """Only GET is exposed; no dispatch, rerun, status mutation or publication."""

    def __init__(self) -> None:
        """Start the five-minute evidence collection deadline."""
        self.started = time.monotonic()

    def read(self, path: str) -> bytes:
        """Fetch a bounded GitHub API route without exposing credentials."""
        if time.monotonic() - self.started > 300:
            raise ReferenceRefusal("Release evidence collection exceeded deadline")
        if (
            not path.startswith("/repos/")
            or "\\" in path
            or ".." in path
            or any(ord(char) < 32 for char in path)
        ):
            raise ReferenceRefusal("Invalid GitHub evidence route")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "bijux-pollenomics-live-r-gate",
        }
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(
            "https://api.github.com" + path, headers=headers, method="GET"
        )
        started = time.monotonic()
        chunks = []
        size = 0
        try:
            with build_opener(_SafeRedirect()).open(request, timeout=15) as opened:
                response = cast(HTTPResponse, opened)
                while True:
                    if (
                        time.monotonic() - started > 45
                        or time.monotonic() - self.started > 300
                    ):
                        raise ReferenceRefusal(
                            "GitHub evidence request exceeded deadline"
                        )
                    chunk = response.read1(min(65536, MAX_RESPONSE_BYTES + 1 - size))
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_RESPONSE_BYTES:
                        raise ReferenceRefusal(
                            "GitHub evidence response exceeds byte limit"
                        )
                    chunks.append(chunk)
        except HTTPError as error:
            raise ReferenceRefusal(
                f"GitHub evidence is unavailable (HTTP {error.code})"
            ) from None
        except (URLError, OSError, TimeoutError):
            raise ReferenceRefusal(
                "GitHub evidence request failed or timed out"
            ) from None
        return b"".join(chunks)


def collection(reader: EvidenceReader, path: str, key: str) -> list[dict[str, Any]]:
    """Bounded pagination; omitted rows never masquerade as a complete inventory."""
    result = []
    expected = None
    for page in range(1, 21):
        separator = "&" if "?" in path else "?"
        response = read_json(
            reader.read(path + separator + f"per_page=100&page={page}")
        )
        if (
            not isinstance(response, dict)
            or type(response.get("total_count")) is not int
            or not isinstance(response.get(key), list)
        ):
            raise ReferenceRefusal("Malformed GitHub collection response")
        count = response["total_count"]
        if expected is None:
            expected = count
        if (
            count != expected
            or count < 0
            or count > 2000
            or any(not isinstance(row, dict) for row in response[key])
        ):
            raise ReferenceRefusal(
                "GitHub collection changed or exceeded its bounded policy"
            )
        result.extend(response[key])
        if len(result) == count:
            return result
        if not response[key] or len(result) > count:
            break
    raise ReferenceRefusal("Incomplete GitHub evidence inventory")
