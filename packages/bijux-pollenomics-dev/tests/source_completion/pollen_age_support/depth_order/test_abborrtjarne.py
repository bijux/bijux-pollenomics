"""Complete artificial retained-ledger handoff; never consume real ABBO outcomes."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    abborrtjarne_joint_membership as independent,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    abborrtjarne_membership as schema,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order import (
    abborrtjarne,
)


def csv_bytes(fields: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def miniature(*, reversal: bool = False) -> tuple[bytes, bytes, bytes]:
    """Construct all107 sample/428 membership rows and exact four-bin bounds."""
    bins = [3, 4, 5, 9]
    support = []
    membership = []
    for index in range(107):
        bin_id = bins[index] if index < 4 else None
        age = bin_id * 500 + 250 if bin_id is not None else 6000 + index
        row = dict(
            zip(
                schema.SUPPORT_FIELDS,
                [
                    f"neotoma:sample:controlled-{index}",
                    str(106 - index if reversal else index),
                    str(age),
                    str(age),
                    str(age),
                    str(bin_id) if bin_id is not None else "",
                    str(bin_id) if bin_id is not None else "",
                    "contained" if bin_id is not None else "outside_common_bins",
                    "2",
                    "1",
                ],
                strict=True,
            )
        )
        support.append(row)
        for target in bins:
            membership.append(
                {
                    **{
                        name: row[name]
                        for name in schema.MEMBERSHIP_FIELDS
                        if name in row
                    },
                    "bin_id": str(target),
                    "bin_younger_cal_bp": str(target * 500),
                    "bin_older_cal_bp_exclusive": str((target + 1) * 500),
                    "membership": "mandatory" if target == bin_id else "outside",
                }
            )
    data = csv_bytes(schema.MEMBERSHIP_FIELDS, membership)
    report = {
        "schema_version": "abbo-conditional-age-membership.v1",
        "sample_count": 107,
        "membership_row_count": 428,
        "membership_sha256": hashlib.sha256(data).hexdigest(),
        "membership_status_counts": dict(
            Counter(row["membership"] for row in membership)
        )
        | {"optional": 0},
        "quantity": "controlled numerator1/native denominator2; no field observation",
        "bounds": [
            {
                "bin_id": i,
                "younger_cal_bp": i * 500,
                "older_cal_bp_exclusive": (i + 1) * 500,
                "closed16_fraction_lower_outer_bound": {
                    "numerator": 1,
                    "denominator": 2,
                },
                "closed16_fraction_upper_outer_bound": {
                    "numerator": 1,
                    "denominator": 2,
                },
            }
            for i in bins
        ],
    }
    return csv_bytes(schema.SUPPORT_FIELDS, support), data, json.dumps(report).encode()


def test_complete_adapter_keeps_all_original_targets_and_exact_native_depths() -> None:
    result = abborrtjarne.derive(*miniature())
    assert result["sample_count"] == result["distinct_depth_count"] == 107
    assert result["membership_row_count"] == 428
    assert (
        result["independently_attainable_corners"]
        == result["attainable_corners_with_order"]
        == 16
    )
    assert result["native_interval_order"]["attainable"]
    assignments = result["native_interval_order"]["assignments"]
    assert len(assignments) == 107 and assignments[0] == {
        "sample_id": "neotoma:sample:controlled-0",
        "depth_cm": "0",
        "possible_native_age": "1750",
    }
    assert all(
        row["independent_attainable"]
        and not row["independent_refusals"]
        and row["age_order"]["attainable"]
        for row in result["corners"]
    )
    assert (
        "conditional" in result["assumption"]
        and "no newly qualified" in result["age_scope"]
    )


def test_source_reversal_is_reported_without_repair_or_loss_of_original_feasibility() -> (
    None
):
    result = abborrtjarne.derive(*miniature(reversal=True))
    assert result["independently_attainable_corners"] == 16
    assert result["attainable_corners_with_order"] == 0
    assert not result["native_interval_order"]["attainable"]
    assert result["native_interval_order"]["assignments"] == []
    assert result["native_interval_order"]["refusal"]["sample_id"]
    assert all(
        row["independent_attainable"]
        and not row["attainable_with_order"]
        and row["age_order"]["refusal"]
        for row in result["corners"]
    )


def test_changed_source_membership_is_not_treated_as_an_order_refusal() -> None:
    support, membership, report = miniature()
    with pytest.raises(ValueError, match="source row"):
        abborrtjarne.derive(
            support.replace(b",2,1\n", b",2,2\n", 1), membership, report
        )
    with pytest.raises(ValueError):
        abborrtjarne.derive(
            support, membership + membership.splitlines(keepends=True)[1], report
        )
    with pytest.raises(ValueError):
        abborrtjarne.derive(
            support.replace(b",0,1750", b",NaN,1750", 1),
            membership.replace(b",0,1750", b",NaN,1750", 1),
            report,
        )


def test_new_count_fraction_mode_returns_exact_bounds_with_complete_witnesses() -> None:
    inputs = miniature()
    original = abborrtjarne.derive(*inputs)
    result = abborrtjarne.derive_count_fraction_bounds(*inputs)
    assert result["schema_version"] == "abbo-ordered-count-fraction-bounds.v1"
    assert (
        result["original_independent_marginal_bounds"]
        == original["marginal_bounds_unchanged"]
    )
    assert len(result["bounds"]) == 4
    for row in result["bounds"]:
        assert row["candidate_block_count"] == row["tested_block_count"] == 5778
        assert row["feasible_block_count"] == 1
        assert row["empty_selection_age_order"] is None
        for side in ("lower", "upper"):
            bound = row[side]
            assert bound["fraction"] == {"numerator": 1, "denominator": 2}
            assert len(bound["selected_sample_ids"]) == 1
            assert len(bound["age_order"]["assignments"]) == 107
    assert abborrtjarne.derive(*inputs) == original
    assert "joint probability" in result["age_scope"]


def test_new_bounds_retains_full_inconsistent_core_refusal() -> None:
    result = abborrtjarne.derive_count_fraction_bounds(*miniature(reversal=True))
    assert all(
        row["refusal"] == "native_age_order_infeasible" for row in result["bounds"]
    )
    assert all(row["lower"] is row["upper"] is None for row in result["bounds"])
    assert all(row["native_age_order"]["refusal"] for row in result["bounds"])


@pytest.mark.parametrize("revision_changes", [False, True])
def test_new_run_records_git_revision_and_only_input_pins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, revision_changes: bool
) -> None:
    support, membership, report = miniature()
    buffers = {
        schema.SUPPORT: support,
        independent.MEMBERSHIP: membership,
        independent.REPORT: report,
    }
    identities = {
        str(path): {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        for path, raw in buffers.items()
    }

    def input_buffers(
        repository: Path, *, include_code_identities: bool = True
    ) -> tuple[dict[Path, bytes], dict[str, Any]]:
        assert repository == tmp_path and not include_code_identities
        return buffers, identities

    revisions = iter(["a" * 40, ("b" if revision_changes else "a") * 40])
    monkeypatch.setattr(abborrtjarne, "_buffers", input_buffers)
    monkeypatch.setattr(abborrtjarne, "_source_revision", lambda _: next(revisions))
    (tmp_path / "artifacts").mkdir()
    output = tmp_path / "artifacts/bounds"
    if revision_changes:
        with pytest.raises(ValueError, match="Git revision changed"):
            abborrtjarne.run(tmp_path, output, count_fraction_bounds=True)
        assert not output.exists()
        assert list((tmp_path / "artifacts").iterdir()) == []
    else:
        result = abborrtjarne.run(tmp_path, output, count_fraction_bounds=True)
        assert result["source_git_revision"] == "a" * 40
        assert result["input_identities"] == identities
        assert "input_and_source_identities" not in result
        assert isinstance(result["command"], list)
        assert json.loads((output / "report.json").read_text()) == result
        assert [p.name for p in output.iterdir()] == ["report.json"]
