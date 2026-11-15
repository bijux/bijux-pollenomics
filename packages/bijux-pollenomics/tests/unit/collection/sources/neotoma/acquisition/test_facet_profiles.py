"""Qualified facet shapes preserve native owners, nulls and unsupported source scope."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

from .test_resource_capture import response, spec


def profiles() -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.facets.profiles"
    )


def qualification() -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.facets.qualification"
    )


def resource(role: str = "development_resource_discovery") -> Any:
    return replace(spec(19913, role=role), site_id=13338, collection_unit_id=14910)


def payload(facet: str) -> dict[str, Any]:
    """Use observed native wrappers with synthetic literal records, not API aliases."""
    if facet == "chronologies":
        data: Any = [
            {
                "chronology": {
                    "agetype": "Calendar years BP",
                    "default": True,
                    "controls": [
                        {
                            "chroncontrolid": 39864,
                            "age": -52,
                            "depth": 648,
                            "thickness": 1,
                            "agetype": None,
                            "controltype": "Core top",
                            "geochron": {"geochronid": None},
                            "controllimits": {"ageolder": None, "ageyounger": None},
                        }
                    ],
                    "datasets": [{"datasetid": 19913, "datasettype": "pollen"}],
                    "modelType": "source model",
                    "preparedby": {"contactid": 8720},
                    "chronologyid": 11516,
                    "datePrepared": "2004-01-01",
                    "chronologyName": "Source chronology",
                    "chronologynotes": None,
                    "reliableagespan": {"older": 900, "younger": -52},
                }
            }
        ]
    elif facet == "lithology":
        data = [
            {
                "datasetid": 19913,
                "lithology": [
                    {
                        "lithologyid": 32530,
                        "depth": {"top": 648, "bottom": 877},
                        "lowerboundary": "",
                        "description": "Literal sediment prose",
                    }
                ],
            }
        ]
    elif facet == "projects":
        data = {"datasetid": 19913, "projects": []}
    elif facet == "publications":
        data = [
            {
                "publication": {
                    "datasets": [
                        {"siteid": 13338, "primary": True, "datasetid": 19913}
                    ],
                    "publicationid": 9435,
                    "doi": None,
                    "author": [
                        {"order": 1, "familyname": "Source", "givennames": "Author"}
                    ],
                }
            }
        ]
    else:
        assert facet == "taxa"
        higher = [1, 2, 3, *range(1000, 1083)]
        data = [
            {
                "taxonid": i + 1,
                "taxonname": f"Taxon {i + 1}",
                "author": None if i == 0 else "Native author",
                "ecolgroup": "UPHE",
                "status": "literal source status",
                "highertaxonid": higher[i % 86],
                "publicationid": i % 24 + 1 if i < 92 else None,
                "publication": "Taxonomic reference" if i < 92 else None,
            }
            for i in range(94)
        ]
    return {"status": "success", "data": data, "message": "Source message"}


def classify(facet: str, value: dict[str, Any], *, root: Any = None) -> dict[str, Any]:
    body = json.dumps(value, ensure_ascii=False).encode()
    return cast(
        dict[str, Any],
        profiles().qualify_neotoma_facet_body(
            resource() if root is None else root,
            facet,
            body,
            expected_body_sha256=sha256(body).hexdigest(),
        ),
    )


@pytest.mark.parametrize(
    "facet", ["chronologies", "lithology", "projects", "publications", "taxa"]
)
def test_literal_source_shapes_remain_separate_from_scientific_admission(
    facet: str,
) -> None:
    source = payload(facet)
    original = deepcopy(source)
    result = classify(facet, source)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["source_payload"] == original and source == original
    assert result["scientific_admission"] == "not_asserted"
    assert result["units_interpreted"] is False
    assert result["owner_verification"]["collection_unit"] == "not_supplied"
    assert result["owner_verification"]["database"] == "not_supplied"
    if facet == "chronologies":
        assert (
            result["source_payload"]["data"][0]["chronology"]["controls"][0]["age"]
            == -52
        )
        assert result["chronology_selected"] is False
    if facet == "taxa":
        assert (
            result["owner_verification"]["dataset"]
            == "authenticated_request_endpoint_only"
        )
    if facet == "projects":
        assert result["population_status"] == "source_explicit_empty_array"
        assert result["received_record_count"] == 0


@pytest.mark.parametrize(
    "facet", ["chronologies", "lithology", "projects", "publications"]
)
def test_foreign_native_dataset_owner_is_not_replaced_by_requested_endpoint(
    facet: str,
) -> None:
    value = payload(facet)
    if facet == "chronologies":
        value["data"][0]["chronology"]["datasets"][0]["datasetid"] = 999
    elif facet == "publications":
        value["data"][0]["publication"]["datasets"][0]["datasetid"] = 999
    elif facet == "projects":
        value["data"]["datasetid"] = 999
    else:
        value["data"][0]["datasetid"] = 999
    result = classify(facet, value)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert "dataset" in result["reason"]
    assert result["source_payload"] == value


def test_foreign_publication_site_and_chronology_type_refuse_source_binding() -> None:
    value = payload("publications")
    value["data"][0]["publication"]["datasets"][0]["siteid"] = 1
    assert (
        classify("publications", value)["qualification_status"]
        == "unqualified_source_schema"
    )
    value = payload("chronologies")
    value["data"][0]["chronology"]["datasets"][0]["datasettype"] = "geochronologic"
    assert (
        classify("chronologies", value)["qualification_status"]
        == "unqualified_source_schema"
    )


@pytest.mark.parametrize("identity", [True, 1.5, "1", None])
def test_native_taxon_id_is_never_coerced_or_dropped(identity: object) -> None:
    value = payload("taxa")
    value["data"][0]["taxonid"] = identity
    result = classify("taxa", value)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert len(result["source_payload"]["data"]) == 94


def test_unobserved_populated_projects_is_not_qualified_as_empty() -> None:
    value = payload("projects")
    value["data"]["projects"] = [{"projectid": 9, "participants": [{"contactid": 8}]}]
    result = classify("projects", value)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert result["source_payload"]["data"]["projects"] == value["data"]["projects"]
    missing = payload("projects")
    del missing["data"]["projects"]
    assert (
        classify("projects", missing)["qualification_status"]
        == "unqualified_source_schema"
    )


def test_null_geochron_and_repeated_native_control_variants_are_not_zero_or_deduplicated() -> (
    None
):
    value = payload("chronologies")
    controls = value["data"][0]["chronology"]["controls"]
    controls.append({**deepcopy(controls[0]), "geochron": {"geochronid": 17863}})
    result = classify("chronologies", value)
    assert result["qualification_status"] == "qualified_source_schema"
    assert len(result["source_payload"]["data"][0]["chronology"]["controls"]) == 2
    assert (
        result["source_payload"]["data"][0]["chronology"]["controls"][0]["geochron"][
            "geochronid"
        ]
        is None
    )


def test_role_and_body_custody_refusals_are_not_schema_qualification() -> None:
    value = payload("taxa")
    with pytest.raises(ValueError, match="exposure role"):
        classify("taxa", value, root=resource("reserved_candidate_confirmation"))
    with pytest.raises(ValueError, match="body identity"):
        profiles().qualify_neotoma_facet_body(
            resource(),
            "taxa",
            json.dumps(value).encode(),
            expected_body_sha256="f" * 64,
        )


def capture(root: Path) -> Any:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        NeotomaFacetPlan,
        capture_neotoma_dataset_facets,
    )

    return capture_neotoma_dataset_facets(
        root,
        plan=NeotomaFacetPlan((resource(),), "b" * 64),
        fetch=lambda url, **_: response(
            url, json.dumps(payload(url.rsplit("/", 1)[-1])).encode()
        ),
    )


def test_authenticated_qualification_preserves_original_capture_labels(
    tmp_path: Path,
) -> None:
    result = capture(tmp_path / "capture")
    before = {p.name: p.read_bytes() for p in (tmp_path / "capture").iterdir()}
    report = qualification().qualify_neotoma_facet_capture(
        tmp_path / "capture",
        expected_manifest_sha256=result.manifest_sha256,
    )
    assert len(report["entries"]) == 5
    assert report["partitions"] == {"qualified_source_schema": 5}
    assert report["capture_assessments_relabelled"] is False
    assert before == {p.name: p.read_bytes() for p in (tmp_path / "capture").iterdir()}


@pytest.mark.parametrize("field", ["contactid", "chronologyName", "age", "geochronid"])
def test_missing_native_member_is_not_an_explicit_null(field: str) -> None:
    source = payload("chronologies")
    chronology = source["data"][0]["chronology"]
    if field == "contactid":
        del chronology["preparedby"][field]
    elif field == "age":
        del chronology["controls"][0][field]
    elif field == "geochronid":
        del chronology["controls"][0]["geochron"][field]
    else:
        del chronology[field]
    result = classify("chronologies", source)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert result["source_payload"] == source


@pytest.mark.parametrize("field", ["age", "depth", "thickness"])
@pytest.mark.parametrize("value", [True, "12", [], {}])
def test_chronology_native_numeric_shape_is_not_coerced(field: str, value: Any) -> None:
    source = payload("chronologies")
    source["data"][0]["chronology"]["controls"][0][field] = value
    assert (
        classify("chronologies", source)["qualification_status"]
        == "unqualified_source_schema"
    )


@pytest.mark.parametrize("field", ["siteid", "database", "collectionunitid"])
def test_unobserved_chronology_owner_extension_is_retained_unqualified(
    field: str,
) -> None:
    source = payload("chronologies")
    source["data"][0]["chronology"][field] = "foreign native context"
    result = classify("chronologies", source)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert result["source_payload"] == source


@pytest.mark.parametrize("facet", ["chronologies", "lithology"])
def test_bound_or_layer_depth_boolean_is_not_a_native_number(facet: str) -> None:
    source = payload(facet)
    if facet == "chronologies":
        source["data"][0]["chronology"]["reliableagespan"]["older"] = True
    else:
        source["data"][0]["lithology"][0]["depth"]["top"] = True
    assert (
        classify(facet, source)["qualification_status"] == "unqualified_source_schema"
    )


def test_signed_raw_nulls_and_shared_relationships_do_not_select_a_model() -> None:
    source = payload("chronologies")
    chronology = source["data"][0]["chronology"]
    chronology["controls"][0].update(age=None, depth=-5, thickness=None)
    chronology["preparedby"]["contactid"] = None
    chronology["datasets"].append({"datasetid": 100, "datasettype": "pollen"})
    result = classify("chronologies", source)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["source_payload"] == source
    assert result["chronology_selected"] is False


def test_unobserved_publication_owner_extension_is_not_reported_as_unsupplied() -> None:
    source = payload("publications")
    source["data"][0]["publication"]["collectionunitid"] = 999
    result = classify("publications", source)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert result["source_payload"] == source


def test_unavailable_and_protected_facets_are_partitioned_without_body_access(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        NeotomaFacetPlan,
        capture_neotoma_dataset_facets,
    )

    root = tmp_path / "capture"
    captured = capture_neotoma_dataset_facets(
        root,
        plan=NeotomaFacetPlan(
            (
                resource(),
                replace(resource("heldout_no_numerical_access"), dataset_id=19914),
            ),
            "b" * 64,
        ),
        fetch=lambda url, **_: response(url, b'{"error":"source failed"}', status=500),
    )
    report = qualification().qualify_neotoma_facet_capture(
        root, expected_manifest_sha256=captured.manifest_sha256
    )
    assert len(report["entries"]) == 10
    assert report["partitions"] == {"source_entity_unavailable": 10}
    assert (
        sum(row["reason"] == "not_attempted_exposure_role" for row in report["entries"])
        == 5
    )
    assert all("source_payload" not in row for row in report["entries"])
