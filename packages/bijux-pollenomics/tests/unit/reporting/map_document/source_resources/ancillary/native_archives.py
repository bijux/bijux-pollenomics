"""Real independently published support archives on their own native source epochs."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
    write_neotoma_context_resource_archive,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
    write_neotoma_ancillary_federation,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
    write_neotoma_unit_metadata_archive,
)
from bijux_pollenomics.reporting.map_document import source_resources as owner

from .....collection.sources.neotoma.ancillary_store.context_resources.native_products import (
    site_context_products as site_context_products,
)
from .....collection.sources.neotoma.ancillary_store.reference_tables.native_prefixes import (
    reference_archive as reference_archive,
)
from .....collection.sources.neotoma.ancillary_store.reference_tables.native_prefixes import (
    reference_source as reference_source,
)
from .....collection.sources.neotoma.ancillary_store.unit_metadata.native_products import (
    unit_products as unit_products,
)


def pin(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def supporting_sources(
    unit_products: Callable[..., dict[str, Any]],
    site_context_products: Callable[..., dict[str, Any]],
    reference_archive: dict[str, Any],
    tmp_path: Path,
) -> Callable[..., dict[str, Any]]:
    def make(kind: str, *, changed: bool = False) -> dict[str, Any]:
        archive = tmp_path / (kind + "-source-archive")
        original = None
        reference: owner.AtlasSourceArchiveInput
        if kind == "context_resources":
            product = site_context_products(change="protected" if changed else None)
            write_neotoma_context_resource_archive(
                archive, **{**product["writer"], "current": product["original"]}
            )
            original, current = product["original"], product["current"]
            context, native = (
                current.context_directory,
                current.native_archive_directory,
            )
            reference = owner.AtlasContextArchiveInput(
                archive, pin(archive / "manifest.json"), original
            )
        else:
            product = unit_products(protected=changed)
            context, native = product["context"], product["native"]
            if kind == "unit_metadata":
                write_neotoma_unit_metadata_archive(archive, **product["writer"])
            elif kind == "reference_tables":
                archive = reference_archive["directory"]
            else:
                raise ValueError("Unknown supporting source family")
            reference = owner.AtlasSourceArchiveInput(
                archive, pin(archive / "manifest.json")
            )
        federation = tmp_path / (kind + "-metadata-federation")
        write_neotoma_ancillary_federation(
            federation,
            context_directory=context,
            expected_context_sha256=pin(context / "manifest.json"),
            native_archive_directory=native,
            capsule_sources={},
        )
        archives: dict[str, Any] = {kind: (reference,)}
        configured = owner.AtlasResourceCatalogueInput(
            native / "catalogue",
            pin(native / "catalogue/manifest.json"),
            archive=owner.AtlasResourceArchiveInput(
                native, pin(native / "manifest.json"), "/data/neotoma/source-resources/"
            ),
            ancillary=owner.AtlasAncillaryFederationInput(
                federation,
                pin(federation / "manifest.json"),
                context,
                pin(context / "manifest.json"),
                {},
                archives=owner.AtlasAncillaryArchivesInput(**archives),
            ),
        )
        return {
            "source": configured,
            "directory": archive,
            "kind": kind,
            "reference": reference,
            "product": product,
            "original": original,
        }

    return make


@pytest.fixture
def second_reference_archive(tmp_path: Path) -> dict[str, Any]:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.reference_tables import (
        write_neotoma_reference_archive,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.reference_tables import (
        NeotomaReferenceTablePlan,
        capture_neotoma_reference_tables,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.transport import (
        NeotomaHttpResponse,
    )

    def fetched(url: str, **_: Any) -> NeotomaHttpResponse:
        body = (
            b'{"status":"success","data":[]}'
            if "geopoliticalunits" in url
            else b'{"status":"success","data":[{"variableunitsid":77,"variableunits":"cm"}]}'
        )
        return NeotomaHttpResponse(url, 200, (), body)

    capture = tmp_path / "another-reference-capture"
    result = capture_neotoma_reference_tables(
        capture,
        plan=NeotomaReferenceTablePlan(("variableunits", "geopoliticalunits")),
        fetch=fetched,
    )
    directory = tmp_path / "another-reference-archive"
    write_neotoma_reference_archive(
        directory,
        capture_directory=capture,
        expected_capture_manifest_sha256=result.manifest_sha256,
    )
    return {"directory": directory, "sha256": pin(directory / "manifest.json")}
