from __future__ import annotations

import ssl
from types import TracebackType
import unittest
from unittest.mock import patch
from urllib.error import URLError

from bijux_pollenomics.core.http import INSECURE_TLS_ENV_VAR, fetch_binary, fetch_text


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class CommonFetchTests(unittest.TestCase):
    def test_fetch_text_does_not_disable_tls_verification_implicitly(self) -> None:
        with (
            patch(
                "bijux_pollenomics.core.http.urlopen",
                side_effect=URLError(
                    ssl.SSLCertVerificationError("certificate verify failed")
                ),
            ),
            self.assertRaises(URLError),
        ):
            fetch_text("https://example.com/data.json")

    def test_fetch_text_uses_unverified_context_only_when_requested(self) -> None:
        def fake_urlopen(request, context=None, timeout=None):  # type: ignore[no-untyped-def]
            self.assertIsNotNone(context)
            self.assertIsNone(timeout)
            return _FakeResponse(b"payload")

        with patch("bijux_pollenomics.core.http.urlopen", side_effect=fake_urlopen):
            self.assertEqual(
                fetch_text("https://example.com/data.json", insecure=True), "payload"
            )

    def test_fetch_binary_uses_unverified_context_only_when_requested(self) -> None:
        def fake_urlopen(request, context=None, timeout=None):  # type: ignore[no-untyped-def]
            self.assertIsNotNone(context)
            self.assertIsNone(timeout)
            return _FakeResponse(b"\x00\x01")

        with patch("bijux_pollenomics.core.http.urlopen", side_effect=fake_urlopen):
            self.assertEqual(
                fetch_binary("https://example.com/data.bin", insecure=True), b"\x00\x01"
            )

    def test_fetch_text_retries_with_unverified_context_when_env_flag_is_enabled(
        self,
    ) -> None:
        call_contexts: list[object] = []

        def fake_urlopen(request, context=None, timeout=None):  # type: ignore[no-untyped-def]
            call_contexts.append(context)
            if len(call_contexts) == 1:
                raise URLError(
                    ssl.SSLCertVerificationError("certificate verify failed")
                )
            return _FakeResponse(b"payload")

        with (
            patch.dict("os.environ", {INSECURE_TLS_ENV_VAR: "1"}, clear=False),
            patch("bijux_pollenomics.core.http.urlopen", side_effect=fake_urlopen),
        ):
            self.assertEqual(fetch_text("https://example.com/data.json"), "payload")

        self.assertIsNone(call_contexts[0])
        self.assertIsNotNone(call_contexts[1])

    def test_fetch_text_retries_transient_network_errors(self) -> None:
        with (
            patch(
                "bijux_pollenomics.core.http.urlopen",
                side_effect=[
                    URLError(OSError(51, "Network is unreachable")),
                    _FakeResponse(b"payload"),
                ],
            ),
            patch("bijux_pollenomics.core.http.time.sleep"),
        ):
            self.assertEqual(fetch_text("https://example.com/data.json"), "payload")

    def test_fetch_text_reraises_last_transient_network_error_after_retry_exhaustion(
        self,
    ) -> None:
        with (
            patch(
                "bijux_pollenomics.core.http.urlopen",
                side_effect=[
                    URLError(OSError(51, "Network is unreachable")),
                    URLError(OSError(51, "Network is unreachable")),
                    URLError(OSError(51, "Network is unreachable")),
                ],
            ),
            patch("bijux_pollenomics.core.http.time.sleep"),
            self.assertRaises(URLError),
        ):
            fetch_text("https://example.com/data.json")


if __name__ == "__main__":
    unittest.main()
