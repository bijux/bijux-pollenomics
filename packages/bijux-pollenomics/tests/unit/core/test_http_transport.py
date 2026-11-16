from __future__ import annotations

from http.client import HTTPResponse, IncompleteRead
from importlib import import_module
from io import BytesIO
import math
from pathlib import Path
import ssl
from unittest.mock import call, patch
from urllib.error import HTTPError, URLError

import pytest

from bijux_pollenomics.core import http


class Response(BytesIO):
    def __init__(self, payload: bytes, *, length: str | None = None) -> None:
        super().__init__(payload)
        self.headers = {} if length is None else {"Content-Length": length}
        self.requests: list[int] = []
        self.observed = 0

    def read(self, size: int = -1) -> bytes:
        self.requests.append(size)
        block = super().read(size)
        self.observed += len(block)
        return block


@pytest.fixture(autouse=True)
def isolated_transport(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    monkeypatch.delenv(http.INSECURE_TLS_ENV_VAR, raising=False)
    with patch.object(http, "urlopen") as opener, patch.object(http.time, "sleep"):
        yield opener


def test_binary_default_is_bounded_and_uses_finite_socket_timeout(isolated_transport):  # type: ignore[no-untyped-def]
    response = Response(b"source")
    isolated_transport.return_value = response
    assert http.fetch_binary("https://example.test/source") == b"source"
    assert isolated_transport.call_args.kwargs["timeout"] == 30.0
    assert all(0 < size <= 64 * 1024 for size in response.requests)
    assert response.closed


@pytest.mark.parametrize("payload", [b"", b"abc", b"abcd"])
def test_binary_accepts_complete_payload_up_to_exact_bound(payload, isolated_transport):  # type: ignore[no-untyped-def]
    response = Response(payload)
    isolated_transport.return_value = response
    assert http.fetch_binary("https://example.test/source", max_bytes=4) == payload
    assert response.requests[-1] <= 5 - len(payload)


@pytest.mark.parametrize("length", [None, "1", "invalid", "-1"])
def test_observed_overflow_reads_only_limit_plus_sentinel(length, isolated_transport):  # type: ignore[no-untyped-def]
    response = Response(b"x" * 100, length=length)
    isolated_transport.return_value = response
    with pytest.raises(ValueError, match="byte limit"):
        http.fetch_binary("https://example.test/source", max_bytes=4)
    assert response.observed == 5
    assert response.closed
    isolated_transport.assert_called_once()


def test_oversized_content_length_refuses_before_body(isolated_transport):  # type: ignore[no-untyped-def]
    response = Response(b"source", length="5")
    isolated_transport.return_value = response
    with pytest.raises(ValueError, match="byte limit"):
        http.fetch_binary("https://example.test/source", max_bytes=4)
    assert response.observed == 0
    assert response.closed


def test_long_zero_padded_content_length_remains_valid(isolated_transport):  # type: ignore[no-untyped-def]
    isolated_transport.return_value = Response(b"abcd", length="0" * 5000 + "4")
    assert http.fetch_binary("https://example.test/source", max_bytes=4) == b"abcd"


def test_long_oversized_content_length_has_policy_error(isolated_transport):  # type: ignore[no-untyped-def]
    response = Response(b"abcd", length="9" * 5000)
    isolated_transport.return_value = response
    with pytest.raises(ValueError, match="byte limit"):
        http.fetch_binary("https://example.test/source", max_bytes=4)
    assert response.observed == 0


def test_short_reads_continue_until_eof(isolated_transport):  # type: ignore[no-untyped-def]
    class ShortResponse(Response):
        def read(self, size: int = -1) -> bytes:
            return super().read(min(size, 1))

    response = ShortResponse(b"abc")
    isolated_transport.return_value = response
    assert http.fetch_binary("https://example.test/source", max_bytes=3) == b"abc"
    assert response.observed == 3
    assert len(response.requests) == 4


@pytest.mark.parametrize("limit", [None, True, False, 0, -1, 1.5, "4"])
def test_invalid_byte_policy_fails_before_io(limit, isolated_transport):  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError, match="max_bytes"):
        http.fetch_binary("https://example.test/source", max_bytes=limit)
    isolated_transport.assert_not_called()


@pytest.mark.parametrize(
    "timeout", [None, True, False, 0, -1, math.inf, math.nan, "30", 10**1000]
)
def test_invalid_timeout_fails_before_io(timeout, isolated_transport):  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError, match="timeout"):
        http.fetch_binary("https://example.test/source", timeout=timeout)
    isolated_transport.assert_not_called()


