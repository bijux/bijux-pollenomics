"""Leakage and identity counterexamples for candidate split preparation."""

from __future__ import annotations

import copy
import json

import pytest
from bijux_pollenomics_dev.lra_validation.split_guard import (
    SplitGuardError,
    build_candidate_split,
    main,
)


def row(
    record_id: str,
    site: str,
    kind: str,
    block: str,
    *,
    alias: list[str] | None = None,
    dependencies: list[str] | None = None,
    publication: str | None = None,
) -> dict[str, object]:
    return {
        "record_id": record_id,
        "site_id": site,
        "core_id": None,
        "publication_id": publication,
        "alias_ids": alias or [],
        "country": "Sweden",
        "spatial_block_id": block,
        "kind": kind,
        "dependency_ids": dependencies or [],
    }


def cohort() -> list[dict[str, object]]:
    return [
        row("v-test", "test", "vegetation", "east", alias=["shared"]),
        row("p-test", "test", "pollen", "east"),
        row("p-alias", "other-id", "pollen", "east", alias=["shared"]),
        row("v-train", "train", "vegetation", "west"),
        row("p-train", "train", "pollen", "west"),
        row("v-next", "next", "vegetation", "east"),
    ]


def test_withheld_target_seals_all_site_aliases_and_block() -> None:
    result = build_candidate_split(
        cohort(),
        test_record_id="v-test",
        target="withheld_pollen_prediction",
        holdout_spatial_block=True,
    )
    assert result["status"] == "candidate_unreviewed"
    assert result["test_record_ids"] == ["p-alias", "p-test", "v-next", "v-test"]
    assert result["train_record_ids"] == ["p-train", "v-train"]
    assert result["allowed_local_pollen_record_id"] is None
    assert result["test_pollen_record_ids"] == ["p-alias", "p-test"]
    assert result["test_vegetation_record_ids"] == ["v-next", "v-test"]


def test_pollen_only_site_can_be_held_out_without_vegetation_score() -> None:
    records = [
        row("p-test", "test", "pollen", "east"),
        row("v-train", "train", "vegetation", "west"),
    ]
    result = build_candidate_split(
        records, test_record_id="p-test", target="withheld_pollen_prediction"
    )
    assert result["test_pollen_record_ids"] == ["p-test"]
    assert result["test_vegetation_record_ids"] == []
    with pytest.raises(SplitGuardError, match="test_record_not_vegetation"):
        build_candidate_split(
            records,
            test_record_id="p-test",
            target="local_pollen_available",
            local_pollen_record_id="p-test",
        )


def test_local_pollen_is_only_an_explicit_raw_test_input() -> None:
    result = build_candidate_split(
        cohort(),
        test_record_id="v-test",
        target="local_pollen_available",
        local_pollen_record_id="p-test",
    )
    assert result["allowed_local_pollen_record_id"] == "p-test"
    assert "p-test" not in result["train_record_ids"]
    with pytest.raises(SplitGuardError, match="withheld_pollen_must_not_be_supplied"):
        build_candidate_split(
            cohort(),
            test_record_id="v-test",
            target="withheld_pollen_prediction",
            local_pollen_record_id="p-test",
        )


@pytest.mark.parametrize("dependency", [["v-test"], ["p-test"]])
def test_derived_train_product_refuses_test_outcomes_and_pollen(
    dependency: list[str],
) -> None:
    records = cohort() + [
        row("regional", "regional", "derived", "west", dependencies=dependency)
    ]
    with pytest.raises(SplitGuardError, match="contaminated_train_input"):
        build_candidate_split(
            records, test_record_id="v-test", target="withheld_pollen_prediction"
        )


def test_transitive_derived_dependency_is_refused() -> None:
    records = cohort() + [
        row("grid", "test", "derived", "east", dependencies=["p-test"]),
        row("regional", "regional", "derived", "west", dependencies=["grid"]),
    ]
    with pytest.raises(SplitGuardError, match="contaminated_train_input"):
        build_candidate_split(
            records, test_record_id="v-test", target="withheld_pollen_prediction"
        )


def test_publication_groups_distinct_site_aliases() -> None:
    records = cohort()
    records[0]["publication_id"] = "article-1"
    records[3]["publication_id"] = "article-1"
    # The same publication across spatial blocks is ambiguous, not silently split.
    with pytest.raises(SplitGuardError, match="identity_crosses_spatial_blocks"):
        build_candidate_split(
            records, test_record_id="v-test", target="withheld_pollen_prediction"
        )


@pytest.mark.parametrize(
    "change, reason",
    [
        ({"outcome": 0.5}, "invalid_record_fields"),
        ({"dependency_ids": ["unlisted"]}, "unresolved_dependency"),
        ({"spatial_block_id": ""}, "missing_identity"),
    ],
)
def test_labels_unresolved_products_and_missing_blocks_refuse(
    change: dict[str, object],
    reason: str,
) -> None:
    records = copy.deepcopy(cohort())
    records[0].update(change)
    with pytest.raises(SplitGuardError, match=reason):
        build_candidate_split(
            records, test_record_id="v-test", target="withheld_pollen_prediction"
        )


def test_cli_publishes_once_without_labels(tmp_path: object) -> None:
    from pathlib import Path

    folder = Path(tmp_path)
    output = folder / "candidate.json"
    plan = folder / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "records": cohort(),
                "test_record_id": "v-test",
                "target": "withheld_pollen_prediction",
                "local_pollen_record_id": None,
                "holdout_spatial_block": False,
                "output_path": str(output),
            }
        )
    )
    assert main([str(plan)]) == 0
    assert json.loads(output.read_text())["status"] == "candidate_unreviewed"
    with pytest.raises(SplitGuardError, match="output_already_exists"):
        main([str(plan)])
