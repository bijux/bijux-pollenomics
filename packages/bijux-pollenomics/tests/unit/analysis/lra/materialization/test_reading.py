"""Authority bytes and sample partitions must bind to the actual source."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.materialization.neotoma import source_accounting
from bijux_pollenomics.analysis.lra.materialization.reading import (
    json_object,
    read_neotoma_evidence,
)

from .support import authorities


def test_changed_or_missing_parts_are_not_accepted(tmp_path: Path) -> None:
    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)
    part = next((normalized / "surfaces/observations").glob("*.json"))
    original = part.read_bytes()
    part.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="changed"):
        list(evidence.rows("observations"))
    with pytest.raises(ValueError, match="changed"):
        evidence.assert_unchanged()
    part.unlink()
    with pytest.raises(ValueError):
        read_neotoma_evidence(raw, normalized)


@pytest.mark.parametrize(
    "selection",
    (
        ("absent-sample",),
        ("neotoma:sample:100", "neotoma:sample:100"),
        (True,),
        "neotoma:sample:100",
    ),
)
def test_sample_selection_cannot_invent_or_repeat_source_ids(
    tmp_path: Path, selection: object
) -> None:
    from collections.abc import Sequence
    from typing import cast

    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)
    with pytest.raises(ValueError):
        source_accounting(evidence, cast(Sequence[str], selection))


def test_duplicate_json_keys_and_nonfinite_values_refuse() -> None:
    for content in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}'):
        with pytest.raises(ValueError):
            json_object(content)


def test_existing_foreign_parent_and_duplicate_observations_are_not_collapsed(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.analysis.lra.materialization.models import (
        SourceRow,
        canonical_bytes,
    )

    raw, normalized = authorities(tmp_path)
    evidence = read_neotoma_evidence(raw, normalized)
    accounting = source_accounting(evidence, None)
    source = next(
        row
        for row in evidence.rows("observations")
        if row.payload()["source_value"] == 9007199254740993
    )
    original = source.payload()
    wrong = {**original, "dataset_id": "neotoma:dataset:2"}
    # An existing foreign dataset is still an invalid owner for this sample/site.
    refused = accounting.observation(
        SourceRow(source.surface, source.path, source.row_index, canonical_bytes(wrong))
    )
    assert refused["count_status"] == "refused"
    assert any(
        "ownership_mismatch" in reason for reason in refused["count_reason_codes"]
    )
    fresh = source_accounting(evidence, None)
    first = fresh.observation(source)
    second = fresh.observation(
        SourceRow(
            source.surface,
            source.path,
            source.row_index + 1,
            canonical_bytes(
                {
                    **original,
                    "observation_id": original["observation_id"] + ":duplicate",
                }
            ),
        )
    )
    assert (
        first["source_observation"]["observation_id"]
        != second["source_observation"]["observation_id"]
    )
    sample = fresh.sample(fresh.indexes["samples"][original["sample_id"]])
    assert sample["observation_count"] == 2
    assert sample["duplicate_variable_unit_groups"][0]["observation_count"] == 2
    assert (
        sample["count_candidate_sums_by_exact_unit"][0]["exact_sum"]
        == 18014398509481986
    )
    assert sample["lra_admission_status"] == "refused"


def test_another_valid_raw_snapshot_cannot_back_the_normalized_claims(
    tmp_path: Path,
) -> None:
    import hashlib
    import json

    from .support import write_json

    raw, normalized = authorities(tmp_path)
    part = raw / "part-001.json"
    payload = json.loads(part.read_bytes())
    payload["rows"][0]["site"]["sitename"] = "Changed synthetic raw site"
    content = write_json(part, payload)
    raw_manifest = json.loads((raw / "manifest.json").read_bytes())
    raw_manifest["parts"][0]["sha256"] = hashlib.sha256(content).hexdigest()
    write_json(raw / "manifest.json", raw_manifest)
    with pytest.raises(ValueError, match="does not bind the raw snapshot"):
        read_neotoma_evidence(raw, normalized)