def test_default_size_refuses_declared_32_mib_plus_one(isolated_transport):  # type: ignore[no-untyped-def]
    isolated_transport.return_value = Response(b"", length=str(32 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match="byte limit"):
        http.fetch_binary("https://example.test/source")


def test_explicit_larger_bound_and_legacy_positional_arguments(isolated_transport):  # type: ignore[no-untyped-def]
    isolated_transport.return_value = Response(b"source")
    assert (
        http.fetch_binary(
            "https://example.test/source",
            {"X-Source": "public"},
            True,
            max_bytes=40 * 1024 * 1024,
            timeout=12,
        )
        == b"source"
    )
    kwargs = isolated_transport.call_args.kwargs
    assert kwargs["timeout"] == 12
    assert kwargs["context"].verify_mode == ssl.CERT_NONE


def forbidden() -> HTTPError:
    return HTTPError("https://example.test/source", 403, "forbidden", {}, BytesIO())


def test_403_browser_retry_keeps_verified_tls_and_caller_headers(isolated_transport):  # type: ignore[no-untyped-def]
    error = forbidden()
    failed_body = error.fp
    isolated_transport.side_effect = [error, Response(b"source")]
    assert (
        http.fetch_binary("https://example.test/source", {"X-Source": "public"})
        == b"source"
    )
    calls = isolated_transport.call_args_list
    assert len(calls) == 2
    assert all(c.kwargs["context"] is None for c in calls)
    assert all(c.kwargs["timeout"] == 30 for c in calls)
    request = calls[1].args[0]
    assert request.get_header("User-agent") == "Mozilla/5.0"
    assert request.get_header("X-source") == "public"
    assert failed_body.closed


def test_403_preserves_explicit_user_agent(isolated_transport):  # type: ignore[no-untyped-def]
    isolated_transport.side_effect = [forbidden(), Response(b"source")]
    http.fetch_binary("https://example.test/source", {"User-Agent": "source-client"})
    assert (
        isolated_transport.call_args.args[0].get_header("User-agent") == "source-client"
    )


@pytest.mark.parametrize("status", [401, 404, 500])
def test_terminal_http_error_preserves_native_identity(status, isolated_transport):  # type: ignore[no-untyped-def]
    error = HTTPError(
        "https://example.test/source", status, "native reason", {"X": "Y"}, BytesIO()
    )
    failed_body = error.fp
    isolated_transport.side_effect = error
    with pytest.raises(HTTPError) as caught:
        http.fetch_binary("https://example.test/source")
    assert caught.value is error
    assert caught.value.code == status
    assert caught.value.reason == "native reason"
    assert caught.value.headers["X"] == "Y"
    assert failed_body.closed
    isolated_transport.assert_called_once()


def test_repeated_403_raises_final_native_error(isolated_transport):  # type: ignore[no-untyped-def]
    first, last = forbidden(), forbidden()
    isolated_transport.side_effect = [first, last]
    with pytest.raises(HTTPError) as caught:
        http.fetch_binary("https://example.test/source")
    assert caught.value is last
    assert isolated_transport.call_count == 2


def test_transient_exhaustion_has_three_total_attempts(isolated_transport):  # type: ignore[no-untyped-def]
    error = URLError(OSError("synthetic unavailable"))
    isolated_transport.side_effect = error
    with patch.object(http.time, "sleep") as sleep, pytest.raises(URLError) as caught:
        http.fetch_binary("https://example.test/source")
    assert caught.value is error
    assert isolated_transport.call_count == 3
    assert sleep.call_args_list == [call(1.0), call(2.0)]


def test_403_and_timeout_share_retry_budget(isolated_transport):  # type: ignore[no-untyped-def]
    error = TimeoutError("socket timed out")
    isolated_transport.side_effect = [forbidden(), error, error]
    with pytest.raises(TimeoutError) as caught:
        http.fetch_binary("https://example.test/source")
    assert caught.value is error
    assert isolated_transport.call_count == 3


@pytest.mark.parametrize("authorized", [False, True])
def test_certificate_retry_requires_environment_opt_in(
    authorized, isolated_transport, monkeypatch
):  # type: ignore[no-untyped-def]
    error = URLError(ssl.SSLCertVerificationError("certificate verify failed"))
    isolated_transport.side_effect = [error, Response(b"source")]
    if authorized:
        monkeypatch.setenv(http.INSECURE_TLS_ENV_VAR, "1")
        assert http.fetch_binary("https://example.test/source") == b"source"
        assert (
            isolated_transport.call_args.kwargs["context"].verify_mode == ssl.CERT_NONE
        )
    else:
        with pytest.raises(URLError) as caught:
            http.fetch_binary("https://example.test/source")
        assert caught.value is error
        isolated_transport.assert_called_once()


def test_partial_read_failure_closes_response_and_restarts_bound(isolated_transport):  # type: ignore[no-untyped-def]
    class BrokenResponse(Response):
        def read(self, size: int = -1) -> bytes:
            if self.observed:
                raise TimeoutError("partial read failed")
            return super().read(min(size, 2))

    failed = BrokenResponse(b"abcd")
    success = Response(b"abcd")
    isolated_transport.side_effect = [failed, success]
    assert http.fetch_binary("https://example.test/source", max_bytes=4) == b"abcd"
    assert failed.closed and success.closed
    assert failed.observed + success.observed <= 2 * 5


def test_certificate_403_and_transient_share_attempt_limit(
    isolated_transport, monkeypatch
):  # type: ignore[no-untyped-def]
    monkeypatch.setenv(http.INSECURE_TLS_ENV_VAR, "1")
    error = TimeoutError("last attempt")
    isolated_transport.side_effect = [
        URLError(ssl.SSLCertVerificationError("certificate verify failed")),
        forbidden(),
        error,
    ]
    with pytest.raises(TimeoutError) as caught:
        http.fetch_binary("https://example.test/source")
    assert caught.value is error
    assert isolated_transport.call_count == 3


@pytest.mark.parametrize("owner", ["catalog", "collection"])
def test_landclim_binary_refusal_preserves_existing_capture(
    owner, tmp_path: Path, isolated_transport
):  # type: ignore[no-untyped-def]
    facade = import_module(f"bijux_pollenomics.collection.sources.landclim.{owner}")
    raw = tmp_path / "raw"
    raw.mkdir()
    prior = raw / "retained-original.bin"
    prior.write_bytes(b"prior capture")
    isolated_transport.return_value = Response(b"", length=str(32 * 1024 * 1024 + 1))
    with (
        patch.object(
            facade,
            "resolve_landclim_asset_urls",
            return_value={
                "landclim_ii_contributors.xlsx": "https://example.test/source",
            },
        ),
        pytest.raises(ValueError, match="byte limit"),
    ):
        facade.download_landclim_raw_assets(raw)
    assert prior.read_bytes() == b"prior capture"
    assert list(raw.iterdir()) == [prior]


@pytest.mark.parametrize("insecure", ["false", 1, 0, None, [], {}])
def test_tls_policy_requires_exact_boolean_before_io(insecure, isolated_transport):  # type: ignore[no-untyped-def]
    isolated_transport.return_value = Response(b"abc")
    with pytest.raises(ValueError, match="insecure"):
        http.fetch_binary("https://example.test/source", insecure=insecure)
    isolated_transport.assert_not_called()


def native_response(body=b"abc", length=3, *, read_error=None, close_error=None):  # type: ignore[no-untyped-def]
    class MemoryFile(BytesIO):
        def read(self, size=-1):  # type: ignore[no-untyped-def]
            if read_error is not None:
                raise read_error
            return super().read(size)

        def close(self):  # type: ignore[no-untyped-def]
            super().close()
            if close_error is not None:
                raise close_error

    stream = MemoryFile(
        b"HTTP/1.1 200 OK\r\nContent-Length: "
        + str(length).encode()
        + b"\r\n\r\n"
        + body
    )
    socket = type("MemorySocket", (), {"makefile": lambda *_args: stream})()
    response = HTTPResponse(socket)
    response.begin()
    return response, stream


def test_native_short_body_retains_incomplete_read_evidence(isolated_transport):  # type: ignore[no-untyped-def]
    response, stream = native_response(length=5)
    isolated_transport.return_value = response
    with pytest.raises(IncompleteRead) as caught:
        http.fetch_binary("https://example.test/source", max_bytes=5)
    assert caught.value.partial == b"abc"
    assert caught.value.expected == 2
    assert stream.closed
    isolated_transport.assert_called_once()


def test_cleanup_failure_does_not_mask_byte_refusal(isolated_transport):  # type: ignore[no-untyped-def]
    response, stream = native_response(
        b"abcde", 5, close_error=RuntimeError("cleanup failed")
    )
    isolated_transport.return_value = response
    with pytest.raises(ValueError, match="byte limit") as caught:
        http.fetch_binary("https://example.test/source", max_bytes=4)
    assert any("cleanup failed" in note for note in caught.value.__notes__)
    assert stream.closed
    isolated_transport.assert_called_once()


def test_native_timeout_keeps_identity_and_cleanup_notes_across_retries(
    isolated_transport,
):  # type: ignore[no-untyped-def]
    primary = TimeoutError("native body timeout")
    responses = [
        native_response(read_error=primary, close_error=RuntimeError("cleanup failed"))
        for _ in range(3)
    ]
    isolated_transport.side_effect = [response for response, _ in responses]
    with pytest.raises(TimeoutError) as caught:
        http.fetch_binary("https://example.test/source", max_bytes=3)
    assert caught.value is primary
    assert len([note for note in primary.__notes__ if "cleanup failed" in note]) == 3
    assert all(stream.closed for _, stream in responses)
    assert isolated_transport.call_count == 3


def test_successful_read_cleanup_error_propagates_without_retry(isolated_transport):  # type: ignore[no-untyped-def]
    cleanup = TimeoutError("successful body close failed")

    class CloseFailure(Response):
        def close(self):  # type: ignore[no-untyped-def]
            super().close()
            raise cleanup

    isolated_transport.return_value = CloseFailure(b"abc")
    with pytest.raises(TimeoutError) as caught:
        http.fetch_binary("https://example.test/source", max_bytes=3)
    assert caught.value is cleanup
    isolated_transport.assert_called_once()
