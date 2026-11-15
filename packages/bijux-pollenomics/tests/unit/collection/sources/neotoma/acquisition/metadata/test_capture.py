from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataLimits,
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
    replay_neotoma_metadata_capture,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from .native_responses import SITE_BODY, response


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
