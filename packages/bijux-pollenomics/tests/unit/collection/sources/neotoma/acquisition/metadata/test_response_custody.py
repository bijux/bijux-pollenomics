"""Generated native HTTP responses retain deterministic transport cleanup."""

from http.client import HTTPResponse
from io import BytesIO
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import transport


class _ResponseStream(BytesIO):
    failure: OSError | None = None

    def read(self, size: int | None = -1) -> bytes:
        if self.failure is not None:
            raise self.failure
        return super().read(size)


def _response(
    monkeypatch: Any,
    *,
    read_error: OSError | None = None,
    response_close_error: OSError | None = None,
    connection_close_error: OSError | None = None,
) -> tuple[HTTPResponse, _ResponseStream, list[str]]:
    stream = _ResponseStream(
        b"HTTP/1.1 200 OK\r\nContent-Length: 64\r\nConnection: close\r\n\r\n"
        + b"x" * 64
    )
    events: list[str] = []

    class Socket:
        def makefile(self, *_args: Any, **_kwargs: Any) -> _ResponseStream:
            return stream

    class Response(HTTPResponse):
        def close(self) -> None:
            events.append("response.close")
            super().close()
            if response_close_error is not None:
                raise response_close_error

    response = Response(cast(Any, Socket()))
    response.begin()
    assert response.will_close
    stream.failure = read_error

    class Connection:
        def putrequest(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def putheader(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def endheaders(self) -> None:
            pass

        def getresponse(self) -> HTTPResponse:
            return response

        def close(self) -> None:
            events.append("connection.close")
            if connection_close_error is not None:
                raise connection_close_error

    monkeypatch.setattr(
        transport, "HTTPSConnection", lambda *_args, **_kwargs: Connection()
    )
    return response, stream, events


def test_truncated_entity_closes_the_detached_native_response(monkeypatch: Any) -> None:
    response, stream, events = _response(monkeypatch)
    try:
        captured = transport._fetch_response(
            "https://api.neotomadb.org/v2.0/data/taxa/1", timeout=1, max_bytes=8
        )
        assert captured.body == b"x" * 9 and captured.body_complete is False
        assert stream.closed
        assert events == ["response.close", "connection.close"]
    finally:
        HTTPResponse.close(response)


def test_primary_read_failure_survives_both_cleanup_failures(monkeypatch: Any) -> None:
    primary = OSError("generated body read failure")
    response, stream, events = _response(
        monkeypatch,
        read_error=primary,
        response_close_error=OSError("generated response close failure"),
        connection_close_error=OSError("generated connection close failure"),
    )
    try:
        with pytest.raises(OSError) as caught:
            transport._fetch_response(
                "https://api.neotomadb.org/v2.0/data/taxa/1", timeout=1, max_bytes=8
            )
        assert caught.value is primary
        assert stream.closed
        assert events == ["response.close", "connection.close"]
        assert len(primary.__notes__) == 2
    finally:
        HTTPResponse.close(response)


def test_response_cleanup_failure_still_closes_the_connection(monkeypatch: Any) -> None:
    close_error = OSError("generated response cleanup failure")
    response, stream, events = _response(monkeypatch, response_close_error=close_error)
    try:
        with pytest.raises(OSError) as caught:
            transport._fetch_response(
                "https://api.neotomadb.org/v2.0/data/taxa/1", timeout=1, max_bytes=8
            )
        assert caught.value is close_error
        assert stream.closed
        assert events == ["response.close", "connection.close"]
    finally:
        HTTPResponse.close(response)


@pytest.mark.parametrize("diagnostic", ["notes", "annotation", "format"])
def test_native_cleanup_diagnostics_preserve_primary_and_all_owners(
    monkeypatch: Any, diagnostic: str
) -> None:
    class Primary(OSError):
        def add_note(self, note: str) -> None:
            if diagnostic == "annotation":
                raise RuntimeError("annotation failed")
            super().add_note(note)

    class BrokenDiagnostic(OSError):
        def __str__(self) -> str:
            raise RuntimeError("cleanup formatting failed")

    primary = Primary("native generated read failure")
    if diagnostic == "notes":
        primary.__notes__ = ()  # type: ignore[assignment]
    secondary = (
        BrokenDiagnostic("secondary")
        if diagnostic == "format"
        else OSError("secondary response close")
    )
    response, stream, events = _response(
        monkeypatch,
        read_error=primary,
        response_close_error=secondary,
        connection_close_error=OSError("secondary connection close"),
    )
    try:
        with pytest.raises(Primary) as caught:
            transport._fetch_response(
                "https://api.neotomadb.org/v2.0/data/taxa/1", timeout=1, max_bytes=8
            )
        assert caught.value is primary
        assert stream.closed
        assert events == ["response.close", "connection.close"]
    finally:
        HTTPResponse.close(response)
