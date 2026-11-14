from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import ssl

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataLimits,
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
    replay_neotoma_metadata_capture,
)
import bijux_pollenomics.collection.sources.neotoma.capture.transport as capture_module
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

SITE_BODY = b'{"status":"success","data":[{"site":{"siteid":12,"collectionunitid":100,"unittype":"Core","datasets":[{"datasetid":201,"datasettype":"pollen"}]}}]}'


def response(url: str, body: bytes = SITE_BODY) -> NeotomaMetadataResponse:
    return NeotomaMetadataResponse(
        final_url=url,
        http_status=200,
        headers=(
            ("Content-Length", str(len(body))),
            ("X-Source", "a"),
            ("X-Source", "b"),
        ),
        body=body,
    )


def test_metadata_capture_preserves_entity_and_duplicate_headers(
    tmp_path: Path,
) -> None:
    output = tmp_path / "capture"

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        assert url == "https://api.neotomadb.org/v2.0/data/sites/12/datasets"
        return response(url)

    result = capture_neotoma_metadata(
        output, plan=NeotomaMetadataPlan(site_ids=(12,)), fetch=fetch
    )
    assert result.site_responses == {12: SITE_BODY}
    replay = replay_neotoma_metadata_capture(
        output, expected_manifest_sha256=result.manifest_sha256
    )
    assert replay.site_responses == {12: SITE_BODY}
    receipt = json.loads((output / "site-12-datasets.receipt.json").read_bytes())
    assert receipt["response_headers"][-2:] == [["X-Source", "a"], ["X-Source", "b"]]
    assert receipt["tls_mode"] == "verified_no_insecure_fallback"
    assert receipt["requested_url"] == receipt["final_url"]


@pytest.mark.parametrize(
    "body",
    [
        b'{"status":"error","data":[]}',
        b'{"status":"success"}',
        b'{"data":[]}',
        b'{"status":"success","data":[null]}',
        b'{"status":"success","data":[{"site":{"siteid":999}}]}',
    ],
)
def test_metadata_capture_keeps_refused_body_without_complete_manifest(
    tmp_path: Path, body: bytes
) -> None:
    output = tmp_path / "capture"
    with pytest.raises(ValueError):
        capture_neotoma_metadata(
            output,
            plan=NeotomaMetadataPlan(site_ids=(12,)),
            fetch=lambda url, **_: response(url, body),
        )
    staging = build_staging_output_dir(output)
    assert not output.exists()
    assert (staging / "site-12-datasets.body").read_bytes() == body
    assert (staging / "refusal.json").is_file()
    assert not (staging / "capture-manifest.json").exists()


def test_metadata_capture_keeps_successes_when_later_transport_fails(
    tmp_path: Path,
) -> None:
    output = tmp_path / "capture"

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        if "/sites/13/" in url:
            raise TimeoutError("bounded source timeout")
        return response(url)

    with pytest.raises(TimeoutError):
        capture_neotoma_metadata(
            output, plan=NeotomaMetadataPlan(site_ids=(12, 13)), fetch=fetch
        )
    staging = build_staging_output_dir(output)
    assert (staging / "site-12-datasets.body").read_bytes() == SITE_BODY
    receipt = json.loads((staging / "site-13-datasets.receipt.json").read_bytes())
    assert receipt["terminal_status"] == "transport_failure"
    assert "TimeoutError" in receipt["error"]
    assert not (staging / "capture-manifest.json").exists()


@pytest.mark.parametrize(
    "kind", ["http_error", "truncated", "body_limit", "length_mismatch", "redirect"]
)
def test_metadata_capture_refuses_incomplete_or_unbound_transport(
    tmp_path: Path, kind: str
) -> None:
    output = tmp_path / "capture"

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        item = response(url)
        if kind == "http_error":
            return replace(item, http_status=503)
        if kind == "truncated":
            return replace(item, body_complete=False)
        if kind == "body_limit":
            return replace(item, body=b"x" * 1025)
        if kind == "length_mismatch":
            return replace(item, headers=(("Content-Length", "999"),))
        return replace(item, final_url="https://example.org/metadata")

    with pytest.raises(ValueError):
        capture_neotoma_metadata(
            output,
            plan=NeotomaMetadataPlan(site_ids=(12,)),
            limits=NeotomaMetadataLimits(max_response_bytes=1024),
            fetch=fetch,
        )
    assert not output.exists()
    assert (build_staging_output_dir(output) / "refusal.json").is_file()


def test_metadata_capture_does_not_replace_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "capture"
    output.mkdir()
    (output / "original").write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        capture_neotoma_metadata(
            output,
            plan=NeotomaMetadataPlan(site_ids=(12,)),
            fetch=lambda *_args, **_kwargs: pytest.fail("must not fetch"),
        )
    assert (output / "original").read_bytes() == b"preserve"


def test_metadata_replay_refuses_body_drift_without_network(tmp_path: Path) -> None:
    output = tmp_path / "capture"
    capture_neotoma_metadata(
        output,
        plan=NeotomaMetadataPlan(site_ids=(12,)),
        fetch=lambda url, **_: response(url),
    )
    (output / "site-12-datasets.body").write_bytes(b"{}")
    with pytest.raises(ValueError, match="identity"):
        replay_neotoma_metadata_capture(output)


