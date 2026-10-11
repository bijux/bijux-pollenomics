"""OpenLand member decisions without requiring a private archive."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.open_land.authority import (
    ADMITTED_CSV_MEMBERS,
    SOURCE_COMMIT,
    SOURCE_DATA_LICENSE,
)
from bijux_pollenomics_dev.source_completion.openland_intake import (
    classify_member,
    validate_upstream_tree,
)

REPOSITORY = Path(__file__).resolve().parents[4]
TREE = REPOSITORY / "docs/report/source-relations/openland-intake/upstream-tree.json"


def test_pinned_primary_tree_has_exact_source_member_vocabulary() -> None:
    payload = json.loads(TREE.read_bytes())
    blobs = validate_upstream_tree(payload)
    assert payload["sha"] == SOURCE_COMMIT
    assert len(blobs) == 28
    assert {
        f"Land-cover Maps/{Path(member).name}" for member in ADMITTED_CSV_MEMBERS
    }.issubset(blobs)


def test_partial_or_replaced_primary_tree_is_refused() -> None:
    payload = json.loads(TREE.read_bytes())
    for mutation in ("truncated", "sha", "missing_blob"):
        changed = deepcopy(payload)
        if mutation == "truncated":
            changed["truncated"] = True
        elif mutation == "sha":
            changed["sha"] = "0" * 40
        else:
            changed["tree"] = changed["tree"][:-1]
        with pytest.raises(ValueError, match="upstream"):
            validate_upstream_tree(changed)


def test_matched_slices_route_to_one_modeled_authority_without_independence() -> None:
    role, rights, redistribution, route, decision, reason = classify_member(
        ADMITTED_CSV_MEMBERS[0], upstream_identity="exact_pinned_git_blob"
    )
    assert role == "pollen_derived_modeled_cover_slice"
    assert rights == SOURCE_DATA_LICENSE
    assert redistribution == "not_authorized_by_this_review"
    assert route == "existing_open_land_source_authority"
    assert decision == "private_source_review_only"
    assert reason == "modeled_source_not_independent_truth"
    with pytest.raises(ValueError, match="lacks exact upstream identity"):
        classify_member(
            ADMITTED_CSV_MEMBERS[0], upstream_identity="no_pinned_upstream_member"
        )


@pytest.mark.parametrize(
    ("member", "role", "decision"),
    [
        (
            "LandCover_OpenLand/Data/res_all.pdf",
            "source_documentation",
            "reference_only",
        ),
        ("LandCover_OpenLand/output.gpkg", "local_interpolated_derivative", "exclude"),
        (
            "LandCover_OpenLand/load_data.R",
            "local_processing_script",
            "reference_only_no_execution",
        ),
        (
            "LandCover_OpenLand/LandCover_OpenLand.Rproj",
            "local_project_configuration",
            "exclude",
        ),
        (
            "LandCover_OpenLand/.Rproj.user/user-state",
            "local_private_project_state",
            "exclude_private_state",
        ),
        (
            "LandCover_OpenLand/unrecognized.bin",
            "unresolved_member",
            "exclude_pending_member_review",
        ),
    ],
)
def test_mixed_archive_members_never_gain_implicit_admission(
    member: str, role: str, decision: str
) -> None:
    actual = classify_member(member, upstream_identity="no_pinned_upstream_member")
    assert actual[0] == role
    assert actual[2] == "not_authorized_by_this_review"
    assert actual[4] == decision
