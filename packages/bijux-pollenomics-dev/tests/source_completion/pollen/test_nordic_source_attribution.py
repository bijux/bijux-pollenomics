"""Keep DOI identity, rights declarations and primary citations distinct."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


PRODUCER = (
    Path(__file__).resolve().parents[5]
    / "reports/science/nordic-source-attribution/qualify.py"
)


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("nordic_source_attribution", PRODUCER)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.mark.parametrize(
    "locator",
    [
        "http://data.neotomadb.org/53969",
        "https://data.neotomadb.org/datasets/53969/index.html",
        "https://api.neotomadb.org/v2.0/data/downloads/53969",
    ],
)
def test_native_dataset_locators(locator: str) -> None:
    assert module().dataset_locator(locator) == 53969


@pytest.mark.parametrize(
    "locator",
    [
        "https://data.neotomadb.org.evil.example/53969",
        "https://elsewhere.example/datasets/53969",
        "https://data.neotomadb.org/datasets/53969/publications",
    ],
)
def test_native_identity_cannot_be_inferred_from_other_urls(locator: str) -> None:
    assert module().dataset_locator(locator) is None


def attributes() -> dict[str, Any]:
    return {
        "doi": "10.21233/2ers-re93",
        "url": "http://data.neotomadb.org/53969",
        "publicationYear": 2022,
        "rightsList": [{"rights": "CC-BY4"}, {"rights": "TK Open to Collaboration"}],
        "relatedIdentifiers": [
            {"relationType": "IsIdenticalTo", "relatedIdentifier": "10.21233/other"}
        ],
    }


def request() -> dict[str, Any]:
    return {"dataset_id": 53969, "native_doi": "10.21233/2ERS-RE93"}


def test_doi_case_is_preserved_without_promoting_registration_to_science() -> None:
    source = attributes()
    account = module().registration_account(source, request())
    assert account["registered_doi"] == source["doi"]
    assert account["source_rights_declarations"] == source["rightsList"]
    assert account["related_identifier_assertions"] == source["relatedIdentifiers"]
    assert account["registration_publication_year"] == 2022
    assert account["native_collection_unit_id"] == 39224
    assert not account["primary_journal_publication_admitted"]
    assert not account["source_year_interpreted_as_sample_date_or_BP_epoch"]
    assert not account["linked_identifiers_establish_byte_identical_pollen_counts"]


@pytest.mark.parametrize(
    "field,value",
    [("doi", "10.21233/unknown"), ("url", "https://data.neotomadb.org/datasets/53970")],
)
def test_wrong_registration_identity_is_refused(field: str, value: str) -> None:
    source = attributes()
    source[field] = value
    with pytest.raises(ValueError):
        module().registration_account(source, request())


def test_missing_rights_are_preserved_without_an_invented_license() -> None:
    source = attributes()
    source.pop("rightsList")
    assert (
        module().registration_account(source, request())["source_rights_declarations"]
        == []
    )


def test_source_tamper_is_refused_before_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    producer = module()
    source = tmp_path / "source"
    source.mkdir()
    (source / "plan.json").write_text("{}")
    monkeypatch.setattr(producer, "DOMAIN", PRODUCER.parent)
    with pytest.raises(ValueError, match="custody differs"):
        producer.qualify(source)
    assert not (source / "output.json").exists()
