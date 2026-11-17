"""Refuse scientific contradictions even when a derived manifest is rehashed."""

from importlib import import_module

import pytest

from . import support

workflow = import_module("bijux_pollenomics.analysis.lra.source_cases.workflow")
reading = import_module("bijux_pollenomics.analysis.lra.source_cases.reading")
results = import_module("bijux_pollenomics.analysis.lra.source_cases.results")
contracts = import_module("bijux_pollenomics.analysis.lra.source_cases.contracts")
errors = import_module("bijux_pollenomics.analysis.lra.engine.errors")


@pytest.fixture
def product(tmp_path, monkeypatch):
    root = tmp_path / "generated"
    _, value = support.fixture(root)
    calls = []

    def refuse(*args, **kwargs):
        calls.append(True)
        raise errors.LRARefusal(
            "lra_numerical_refusal", "generated refusal; no model run"
        )

    monkeypatch.setattr(workflow, "run_lra_request", refuse)
    product = workflow.run_source_lra_cases(
        contracts.SourceCasePlan.from_dict(value),
        input_root=root,
        destination=tmp_path / "derived",
    )
    assert len(calls) == 2
    manifest = product.manifest()
    assert all(row["status"] == "refused" for row in manifest["cases"])
    assert (
        reading.read_source_lra_cases(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        ).manifest()
        == manifest
    )
    return product, manifest


@pytest.mark.parametrize(
    "change",
    [
        "negative_refused_mass",
        "unknown_design",
        "unknown_outcome",
        "unknown_full_but_zero_excluded",
        "native_zero_below_panel",
        "authenticity_claim",
    ],
)
def test_reader_refuses_inconsistent_scientific_contract(product, change):
    product, manifest = product
    if change == "negative_refused_mass":
        manifest["cases"][0]["mass"] = "-1"
        manifest["cases"][1]["mass"] = "2"
    elif change == "unknown_design":
        manifest["design_kind"] = "posterior_probability"
        for row in manifest["cases"]:
            row["mass"] = None
    elif change == "unknown_outcome":
        manifest["cases"][0]["status"] = "excluded_favorable_subset"
    elif change == "unknown_full_but_zero_excluded":
        manifest["source_coverage"][0]["excluded_native_pollen_N"] = 0
    elif change == "native_zero_below_panel":
        manifest["source_coverage"][0].update(
            native_full_pollen_N=0, excluded_native_pollen_N=0
        )
    elif change == "authenticity_claim":
        manifest["empirical_source_authenticity_verified"] = True
    manifest["summaries"] = results.design_summaries(
        manifest["cases"],
        weighted=manifest["design_kind"] == "caller_weighted_finite_design",
    )
    manifest["scientific_content_sha256"] = reading.scientific_identity(manifest)
    raw = contracts.canonical(manifest)
    (product.directory / "manifest.json").write_bytes(raw)
    with pytest.raises((errors.LRARefusal, ValueError)):
        reading.read_source_lra_cases(
            product.directory, expected_manifest_sha256=contracts.digest(raw)
        )
