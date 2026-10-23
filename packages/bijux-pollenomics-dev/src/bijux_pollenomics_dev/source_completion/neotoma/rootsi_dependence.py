"""Join qualified count witnesses to Rootsi metadata without merging observations.

The five retained comparisons support partial observation dependence. They do
not establish complete count equivalence, physical-core identity, an original
EPD accession, historical LandClim inputs, chronology or analytical-use rights.
Rows outside those five comparisons remain unassessed, rather than independent.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from ...ci.report_rebuild.source_paths import safe_source_file

NATIVE_REPORTS = (
    (
        "docs/report/source-relations/neotoma/abbo-native-correspondence/report.json",
        "abborrtjarne-native-count-correspondence.v1",
        "counts",
    ),
    (
        "docs/report/source-relations/neotoma/boke-native-correspondence/report.json",
        "bokesjon-native-count-correspondence.v1",
        "cell_status_counts",
    ),
    (
        "docs/report/source-relations/neotoma/bus-native-correspondence/report.json",
        "bussjosjon-native-count-correspondence.v1",
        "cell_status_counts",
    ),
)
CHRONOLOGY_REPORT = (
    "docs/report/source-relations/landclim/neotoma-chronology-witness/report.json"
)
FIELDS = (
    "neotoma_dataset_id",
    "neotoma_site_id",
    "neotoma_dependence_posture",
    "count_witness_locator",
    "count_witness_samples",
    "count_statuses_json",
    "witness_limits_json",
    "independent_corroboration_admitted",
    "physical_core_equivalence_admitted",
)


@dataclass(frozen=True)
class CountWitness:
    """A report-owned partial comparison, with its native identities and limits."""

    workbook_member: str
    workbook_sha256: str
    dataset_id: int
    site_id: int
    locator: str
    samples: int
    count_statuses_json: str
    limits_json: str


def _object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise ValueError("Rootsi count witness must be an object")
    return value


def _integer(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(
            "Rootsi count witness native identities/counts must be positive integers"
        )
    return value


def _digest(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{64}", value):
        raise ValueError("Rootsi count witness requires its original workbook identity")
    return value


def _member(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Rootsi count witness workbook member is absent")
    path = PurePosixPath(value)
    if (
        len(path.parts) != 2
        or path.parts[0] != "rootsi"
        or path.suffix != ".xls"
        or path.name in {".", ".."}
        or "\\" in value
        or str(path) != value
    ):
        raise ValueError("Rootsi count witness workbook member is invalid")
    return value


def _json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _counts(value: object) -> str:
    counts = _object(value)
    if not counts or any(type(v) is not int or v < 0 for v in counts.values()):
        raise ValueError("Rootsi count witness comparison populations are invalid")
    return _json(counts)


def _report(repository: Path, path: str, pins: Mapping[str, object]) -> dict[str, Any]:
    expected = pins.get(path)
    if not isinstance(expected, str) or not re.fullmatch("[0-9a-f]{64}", expected):
        raise ValueError(
            f"Numeric count witness lacks existing source-lock authority: {path}"
        )
    raw = safe_source_file(repository, path, "Rootsi count witness").read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"Numeric count witness bytes changed: {path}")
    return _object(json.loads(raw))


def load_witnesses(repository: Path) -> tuple[CountWitness, ...]:
    """Read four selected numerical report pins without binding the whole lock."""
    lock = _object(
        json.loads(
            safe_source_file(
                repository, "reports/source-lock.json", "Scientific source lock"
            ).read_bytes()
        )
    )
    pins = _object(lock.get("sources"))
    witnesses = []
    for path, schema, count_field in NATIVE_REPORTS:
        report = _report(repository, path, pins)
        if (
            report.get("schema_version") != schema
            or type(report.get("lra_admitted_samples")) is not int
            or report.get("lra_admitted_samples") != 0
        ):
            raise ValueError("Rootsi native count witness schema/admission changed")
        source = _object(report.get("input_sha256"))
        _digest(source.get("neotoma_raw_part"))
        limits = {
            key: value
            for key, value in report.items()
            if key
            not in {
                "schema_version",
                "neotoma_dataset_id",
                "neotoma_site_id",
                "rootsi_archive_member",
                "input_sha256",
                "samples",
                count_field,
                "workbook_taxon_labels",
                "neotoma_taxon_labels",
                "exact_shared_taxon_labels",
                "workbook_only_taxon_labels",
                "neotoma_only_taxon_labels",
            }
        }
        witnesses.append(
            CountWitness(
                _member(report.get("rootsi_archive_member")),
                _digest(source.get("rootsi_workbook")),
                _integer(report.get("neotoma_dataset_id")),
                _integer(report.get("neotoma_site_id")),
                path,
                _integer(report.get("samples")),
                _counts(report.get(count_field)),
                _json(limits),
            )
        )
    report = _report(repository, CHRONOLOGY_REPORT, pins)
    if report.get("schema_version") != "rootsi-neotoma-chronology-witness.v1":
        raise ValueError("Rootsi chronology witness schema changed")
    findings = report.get("findings")
    if not isinstance(findings, list) or len(findings) != 2:
        raise ValueError("Rootsi chronology witness comparison population changed")
    for index, value in enumerate(findings):
        item = _object(value)
        if (
            item.get("historical_landclim_input_authenticated") is not False
            or type(item.get("lra_admitted_samples")) is not int
            or item.get("lra_admitted_samples") != 0
        ):
            raise ValueError("Rootsi chronology witness admission changed")
        count_fields = {"selected_count_cell_status", "count_cell_status"} & item.keys()
        if len(count_fields) != 1:
            raise ValueError("Rootsi chronology witness count scope is ambiguous")
        count_field = count_fields.pop()
        samples = _integer(item.get("paired_depth_rows"))
        if (
            item.get("workbook_sample_rows") != samples
            or item.get("neotoma_sample_rows") != samples
        ):
            raise ValueError("Rootsi chronology witness depth populations differ")
        limits = {
            k: v
            for k, v in item.items()
            if k
            not in {
                "workbook_member",
                "workbook_sha256",
                "neotoma_dataset_id",
                "neotoma_site_id",
                count_field,
            }
        }
        witnesses.append(
            CountWitness(
                _member(item.get("workbook_member")),
                _digest(item.get("workbook_sha256")),
                _integer(item.get("neotoma_dataset_id")),
                _integer(item.get("neotoma_site_id")),
                f"{CHRONOLOGY_REPORT}#/findings/{index}",
                samples,
                _counts(item.get(count_field)),
                _json(limits),
            )
        )
    return tuple(witnesses)


def dependence_rows(
    rows: Sequence[Mapping[str, object]], witnesses: Sequence[CountWitness]
) -> list[dict[str, object]]:
    """Join only exact member/hash pairs; partial agreement never admits equivalence."""
    if len(rows) != 79 or len(witnesses) != 5:
        raise ValueError(
            "Rootsi dependence requires 79 candidates and five qualified witnesses"
        )
    by_member = {w.workbook_member: w for w in witnesses}
    if len(by_member) != 5 or len({(w.dataset_id, w.site_id) for w in witnesses}) != 5:
        raise ValueError("Rootsi dependence witness identities are duplicated")
    result = []
    used = set()
    for row in rows:
        member = _member(row.get("typed_workbook_member"))
        digest = _digest(row.get("typed_workbook_sha256"))
        if (
            member in used
            or row.get("independent_ground_truth") != "refused_candidate_overlap"
        ):
            raise ValueError("Rootsi candidate ownership/independence refusal changed")
        used.add(member)
        witness = by_member.get(member)
        if witness is not None and witness.workbook_sha256 != digest:
            raise ValueError(
                "Rootsi count witness workbook bytes differ from candidate"
            )
        extended = dict(row)
        extended.update(dict.fromkeys(FIELDS, ""))
        extended.update(
            neotoma_dependence_posture="not_assessed_by_selected_count_witnesses",
            independent_corroboration_admitted="false",
            physical_core_equivalence_admitted="false",
        )
        if witness is not None:
            extended.update(
                neotoma_dataset_id=f"neotoma:dataset:{witness.dataset_id}",
                neotoma_site_id=f"neotoma:site:{witness.site_id}",
                neotoma_dependence_posture="partial_count_correspondence_independence_not_admitted",
                count_witness_locator=witness.locator,
                count_witness_samples=witness.samples,
                count_statuses_json=witness.count_statuses_json,
                witness_limits_json=witness.limits_json,
            )
        result.append(extended)
    if not set(by_member) <= used:
        raise ValueError("Rootsi count witness has no candidate workbook member")
    return result
