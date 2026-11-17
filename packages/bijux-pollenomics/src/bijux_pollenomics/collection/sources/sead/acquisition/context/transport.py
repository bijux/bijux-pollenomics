"""Bound injected source streams before decoding and before every request."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import partial
import json
import re
import time
from typing import Any, Protocol
from urllib.error import HTTPError
from urllib.parse import urlencode

from bijux_pollenomics.core.errors.cleanup import add_cleanup_note

from ..client import SEAD_POSTGREST_ROOT
from .contracts import SeadContextLimits


def _cleanup_message(error: BaseException) -> str:
    """Render secondary diagnostics only inside the failure-proof note owner."""
    return f"Context response close failed: {error}"


class ContextResponse(Protocol):
    """An opener-owned response reporting its final URL without redirects."""

    url: str
    status: int

    def read(self, size: int) -> bytes:
        """Read at most the requested byte count."""
        ...

    def close(self) -> None:
        """Release the response on success and refusal."""
        ...


def decode(raw: bytes) -> Any:
    """Reject duplicate fields and non-finite JSON scalars without coercion."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("Context source JSON repeats an object key")
            result[key] = value
        return result

    result = json.loads(raw, object_pairs_hook=pairs)
    json.dumps(result, allow_nan=False)
    return result


class ContextTransport:
    """One-attempt byte transport retaining bounded responses and request evidence.

    The injected opener must disable redirects and retries itself. Final URL
    comparison detects a violated redirect contract before consuming its body;
    it cannot undo network requests made by a misconfigured injected opener.
    """

    def __init__(
        self,
        opener: Callable[..., ContextResponse],
        *,
        limits: SeadContextLimits,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Start one finite source epoch without any request or implicit opener."""
        self.opener, self.limits, self.clock = opener, limits, clock
        self.started = clock()
        self.request_count = self.byte_count = self.row_count = 0
        self.responses: dict[str, bytes] = {}
        self.requests: list[dict[str, object]] = []

    def check(self) -> None:
        """Refuse exhausted aggregate budgets before another response is opened."""
        if (
            self.clock() - self.started >= self.limits.max_seconds
            or self.request_count >= self.limits.max_requests
            or self.byte_count >= self.limits.max_bytes - 1
        ):
            raise ValueError("Context aggregate request/byte/time budget exhausted")

    def fetch(
        self,
        endpoint: str,
        *,
        params: Sequence[tuple[str, str]],
        headers: dict[str, str],
        timeout: float,
    ) -> object:
        """Adapt bounded literal JSON pages to the existing EOF acquisition owner."""
        self.check()
        if not re.fullmatch(
            re.escape(SEAD_POSTGREST_ROOT) + r"/tbl_[a-z0-9_]+", endpoint
        ):
            raise ValueError("Context request endpoint is outside the fixed source")
        url = endpoint + "?" + urlencode(params)
        self.request_count += 1
        name = f"responses/{self.request_count:04d}.json"
        record: dict[str, object] = {
            "url": url,
            "headers": dict(headers),
            "response": name,
        }
        self.requests.append(record)
        response: ContextResponse | None = None
        chunks: list[bytes] = []
        count = 0
        primary: BaseException | None = None
        try:
            try:
                response = self.opener(
                    url,
                    headers=dict(headers),
                    timeout=min(timeout, self.limits.timeout_seconds),
                )
            except HTTPError as error:
                try:
                    error.close()
                except BaseException as cleanup:
                    add_cleanup_note(error, partial(_cleanup_message, cleanup))
                raise
            if response.url != url:
                raise ValueError("Context response redirect or final URL mismatch")
            if response.status not in {200, 206}:
                raise ValueError("Context response status is not successful")
            limit = min(
                self.limits.response_bytes,
                self.limits.max_bytes - self.byte_count - 1,
            )
            while True:
                if self.clock() - self.started >= self.limits.max_seconds:
                    raise ValueError("Context time budget exhausted while reading")
                chunk = response.read(min(64 * 1024, limit + 1 - count))
                if type(chunk) is not bytes:
                    raise ValueError("Context response must supply immutable bytes")
                if not chunk:
                    break
                chunks.append(chunk)
                count += len(chunk)
                self.byte_count += len(chunk)
                if count > limit:
                    raise ValueError("Context response byte budget exceeded")
            result = decode(b"".join(chunks))
            if not isinstance(result, list) or any(
                type(row) is not dict for row in result
            ):
                raise ValueError("Context source page must contain JSON objects")
            self.row_count += len(result)
            if self.row_count > self.limits.max_rows:
                raise ValueError("Context aggregate row budget exceeded")
            return result
        except BaseException as error:
            primary = error
            record["failure_type"] = type(error).__name__
            raise
        finally:
            self.responses[name] = b"".join(chunks)
            record["byte_count"] = count
            if response is not None:
                try:
                    response.close()
                except BaseException as cleanup:
                    if primary is None:
                        raise
                    add_cleanup_note(primary, partial(_cleanup_message, cleanup))
