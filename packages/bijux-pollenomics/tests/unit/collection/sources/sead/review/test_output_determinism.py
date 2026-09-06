from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.sources.sead.review import write_sead_review_outputs

_LINEAGE = {
    "source_run_id": "sead-test-run",
    "build_id": "sha256:" + "b" * 64,
    "acquisition_manifest_sha256": "a" * 64,
    "parent_admission_sha256": "p" * 64,
}


def _record() -> ContextPointRecord:
    return ContextPointRecord(
        source="SEAD",
        layer_key="sead",
        layer_label="SEAD",
        category="Environmental archaeology",
        country="Sweden",
        record_id="1",
        name="Å site",
        latitude=56.0,
        longitude=14.0,
        geometry_type="Point",
        subtitle="",
        description="",
        source_url="https://browser.sead.se/site/1",
        record_count=1,
        popup_rows=(),
        time_start_bp=None,
        time_end_bp=None,
        temporal_semantics={
            "comparability_posture": "unresolved",
            "summary_label": "Chronology unresolved",
            "normalized_labels": [],
            "original_labels": [],
            "uncertainty_notes": ["No interval inferred"],
        },
    )


def _file_map(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_representative_review_outputs_are_byte_deterministic(tmp_path: Path) -> None:
    rows: list[dict[str, object]] = [
        {
            "site_id": 1,
            "site_uuid": "site-uuid-1",
            "site_name": "Å site",
            "bibliography_rows": [],
        }
    ]
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_paths = write_sead_review_outputs(
        first, rows=rows, records=[_record()], lineage=_LINEAGE
    )
    second_paths = write_sead_review_outputs(
        second, rows=rows, records=[_record()], lineage=_LINEAGE
    )
    assert first_paths == second_paths
    assert len(first_paths) == 12
    assert _file_map(first) == _file_map(second)


def test_review_outputs_carry_site_identity_lineage_and_affected_sites(
    tmp_path: Path,
) -> None:
    rows: list[dict[str, object]] = [
        {
            "site_id": 1,
            "site_uuid": "site-uuid-1",
            "site_name": "Å site",
            "bibliography_rows": [],
        }
    ]
    write_sead_review_outputs(
        tmp_path, rows=rows, records=[_record()], lineage=_LINEAGE
    )

    for stem in (
        "access_model",
        "evidence_legibility_review",
        "recovery_requirements",
        "temporal_review",
    ):
        payload = json.loads(
            (tmp_path / "review" / f"{stem}.json").read_text(encoding="utf-8")
        )
        assert payload["lineage"] == _LINEAGE

    for stem in ("access_model", "evidence_legibility_review", "temporal_review"):
        payload = json.loads(
            (tmp_path / "review" / f"{stem}.json").read_text(encoding="utf-8")
        )
        assert payload["rows"][0]["site_uuid"] == "site-uuid-1"

    recovery = json.loads(
        (tmp_path / "review" / "recovery_requirements.json").read_text(
            encoding="utf-8"
        )
    )
    assert all(
        row["affected_site_uuids"] == ["site-uuid-1"]
        for row in recovery["rows"]
    )