def test_inventory_metadata_requires_short_page_and_unique_units(
    tmp_path: Path,
) -> None:
    body = b'{"status":"success","data":[{"site":{"siteid":12,"collectionunitid":100,"datasets":[{"datasetid":201,"datasettype":"pollen"}]}}]}'
    calls = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        calls.append(url)
        return response(
            url, body if len(calls) == 1 else b'{"status":"success","data":[]}'
        )

    result = capture_neotoma_metadata(
        tmp_path / "capture",
        plan=NeotomaMetadataPlan(
            inventory_bbox=(4.0, 54.0, 35.0, 72.0), inventory_limits=(1,)
        ),
        fetch=fetch,
    )
    assert len(calls) == 2
    assert len(result.inventory_rows[1]) == 1
    assert "offset=1" in calls[1]

    with pytest.raises(ValueError, match="duplicate"):
        capture_neotoma_metadata(
            tmp_path / "repeated",
            plan=NeotomaMetadataPlan(
                inventory_bbox=(4.0, 54.0, 35.0, 72.0), inventory_limits=(1,)
            ),
            fetch=lambda url, **_: response(url, body),
        )


@pytest.mark.parametrize(
    "limits",
    [
        NeotomaMetadataLimits(max_requests=1),
        NeotomaMetadataLimits(max_total_bytes=100),
        NeotomaMetadataLimits(max_pages_per_inventory=1),
    ],
)
def test_metadata_capture_enforces_declared_quotas(
    tmp_path: Path, limits: NeotomaMetadataLimits
) -> None:
    with pytest.raises(ValueError, match="limit|budget|termination"):
        capture_neotoma_metadata(
            tmp_path / "capture",
            plan=NeotomaMetadataPlan(
                inventory_bbox=(4.0, 54.0, 35.0, 72.0), inventory_limits=(1,)
            ),
            limits=limits,
            fetch=lambda url, **_: response(url),
        )


def test_metadata_replay_enforces_callers_stricter_page_budget(tmp_path: Path) -> None:
    output = tmp_path / "capture"
    calls = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        calls.append(url)
        return response(
            url, SITE_BODY if len(calls) == 1 else b'{"status":"success","data":[]}'
        )

    capture_neotoma_metadata(
        output,
        plan=NeotomaMetadataPlan(
            inventory_bbox=(4.0, 54.0, 35.0, 72.0), inventory_limits=(1,)
        ),
        fetch=fetch,
    )
    with pytest.raises(ValueError, match="budget|termination"):
        replay_neotoma_metadata_capture(
            output, limits=NeotomaMetadataLimits(max_pages_per_inventory=1)
        )


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


def rewrite_json(path: Path, payload: object) -> str:
    content = json.dumps(payload).encode()
    path.write_bytes(content)
    return sha256(content).hexdigest()


@pytest.mark.parametrize(
    "malformation",
    [
        "plan_not_object",
        "limits_not_object",
        "site_ids_null",
        "site_ids_nested",
        "inventory_limits_nested",
        "unknown_plan_field",
        "record_not_object",
    ],
)
def test_metadata_replay_refuses_malformed_control_objects_with_value_error(
    tmp_path: Path, malformation: str
) -> None:
    output = tmp_path / "capture"
    capture_neotoma_metadata(
        output,
        plan=NeotomaMetadataPlan(site_ids=(12,)),
        fetch=lambda url, **_: response(url),
    )
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    plan_path = output / "request-plan.json"
    plan = json.loads(plan_path.read_bytes())
    if malformation == "plan_not_object":
        plan["plan"] = None
    elif malformation == "limits_not_object":
        plan["limits"] = []
    elif malformation == "site_ids_null":
        plan["plan"]["site_ids"] = None
    elif malformation == "site_ids_nested":
        plan["plan"]["site_ids"] = [[]]
    elif malformation == "inventory_limits_nested":
        plan["plan"]["inventory_bbox"] = [4.0, 54.0, 35.0, 72.0]
        plan["plan"]["inventory_limits"] = [[]]
    elif malformation == "unknown_plan_field":
        plan["plan"]["endpoint"] = "downloads/201"
    else:
        manifest["records"] = [None]
    manifest["plan_sha256"] = rewrite_json(plan_path, plan)
    rewrite_json(manifest_path, manifest)
    with pytest.raises(ValueError):
        replay_neotoma_metadata_capture(output)


@pytest.mark.parametrize("role", ["site", "inventory"])
def test_metadata_capture_refuses_numerical_outcomes_in_metadata_endpoint(
    tmp_path: Path, role: str
) -> None:
    payload = json.loads(SITE_BODY)
    payload["data"][0]["site"]["datasets"][0]["samples"] = [{"datum": [{"value": 12}]}]
    body = json.dumps(payload).encode()
    plan = (
        NeotomaMetadataPlan(site_ids=(12,))
        if role == "site"
        else NeotomaMetadataPlan(
            inventory_bbox=(4.0, 54.0, 35.0, 72.0), inventory_limits=(400,)
        )
    )
    with pytest.raises(ValueError, match="metadata|outcome"):
        capture_neotoma_metadata(
            tmp_path / "capture", plan=plan, fetch=lambda url, **_: response(url, body)
        )


def test_metadata_replay_refuses_backward_sequential_request_times(
    tmp_path: Path,
) -> None:
    output = tmp_path / "capture"

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        source = json.loads(SITE_BODY)
        if "/sites/13/" in url:
            source["data"][0]["site"]["siteid"] = 13
        return response(url, json.dumps(source).encode())

    capture_neotoma_metadata(
        output, plan=NeotomaMetadataPlan(site_ids=(12, 13)), fetch=fetch
    )
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    first = json.loads((output / "site-12-datasets.receipt.json").read_bytes())
    second_path = output / "site-13-datasets.receipt.json"
    second = json.loads(second_path.read_bytes())
    second["utc_start"] = manifest["capture_utc_start"]
    second["utc_end"] = first["utc_end"]
    manifest["records"][1]["receipt_sha256"] = rewrite_json(second_path, second)
    rewrite_json(manifest_path, manifest)
    with pytest.raises(ValueError, match="time|sequential"):
        replay_neotoma_metadata_capture(output)
