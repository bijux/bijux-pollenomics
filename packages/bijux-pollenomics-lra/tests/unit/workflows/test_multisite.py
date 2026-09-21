"""Scientific counterexamples for the named publication-source profile."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from bijux_pollenomics_lra.api import (
    MultisiteRevealsInput,
    PublicationRevealsConfig,
    ValidationError,
    run_reveals_multisite,
)
from bijux_pollenomics_lra.models.publication import PUBLICATION_LIMITATIONS
from bijux_pollenomics_lra.reconstruction.publication import bootstrap_cover_variance


def draws() -> dict[str, np.ndarray]:
    return {"recent": np.tile([[0, 0], [0, 1], [1, 0], [1, 1]], (250, 1))}


def test_single_site_matches_pinned_independent_r_counterexample(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    inputs = publication_inputs
    single = replace(
        inputs,
        site_ids=("small",),
        counts=inputs.counts[:1],
        availability=inputs.availability[:1],
        basin_radius_m=inputs.basin_radius_m[:1],
        basin_type=inputs.basin_type[:1],
    )
    result = run_reveals_multisite(
        single, PublicationRevealsConfig("synthetic-bp-v1"), bootstrap_indices={}
    )
    # Exact standalone 2016 R source; r-experiment/challenge.R in audit receipt.
    np.testing.assert_allclose(
        result.cover.iloc[0],
        [0.254501251306663, 0.316514363146838, 0.428984385546499],
        atol=1e-14,
        rtol=0,
    )
    np.testing.assert_allclose(
        result.standard_error.iloc[0],
        [0.0522386061086609, 0.0830948543677374, 0.147384766103033],
        atol=1e-14,
        rtol=0,
    )
    assert result.site_count.iloc[0] == 1


def test_bootstrap_corrects_individual_geometry_and_accumulates_unclosed_ratios() -> (
    None
):
    counts = np.array([[9.0, 1.0], [1.0, 9.0]])
    k = np.array([[1.0, 2.0], [4.0, 1.0]])
    ppe = np.array([1.0, 3.0])
    indices = np.tile([[0, 0], [1, 1]], (500, 1))
    mean, _ = bootstrap_cover_variance(counts, k, ppe, indices)
    # Equal bootstrap frequency of these two same-site pools gives Qa vectors
    # [18/19, 1/57] and [1/37, 12/37], respectively, before final normalization.
    qa = np.array([[18 / 19, 1 / 57], [1 / 37, 12 / 37]])
    expected = qa.sum(axis=0) / qa.sum()
    np.testing.assert_allclose(mean, expected, rtol=1e-13, atol=1e-13)
    assert not np.allclose(mean, (qa / qa.sum(axis=1, keepdims=True)).mean(axis=0))
    assert not np.allclose(mean, [0.75, 0.25])  # A raw count pool with PPE correction.


def test_explicit_source_limitations_and_fixed_ppe_bootstrap(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    inputs = publication_inputs
    config = PublicationRevealsConfig("synthetic-bp-v1")
    first = run_reveals_multisite(inputs, config, bootstrap_indices=draws())
    second = run_reveals_multisite(
        replace(inputs, ppe_covariance=inputs.ppe_covariance * 10),
        config,
        bootstrap_indices=draws(),
    )
    np.testing.assert_array_equal(first.cover, second.cover)
    np.testing.assert_array_equal(first.standard_error, second.standard_error)
    assert not np.allclose(
        first.site_standard_error["small"], second.site_standard_error["small"]
    )
    assert first.manifest.parameters["known_source_limitations"] == list(
        PUBLICATION_LIMITATIONS
    )
    assert first.manifest.reference_package == "LRA-REVEALS-release.R"
    assert first.manifest.inputs != second.manifest.inputs
    assert not np.allclose(first.deposition["small"], first.deposition["large"])


def test_bootstrap_indices_use_original_available_site_positions(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    inputs = publication_inputs
    invalid = {"recent": np.full((1000, 2), 2)}
    with pytest.raises(ValidationError, match="unavailable or unknown"):
        run_reveals_multisite(
            inputs,
            PublicationRevealsConfig("synthetic-bp-v1"),
            bootstrap_indices=invalid,
        )
    with pytest.raises(ValidationError, match="exactly"):
        run_reveals_multisite(
            inputs, PublicationRevealsConfig("synthetic-bp-v1"), bootstrap_indices={}
        )


def test_missing_bin_is_masked_and_bundle_preserves_support(
    publication_inputs: MultisiteRevealsInput, tmp_path: Path
) -> None:
    inputs = publication_inputs
    extended = replace(
        inputs,
        bin_ids=("recent", "absent"),
        counts=np.concatenate(
            [inputs.counts, np.full_like(inputs.counts, np.nan)], axis=1
        ),
        availability=np.array([[True, False], [True, False]]),
        basin_radius_m=np.array([[25.0, np.nan], [100.0, np.nan]]),
        basin_type=np.array([["peatland", None], ["lake", None]], dtype=object),
        bin_bounds_bp=np.array([[0.0, 100.0], [100.0, 350.0]]),
    )
    result = run_reveals_multisite(
        extended, PublicationRevealsConfig("synthetic-bp-v1"), bootstrap_indices=draws()
    )
    assert result.cover.loc["absent"].isna().all()
    assert result.site_count.loc["absent"] == 0
    assert {"bin_id": "absent", "reason_code": "no_site_support"} in result.diagnostics
    result.write(tmp_path)
    assert (tmp_path / "availability.csv").is_file()
    assert (tmp_path / "bootstrap-indices.json").is_file()
    assert (tmp_path / "checksums.json").is_file()


def test_draws_are_owned_and_hashed(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    supplied = draws()
    result = run_reveals_multisite(
        publication_inputs,
        PublicationRevealsConfig("synthetic-bp-v1"),
        bootstrap_indices=supplied,
    )
    supplied["recent"][:] = 1
    assert result.bootstrap_indices["recent"][0, 0] == 0
    changed = run_reveals_multisite(
        publication_inputs,
        PublicationRevealsConfig("synthetic-bp-v1"),
        bootstrap_indices=supplied,
    )
    assert (
        result.manifest.inputs["bootstrap_indices"]
        != changed.manifest.inputs["bootstrap_indices"]
    )


def test_site_permutation_preserves_geometry_and_explicit_draw_identity(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    inputs = publication_inputs
    config = PublicationRevealsConfig("synthetic-bp-v1")
    first = run_reveals_multisite(inputs, config, bootstrap_indices=draws())
    reordered = replace(
        inputs,
        site_ids=inputs.site_ids[::-1],
        counts=inputs.counts[::-1],
        availability=inputs.availability[::-1],
        basin_radius_m=inputs.basin_radius_m[::-1],
        basin_type=inputs.basin_type[::-1],
    )
    second = run_reveals_multisite(
        reordered, config, bootstrap_indices={"recent": 1 - draws()["recent"]}
    )
    np.testing.assert_allclose(first.cover, second.cover, rtol=0, atol=1e-14)
    np.testing.assert_allclose(
        first.standard_error, second.standard_error, rtol=0, atol=1e-14
    )


def test_taxon_permutation_retains_known_source_se_defect_explicitly(
    publication_inputs: MultisiteRevealsInput,
) -> None:
    inputs = publication_inputs
    config = PublicationRevealsConfig("synthetic-bp-v1")
    first = run_reveals_multisite(inputs, config, bootstrap_indices=draws())
    permutation = [2, 0, 1]
    reordered = replace(
        inputs,
        taxon_ids=tuple(inputs.taxon_ids[index] for index in permutation),
        counts=inputs.counts[:, :, permutation],
        ppe=inputs.ppe[permutation],
        ppe_covariance=inputs.ppe_covariance[np.ix_(permutation, permutation)],
        fall_speed_m_s=inputs.fall_speed_m_s[permutation],
    )
    second = run_reveals_multisite(reordered, config, bootstrap_indices=draws())
    np.testing.assert_allclose(
        first.site_cover["small"],
        second.site_cover["small"].loc[:, list(inputs.taxon_ids)],
        rtol=0,
        atol=1e-14,
    )
    assert not np.allclose(
        first.site_standard_error["small"],
        second.site_standard_error["small"].loc[:, list(inputs.taxon_ids)],
    )
