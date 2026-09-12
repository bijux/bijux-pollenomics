"""Exercise the real bounded transport class with controlled response streams."""

from __future__ import annotations

from io import BytesIO
from urllib.request import Request

import pytest

from bijux_pollenomics_dev.ci.lra_reference import remote
from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal


class FakeOpener:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.requests: list[Request] = []

    def open(self, request: Request, timeout: int) -> BytesIO:
        assert timeout == 15
        assert request.get_method() == "GET"
        self.requests.append(request)
        return BytesIO(self.data)


def test_actual_reader_constructor_and_body(monkeypatch: pytest.MonkeyPatch) -> None:
    opener = FakeOpener(b'{"value":1}')
    monkeypatch.setattr(remote, "build_opener", lambda _redirect: opener)
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-token")
    reader = remote.GitHubReader()
    assert reader.read("/repos/example/pollenomics/actions/runs") == b'{"value":1}'
    assert opener.requests[0].get_header("Authorization") == "Bearer synthetic-token"


def test_actual_reader_byte_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    opener = FakeOpener(b"oversize")
    monkeypatch.setattr(remote, "build_opener", lambda _redirect: opener)
    monkeypatch.setattr(remote, "MAX_RESPONSE_BYTES", 3)
    with pytest.raises(ReferenceRefusal, match="byte limit"):
        remote.GitHubReader().read("/repos/example/pollenomics/actions/runs")


def test_actual_reader_overall_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    times = iter([0.0, 301.0])
    monkeypatch.setattr(
        "bijux_pollenomics_dev.ci.lra_reference.remote.time.monotonic",
        lambda: next(times),
    )
    reader = remote.GitHubReader()
    with pytest.raises(ReferenceRefusal, match="deadline"):
        reader.read("/repos/example/pollenomics/actions/runs")


def test_cross_host_redirect_drops_credentials() -> None:
    request = Request(
        "https://api.github.com/repos/example/pollenomics/actions/artifacts/1/zip",
        headers={"Authorization": "Bearer synthetic-token"},
    )
    redirected = remote._SafeRedirect().redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://synthetic.blob.core.windows.net/artifact.zip",
    )
    assert redirected is not None
    assert redirected.get_header("Authorization") is None
    with pytest.raises(ReferenceRefusal, match="HTTPS"):
        remote._SafeRedirect().redirect_request(
            request, None, 302, "Found", {}, "http://example.org/artifact.zip"
        )
