"""Ownership and permutation invariants for multi-site REVEALS results."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from bijux_pollenomics_lra.api import (
    MultisiteRevealsInput,
    PublicationRevealsConfig,
    run_reveals_multisite,
)


def draws() -> dict[str, np.ndarray]:
    return {"recent": np.tile([[0, 0], [0, 1], [1, 0], [1, 1]], (250, 1))}


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
