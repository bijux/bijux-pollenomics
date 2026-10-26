"""Independent controls for source-supported panels and unchanged native masks."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json

import numpy as np
import pytest

from .abborrtjarnen_age_ppe.independent_count_profiles import recorded_zero_panels
from .abborrtjarnen_age_ppe.independent_profile_comparison import ProfileComparison
from .abborrtjarnen_age_ppe.independent_sources import Sample, memberships
from .abborrtjarnen_source_counts.independent_controls import (
    native_control,
    original_control,
    producer_control_result,
)


def control_samples() -> dict[int, Sample]:
    return {
        10: Sample(10, 101, (2, 0, 3, 4, 5), 14),
        20: Sample(20, 102, (6, None, 8, 9, 10), 33),
    }


def test_recorded_source_zero_changes_only_separate_analytical_panel() -> None:
    original, native = original_control(), native_control()
    samples = control_samples()
    snapshot = deepcopy(samples)
    qualified = producer_control_result(original, native)
    analytical, support = recorded_zero_panels(
        original,
        json.dumps(native).encode(),
        qualified,
        samples,
        expected_samples=2,
        expected_reported=9,
    )
    assert samples == snapshot and analytical[10] == samples[10]
    assert analytical[20].panel == (6, 0, 8, 9, 10)
    assert analytical[20].reported_nisp == samples[20].reported_nisp
    assert len(support) == 1 and support[0]["native_sample_id"] == 20
    ages = np.array([1500, 2000])
    strict = memberships(ages, tuple(samples), samples)
    source = memberships(ages, tuple(samples), analytical)
    assert strict[0] == source[0]
    assert strict[1].status == "refused_missing_explicit_panel"
    assert (
        source[1].status == "defined"
        and source[1].panel_subtotal == strict[1].panel_subtotal
    )
    assert strict[2:] == source[2:]


@pytest.mark.parametrize("token", ["", "5", "-1", "1.5", "oops"])
def test_native_omission_requires_original_zero_not_blank_or_positive(
    token: str,
) -> None:
    original, native = original_control(token), native_control()
    qualified = producer_control_result(original, native)
    with pytest.raises(ValueError, match="literal original zero"):
        recorded_zero_panels(
            original,
            json.dumps(native).encode(),
            qualified,
            control_samples(),
            expected_samples=2,
            expected_reported=9,
        )


def test_reported_count_conflict_prevents_any_source_support() -> None:
    original = original_control().replace(b"1.01\t2\t", b"1.01\t3\t")
    native = native_control()
    with pytest.raises(ValueError, match="precondition"):
        recorded_zero_panels(
            original,
            json.dumps(native).encode(),
            producer_control_result(original, native),
            control_samples(),
            expected_samples=2,
            expected_reported=9,
        )


def test_stale_support_packet_cannot_replace_raw_original_evidence() -> None:
    original, native = original_control(), native_control()
    qualified = producer_control_result(original, native)
    qualified["absence_candidates"][0]["original_token"] = "0.00"
    with pytest.raises(ValueError, match="absence_candidates"):
        recorded_zero_panels(
            original,
            json.dumps(native).encode(),
            qualified,
            control_samples(),
            expected_samples=2,
            expected_reported=9,
        )


def saved_membership_row(
    seed: int,
    index: int,
    ages: np.ndarray,
    samples: dict[int, Sample],
    native: dict[int, Sample] | None = None,
) -> dict[str, str]:
    from .abborrtjarnen_age_ppe.independent_ledger import STATUS
    from .abborrtjarnen_age_ppe.independent_moments import fixed_window
    from .abborrtjarnen_age_ppe.independent_sources import BINS, TAXON_IDS

    windows = memberships(ages, tuple(samples), samples)
    row = {
        "seed": str(seed),
        "native_row": str(index),
        "complete": str(int(all(w.status == "defined" for w in windows))),
    }
    strict = memberships(ages, tuple(samples), native or samples)
    row["native_complete"] = str(int(all(w.status == "defined" for w in strict)))
    for b, w, old in zip(BINS, windows, strict, strict=True):
        prefix = f"bin_{b}_"
        row[prefix + "native_missing_members"] = json.dumps(old.missing)
        row[prefix + "source_recorded_zero_sample_ids"] = json.dumps(
            [i for i in old.sample_ids if i in old.missing]
        )
        row.update(
            {
                prefix + "status": STATUS[w.status],
                prefix + "sample_ids": json.dumps(w.sample_ids),
                prefix + "sample_count": str(len(w.sample_ids)),
                prefix + "reported_panel_subtotal": str(w.panel_subtotal),
                prefix + "panel_mass": "" if w.missing else str(w.panel_subtotal),
                prefix + "all_reported_pollen_nisp": str(w.reported_nisp),
                prefix + "omitted_reported_pollen_nisp": str(
                    w.reported_nisp - w.panel_subtotal
                ),
                prefix + "missing_members": json.dumps(w.missing),
            }
        )
        cover = (
            fixed_window(w.pooled, np.ones(5), np.ones(5))[0]
            if w.status == "defined" and w.pooled is not None
            else None
        )
        for j, taxon_id in enumerate(TAXON_IDS):
            row[f"cover_{b}_{taxon_id}"] = str(cover[j]) if cover is not None else ""
    return row


def comparison_control() -> tuple[
    dict[int, Sample], dict[int, Sample], list[np.ndarray]
]:

    native = {i: Sample(i, i, (i, i, i, i, i), 5 * i) for i in range(1, 5)}
    native[5] = Sample(5, 5, (2, None, 1, 1, 1), 5)
    active = dict(native)
    active[5] = replace(native[5], panel=(2, 0, 1, 1, 1))
    ages = [
        np.array(row)
        for row in [
            (1550, 2050, 2550, 4550, -52),
            (1550, 2050, 2550, 4550, 1551),
            (1550, 2050, 2550, -52, 1551),
        ]
    ]
    return native, active, ages


def test_every_identity_retains_native_event_and_records_support_transitions() -> None:

    native, active, ages = comparison_control()
    old = [saved_membership_row(1, i, a, native) for i, a in enumerate(ages)]
    observed = ProfileComparison(native, iter(old), np.ones(5), np.ones(5), np.zeros(5))
    for i, a in enumerate(ages):
        observed.observe(
            saved_membership_row(1, i, a, active, native),
            a,
            tuple(native),
            memberships(a, tuple(native), active),
        )
    observed.finish(3)
    assert observed.transitions == {"1->1": 1, "0->1": 1, "0->0": 1}
    assert observed.observed.complete == observed.observed.moments.observations == 1
    np.testing.assert_allclose(
        observed.observed.moments.finish()["mean"], 0.2, rtol=0, atol=1e-16
    )


@pytest.mark.parametrize(
    "fault", ["identity", "native_complete_lost", "changed_count", "trailing_row"]
)
def test_comparison_cannot_change_old_event_or_drop_identities(fault: str) -> None:

    native, active, ages = comparison_control()
    a = ages[0]
    old = saved_membership_row(1, 0, a, native)
    if fault == "identity":
        old["seed"] = "2"
    elif fault == "native_complete_lost":
        active[1] = replace(active[1], panel=(None, 1, 1, 1, 1))
    elif fault == "changed_count":
        active[1] = replace(active[1], panel=(2, 1, 1, 1, 1))
    observed = ProfileComparison(
        native,
        iter([old, old] if fault == "trailing_row" else [old]),
        np.ones(5),
        np.ones(5),
        np.zeros(5),
    )
    with pytest.raises(ValueError):
        observed.observe(
            saved_membership_row(1, 0, a, active, native),
            a,
            tuple(native),
            memberships(a, tuple(native), active),
        )
        observed.finish(1)
