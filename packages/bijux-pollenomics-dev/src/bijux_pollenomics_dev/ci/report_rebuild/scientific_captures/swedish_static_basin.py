"""Transport fixed scientific captures and a native figure without replay claims."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import _regular_confined_file

FAMILY = "docs/report/pollen-reconstruction/swedish-static-basin-scenarios"
OWNER = "pollen-reconstruction/swedish-static-basin-scenarios/scientific-capture"
# Each pin admits an independently retained source/decision/capture projection.
# Capture custody preserves its actual original scope; transporting these bytes
# does not run a model, renderer, observation capture or qualified review again.
CAPTURE_PINS = {
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/assumptions/source-reconciliation.json": "c88355fa3ad588e91261f6906884e2d68fe6968dc6f1aa4eccb36ae04b94cb6e",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/actual-runs.json": "7f063989a7a33f7deae9b46733eb967150405bfe5357579c2c6f3ad19638efcf",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/figure-capture.json": "43bf80dfa7aa2b9561010d9f70936535974e4bc2e072800db87bda0684aa9b1c",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/import-observation-capture.json": "5c14f017773f7cd1ae93eeac7cfed6bc217fe4d6c32dc41b13d7e40186acbc90",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/independent-math-review.json": "bbe0fa0fb324ff7eaa4b2a295d6624c31ab58cdc364720887e5d2064f3e3fc8a",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/maintained-producer-capture.json": "2c0a7a5b1810ac1afcc439f07aa6648399da90c4bcb110fa80d803f58fd42238",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/observed-imports.json": "e59d28594db8344907777ed3567c83773c1f3afe868835bc534afb04ad79256d",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/figures/panel-comparison.png": "1c5cd34d7cb28cb9d60a01a86e124a4f23226f67893abaee1be86af92f410ed6",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/inputs/engine-source-identities.json": "f6c5f6e885210505884305c144cbaffbdda43b129dcda2ace89a752b93fea5cb",
}
OWNER_PATHS = {
    OWNER: [
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/assumptions/source-reconciliation.json",
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/actual-runs.json",
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/figure-capture.json",
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/import-observation-capture.json",
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/independent-math-review.json",
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/maintained-producer-capture.json",
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/observed-imports.json",
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/inputs/engine-source-identities.json",
    ],
    "pollen-reconstruction/swedish-static-basin-scenarios/figure-native-capture": [
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/figures/panel-comparison.png"
    ],
}
NATIVE_FIGURE_AUTHORITY = {
    "original_candidate": "19858168e2d1c6f565c585bda4b5d22a8bbb440c",
    "actual_plan_sha256": "b74fe3eda156b4fb267193eb3bb1cb498dc4abab6cae913e671aff7606e90946",
    "actual_terminal_sha256": "ddfa56a61c1761e15d092d8cc08831ce76205d80358a333250aadc77ab2ad872",
    "original_Rscript_sha256": "58d830b0975f48d1b34696510ba7ecaf032db4be74c1070af6ce214b3abc73d2",
    "original_R_executable_sha256": "15e31d349bf5e18974e729ceff13c94138e9522b861f91c655ec6d9c421c2615",
    "original_R_revision_record_sha256": "26223d2029a1c8eeb96c17be32ae4c6fa556879b4bc1edf55f125676bfbfaab5",
    "source_csv_sha256": "b0c1b150b0bb2345e5cdbccb554538b8af6000833bf840561791c76f842ca278",
    "renderer_sha256": "b093e8c2254ad710da8f71db2e2dabe3c78f87eafb9927ba87cf8e3bbcde7db0",
    "png_sha256": "1c5cd34d7cb28cb9d60a01a86e124a4f23226f67893abaee1be86af92f410ed6",
    "native_scope": (
        "The actual original R4.6 Quartz renderer consumed the exact CSV; "
        "native exit 0 does not establish original CSV derivation authority. "
        "Current transport copies admitted PNG bytes without current R execution. "
        "CSV generation is separately qualified by its maintained projection; "
        "final actual R, browser and portable-document coverage remains separate."
    ),
}


def validated_swedish_static_basin_captures(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Refuse altered, partial or aliased capture families on current transport."""
    rows = [row for row in owners if row.get("owner_id") in OWNER_PATHS]
    active = bool(rows) or any(
        name.startswith(FAMILY + "/") for name in tracked_by_path
    )
    if not active:
        return (), {}
    retained_rows = [
        row
        for row in owners
        if row.get("role") == "retained_source"
        and any(
            isinstance(name, str) and name.startswith(FAMILY + "/")
            for name in row.get("paths", [])
        )
    ]
    if len(rows) != len(OWNER_PATHS) or retained_rows != rows:
        raise ReportRebuildError("Swedish scientific capture owner differs")
    for owner, paths in OWNER_PATHS.items():
        matching = [row for row in rows if row.get("owner_id") == owner]
        if len(matching) != 1:
            raise ReportRebuildError("Swedish scientific capture owner differs")
        row = matching[0]
        if (
            row.get("role") != "retained_source"
            or row.get("paths") != paths
            or row.get("producer_paths") != []
            or row.get("producer_inputs") != []
        ):
            raise ReportRebuildError("Swedish scientific capture declaration differs")
    accepted = []
    for name, expected in sorted(CAPTURE_PINS.items()):
        try:
            path = _regular_confined_file(
                repository, name, "Swedish scientific capture"
            )
            body = path.read_bytes()
            valid_format = (
                body.startswith(b"\x89PNG\r\n\x1a\n")
                if name.endswith(".png")
                else isinstance(json.loads(body), dict)
            )
            entry = tracked_by_path.get(name)
        except (OSError, ValueError) as error:
            raise ReportRebuildError(
                "Swedish scientific capture input refused"
            ) from error
        if (
            not valid_format
            or entry is None
            or entry.kind != "file"
            or entry.size != len(body)
            or entry.sha256 != expected
            or hashlib.sha256(body).hexdigest() != expected
        ):
            raise ReportRebuildError("Swedish scientific capture bytes changed")
        accepted.append(entry)
    return tuple(accepted), {
        "owner_paths": dict(OWNER_PATHS),
        "native_figure_capture_authority": dict(NATIVE_FIGURE_AUTHORITY),
        "reviewed_capture_sha256": dict(CAPTURE_PINS),
        "paths": [entry.path for entry in accepted],
        "source_scope": (
            "Eight exact immutable JSON source/decision captures and one actual native PNG, "
            "maintained-producer, import-observation, figure and independent "
            "mathematical review projections. Actual original candidate/source/"
            "native receipt authority remains in each bound source record. "
            "Current custody does not repeat any numerical computation or "
            "confer new scientific review, source rights, R parity, historical "
            "reproduction, reader qualification or vegetation accuracy."
        ),
    }
