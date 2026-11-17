"""Native response lengths must agree before a byte payload can be accepted."""

from http.client import HTTPResponse, IncompleteRead
from io import BytesIO
import socket
import ssl
from typing import cast

import pytest

from bijux_pollenomics.core import http


class _WireStream(BytesIO):
    """Observe entity reads separately from native HTTP header parsing."""

    observed = 0

    def read(self, size: int | None = -1) -> bytes:
        raw = super().read(size)
        self.observed += len(raw)
        return raw


class _Socket:
    def __init__(self, stream: _WireStream) -> None:
        self.stream = stream

    def makefile(self, *_args: object, **_kwargs: object) -> _WireStream:
        return self.stream


def _native(
    monkeypatch: pytest.MonkeyPatch,
    lengths: tuple[str, ...],
    body: bytes,
    *,
    status: int = 200,
    method: str = "GET",
    transfer_encoding: str | tuple[str, ...] | None = None,
    close_error: Exception | None = None,
) -> tuple[HTTPResponse, _WireStream, list[float]]:
    headers = b"".join(
        b"Content-Length: " + value.encode("ascii") + b"\r\n" for value in lengths
    )
    if transfer_encoding is not None:
        values = (
            (transfer_encoding,)
            if isinstance(transfer_encoding, str)
            else transfer_encoding
        )
        headers += b"".join(
            b"Transfer-Encoding: " + value.encode() + b"\r\n" for value in values
        )
    stream = _WireStream(
        f"HTTP/1.1 {status} Generated\r\n".encode()
        + headers
        + b"Connection: close\r\n\r\n"
        + body
    )

    class Response(HTTPResponse):
        def close(self) -> None:
            closed = self.closed
            super().close()
            if not closed and close_error is not None:
                raise close_error

    # HTTPResponse uses only the socket's makefile interface in this fixture.
    response = Response(cast(socket.socket, _Socket(stream)), method=method)
    response.begin()
    calls: list[float] = []

    def opened(
        _request: object, *, context: ssl.SSLContext | None, timeout: float
    ) -> HTTPResponse:
        assert context is None
        calls.append(timeout)
        return response

    monkeypatch.setattr(http, "urlopen", opened)
    return response, stream, calls


@pytest.mark.parametrize("owner", ["binary", "text", "json"])
@pytest.mark.parametrize("lengths", [("2", "3"), ("0", "1"), ("2, 3",), ("2, 2", "3")])
def test_native_conflicting_lengths_refuse_before_body(
    monkeypatch: pytest.MonkeyPatch, owner: str, lengths: tuple[str, ...]
) -> None:
    _, stream, calls = _native(monkeypatch, lengths, b"abc")
    reader = {
        "binary": http.fetch_binary,
        "text": http.fetch_text,
        "json": http.fetch_json,
    }[owner]
    with pytest.raises(ValueError, match="Content-Length"):
        reader("https://example.test/source", max_bytes=4)
    assert stream.observed == 0 and stream.closed
    assert calls == [30.0]


@pytest.mark.parametrize(
    "lengths",
    [("4",), ("04", "4"), ("4, 4",), ("04,\t004", "4"), ("0" * 5000 + "4", "4")],
)
def test_native_equivalent_decimal_lengths_recover_one_entity_boundary(
    monkeypatch: pytest.MonkeyPatch, lengths: tuple[str, ...]
) -> None:
    _, stream, calls = _native(monkeypatch, lengths, b"abcdFOLLOWING")
    assert http.fetch_binary("https://example.test/source", max_bytes=4) == b"abcd"
    assert stream.observed == 4 and stream.closed and calls == [30.0]


@pytest.mark.parametrize("lengths", [("0", "00"), ("0, 000",)])
def test_native_zero_duplicate_lengths_preserve_empty_entity(
    monkeypatch: pytest.MonkeyPatch, lengths: tuple[str, ...]
) -> None:
    _, stream, _ = _native(monkeypatch, lengths, b"FOLLOWING")
    assert http.fetch_binary("https://example.test/source", max_bytes=4) == b""
    assert stream.observed == 0 and stream.closed


