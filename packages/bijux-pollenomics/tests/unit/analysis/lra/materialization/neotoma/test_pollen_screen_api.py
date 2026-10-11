"""The installed Neotoma facade exposes the source-wide refusal-only screen."""

from pathlib import Path

from bijux_pollenomics.analysis.lra.materialization import (
    NeotomaPollenScreen,
    inspect_neotoma_lra_pollen_screen,
)

from ..support import authorities


def test_public_pollen_screen_facade_keeps_source_partition_and_refusal(
    tmp_path: Path,
) -> None:
    raw, normalized = authorities(tmp_path, context_only_sample=100)
    result = inspect_neotoma_lra_pollen_screen(raw_root=raw, normalized_root=normalized)

    assert isinstance(result, NeotomaPollenScreen)
    payload = result.as_dict()
    assert payload["source_denominators"]["available_samples"] == 9
    assert payload["screen_denominators"]["necessary_candidate_samples"] == 8
    assert payload["screen_denominators"]["refused_samples"] == 1
    assert payload["lra_accepted_samples"] == 0
    assert payload["executable_request"] is None
    assert len(payload["sample_decisions"]) == 9
