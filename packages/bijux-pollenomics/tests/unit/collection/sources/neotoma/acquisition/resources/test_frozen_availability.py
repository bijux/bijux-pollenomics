"""Frozen resource schemas are qualified from authenticated source bytes offline."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourcePlan,
    capture_neotoma_resources,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.frozen import (
    qualify_neotoma_frozen_capture,
)

from .frozen_payloads import _NO_FROZEN_RECORD, capture, encode, spec


def test_successful_empty_frozen_set_is_not_absence_certified(tmp_path: Path) -> None:
    source = tmp_path / "source"
    captured = capture(source, b'{"status":"success","data":[]}')
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert (
        qualified["resources"][0]["qualification_status"]
        == "unavailable_frozen_api_empty"
    )
    assert qualified["resources"][0]["absence_certified"] is False


def test_exact_provider_frozen_unavailability_is_not_empty_or_absence_certified(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    captured = capture(
        source,
        encode(
            {
                "status": "success",
                "data": _NO_FROZEN_RECORD,
                "message": "Retrieved all tables",
            }
        ),
    )
    original = {path.name: path.read_bytes() for path in source.iterdir()}
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    row = qualified["resources"][0]
    assert row["qualification_status"] == "unavailable_frozen_record"
    assert row["absence_certified"] is False
    assert (
        row["source"]["body_sha256"]
        == sha256(
            encode(
                {
                    "status": "success",
                    "data": _NO_FROZEN_RECORD,
                    "message": "Retrieved all tables",
                }
            )
        ).hexdigest()
    )
    assert original == {path.name: path.read_bytes() for path in source.iterdir()}
    assert captured.resources[0]["terminal_status"] == "unresolved_frozen_schema"


@pytest.mark.parametrize(
    "status,message",
    [
        ("error", _NO_FROZEN_RECORD),
        (True, _NO_FROZEN_RECORD),
        ("success", "Unknown message"),
        ("success", "There is no frozen record for this dataset. invented remainder"),
        (
            "success",
            "Other text mentions no frozen record but is not an availability response",
        ),
    ],
)
def test_only_successful_exact_provider_availability_message_is_recognized(
    tmp_path: Path, status: object, message: str
) -> None:
    source = tmp_path / "source"
    captured = capture(source, encode({"status": status, "data": message}))
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert qualified["resources"][0]["qualification_status"] == "refused_frozen_native"


def test_provider_no_record_message_does_not_override_failed_http(
    tmp_path: Path,
) -> None:
    content = encode({"status": "success", "data": _NO_FROZEN_RECORD})
    source = tmp_path / "source"
    captured = capture_neotoma_resources(
        source,
        plan=NeotomaResourcePlan((spec(),), "b" * 64),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 404, (), content),
    )
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert (
        qualified["resources"][0]["qualification_status"]
        == "not_qualified_source_result"
    )
    assert qualified["resources"][0]["source_terminal_status"] == "unavailable_http"


@pytest.mark.parametrize("success", [False, 0])
def test_provider_availability_does_not_override_contradictory_success_field(
    tmp_path: Path, success: object
) -> None:
    source = tmp_path / "source"
    captured = capture(
        source,
        encode({"status": "success", "success": success, "data": _NO_FROZEN_RECORD}),
    )
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert qualified["resources"][0]["qualification_status"] == "refused_frozen_native"


@pytest.mark.parametrize(
    "status,data,expected",
    [
        ("success", [], "unavailable_frozen_api_empty"),
        ("success", _NO_FROZEN_RECORD, "unavailable_frozen_record"),
        ("error", _NO_FROZEN_RECORD, "refused_frozen_native"),
        ("success", "Unknown message", "refused_frozen_native"),
    ],
)
def test_snapshot_availability_keeps_existing_source_error_distinctions(
    tmp_path: Path, status: str, data: object, expected: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import frozen

    source = tmp_path / "source"
    captured = capture(source, encode({"status": status, "data": data}))
    result = frozen.qualify_neotoma_frozen_snapshot_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert result["resources"][0]["qualification_status"] == expected
