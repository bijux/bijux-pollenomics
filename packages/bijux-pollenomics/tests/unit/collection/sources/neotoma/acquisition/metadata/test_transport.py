from __future__ import annotations

import json
from pathlib import Path
import ssl

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataPlan,
    capture_neotoma_metadata,
)
import bijux_pollenomics.collection.sources.neotoma.capture.transport as capture_module
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from .native_responses import SITE_BODY


@pytest.mark.parametrize("truncated", [False, True])
def test_real_capture_transport_verifies_tls_and_sends_recorded_headers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, truncated: bool
) -> None:
    monkeypatch.setenv("BIJUX_POLLENOMICS_ALLOW_INSECURE_TLS", "1")

    class Connection:
        status = 200

        def __init__(
            self, host: str, *, timeout: float, context: ssl.SSLContext
        ) -> None:
            assert host == "api.neotomadb.org"
            assert timeout == 45.0
            assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
            self.headers: list[tuple[str, str]] = []

        def putrequest(
            self,
            method: str,
            target: str,
            *,
            skip_host: bool,
            skip_accept_encoding: bool,
        ) -> None:
            assert (method, target) == ("GET", "/v2.0/data/sites/12/datasets")
            assert skip_host and skip_accept_encoding

        def putheader(self, name: str, value: str) -> None:
            self.headers.append((name, value))

        def endheaders(self) -> None:
            assert self.headers == [
                ("Host", "api.neotomadb.org"),
                ("Accept", "application/json"),
                ("Accept-Encoding", "identity"),
                ("User-Agent", "bijux-pollenomics"),
                ("Connection", "close"),
            ]

        def getresponse(self) -> Connection:
            return self

        def read(self, maximum: int) -> bytes:
            assert maximum == 2 * 1024 * 1024 + 1
            return SITE_BODY[:-1] if truncated else SITE_BODY

        def getheaders(self) -> list[tuple[str, str]]:
            return [("Content-Length", str(len(SITE_BODY)))]

        def close(self) -> None:
            pass

    monkeypatch.setattr(capture_module, "HTTPSConnection", Connection)
    output = tmp_path / "capture"
    if truncated:
        with pytest.raises(ValueError):
            capture_neotoma_metadata(output, plan=NeotomaMetadataPlan(site_ids=(12,)))
        receipt = json.loads(
            (
                build_staging_output_dir(output) / "site-12-datasets.receipt.json"
            ).read_bytes()
        )
        assert receipt["body_complete"] is False
    else:
        assert capture_neotoma_metadata(
            output, plan=NeotomaMetadataPlan(site_ids=(12,))
        ).site_responses == {12: SITE_BODY}
