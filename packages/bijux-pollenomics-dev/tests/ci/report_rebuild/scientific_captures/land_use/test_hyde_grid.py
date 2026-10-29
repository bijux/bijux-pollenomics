"""Keep HYDE grid custody distinct from country-table and ecological evidence."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.land_use import (
    hyde_grid as subject,
)


def owner() -> dict[str, Any]:
    return {
        "owner_id": subject.OWNER,
        "role": "retained_source",
        "paths": subject.OWNER_PATHS,
        "producer_paths": [],
        "producer_inputs": [],
    }


def test_exact_owner_and_disjoint_country_table() -> None:
    subject.validate_owners(
        [
            owner(),
            {
                "owner_id": "country-table",
                "paths": [
                    "docs/report/regions/nordic/hyde-country-cropland/report.json"
                ],
            },
        ]
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("role", "unresolved"),
        ("paths", []),
        ("paths", ["not-a-grid-product"]),
        ("producer_paths", ["replay.py"]),
        ("producer_inputs", ["private.zip"]),
    ],
)
def test_owner_recipe_refusals(key: str, value: Any) -> None:
    changed = deepcopy(owner())
    changed[key] = value
    with pytest.raises(ValueError):
        subject.validate_owners([changed])


def test_duplicate_and_overlapping_owners_refused() -> None:
    for rows in (
        [],
        [owner(), owner()],
        [owner(), {"owner_id": "other", "paths": subject.OWNER_PATHS[:1]}],
    ):
        with pytest.raises(ValueError):
            subject.validate_owners(rows)


def test_optional_absence_does_not_admit_present_or_linked_capture(
    tmp_path: Path,
) -> None:
    assert subject.validated_hyde_grid_source_captures(tmp_path, {}, []) == ((), {})
    assert not subject.source_absent(tmp_path, [owner()])
    capture = tmp_path / subject.CAPTURE
    capture.parent.mkdir(parents=True)
    capture.symlink_to(tmp_path / "absent-capture")
    assert not subject.source_absent(tmp_path, [])
    with pytest.raises(ReportRebuildError):
        subject.validated_hyde_grid_source_captures(tmp_path, {}, [])


@pytest.mark.parametrize("name", [".", "", "../payload", "/payload", "a//b", "a\\b"])
def test_payload_paths_refused(name: str) -> None:
    with pytest.raises(ValueError):
        subject.member_name(name)


@pytest.mark.parametrize("value", [False, 0.0, "0"])
def test_metadata_boolean_or_numeric_coercion_refused(value: Any) -> None:
    with pytest.raises(ValueError):
        subject.same({"native_exit": 0}, {"native_exit": value})
