"""Account for a selected Krageholm chronology and literal regional panel support."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import inspect
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any, cast

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..physical_forward.inputs import decode, require
from .native_panel_source import buffer

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/krageholm-regional-source-support/protocol.json"
)
SOURCE: dict[str, Any] = {
    "path": "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-005.json",
    "bytes": 23953555,
    "sha256": "93a673c6fa66522667be2292cda076489330cbe1b5da8cea6b000d9c124c10cc",
}
IDENTITY = {
    "site_id": 3204,
    "dataset_id": 23013,
    "collection_unit_id": 16622,
    "handle": "KRAGMJNY",
    "source_sample_count": 96,
}
CHRONOLOGY: dict[str, Any] = {
    "selected_id": 13366,
    "selected_name": "Giesecke et al. 2014 (MADCAP)",
    "selected_native_type": "Calibrated radiocarbon years BP",
    "reference_epoch_ad": 1950,
    "native_collection_default_reference": 13365,
    "source_default_flags": {"13365": True, "13366": True},
}
TAXA = ({"label": "Betula", "taxon_id": 29}, {"label": "Ulmus", "taxon_id": 310})
WINDOWS = tuple((year, year + 500) for year in range(2700, 5700, 500))


def mapping(value: object) -> dict[str, Any]:
    require(
        type(value) is dict and all(type(key) is str for key in value),
        "Native JSON object required",
    )
    return cast(dict[str, Any], value)


def objects(value: object) -> list[dict[str, Any]]:
    require(type(value) is list, "Native JSON row array required")
    return [mapping(row) for row in cast(list[object], value)]


def integer(value: object) -> bool:
    return type(value) is int and value >= 0


def finite(value: object) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(cast(float, value))
    except OverflowError:
        return False


def count_state(row: dict[str, Any]) -> str:
    if "value" not in row:
        return "missing_native_value"
    if row["value"] is None:
        return "null_native_value"
    if not integer(row["value"]):
        return "invalid_count"
    return "measured_zero" if row["value"] == 0 else "measured"


def count_metadata(row: dict[str, Any]) -> bool:
    return (
        row.get("element") == row.get("elementtype") == "pollen"
        and row.get("units") == "NISP"
        and "context" in row
        and row["context"] is None
    )


def literal_panel(datum: list[dict[str, Any]]) -> dict[str, Any]:
    taxa = []
    counts: list[int | None] = []
    for taxon in TAXA:
        matches = [
            (i, row)
            for i, row in enumerate(datum)
            if row.get("variablename") == taxon["label"]
            or row.get("taxonid") == taxon["taxon_id"]
        ]
        labels = [
            (i, row) for i, row in matches if row.get("variablename") == taxon["label"]
        ]
        count = None
        if not labels:
            status = "id_label_conflict" if matches else "missing_literal"
        elif len(labels) != 1:
            status = "duplicate_literal"
        elif (
            len(matches) != 1
            or labels[0][1].get("taxonid") != taxon["taxon_id"]
            or not integer(labels[0][1].get("taxonid"))
        ):
            status = "id_label_conflict"
        elif not count_metadata(labels[0][1]):
            status = "incompatible_metadata"
        else:
            status = count_state(labels[0][1])
            if status in {"measured", "measured_zero"}:
                count = labels[0][1]["value"]
        counts.append(count)
        taxa.append(
            {
                **taxon,
                "status": status,
                "native_matches": [
                    {"datum_index": i, "native": deepcopy(row)} for i, row in matches
                ],
            }
        )
    complete = all(count is not None for count in counts)
    return {
        "taxa": taxa,
        "panel_counts": counts,
        "panel_complete": complete,
        "panel_N": sum(cast(list[int], counts)) if complete else None,
    }


def pollen_mass(datum: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [
        (i, row)
        for i, row in enumerate(datum)
        if row.get("element") == "pollen" or row.get("elementtype") == "pollen"
    ]
    ids = Counter(
        row.get("taxonid") for _, row in candidates if integer(row.get("taxonid"))
    )
    labels = Counter(
        row.get("variablename")
        for _, row in candidates
        if type(row.get("variablename")) is str
    )
    statuses: Counter[str] = Counter()
    problems = []
    known = 0
    for index, row in candidates:
        identity_valid = (
            integer(row.get("taxonid"))
            and type(row.get("variablename")) is str
            and bool(row["variablename"])
        )
        metadata_valid = count_metadata(row)
        value_state = count_state(row)
        if (
            identity_valid
            and metadata_valid
            and value_state in {"measured", "measured_zero"}
        ):
            known += row["value"]
        if not identity_valid:
            status = "invalid_native_identity"
        elif not metadata_valid:
            status = "incompatible_metadata"
        elif value_state not in {"measured", "measured_zero"}:
            status = value_state
        elif ids[row["taxonid"]] != 1 or labels[row["variablename"]] != 1:
            status = "duplicate_pollen_identity"
        else:
            status = "valid_pollen_NISP"
        statuses[status] += 1
        if status != "valid_pollen_NISP":
            problems.append(
                {"datum_index": index, "status": status, "native": deepcopy(row)}
            )
    non_pollen = len(datum) - len(candidates)
    statuses["non_pollen"] = non_pollen
    complete = bool(candidates) and not problems
    return {
        "datum_row_count": len(datum),
        "datum_status_counts": dict(statuses),
        "pollen_row_count": len(candidates),
        "non_pollen_row_count": non_pollen,
        "known_valid_pollen_cell_sum": known,
        "pollen_denominator_status": "complete"
        if complete
        else "refused_invalid_or_duplicate_pollen_rows",
        "pollen_N": known if complete else None,
        "pollen_problems": problems,
    }


def selected_age(sample: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    claims = objects(sample["ages"])
    matches = [
        claim
        for claim in claims
        if type(claim.get("chronologyid")) is int and claim["chronologyid"] == 13366
    ]
    if not matches:
        return "missing_selected_age", None
    if len(matches) != 1:
        return "duplicate_selected_age", None
    selected = deepcopy(matches[0])
    if (
        selected.get("agetype") != CHRONOLOGY["selected_native_type"]
        or selected.get("chronologyname") != CHRONOLOGY["selected_name"]
    ):
        return "incompatible_selected_age_type_or_name", selected
    if not finite(selected.get("age")) or any(
        key not in selected or (selected[key] is not None and not finite(selected[key]))
        for key in ("ageyounger", "ageolder")
    ):
        return "invalid_selected_age_value", selected
    if (
        selected["ageyounger"] is not None and selected["ageyounger"] > selected["age"]
    ) or (selected["ageolder"] is not None and selected["ageolder"] < selected["age"]):
        return "conflicting_selected_age_bounds", selected
    return "selected_typed_point", selected


def sample_account(sample: dict[str, Any], index: int) -> dict[str, Any]:
    datum = objects(sample["datum"])
    age_status, selected = selected_age(sample)
    window = None
    if age_status != "selected_typed_point":
        disposition = "unassignable_selected_age"
    else:
        assert selected is not None
        matches = [
            list(window)
            for window in WINDOWS
            if window[0] <= selected["age"] < window[1]
        ]
        require(len(matches) <= 1, "Overlapping requested windows")
        window = matches[0] if matches else None
        disposition = (
            "negative_native_age_retained"
            if selected["age"] < 0
            else "in_requested_window"
            if window
            else "outside_requested_windows"
        )
    panel, mass = literal_panel(datum), pollen_mass(datum)
    panel_n, pollen_n = panel["panel_N"], mass["pollen_N"]
    require(
        panel_n is None or pollen_n is None or 0 <= panel_n <= pollen_n,
        "Panel exceeds complete literal pollen denominator",
    )
    return {
        "native_sample_index": index,
        "sample_id": sample["sampleid"],
        "analysisunit_id": sample.get("analysisunitid"),
        "native_depth": sample.get("depth"),
        "native_thickness": sample.get("thickness"),
        "native_ages": deepcopy(sample["ages"]),
        "selected_age": selected,
        "selected_age_status": age_status,
        "age_disposition": disposition,
        "window": window,
        **panel,
        **mass,
        "excluded_pollen_N": pollen_n - panel_n
        if pollen_n is not None and panel_n is not None
        else None,
    }


def aggregate(samples: list[dict[str, Any]], unassignable: list[int]) -> dict[str, Any]:
    panel_defined = (
        bool(samples)
        and not unassignable
        and all(row["panel_complete"] for row in samples)
    )
    full_defined = (
        bool(samples)
        and not unassignable
        and all(row["pollen_denominator_status"] == "complete" for row in samples)
    )
    counts = (
        [sum(row["panel_counts"][axis] for row in samples) for axis in range(2)]
        if panel_defined
        else None
    )
    panel_n = sum(counts) if counts is not None else None
    pollen_n = sum(row["pollen_N"] for row in samples) if full_defined else None
    status = (
        "suppressed_unassignable_age"
        if unassignable
        else "empty_window"
        if not samples
        else "suppressed_incomplete_panel"
        if not panel_defined
        else "suppressed_zero_panel"
        if panel_n == 0
        else "suppressed_full_mass"
        if not full_defined
        else "supported"
    )
    return {
        "sample_ids": [row["sample_id"] for row in samples],
        "member_count": len(samples),
        "unassignable_source_sample_ids": unassignable,
        "status": status,
        "panel_counts": counts,
        "panel_N": panel_n,
        "pollen_N": pollen_n,
        "excluded_pollen_N": pollen_n - panel_n
        if pollen_n is not None and panel_n is not None
        else None,
    }


def project(source: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    """Account for every source owner before any window support is admitted."""
    require(
        protocol["schema_version"] == "krageholm-regional-literal-panel-protocol.v1"
        and protocol["source"] == SOURCE
        and protocol["identity"] == IDENTITY
        and protocol["chronology"] == CHRONOLOGY
        and protocol["taxa"] == list(TAXA)
        and protocol["windows"] == [list(window) for window in WINDOWS],
        "Prospective source/identity/chronology/panel/window contract differs",
    )
    sites = [mapping(row["site"]) for row in objects(source["rows"])]
    selected = [
        site for site in sites if mapping(site["dataset"]).get("datasetid") == 23013
    ]
    require(len(selected) == 1, "One exact selected source dataset required")
    site = selected[0]
    unit, dataset = (
        mapping(site["collectionunit"]),
        mapping(mapping(site["collectionunit"])["dataset"]),
    )
    require(
        type(site.get("siteid")) is int
        and site["siteid"] == 3204
        and type(unit.get("collectionunitid")) is int
        and unit["collectionunitid"] == 16622
        and unit.get("handle") == "KRAGMJNY"
        and type(dataset.get("datasetid")) is int
        and dataset["datasetid"] == 23013
        and dataset.get("datasettype") == "pollen",
        "Native nested site/unit/dataset identity differs",
    )
    require(
        type(unit.get("defaultchronology")) is int
        and unit["defaultchronology"] == 13365,
        "Native collection chronology reference differs",
    )
    declarations = [mapping(row["chronology"]) for row in objects(unit["chronologies"])]
    require(
        all(type(row.get("chronologyid")) is int for row in declarations)
        and len({row["chronologyid"] for row in declarations}) == len(declarations),
        "Ambiguous chronology declaration IDs",
    )
    selected_chronologies = [
        row for row in declarations if row["chronologyid"] == 13366
    ]
    require(
        len(selected_chronologies) == 1, "Selected13366 chronology declaration missing"
    )
    flags = {
        str(row["chronologyid"]): mapping(row["chronology"]).get("isdefault")
        for row in declarations
    }
    require(
        all(
            flags.get(key) is value
            for key, value in CHRONOLOGY["source_default_flags"].items()
        ),
        "Both literal native default flags must be preserved",
    )
    metadata = mapping(selected_chronologies[0]["chronology"])
    require(
        metadata.get("chronologyname") == CHRONOLOGY["selected_name"]
        and metadata.get("modelagetype") == CHRONOLOGY["selected_native_type"],
        "Explicit selected chronology name/type differs",
    )
    native_samples = objects(dataset["samples"])
    ids = [sample.get("sampleid") for sample in native_samples]
    require(
        len(native_samples) == 96
        and all(integer(value) for value in ids)
        and len(set(ids)) == 96,
        "All96unique native sample owners required",
    )
    samples = [
        sample_account(sample, index) for index, sample in enumerate(native_samples)
    ]
    unassignable = [
        row["sample_id"]
        for row in samples
        if row["age_disposition"] == "unassignable_selected_age"
    ]
    windows = [
        {
            "window": list(window),
            **aggregate(
                [row for row in samples if row["window"] == list(window)], unassignable
            ),
        }
        for window in WINDOWS
    ]
    source_totals = aggregate(samples, [])
    source_totals["known_valid_pollen_cell_sum"] = sum(
        row["known_valid_pollen_cell_sum"] for row in samples
    )
    return {
        "schema_version": "krageholm-regional-source-support.v1",
        "status": "literal_source_support_accounted",
        "source": dict(SOURCE),
        "identity": dict(IDENTITY),
        "chronology": {
            "selected_chronology_id": 13366,
            "selected_native_metadata": deepcopy(metadata),
            "native_collection_default_reference": unit["defaultchronology"],
            "source_chronology_declarations": [
                {
                    "chronology_id": row["chronologyid"],
                    "native_metadata": deepcopy(mapping(row["chronology"])),
                }
                for row in declarations
            ],
            "reference_epoch_ad": 1950,
            "selection_policy": "explicit_selected_chronology_not_generic_default",
        },
        "samples": samples,
        "windows": windows,
        "population": {
            "samples": len(samples),
            "age_disposition_counts": dict(
                Counter(row["age_disposition"] for row in samples)
            ),
            "selected_age_status_counts": dict(
                Counter(row["selected_age_status"] for row in samples)
            ),
            "panel_complete_samples": sum(row["panel_complete"] for row in samples),
            "full_mass_complete_samples": sum(
                row["pollen_denominator_status"] == "complete" for row in samples
            ),
        },
        "source_totals": source_totals,
        "support_summary": {
            "supported_windows": sum(row["status"] == "supported" for row in windows),
            "window_status_counts": dict(Counter(row["status"] for row in windows)),
            "literal_taxon_state_counts": dict(
                Counter(taxon["status"] for row in samples for taxon in row["taxa"])
            ),
            "datum_status_counts": dict(
                sum((Counter(row["datum_status_counts"]) for row in samples), Counter())
            ),
        },
        "engine_calls": 0,
        "model_fits": 0,
        "source_acquisition": False,
        "scientific_or_field_admission": False,
        "scope": protocol["scope"],
        "suppression_semantics": protocol["suppression_semantics"],
        "rights_and_attribution": protocol["rights_and_attribution"],
    }


def source_revision(repository: Path) -> str:
    files = [
        Path(__file__),
        repository / PROTOCOL,
        *[
            Path(inspect.getfile(function))
            for function in (buffer, decode, require_absent_artifact_output)
        ],
    ]
    relative = sorted({str(path.resolve().relative_to(repository)) for path in files})
    git = ["git", "-C", str(repository)]
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    for command in (
        [*git, "ls-files", "--error-unmatch", "--", *relative],
        [*git, "diff", "--exit-code", revision, "--", *relative],
    ):
        subprocess.run(command, check=True, capture_output=True)
    return revision


def publish(repository: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    destination = require_absent_artifact_output(repository, output)
    revision = source_revision(repository)
    protocol = decode((repository / PROTOCOL).read_bytes())
    raw = buffer(
        repository / SOURCE["path"],
        str(SOURCE["sha256"]),
        int(SOURCE["bytes"]),
        protocol["source_max_bytes"],
    )
    result = project(decode(raw), protocol)
    result["source_commit"] = revision
    require(
        buffer(
            repository / SOURCE["path"],
            str(SOURCE["sha256"]),
            int(SOURCE["bytes"]),
            protocol["source_max_bytes"],
        )
        == raw
        and source_revision(repository) == revision,
        "Consumed source changed during literal panel audit",
    )
    result["elapsed_seconds"] = time.monotonic() - started
    body = json.dumps(result, indent=2, allow_nan=False) + "\n"
    require(
        result["elapsed_seconds"] <= protocol["resource_budget"]["wall_seconds"]
        and len(body.encode()) <= protocol["resource_budget"]["output_bytes"],
        "Literal source audit runtime/output budget exceeded",
    )
    destination.mkdir()
    (destination / "result.json").write_text(body)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.repository, args.output)
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_commit": result["source_commit"],
                "population": result["population"],
                "support_summary": result["support_summary"],
                "elapsed_seconds": result["elapsed_seconds"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
