"""Pure HTTP/parser/refusal controls; never open a network connection."""

from __future__ import annotations

import copy
from email.message import Message
import hashlib
import io
from pathlib import Path
import ssl
import sys
import tempfile
import time
from typing import Any
import unittest
from unittest.mock import patch
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).absolute().parent))
from acquire import Redirects, bounded_body, fetch
from contracts import (
    PAGE,
    PDF,
    PDF_BYTES,
    PDF_SHA,
    RETAINED,
    guide_bytes,
    https_url,
    literal_pdf_link,
    response_headers,
    validate_response,
)
from observe import validate_claims
from prepare import native_aliases
from runtime_custody import aliases_unchanged

R = Path(__file__).absolute().parents[3]


def record(body: bytes, kind: str = "page") -> dict[str, Any]:
    url = PAGE if kind == "page" else PDF
    return {
        "requested_url": url,
        "final_url": url,
        "status": 200,
        "headers": [
            ("Content-Type", "text/html" if kind == "page" else "application/pdf")
        ],
        "redirects": [],
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "started_UTC": "2026-10-14T01:02:03+00:00",
        "completed_UTC": "2026-10-14T01:02:04+00:00",
    }


class Controls(unittest.TestCase):
    def test_declared_native_parent_aliases_bind_targets_and_literal_links(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).parent / "preflight"
        ) as folder:
            root = Path(folder)
            target = root / "cellar" / "library"
            target.mkdir(parents=True)
            library = target / "library.dylib"
            library.write_bytes(b"controlled native library")
            entry = root / "opt"
            entry.symlink_to(Path("cellar/library"))
            from contracts import pin

            authority = [
                {"lexical_path": str(entry / "library.dylib"), "target": pin(library)}
            ]
            aliases, links = native_aliases(authority)
            self.assertEqual(aliases, {str(entry): str(target)})
            self.assertTrue(aliases_unchanged(aliases, link_text=links))
            entry.unlink()
            entry.symlink_to(target)
            self.assertFalse(aliases_unchanged(aliases, link_text=links))
            other = root / "other"
            other.mkdir()
            (other / "library.dylib").write_bytes(b"controlled native library")
            entry.unlink()
            entry.symlink_to(other)
            self.assertFalse(aliases_unchanged(aliases, link_text=links))
            with self.assertRaises(ValueError):
                native_aliases(authority)
            self.assertEqual(native_aliases([]), ({}, {}))

    def test_literal_absolute_and_relative_href(self) -> None:
        for href in [PDF, PDF.removeprefix("https://www.slu.se")]:
            raw = (
                f'<html><a href="{href}">Information about dataset</a></html>'.encode()
            )
            link = literal_pdf_link(raw, PAGE)
            self.assertEqual(link["resolved_pdf_url"], PDF)
            self.assertEqual(link["matches"][0]["literal_href"], href)
            self.assertIn(href, link["matches"][0]["raw_start_tag"])

    def test_comments_or_script_strings_are_not_links(self) -> None:
        for raw in [
            f'<!-- <a href="{PDF}">guide</a> -->',
            f"<script>const link='<a href=\"{PDF}\">guide</a>';</script>",
        ]:
            with self.assertRaises(ValueError):
                literal_pdf_link(raw.encode(), PAGE)

    def test_missing_or_other_guide_is_not_inferred(self) -> None:
        for href in [
            "https://other.invalid/guide.pdf",
            PDF + "?version=other",
            PDF + "#guide",
            PDF.replace("info-data", "other-data"),
        ]:
            with self.assertRaises(ValueError):
                literal_pdf_link(
                    f'<a href="{href}">Information about dataset</a>'.encode(), PAGE
                )

    def test_duplicate_href_and_invalid_UTF8_refuse(self) -> None:
        with self.assertRaises(ValueError):
            literal_pdf_link(f'<a href="{PDF}" href="{PDF}">guide</a>'.encode(), PAGE)
        with self.assertRaises(UnicodeDecodeError):
            literal_pdf_link(b"\xff", PAGE)

    def test_hosts_scheme_userinfo_and_port_are_closed(self) -> None:
        https_url(PAGE)
        https_url(PDF)
        https_url("https://slu.se/official")
        for value in [
            "http://www.slu.se/x",
            "https://www.slu.se.evil/x",
            "https://user@www.slu.se/x",
            "https://www.slu.se:8443/x",
            "file:///guide",
            "https://www.slu.se/x#f",
            "https://www.slu.se/x\n",
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                https_url(value)

    def test_redirects_are_checked_before_request(self) -> None:
        handler = Redirects(time.monotonic() + 10)
        headers = Message()
        headers["Location"] = "/official"
        next_request = handler.redirect_request(
            Request(PAGE), None, 302, "", headers, "https://www.slu.se/official"
        )
        self.assertEqual(next_request.full_url, "https://www.slu.se/official")
        headers.replace_header("Location", "https://other.invalid/x")
        with self.assertRaises(ValueError):
            handler.redirect_request(
                Request(PAGE), None, 302, "", headers, "https://other.invalid/x"
            )

    def test_redirect_count_and_duplicate_location_refuse(self) -> None:
        handler = Redirects(time.monotonic() + 10)
        headers = Message()
        headers["Location"] = "/official"
        handler.rows = [{}] * 3
        with self.assertRaises(ValueError):
            handler.redirect_request(
                Request(PAGE), None, 302, "", headers, "https://www.slu.se/official"
            )
        handler.rows = []
        headers["Location"] = "/other"
        with self.assertRaises(ValueError):
            handler.redirect_request(
                Request(PAGE), None, 302, "", headers, "https://www.slu.se/official"
            )

    def test_body_budget_empty_and_deadline_refuse(self) -> None:
        self.assertEqual(
            bounded_body(io.BytesIO(b"123"), 3, time.monotonic() + 1), b"123"
        )
        for body, limit, deadline in [
            (b"1234", 3, time.monotonic() + 1),
            (b"", 3, time.monotonic() + 1),
            (b"123", 3, time.monotonic() - 1),
        ]:
            with self.assertRaises(ValueError):
                bounded_body(io.BytesIO(body), limit, deadline)

    def test_header_encoding_length_and_media_refuse(self) -> None:
        response_headers([("Content-Type", "application/pdf")], "pdf")
        for rows in [
            [("Content-Type", "application/pdf"), ("Content-Encoding", "gzip")],
            [("Content-Type", "text/html")],
            [("Content-Type", "application/pdf"), ("Content-Length", "999999")],
            [("Content-Type", "application/pdf"), ("Content-Type", "application/pdf")],
        ]:
            with self.assertRaises(ValueError):
                response_headers(rows, "pdf")

    def test_response_status_body_redirect_and_UTC_bound(self) -> None:
        body = b"<html>official</html>"
        valid = record(body)
        validate_response(valid, PAGE, body, "page")
        for key, replacement in [
            ("status", True),
            ("status", 404),
            ("sha256", "a" * 64),
            ("bytes", 0),
            ("final_url", "https://other.invalid/x"),
            ("completed_UTC", "2026-10-14T00:00:00+00:00"),
            ("completed_UTC", "2026-10-14T01:02:04+01:00"),
        ]:
            changed = copy.deepcopy(valid)
            changed[key] = replacement
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_response(changed, PAGE, body, "page")

    def test_response_content_length_cannot_relabel_actual_bytes(self) -> None:
        body = b"official"
        valid = record(body)
        valid["headers"].append(("Content-Length", str(len(body))))
        validate_response(valid, PAGE, body, "page")
        valid["headers"][-1] = ("Content-Length", "1")
        with self.assertRaises(ValueError):
            validate_response(valid, PAGE, body, "page")

    def test_actual_retained_PDF_is_sealed_source_only(self) -> None:
        raw = (R / RETAINED).read_bytes()
        guide_bytes(raw, raw)
        self.assertEqual(len(raw), PDF_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), PDF_SHA)
        for changed in [raw[:-1], raw[:-1] + bytes([raw[-1] ^ 1])]:
            with self.assertRaises(ValueError):
                guide_bytes(changed, raw)
        with self.assertRaises(ValueError):
            guide_bytes(raw, raw + b" ")

    def test_current_claims_cannot_recover_original_history(self) -> None:
        plan = {
            "candidate": "controlled",
            "retained_guide": {"sha256": PDF_SHA, "bytes": PDF_BYTES},
        }
        report = {
            "schema_version": "current-official-slu-guide-retrieval.v1",
            "candidate": "controlled",
            "actual_exit": 0,
            "current_retrieval_only": True,
            "original_2026_09_21_acquisition_recovered": False,
            "historical_a063_receipt_recovered": False,
            "workbook_or_outcome_requests": 0,
            "same_raw_PDF_bytes": True,
            "retained_guide": plan["retained_guide"],
        }
        validate_claims(report, plan)
        for key, replacement in [
            ("candidate", "other"),
            ("actual_exit", False),
            ("original_2026_09_21_acquisition_recovered", True),
            ("historical_a063_receipt_recovered", True),
            ("workbook_or_outcome_requests", 1),
            ("workbook_or_outcome_requests", False),
            ("same_raw_PDF_bytes", False),
        ]:
            bad = {**report, key: replacement}
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_claims(bad, plan)

    def test_fetch_transport_TLS_and_no_proxy_are_explicit(self) -> None:
        body = b"<html>official</html>"

        class Response:
            status = 200
            headers = Message()
            headers["Content-Type"] = "text/html"

            def __init__(self) -> None:
                self.stream = io.BytesIO(body)

            def __enter__(self) -> Response:
                return self

            def __exit__(self, *args: object) -> None:
                pass

            def geturl(self) -> str:
                return PAGE

            def read(self, size: int) -> bytes:
                return self.stream.read(size)

        class Opener:
            def open(self, request: Request, timeout: float) -> Response:
                self.request = request
                return Response()

        opener = Opener()
        ca = Path(ssl.get_default_verify_paths().openssl_cafile).resolve()
        with patch("acquire.build_opener", return_value=opener) as build:
            raw, result = fetch(PAGE, "page", ca, time.monotonic() + 10)
        self.assertEqual(raw, body)
        self.assertTrue(result["TLS"]["hostname_verification"])
        self.assertTrue(result["TLS"]["certificate_verification_required"])
        self.assertEqual(build.call_args.args[0].proxies, {})
        self.assertEqual(opener.request.get_header("Accept-encoding"), "identity")
        with patch("acquire.build_opener") as build:
            build.return_value.open.side_effect = ssl.SSLError("controlled TLS refusal")
            with self.assertRaises(ssl.SSLError):
                fetch(PAGE, "page", ca, time.monotonic() + 10)
            self.assertEqual(build.return_value.open.call_count, 1)


if __name__ == "__main__":
    unittest.main()
