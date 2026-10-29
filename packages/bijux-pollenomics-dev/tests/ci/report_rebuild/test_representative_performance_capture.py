"""Retained timing source, refusal and report ownership stay independently bound."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.representative_performance import (
    CAPTURE,
    CAPTURE_SHA256,
    OWNER,
    REPORT,
    validated_representative_performance_capture,
)
from bijux_pollenomics_dev.native_backend.retained_performance import _output_targets

Fixture = tuple[Path, dict[str, InventoryEntry], list[dict[str, Any]]]
REPOSITORY = Path(__file__).resolve().parents[5]


@pytest.fixture(scope="module")
def retained_view(tmp_path_factory: pytest.TempPathFactory) -> Fixture:
    root = tmp_path_factory.mktemp("retained-performance")
    shutil.copytree((REPOSITORY / CAPTURE).parent, (root / CAPTURE).parent)
    source = root / Path(CAPTURE).parent / "publication/report.json"
    current = root / REPORT
    current.parent.mkdir(parents=True)
    shutil.copyfile(source, current)
    raw = current.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    entry = InventoryEntry(
        REPORT.removeprefix("docs/report/"), "file", len(raw), digest, digest
    )
    owners = [
        {
            "owner_id": OWNER,
            "paths": [REPORT],
            "role": "retained_source",
            "producer_paths": [],
            "producer_inputs": [],
        }
    ]
    return root, {REPORT: entry}, owners


def test_actual_six_measurements_and_all_fourteen_outputs(
    retained_view: Fixture,
) -> None:
    entries, evidence = validated_representative_performance_capture(*retained_view)
    assert len(entries) == 1
    assert evidence["capture_sha256"] == CAPTURE_SHA256
    assert (
        evidence["primary_measurements"] == 6
        and evidence["all_worker_measurements"] == 14
    )
    assert evidence["new_timing_profile_model_compiler_R_calls"] == 0


@pytest.mark.parametrize(
    "change", ["role", "producer", "input", "missing", "duplicate", "paths", "overlap"]
)
def test_owner_contract_changes_refuse(retained_view: Fixture, change: str) -> None:
    root, tracked, original = retained_view
    owners = copy.deepcopy(original)
    if change == "role":
        owners[0]["role"] = "unresolved"
    elif change == "producer":
        owners[0]["producer_paths"] = ["unowned.py"]
    elif change == "input":
        owners[0]["producer_inputs"] = ["unowned.json"]
    elif change == "missing":
        owners.clear()
    elif change == "duplicate":
        owners.append(copy.deepcopy(owners[0]))
    elif change == "paths":
        owners[0]["paths"] = []
    else:
        owners.append(
            {"owner_id": "another", "paths": [REPORT], "role": "retained_source"}
        )
    with pytest.raises(ReportRebuildError):
        validated_representative_performance_capture(root, tracked, owners)


@pytest.mark.parametrize(
    "name",
    [
        "execution/scaling.json",
        "source-code/packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py",
        "publication/report.json",
    ],
)
def test_changed_source_or_measurement_refuses(
    retained_view: Fixture, name: str
) -> None:
    root, tracked, owners = retained_view
    path = root / Path(CAPTURE).parent / name
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\n")
        with pytest.raises(ReportRebuildError):
            validated_representative_performance_capture(root, tracked, owners)
    finally:
        path.write_bytes(original)


def test_new_hotspot_or_compiled_claim_cannot_replace_original(
    retained_view: Fixture,
) -> None:
    root, tracked, owners = retained_view
    path = root / REPORT
    original = path.read_bytes()
    body = json.loads(original)
    body["new_cpp_allowed"] = True
    try:
        path.write_text(json.dumps(body))
        with pytest.raises(ReportRebuildError):
            validated_representative_performance_capture(root, tracked, owners)
    finally:
        path.write_bytes(original)


def test_linked_transport_descendant_refuses(tmp_path: Path) -> None:
    output, outside = tmp_path / "owned", tmp_path / "outside"
    output.mkdir()
    outside.mkdir()
    (output / "docs").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="target or ancestor"):
        _output_targets(output)
    assert list(outside.iterdir()) == []


def test_absent_capture_and_unselected_owner_need_no_evidence(tmp_path: Path) -> None:
    assert validated_representative_performance_capture(tmp_path, {}, []) == ((), {})


def test_current_reader_preserves_actual_authored_measurements() -> None:
    from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
        authored_reader,
        parse_routes,
        render_route,
    )
    from bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications import (
        validate_evidence,
    )

    authority = (
        REPOSITORY
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_accounts.json"
    )
    reader = REPORT.removesuffix("report.json") + "README.md"
    route = parse_routes(authority.read_text())[reader]
    current = (REPOSITORY / reader).read_bytes()
    original = (
        REPOSITORY / Path(CAPTURE).parent / "publication/README.md"
    ).read_bytes()
    assert authored_reader(current) == original
    assert render_route(current, route) == current
    assert route.qualification is not None
    validate_evidence(REPOSITORY, route.qualification, portal=False)
    assert {row.path for row in route.qualification.evidence} == {
        REPORT,
        "docs/report/numerical-performance/native-forward/report.json",
        "docs/report/numerical-performance/native-memory/report.json",
    }


def test_current_editorial_admission_has_exact_owned_membership() -> None:
    from bijux_pollenomics_dev.ci.report_rebuild.contracts import canonical_json_sha256
    from bijux_pollenomics_dev.ci.report_rebuild.maintained_sources import (
        MAINTAINED_ROLE_PATHS,
    )

    owners = json.loads((REPOSITORY / "configs/ci/report-ownership.json").read_text())[
        "owners"
    ]
    paths = sorted(
        path
        for owner in owners
        if owner["role"] == "maintained_editorial"
        for path in owner["paths"]
    )
    count, digest = MAINTAINED_ROLE_PATHS["maintained_editorial"]
    assert len(paths) == len(set(paths)) == count
    assert canonical_json_sha256(paths) == digest
    assert REPORT.removesuffix("report.json") + "README.md" in paths
