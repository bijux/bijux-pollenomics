"""Opt-in current profiles retain original classification and authenticated access."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as api

from ..acquisition.resources.current.native_payloads import payload, resource


def inputs(
    make: Callable[..., dict[str, Any]], kind: str = "speleothem"
) -> dict[str, Any]:
    samples = payload(resource())["data"][0]["site"]["collectionunit"]["dataset"][
        "samples"
    ]
    return make(
        auxiliary_type=kind, source_database="Native database", sample_metadata=samples
    )


def publish(
    root: Path, settings: dict[str, Any]
) -> tuple[dict[str, Any], Path, str, dict[str, Path]]:
    catalogue = api.build_neotoma_resource_catalogue(**settings)
    sources = {**settings["metadata_captures"], **settings["resource_captures"]}
    output = root / "public"
    api.write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        capture_sources=sources,
        roster_path=settings["roster_path"],
    )
    return (
        catalogue,
        output,
        sha256((output / "manifest.json").read_bytes()).hexdigest(),
        sources,
    )


def edit_publication(output: Path, change: Callable[[dict[str, Any]], None]) -> str:
    path = output / "catalogue.json"
    catalogue = json.loads(path.read_bytes())
    change(catalogue)
    path.write_text(json.dumps(catalogue))
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["catalogue.json"] = sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    return sha256(manifest_path.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "damage",
    [
        "legacy_admission",
        "unknown_profile",
        "scientific_admission",
        "unit_conversion",
        "physical_inference",
        "wrong_type",
        "boolean_count",
    ],
)
def test_rehashed_compact_claims_cannot_rewrite_original_or_profile_contract(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path, damage: str
) -> None:
    settings = inputs(catalogue_sources)
    settings["qualify_current_source_profiles"] = True
    _, output, digest, sources = publish(tmp_path, settings)
    baseline = api.read_neotoma_catalogue_resource(
        output,
        expected_manifest_sha256=digest,
        dataset_id=202,
        version="current",
        capture_sources=sources,
    )
    assert baseline["qualification_status"] == "parsed_current_source"

    def change(catalogue: dict[str, Any]) -> None:
        version = catalogue["resources"][1]["versions"]["current"]
        summary = version["current_source_summary"]
        if damage == "legacy_admission":
            version["qualification_status"] = "parsed_native"
        elif damage == "unknown_profile":
            summary["parser_profile"] = "unknown_unimplemented_profile"
        elif damage == "scientific_admission":
            summary["scientific_admission"] = "admitted"
        elif damage == "unit_conversion":
            summary["units_interpreted"] = True
        elif damage == "physical_inference":
            summary["physical_depth_or_chronology_inferred"] = True
        elif damage == "wrong_type":
            summary["dataset_type"] = "pollen"
        else:
            summary["sample_rows"] = True

    digest = edit_publication(output, change)
    with pytest.raises(ValueError, match="[Cc]urrent source"):
        api.load_neotoma_resource_catalogue(output, expected_manifest_sha256=digest)


def test_selected_buffer_rechecks_the_entire_declared_context_summary(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    settings = inputs(catalogue_sources)
    settings["qualify_current_source_profiles"] = True
    _, output, digest, sources = publish(tmp_path, settings)

    def change(catalogue: dict[str, Any]) -> None:
        version = catalogue["resources"][1]["versions"]["current"]
        summary = version["current_source_summary"]
        for context in summary["native_contexts"]:
            if context["units"] == "cm":
                context["units"] = "invented measure"
        summary["source_units"] = ["NISP", "invented measure", "per mille"]
        version["native_counts"]["source_units"] = summary["source_units"]

    digest = edit_publication(output, change)
    with pytest.raises(ValueError, match="[Cc]urrent source summary"):
        api.read_neotoma_catalogue_resource(
            output,
            expected_manifest_sha256=digest,
            dataset_id=202,
            version="current",
            capture_sources=sources,
            include_native_body=True,
        )


@pytest.mark.parametrize("capture_present", [False, True])
@pytest.mark.parametrize(
    "role", ["reserved_candidate_confirmation", "heldout_no_numerical_access"]
)
def test_protected_new_types_have_one_explicit_derived_posture(
    catalogue_sources: Callable[..., dict[str, Any]], capture_present: bool, role: str
) -> None:
    settings = catalogue_sources(
        auxiliary_type="speleothem",
        auxiliary_role=role,
        capture_resources=capture_present,
    )
    catalogue = api.build_neotoma_resource_catalogue(
        **settings, qualify_current_source_profiles=True
    )
    current = catalogue["resources"][1]["versions"]["current"]
    assert (
        current["current_source_qualification_status"] == "not_qualified_exposure_role"
    )
    assert "current_source_summary" not in current


@pytest.mark.parametrize("marker", [False, 1, None, "unimplemented_current_profile"])
def test_unrecognized_current_profile_namespace_refuses_before_source_access(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path, marker: Any
) -> None:
    settings = inputs(catalogue_sources)
    settings["qualify_current_source_profiles"] = True
    _, output, _, _ = publish(tmp_path, settings)
    digest = edit_publication(
        output, lambda c: c.update(current_source_profile_schema=marker)
    )
    with pytest.raises(ValueError, match="[Cc]urrent source"):
        api.load_neotoma_resource_catalogue(output, expected_manifest_sha256=digest)


def test_unmarked_derived_claims_cannot_promote_legacy_publications(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    settings = inputs(catalogue_sources)
    settings["qualify_current_source_profiles"] = True
    _, output, _, _ = publish(tmp_path, settings)

    def change(catalogue: dict[str, Any]) -> None:
        del catalogue["current_source_profile_schema"]
        catalogue["resources"][1]["method_capability"].update(
            status="unsupported_dataset_type", evidence_role=None
        )

    digest = edit_publication(output, change)
    with pytest.raises(ValueError, match="[Cc]urrent source"):
        api.load_neotoma_resource_catalogue(output, expected_manifest_sha256=digest)


def test_unknown_native_kind_cannot_inherit_a_known_derived_profile(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    settings = inputs(catalogue_sources, "unobserved native type")
    settings["qualify_current_source_profiles"] = True
    _, output, _, _ = publish(tmp_path, settings)

    def change(catalogue: dict[str, Any]) -> None:
        catalogue["resources"][1]["versions"]["current"][
            "current_source_qualification_status"
        ] = "parsed_current_source"

    digest = edit_publication(output, change)
    with pytest.raises(ValueError, match="[Cc]urrent source"):
        api.load_neotoma_resource_catalogue(output, expected_manifest_sha256=digest)


def test_default_catalogue_retains_original_unsupported_capture_projection(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    settings = inputs(catalogue_sources)
    catalogue = api.build_neotoma_resource_catalogue(**settings)
    explicit = api.build_neotoma_resource_catalogue(
        **settings, qualify_current_source_profiles=False
    )
    assert catalogue == explicit
    assert "current_source_profile_schema" not in catalogue
    current = catalogue["resources"][1]["versions"]["current"]
    assert current["source_terminal_status"] == "unsupported_dataset_type"
    assert current["qualification_status"] == "not_qualified"
    assert "current_source_qualification_status" not in current


def test_declared_current_profiles_publish_raw_checks_without_changing_source_ledgers(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    settings = inputs(catalogue_sources)
    roots = list(settings["resource_captures"].values())
    before = {
        str(p): sha256(p.read_bytes()).hexdigest()
        for root in roots
        for p in root.iterdir()
    }
    settings["qualify_current_source_profiles"] = True
    catalogue, output, digest, sources = publish(tmp_path, settings)
    assert (
        catalogue["current_source_profile_schema"]
        == "neotoma-current-source-qualification.v1"
    )
    row = catalogue["resources"][1]
    current = row["versions"]["current"]
    assert current["acquisition_status"] == "unsupported_dataset_type"
    assert current["source_terminal_status"] == "unsupported_dataset_type"
    assert current["qualification_status"] == "not_qualified"
    assert current["current_source_qualification_status"] == "parsed_current_source"
    assert current["native_counts"]["raw_sample_rows"] == 1
    assert current["native_counts"]["raw_datum_rows"] == 3
    assert (
        current["current_source_summary"]["biological_denominator"] == "not_established"
    )
    assert row["method_capability"]["independent_lra_accuracy"] is False
    assert row["method_capability"]["scientific_admission"] == "not_asserted"
    readback = api.load_neotoma_resource_catalogue(
        output,
        expected_manifest_sha256=digest,
        capture_sources=sources,
        require_source_bodies=True,
    )
    assert readback == catalogue
    assert before == {
        str(p): sha256(p.read_bytes()).hexdigest()
        for root in roots
        for p in root.iterdir()
    }


def test_typed_reader_can_use_qualified_new_current_source_and_exact_body(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    settings = inputs(catalogue_sources)
    settings["qualify_current_source_profiles"] = True
    _, output, digest, sources = publish(tmp_path, settings)
    result = api.read_neotoma_catalogue_resource(
        output,
        expected_manifest_sha256=digest,
        dataset_id=202,
        version="current",
        capture_sources=sources,
        include_native_body=True,
    )
    assert result["qualification_status"] == "parsed_current_source"
    assert result["source_terminal_status"] == "unsupported_dataset_type"
    assert result["parser_profile"] == "current_native_proxy_hierarchy.v1"
    assert sha256(result["native_body"]).hexdigest() == result["source"]["body_sha256"]
    assert json.loads(result["native_body"]) == result["native_payload"]
    sample = result["native_payload"]["data"][0]["site"]["collectionunit"]["dataset"][
        "samples"
    ][0]
    assert sample["depth"] is None
    assert sample["datum"][0]["value"] == 3.5
    assert sample["datum"][2]["value"] == -24.2


def test_opt_in_does_not_change_frozen_or_existing_native_qualifications(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    settings = inputs(catalogue_sources)
    old = api.build_neotoma_resource_catalogue(**settings)
    new = api.build_neotoma_resource_catalogue(
        **settings, qualify_current_source_profiles=True
    )
    for a, b in zip(old["resources"], new["resources"], strict=True):
        assert a["versions"]["doi_frozen"] == b["versions"]["doi_frozen"]
        if a["dataset_type"] == "pollen":
            assert a["versions"]["current"] == b["versions"]["current"]


@pytest.mark.parametrize("bad", [1, "true", None, [], {}])
def test_profile_opt_in_requires_literal_bool_before_source_access(
    tmp_path: Path, bad: Any
) -> None:
    with pytest.raises(ValueError, match="literal boolean"):
        api.build_neotoma_resource_catalogue(
            roster_path=tmp_path / "absent",
            expected_roster_sha256="0" * 64,
            metadata_captures={},
            resource_captures={},
            qualify_current_source_profiles=bad,
        )


@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_profile_opt_in_does_not_authorize_protected_resources(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path, version: str
) -> None:
    settings = inputs(catalogue_sources)
    settings["qualify_current_source_profiles"] = True
    _, output, digest, _ = publish(tmp_path, settings)

    class NoOutcome(dict[str, Path]):
        def __contains__(self, key: object) -> bool:
            raise AssertionError("Protected resolver consulted")

        def __getitem__(self, key: str) -> Path:
            raise AssertionError("Protected source opened")

    with pytest.raises(ValueError, match="exposure role"):
        api.read_neotoma_catalogue_resource(
            output,
            expected_manifest_sha256=digest,
            dataset_id=203,
            version=version,
            capture_sources=NoOutcome(),
            include_native_body=True,
        )
