"""Adversarial row ownership and alternative-claim partition checks."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.projection import (
    iter_member_documents,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.validation import (
    validate_member_ownership,
)
from tests.unit.collection.sources.aadr.materialization.accountability.support import (
    reconciliation,
)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_row",
        "missing_row",
        "unknown_owner_row",
        "admission",
        "numeric_admission",
        "cross_owner_claim",
        "duplicate_claim",
        "bool_count",
    ],
)
def test_invalid_membership_cannot_hide_behind_equal_counts(
    tmp_path: Path, mutation: str
) -> None:
    records = deepcopy(
        list(
            iter_member_documents(
                reconciliation(tmp_path), release_manifest_sha256="a" * 64
            )
        )
    )
    row_index = next(
        i for i, (name, _) in enumerate(records) if name == "source_rows.ndjson"
    )
    member = next(record for name, record in records if name == "members.ndjson")
    if mutation == "duplicate_row":
        records.append(deepcopy(records[row_index]))
    elif mutation == "missing_row":
        records.pop(row_index)
    elif mutation == "unknown_owner_row":
        member["source_row_keys"] = ["unknown"]
    elif mutation in {"admission", "numeric_admission"}:
        boundary = member["admission_boundary"]
        assert isinstance(boundary, dict)
        boundary["scientifically_admitted"] = True if mutation == "admission" else 0
    elif mutation == "cross_owner_claim":
        claim = next(
            record for name, record in records if name == "coordinate_claims.ndjson"
        )
        claim["owner_key"] = "wrong"
    elif mutation == "duplicate_claim":
        records.append(
            deepcopy(
                next(item for item in records if item[0] == "chronology_claims.ndjson")
            )
        )
    else:
        header = records[0][1]["source_files"]
        assert isinstance(header, list)
        header[0]["source_row_count"] = True
    with pytest.raises(ValueError):
        validate_member_ownership(records, release_manifest_sha256="a" * 64)
