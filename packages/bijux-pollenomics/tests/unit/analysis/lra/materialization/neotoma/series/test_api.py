"""The installed host facade reads the same authenticated source series."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.materialization import (
    NeotomaCandidateSeries,
    inspect_neotoma_lra_candidate_series,
)

from ...support import authorities


def test_public_candidate_series_facade_keeps_refusal_and_source_identity(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path)
    result = inspect_neotoma_lra_candidate_series(
        raw_root=raw,
        normalized_root=normalized,
        selected_sample_ids=("neotoma:sample:100",),
    )

    assert isinstance(result, NeotomaCandidateSeries)
    payload = result.as_dict()
    assert payload["selection"]["sample_ids"] == ["neotoma:sample:100"]
    assert payload["selected_denominators"]["observations"] == 5
    assert payload["lra_accepted_samples"] == 0
    assert payload["executable_request"] is None


def test_public_candidate_series_facade_refuses_unowned_sample(tmp_path: Path) -> None:
    raw, normalized = authorities(tmp_path)
    with pytest.raises(ValueError, match="absent from the source inventory"):
        inspect_neotoma_lra_candidate_series(
            raw_root=raw,
            normalized_root=normalized,
            selected_sample_ids=("neotoma:sample:missing",),
        )
