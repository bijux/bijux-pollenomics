"""Exercise full-cardinality transport without claiming chronology/native admission."""

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import index as retained

from .fixtures import (
    PREFIX,
    RUNTIME_MEMBER,
    RUNTIME_PATH,
    Catalogue,
)
from .fixtures import (
    catalogue as catalogue,
)


def test_complete_logical_catalogue_has_only_300_physical_payloads(
    catalogue: Catalogue,
) -> None:
    document = catalogue.document
    assert len(document["files"]) == 1472
    assert len(document["source_footprint"]) == len(document["source_members"]) == 1226
    assert len(catalogue.state.bodies) == 1171
    assert len(catalogue.payloads) == 300
    assert sum(name.startswith("source/") for name in catalogue.payloads) == 55
    assert len(document["cases"]) == 9 and len(document["generations"]) == 5
    assert len(document["products"]) == 43
    assert len(catalogue.own_runtime) == 539
    assert RUNTIME_PATH not in document["source_footprint"]
    capsule = catalogue.validate()
    assert len(capsule.detached) == 1172
    assert catalogue.state.body_reads == 1171
    assert capsule.read_source(RUNTIME_MEMBER) == catalogue.own_runtime
    assert (
        capsule.read_source("source/packages/own/chronology_0000.py")
        == catalogue.state.bodies["packages/own/chronology_0000.py"]
    )
    assert (
        capsule.read_source("source/data/own/source_000.json")
        == catalogue.payloads["source/data/own/source_000.json"]
    )
    assert (
        len([path for path in catalogue.directory.rglob("*") if path.is_file()]) == 302
    )
    assert not (catalogue.directory / RUNTIME_MEMBER).exists()
    assert not (catalogue.directory / "source/packages/own/chronology_0000.py").exists()


def test_existing_index_path_api_uses_only_fixture_owned_pins(
    catalogue: Catalogue,
) -> None:
    capsule = catalogue.validate(indexed=True)
    assert len(capsule.detached) == 1172
    logical = Path(PREFIX) / RUNTIME_MEMBER
    assert (
        retained.read_source_path(catalogue.repository, logical)
        == catalogue.own_runtime
    )
    assert retained.source_revision(catalogue.repository, "a" * 40) == "b" * 40
    with pytest.raises(ReportRebuildError, match="unique indexed capsule"):
        retained.read_source_path(
            catalogue.repository, "data/atlas/unregistered/runtime.py"
        )


@pytest.mark.parametrize(
    "field", ["source_footprint", "cases", "generations", "products"]
)
def test_transport_does_not_substitute_for_native_population_admission(
    catalogue: Catalogue, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    value = catalogue.document[field]
    if isinstance(value, dict):
        del value[next(iter(value))]
    else:
        value.pop()
    catalogue.refresh(monkeypatch)
    # The generic API owns byte transport, not these native schema predicates.
    assert len(catalogue.validate().detached) == 1172
    assert catalogue.document["scientific_admission"] is False
    assert catalogue.document["sample_chronology_admission"] is False
    assert catalogue.document["numerical_execution"] is False