@pytest.mark.parametrize(
    "value", ["-1", "+4", "4.0", "four", "", "4,", "4,,4", "4, nope"]
)
def test_native_malformed_lengths_refuse_before_body(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    _, stream, calls = _native(monkeypatch, (value,), b"abcd")
    with pytest.raises(ValueError, match="Content-Length"):
        http.fetch_binary("https://example.test/source", max_bytes=4)
    assert stream.observed == 0 and stream.closed and calls == [30.0]


@pytest.mark.parametrize("lengths", [("5, 005",), ("9" * 5000,)])
def test_native_recovered_lengths_still_refuse_oversize_before_body(
    monkeypatch: pytest.MonkeyPatch, lengths: tuple[str, ...]
) -> None:
    _, stream, _ = _native(monkeypatch, lengths, b"abcd")
    with pytest.raises(ValueError, match="byte limit"):
        http.fetch_binary("https://example.test/source", max_bytes=4)
    assert stream.observed == 0 and stream.closed


def test_native_recovered_length_preserves_short_body_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, stream, _ = _native(monkeypatch, ("4, 04",), b"abc")
    with pytest.raises(IncompleteRead) as caught:
        http.fetch_binary("https://example.test/source", max_bytes=4)
    assert caught.value.partial == b"abc" and caught.value.expected == 1
    assert stream.closed


@pytest.mark.parametrize(
    "method,status", [("HEAD", 200), ("GET", 204), ("GET", 304), ("GET", 101)]
)
def test_native_bodyless_framing_precedes_content_length(
    monkeypatch: pytest.MonkeyPatch, method: str, status: int
) -> None:
    _, stream, _ = _native(
        monkeypatch, ("999999", "bad"), b"", method=method, status=status
    )
    assert http.fetch_binary("https://example.test/source", max_bytes=4) == b""
    assert stream.observed == 0 and stream.closed


def test_native_chunked_framing_precedes_content_length(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, stream, _ = _native(
        monkeypatch,
        ("999999", "bad"),
        b"4\r\nabcd\r\n0\r\n\r\n",
        transfer_encoding="chunked",
    )
    assert http.fetch_binary("https://example.test/source", max_bytes=4) == b"abcd"
    assert stream.closed


def test_native_framing_refusal_survives_close_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, stream, calls = _native(
        monkeypatch, ("2", "3"), b"abc", close_error=OSError("cleanup failed")
    )
    with pytest.raises(ValueError, match="Content-Length") as caught:
        http.fetch_binary("https://example.test/source", max_bytes=4)
    assert any("cleanup failed" in note for note in caught.value.__notes__)
    assert stream.observed == 0 and stream.closed and calls == [30.0]


def test_generic_binary_stream_retains_legacy_non_native_header_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class LegacyStream(BytesIO):
        headers = {"Content-Length": "legacy unspecified length"}

    stream = LegacyStream(b"abcd")
    monkeypatch.setattr(http, "urlopen", lambda *_args, **_kwargs: stream)
    assert http.fetch_binary("https://example.test/source", max_bytes=4) == b"abcd"
    assert stream.closed


@pytest.mark.parametrize(
    "encoding",
    ["", "identity", "gzip", "gzip, chunked", "chunked ", "chunked; unsupported=true"],
)
@pytest.mark.parametrize("lengths", [(), ("3",), ("2", "3")])
def test_native_unsupported_transfer_framing_refuses_before_body(
    monkeypatch: pytest.MonkeyPatch, encoding: str, lengths: tuple[str, ...]
) -> None:
    _, stream, calls = _native(
        monkeypatch, lengths, b"3\r\nabc\r\n0\r\n\r\n", transfer_encoding=encoding
    )
    with pytest.raises(ValueError, match="Transfer-Encoding"):
        http.fetch_binary("https://example.test/source", max_bytes=64)
    assert stream.observed == 0 and stream.closed and calls == [30.0]


@pytest.mark.parametrize(
    "encodings",
    [("chunked", "gzip"), ("chunked", "chunked"), ("gzip", "chunked"), ("chunked", "")],
)
def test_native_repeated_transfer_fields_do_not_hide_unsupported_codings(
    monkeypatch: pytest.MonkeyPatch, encodings: tuple[str, ...]
) -> None:
    _, stream, calls = _native(
        monkeypatch, ("2", "3"), b"3\r\nabc\r\n0\r\n\r\n", transfer_encoding=encodings
    )
    with pytest.raises(ValueError, match="Transfer-Encoding"):
        http.fetch_binary("https://example.test/source", max_bytes=64)
    assert stream.observed == 0 and stream.closed and calls == [30.0]


@pytest.mark.parametrize("encoding", ["chunked", "CHUNKED", "cHuNkEd"])
@pytest.mark.parametrize("lengths", [(), ("2", "3")])
def test_native_supported_chunked_decoding_retains_precedence(
    monkeypatch: pytest.MonkeyPatch, encoding: str, lengths: tuple[str, ...]
) -> None:
    _, stream, calls = _native(
        monkeypatch, lengths, b"3\r\nabc\r\n0\r\n\r\n", transfer_encoding=encoding
    )
    assert http.fetch_binary("https://example.test/source", max_bytes=3) == b"abc"
    assert stream.closed and calls == [30.0]


@pytest.mark.parametrize("method,status", [("HEAD", 200), ("GET", 304)])
@pytest.mark.parametrize("encoding", ["gzip", "identity", ""])
def test_native_bodyless_response_does_not_require_transfer_decoding(
    monkeypatch: pytest.MonkeyPatch, method: str, status: int, encoding: str
) -> None:
    _, stream, calls = _native(
        monkeypatch,
        ("999999", "bad"),
        b"",
        method=method,
        status=status,
        transfer_encoding=encoding,
    )
    assert http.fetch_binary("https://example.test/source", max_bytes=3) == b""
    assert stream.observed == 0 and stream.closed and calls == [30.0]


def test_generic_stream_does_not_acquire_native_transfer_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class LegacyStream(BytesIO):
        headers = {"Transfer-Encoding": "opaque legacy metadata"}

    stream = LegacyStream(b"abc")
    monkeypatch.setattr(http, "urlopen", lambda *_args, **_kwargs: stream)
    assert http.fetch_binary("https://example.test/source", max_bytes=3) == b"abc"
    assert stream.closed


def test_native_transfer_refusal_preserves_primary_during_cleanup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, stream, calls = _native(
        monkeypatch,
        ("2", "3"),
        b"abc",
        transfer_encoding="gzip",
        close_error=OSError("cleanup failed"),
    )
    with pytest.raises(ValueError, match="Transfer-Encoding") as caught:
        http.fetch_binary("https://example.test/source", max_bytes=64)
    assert any("cleanup failed" in note for note in caught.value.__notes__)
    assert stream.observed == 0 and stream.closed and calls == [30.0]
