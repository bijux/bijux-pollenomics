"""SEAD point evidence for governed boundary review."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..models import JsonObject, PointEvidence
from ..serialization import (
    _object_rows,
    _optional_text,
    _read_json_object,
    _required_int,
    _required_number,
)
from .records import _artifact_records, _lineage


def _load_sead_points(
    root: Path,
) -> tuple[str, list[PointEvidence], list[JsonObject]]:
    decisions_path = Path(
        "data/sead/raw/acquisitions/"
        "sead-live-d1fd2058913372eda1c12e526e0eb7c8a6cec415e9f9e9b5b92b8896597b35ac/"
        "country-decisions.json"
    )
    source_path = decisions_path.parent / "payloads/tbl_sites.json"
    payload = _read_json_object(root / decisions_path)
    rows = _object_rows(payload, "decisions", decisions_path)
    points: list[PointEvidence] = []
    for index, row in enumerate(rows):
        decision = row.get("decision")
        if not isinstance(decision, Mapping):
            raise TypeError(f"SEAD country decision is invalid at row {index}")
        site_id = _required_int(row.get("site_id"), "SEAD site ID")
        governed_code = _optional_text(row.get("governed_country_code"))
        points.append(
            PointEvidence(
                source_family="sead",
                source_scope="four_country_expected",
                source_record_id=f"sead:site:{site_id}",
                longitude=_required_number(row.get("longitude_dd"), "SEAD longitude"),
                latitude=_required_number(row.get("latitude_dd"), "SEAD latitude"),
                raw_country=_optional_text(decision.get("raw_country")),
                published_country=(
                    governed_code
                    if governed_code is not None and governed_code != "UNASSIGNED"
                    else None
                ),
                lineage=(
                    _lineage(
                        source_path, f"rows[site_id={site_id}]", "source_native_row"
                    ),
                    _lineage(
                        decisions_path,
                        f"decisions[{index}]",
                        "prior_country_decision",
                    ),
                ),
                prior_decision={
                    "decision_status": decision.get("decision_status"),
                    "decision_method": decision.get("decision_method"),
                    "derived_country": decision.get("derived_country"),
                    "boundary_artifact_digest": decision.get(
                        "boundary_artifact_digest"
                    ),
                },
            )
        )
    return "sead", points, _artifact_records(root, (decisions_path, source_path))
