"""Validate source-native measure partitions and atomic refusal boundaries."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion import nordic_direct_pollen as study
from bijux_pollenomics_dev.source_completion.neotoma import (
    direct_pollen_measure_strata as account,
)


def observation(
    oid: str,
    sample: str,
    *,
    unit: object = "NISP",
    family: object = "count",
    value: object = 3,
    element: str = "pollen",
    name: str = "Betula",
) -> dict[str, Any]:
    """Construct one native source observation without substituting unit meaning."""
    return {
        "observation_id": oid,
        "sample_id": sample,
        "site_id": "neotoma:site:1",
        "country_code": "FI",
        "source_unit": unit,
        "unit_family": family,
        "source_element": element,
        "source_element_type": element,
        "detection_status": "reported_value",
        "source_value": value,
        "source_reported_name": name,
    }


def selected() -> dict[str, dict[str, str]]:
    """Keep two physical samples at one source site."""
    return {
        "neotoma:sample:1": {"country_code": "FI", "site_id": "neotoma:site:1"},
        "neotoma:sample:2": {"country_code": "FI", "site_id": "neotoma:site:1"},
    }


def test_distinct_native_measures_and_multimembership() -> None:
    """No count, proportion, influx or concentration enters another denominator."""
    rows = [
        observation("o1", "neotoma:sample:1"),
        observation("o2", "neotoma:sample:2", value=0),
        observation("o3", "neotoma:sample:1", unit="%", family="percentage"),
        observation(
            "o4",
            "neotoma:sample:1",
            unit="grains/cm²/yr",
            family="influx_per_area_time",
        ),
        observation(
            "o5", "neotoma:sample:2", unit="grains/g", family="concentration_per_mass"
        ),
        observation("o6", "neotoma:sample:2", unit=None, family=None),
        observation(
            "o7", "neotoma:sample:2", unit="presence", family="presence_absence"
        ),
        observation("o8", "neotoma:sample:1", value=True),
    ]
    groups, summary = account.account_rows(rows, selected())
    assert summary["unique_observation_count"] == 8
    assert summary["country_denominators"]["FI"] == {
        "candidate_sample_count": 2,
        "observed_sample_count": 2,
        "observed_site_count": 1,
        "observed_source_reported_name_count": 1,
        "accepted_observation_count": 2,
        "refused_observation_count": 6,
    }
    assert summary["refusal_reason_counts"] == {
        "nonnegative_integer_count_required": 1,
        "source_unit_not_native_NISP": 5,
    }
    assert summary["source_measure_observation_counts"] == {
        "NISP_raw_count": 3,
        "percentage_or_proportion": 1,
        "concentration": 1,
        "influx": 1,
        "presence_or_absence": 1,
        "missing_source_unit": 1,
        "other_literal_source_unit": 0,
    }
    accepted = [row for row in groups if row["decision"] == "accepted"]
    assert len(accepted) == 1
    assert accepted[0]["observation_count"] == 2
    assert accepted[0]["unique_sample_count"] == 2
    assert sum(row["observation_count"] for row in groups) == 8


def test_source_identity_collisions_refuse() -> None:
    """A repeated native ID or conflicting parent cannot inflate a denominator."""
    first = observation("o1", "neotoma:sample:1")
    with pytest.raises(ValueError, match="duplicate"):
        account.account_rows([first, first], selected())
    changed = {**first, "site_id": "neotoma:site:other"}
    with pytest.raises(ValueError, match="identity"):
        account.account_rows([changed], selected())


def test_published_predicate_preserves_boolean_and_source_element() -> None:
    """Python True is not the native integer count one."""
    for row, reason in (
        (observation("o1", "neotoma:sample:1"), None),
        (
            observation("o2", "neotoma:sample:1", value=True),
            "nonnegative_integer_count_required",
        ),
        (
            observation("o3", "neotoma:sample:1", element="charcoal"),
            "source_element_labels_not_both_pollen",
        ),
        (
            observation("o4", "neotoma:sample:1", unit="NISP digitized"),
            "source_unit_not_native_NISP",
        ),
    ):
        assert account.refusal_reason(row) == reason
        assert (reason is None) == study._is_direct_pollen_count(row)


def test_source_default_age_and_candidate_identity_refusals() -> None:
    """Ambiguous ages cannot silently enter the published country denominator."""
    ages = {
        "neotoma:sample:1": [
            {
                "chronology_id": "c1",
                "source_age_type": "Calendar years BP",
            },
            {
                "chronology_id": "c2",
                "source_age_type": "Calendar years BP",
            },
        ]
    }
    chronologies = {
        "c1": {"source_is_default_assertion": False},
        "c2": {"source_is_default_assertion": False},
    }
    with pytest.raises(ValueError, match="denominators"):
        account.chosen_target_samples(
            ["neotoma:sample:1"], selected(), ages, chronologies, {"FI": 1}
        )
    chronologies["c2"]["source_is_default_assertion"] = True
    assert set(
        account.chosen_target_samples(
            ["neotoma:sample:1"], selected(), ages, chronologies, {"FI": 1}
        )
    ) == {"neotoma:sample:1"}
    with pytest.raises(ValueError, match="repeat"):
        account.chosen_target_samples(
            ["neotoma:sample:1"] * 2,
            selected(),
            ages,
            chronologies,
            {"FI": 1},
        )


def test_source_path_refuses_linked_member(tmp_path: Path) -> None:
    """A named source member cannot escape the repository through a symlink."""
    source = tmp_path / "source.json"
    source.write_bytes(b"source")
    alias = tmp_path / "alias.json"
    alias.symlink_to(source)
    digest = hashlib.sha256(b"source").hexdigest()
    with pytest.raises(ValueError, match="linked"):
        account._read(tmp_path.resolve(), Path("alias.json"), digest)


def test_preexisting_output_refuses_before_source_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A conflicting output is preserved without invoking the 500 MB source read."""
    artifacts = tmp_path / "artifacts" / "review"
    artifacts.mkdir(parents=True)
    output = artifacts / "report.json"
    output.write_bytes(b"keep")
    monkeypatch.setattr(
        account, "build_report", lambda _repository: pytest.fail("source read started")
    )
    with pytest.raises(ReportRebuildError, match="absent"):
        account.run(tmp_path.resolve(), output)
    assert output.read_bytes() == b"keep"


def test_postread_change_refuses_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The completed stage is removed if a consumed byte changes before rename."""
    artifacts = tmp_path / "artifacts" / "review"
    artifacts.mkdir(parents=True)
    source = tmp_path / "source.json"
    source.write_bytes(b"original")
    digest = hashlib.sha256(b"original").hexdigest()
    origin = study.__file__
    assert origin is not None
    fake = {
        "source_readset_sha256": {"source.json": digest},
        "published_study_producer_sha256": hashlib.sha256(
            Path(origin).read_bytes()
        ).hexdigest(),
    }
    monkeypatch.setattr(account, "build_report", lambda _repository: fake)
    source.write_bytes(b"altered")
    output = artifacts / "report.json"
    with pytest.raises(ValueError, match="identity differs"):
        account.run(tmp_path.resolve(), output)
    assert not output.exists()
    assert not output.with_name("report.json.stage").exists()
