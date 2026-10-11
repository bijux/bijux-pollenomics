from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.materialization.requests import (
    project_synthetic_neotoma_request,
)
from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.production import (
    load_validated_neotoma_raw_archive,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)

from .fixture import projection_fixture


@pytest.mark.parametrize(
    "surface", ["observations", "age_claims", "sites", "variables"]
)
def test_rehashed_normalized_rows_cannot_authorize_their_own_raw_lineage(
    tmp_path: Path, surface: str
) -> None:
    inputs = projection_fixture(tmp_path)
    before = {path.name: path.read_bytes() for path in inputs["raw_root"].iterdir()}
    rows, identity = load_validated_neotoma_raw_archive(inputs["raw_root"])
    raw_manifest = json.loads((inputs["raw_root"] / "manifest.json").read_bytes())
    snapshot = build_neotoma_relational_snapshot(
        rows,
        source_snapshot_id=identity,
        build_id="synthetic-test-build",
        country_by_site_id=raw_manifest["synthetic_country_by_site_id"],
    )
    records = snapshot[surface]
    assert isinstance(records, list)
    if surface == "observations":
        target = next(
            row
            for row in records
            if row["sample_id"] == "neotoma:sample:100"
            and row["source_reported_name"] == "Alnus"
        )
        assert target["source_value"] == target["source_payload"]["value"] == 0
        target["source_value"] = target["source_payload"]["value"] = 2
    elif surface == "age_claims":
        records[0]["younger_bp"] = 5450
    elif surface == "sites":
        records[0]["derived_country"] = "NO"
        records[0]["country_candidates"] = ["NO"]
    else:
        records[0]["source_reported_name"] = "Forged taxon"
    forged = tmp_path / "forged-normalized"
    materialize_neotoma_relational_snapshot(forged, snapshot, rows_per_part=3)
    inputs["normalized_root"] = forged
    with pytest.raises(LRARefusal) as error:
        project_synthetic_neotoma_request(**inputs)
    assert error.value.reason_code == "source_projection_replay_mismatch"
    assert str(error.value) == surface
    assert before == {
        path.name: path.read_bytes() for path in inputs["raw_root"].iterdir()
    }
    assert not inputs["output_directory"].exists()


def test_success_receipt_binds_every_replayed_surface(tmp_path: Path) -> None:
    result = project_synthetic_neotoma_request(**projection_fixture(tmp_path))
    manifest = json.loads((result.output_directory / "manifest.json").read_bytes())
    verification = manifest["source_projection_verification"]
    assert verification["status"] == "exact_source_replay_match"
    assert len(verification["surfaces"]) == 11
    assert verification["surfaces"]["observations"]["row_count"] == 18
    assert verification["surfaces"]["age_claims"]["row_count"] == 9
    assert verification["surfaces"]["conflicts"]["row_count"] == 0
