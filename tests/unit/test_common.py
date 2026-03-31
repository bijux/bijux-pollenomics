from __future__ import annotations

import ssl
import unittest
from urllib.error import URLError
from unittest.mock import patch

from bijux_pollenomics.core.http import fetch_binary, fetch_text


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class CommonFetchTests(unittest.TestCase):
    def test_fetch_text_does_not_disable_tls_verification_implicitly(self) -> None:
        with patch(
            "bijux_pollenomics.core.http.urlopen",
            side_effect=URLError(ssl.SSLCertVerificationError("certificate verify failed")),
        ):
            with self.assertRaises(URLError):
                fetch_text("https://example.com/data.json")

    def test_fetch_text_uses_unverified_context_only_when_requested(self) -> None:
        def fake_urlopen(request, context=None, timeout=None):  # type: ignore[no-untyped-def]
            self.assertIsNotNone(context)
            self.assertIsNone(timeout)
            return _FakeResponse(b"payload")

        with patch("bijux_pollenomics.core.http.urlopen", side_effect=fake_urlopen):
            self.assertEqual(fetch_text("https://example.com/data.json", insecure=True), "payload")

    def test_fetch_binary_uses_unverified_context_only_when_requested(self) -> None:
        def fake_urlopen(request, context=None, timeout=None):  # type: ignore[no-untyped-def]
            self.assertIsNotNone(context)
            self.assertIsNone(timeout)
            return _FakeResponse(b"\x00\x01")

        with patch("bijux_pollenomics.core.http.urlopen", side_effect=fake_urlopen):
            self.assertEqual(fetch_binary("https://example.com/data.bin", insecure=True), b"\x00\x01")


if __name__ == "__main__":
    unittest.main()
