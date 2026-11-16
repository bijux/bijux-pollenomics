"""Text and JSON downloads must not bypass finite binary transfer safeguards."""

from email.message import Message
from io import BytesIO
import math
import time
from typing import Any
from urllib.error import HTTPError

import pytest

from bijux_pollenomics.collection.sources.neotoma.client import fetch_neotoma_json
from bijux_pollenomics.core import http


class SourceResponse(BytesIO):
    """Observe actual requested and returned bytes without a provider request."""

    def __init__(self, payload: bytes, length: str | None = None) -> None:
        super().__init__(payload)
        self.headers = {} if length is None else {"Content-Length": length}
        self.requested: list[int | None] = []
        self.observed = 0

    def read(self, size: int | None = -1) -> bytes:
        self.requested.append(size)
        raw = super().read(size)
        self.observed += len(raw)
        return raw


def transport(
    monkeypatch: pytest.MonkeyPatch, response: SourceResponse
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def opened(*args: Any, **kwargs: Any) -> SourceResponse:
        calls.append(
            {
                **kwargs,
                "url": args[0].full_url,
                "source_header": args[0].get_header("X-source"),
            }
        )
        return response

    monkeypatch.setattr(http, "urlopen", opened)
    return calls


def test_text_default_never_requests_unbounded_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = SourceResponse(b"source")
    calls = transport(monkeypatch, response)
    assert http.fetch_text("https://example.test/source") == "source"
    assert response.closed
    assert response.requested and all(
        size is not None and 0 < size <= 65536 for size in response.requested
    )
    assert calls[0]["timeout"] == 30


@pytest.mark.parametrize(
    "reader", [http.fetch_text, http.fetch_json, fetch_neotoma_json]
)
def test_text_and_json_default_refuse_oversized_declarations_before_body(
    monkeypatch: pytest.MonkeyPatch, reader: Any
) -> None:
    response = SourceResponse(b"{}", str(32 * 1024 * 1024 + 1))
    calls = transport(monkeypatch, response)
    with pytest.raises(ValueError, match="byte limit"):
        reader("https://example.test/source")
    assert response.observed == 0
    assert response.closed
    assert len(calls) == 1


@pytest.mark.parametrize("length", [None, "1", "invalid"])
def test_text_overflow_observes_only_the_limit_and_one_sentinel(
    monkeypatch: pytest.MonkeyPatch, length: str | None
) -> None:
    response = SourceResponse(b"abcdefgh", length)
    calls = transport(monkeypatch, response)
    with pytest.raises(ValueError, match="byte limit"):
        http.fetch_text("https://example.test/source", max_bytes=4)
    assert response.observed == 5
    assert response.closed
    assert len(calls) == 1


@pytest.mark.parametrize("reader", [http.fetch_json, fetch_neotoma_json])
def test_explicit_json_byte_limit_applies_before_utf8_decoding(
    monkeypatch: pytest.MonkeyPatch, reader: Any
) -> None:
    response = SourceResponse('{"é":0}'.encode())
    transport(monkeypatch, response)
    with pytest.raises(ValueError, match="byte limit"):
        reader("https://example.test/source", max_bytes=4)
    assert response.observed == 5
    assert response.closed


@pytest.mark.parametrize("limit", [True, False, 0, -1, 1.5, None])
def test_invalid_text_byte_limits_refuse_before_transport(
    monkeypatch: pytest.MonkeyPatch, limit: Any
) -> None:
    calls = transport(monkeypatch, SourceResponse(b"source"))
    with pytest.raises(ValueError, match="max_bytes"):
        http.fetch_text("https://example.test/source", max_bytes=limit)
    assert calls == []


@pytest.mark.parametrize("timeout", [True, False, 0, -1, math.inf, math.nan, "30"])
def test_invalid_text_timeouts_refuse_before_transport(
    monkeypatch: pytest.MonkeyPatch, timeout: Any
) -> None:
    calls = transport(monkeypatch, SourceResponse(b"source"))
    with pytest.raises(ValueError, match="timeout"):
        http.fetch_text("https://example.test/source", timeout=timeout)
    assert calls == []


def test_explicit_text_profile_preserves_content_headers_and_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = SourceResponse(b"exact", "5")
    calls = transport(monkeypatch, response)
    assert (
        http.fetch_text(
            "https://example.test/source",
            {"limit": "2"},
            {"X-Source": "native"},
            False,
            12,
            max_bytes=5,
        )
        == "exact"
    )
    assert response.observed == 5
    assert response.closed
    assert calls[0]["url"] == "https://example.test/source?limit=2"
    assert calls[0]["source_header"] == "native"
    assert calls[0]["timeout"] == 12


def test_text_close_failure_preserves_the_original_byte_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenClose(SourceResponse):
        def close(self) -> None:
            super().close()
            raise RuntimeError("source cleanup failed")

    response = BrokenClose(b"source", "6")
    calls = transport(monkeypatch, response)
    with pytest.raises(ValueError, match="byte limit") as caught:
        http.fetch_text("https://example.test/source", max_bytes=4)
    assert response.closed and response.observed == 0
    assert len(calls) == 1
    assert any("source cleanup failed" in note for note in caught.value.__notes__)


def test_successful_text_cleanup_timeout_is_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    primary = TimeoutError("successful source cleanup failed")

    class BrokenClose(SourceResponse):
        def close(self) -> None:
            super().close()
            raise primary

    response = BrokenClose(b"source")
    calls = transport(monkeypatch, response)
    with pytest.raises(TimeoutError) as caught:
        http.fetch_text("https://example.test/source", max_bytes=6)
    assert caught.value is primary
    assert response.closed and len(calls) == 1


@pytest.mark.parametrize("close_failure", [False, True])
def test_text_http_error_bodies_close_before_the_next_attempt(
    monkeypatch: pytest.MonkeyPatch, close_failure: bool
) -> None:
    class ErrorBody(BytesIO):
        def close(self) -> None:
            super().close()
            if close_failure:
                raise RuntimeError("error body cleanup failed")

    bodies = [ErrorBody(b"provider refusal") for _ in range(3)]
    headers = Message()
    headers["X-Source"] = "native"
    errors = [
        HTTPError(
            "https://example.test/source",
            503,
            "native unavailable",
            headers,
            body,
        )
        for body in bodies
    ]
    calls = 0

    def opened(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        if calls:
            assert bodies[calls - 1].closed
        error = errors[calls]
        calls += 1
        raise error

    monkeypatch.setattr(http, "urlopen", opened)
    monkeypatch.setattr(time, "sleep", lambda _: None)
    with pytest.raises(HTTPError) as caught:
        http.fetch_text("https://example.test/source")
    assert calls == 3 and all(body.closed for body in bodies)
    assert caught.value is errors[-1]
    assert caught.value.code == 503 and caught.value.reason == "native unavailable"
    assert caught.value.headers["X-Source"] == "native"
    if close_failure:
        assert any(
            "error body cleanup failed" in note for note in caught.value.__notes__
        )
