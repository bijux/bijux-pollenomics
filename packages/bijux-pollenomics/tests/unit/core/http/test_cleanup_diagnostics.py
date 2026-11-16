"""Cleanup diagnostics cannot alter HTTP primary errors or existing retry budgets."""

from email.message import Message
from io import BytesIO
import time
from typing import Any
from urllib.error import HTTPError

import pytest

from bijux_pollenomics.core import http


class _BrokenDiagnostic(OSError):
    def __str__(self) -> str:
        raise RuntimeError("cleanup formatting failed")


@pytest.mark.parametrize("owner", ["binary", "text"])
@pytest.mark.parametrize("boundary", ["read", "http_error"])
@pytest.mark.parametrize("diagnostic", ["notes", "annotation", "format"])
def test_cleanup_diagnostic_failure_preserves_native_error_and_attempt_budget(
    monkeypatch: pytest.MonkeyPatch, owner: str, boundary: str, diagnostic: str
) -> None:
    class ReadFailure(OSError):
        def add_note(self, note: str) -> None:
            if diagnostic == "annotation":
                raise RuntimeError("annotation failed")
            super().add_note(note)

    close_error = (
        _BrokenDiagnostic("secondary")
        if diagnostic == "format"
        else OSError("secondary cleanup")
    )
    calls: list[str] = []
    closed: list[str] = []
    primary: BaseException

    class Response(BytesIO):
        headers: dict[str, str] = {}

        def read(self, size: int | None = -1) -> bytes:
            raise primary

        def close(self) -> None:
            super().close()
            closed.append("response")
            raise close_error

    class NativeError(HTTPError):
        def add_note(self, note: str) -> None:
            if diagnostic == "annotation":
                raise RuntimeError("annotation failed")
            super().add_note(note)

        def close(self) -> None:
            super().close()
            closed.append("http_error")
            raise close_error

    primary = (
        NativeError(
            "https://example.test/source", 503, "native refusal", Message(), BytesIO()
        )
        if boundary == "http_error"
        else ReadFailure("native source read failure")
    )
    if diagnostic == "notes":
        primary.__notes__ = ()  # type: ignore[assignment]

    def opened(*args: Any, **kwargs: Any) -> Any:
        calls.append("request")
        if boundary == "http_error":
            raise primary
        return Response(b"source")

    monkeypatch.setattr(http, "urlopen", opened)
    monkeypatch.setattr(time, "sleep", lambda _: None)
    fetch = http.fetch_binary if owner == "binary" else http.fetch_text
    with pytest.raises(type(primary)) as caught:
        fetch("https://example.test/source", max_bytes=16)
    assert caught.value is primary
    expected = 3 if owner == "text" and boundary == "http_error" else 1
    assert len(calls) == len(closed) == expected
