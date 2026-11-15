"""Literal global response predating a second native source occurrence."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as catalogue
from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
    write_neotoma_ancillary_context,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
    write_neotoma_ancillary_capsule,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
    write_neotoma_ancillary_federation,
)
from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
    capture_neotoma_dataset_facets,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    NeotomaLinkedResourcePlan,
    NeotomaLinkedTarget,
    publish_neotoma_linked_evidence,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    write_neotoma_source_archive,
)

from ....acquisition.linked_resources.evidence.native_products import (
    capture_legacy_linked_fixture,
    payload,
    products,
)
from ....acquisition.resources.native_payloads import response


def pin(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def association_products(
    tmp_path: Path, request: pytest.FixtureRequest
) -> dict[str, Any]:
    (tmp_path / "inputs").mkdir()
    inputs = products(tmp_path / "inputs", separate=True)
    scope = inputs["scope"]
    source = next(iter(inputs["source_facets"].values()))
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.replay import (
        _control,
    )

    _, plan, _, _ = _control(source, pin(source / "capture-manifest.json"))
    sources = {}
    for resource in plan.resources:
        directory = tmp_path / f"facet-{resource.dataset_id}"
        captured = capture_neotoma_dataset_facets(
            directory,
            plan=replace(plan, resources=(resource,)),
            scope=scope,
            fetch=lambda url, **_: response(
                url,
                json.dumps(
                    payload(int(url.split("/")[-2]), url.split("/")[-1])
                ).encode(),
            ),
        )
        sources[captured.manifest_sha256] = directory
    # Include the protected source as a complete recorded zero-request scope.
    for digest, directory in inputs["source_facets"].items():
        if directory.name == "protected-facets":
            sources[digest] = directory
    selected = next(
        (digest, root) for digest, root in sources.items() if root.name == "facet-201"
    )
    legacy = tmp_path / "legacy-linked"
    native: dict[str, Any] = {
        "taxonid": 11,
        "taxoncode": "Native",
        "taxonname": "Native plant",
        "author": None,
        "ecolgroup": "UPHE",
        "highertaxonid": None,
        "status": "extant",
        "taxagroupid": "VPL",
        "publicationid": None,
        "publication": None,
    }
    scenario = getattr(request, "param", "taxon")
    kind = "contact" if scenario == "contact" else "taxon"
    native_id = 900 if kind == "contact" else 11
    if kind == "contact":
        from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.profiles import (
            _CONTACT_FIELDS,
        )

        native = dict.fromkeys(_CONTACT_FIELDS)
        native["contactid"] = native_id
    captured = capture_legacy_linked_fixture(
        legacy,
        plan=NeotomaLinkedResourcePlan(
            (selected[0],), (NeotomaLinkedTarget(kind, native_id),)
        ),
        source_facets={selected[0]: selected[1]},
        scope_inputs={inputs["expected_roster_sha256"]: scope},
        fetch=lambda url, **_: replace(
            response(
                url,
                json.dumps(
                    {
                        "status": "success",
                        "data": [native],
                        "message": "Literal native response",
                    }
                ).encode(),
            ),
            http_status=503 if scenario == "unavailable" else 200,
        ),
    )
    evidence = publish_neotoma_linked_evidence(
        tmp_path / "evidence", **{**inputs, "source_facets": sources}
    )
    public = tmp_path / "catalogue"
    logical = catalogue.build_neotoma_resource_catalogue(
        roster_path=scope.roster_path,
        expected_roster_sha256=inputs["expected_roster_sha256"],
        metadata_captures=scope.metadata_captures,
        resource_captures={},
        country_boundaries={},
    )
    catalogue.write_neotoma_resource_catalogue(
        public,
        catalogue=logical,
        roster_path=scope.roster_path,
        capture_sources=scope.metadata_captures,
    )
    native_root = tmp_path / "native"
    write_neotoma_source_archive(
        native_root,
        catalogue_directory=public,
        expected_catalogue_manifest_sha256=pin(public / "manifest.json"),
        capture_sources=scope.metadata_captures,
    )
    authority = tmp_path / "authority.json"
    authority.write_text('{"status":"literal_source_review"}')
    context = tmp_path / "context"
    write_neotoma_ancillary_context(
        context,
        native_archive_directory=native_root,
        expected_native_archive_sha256=pin(native_root / "manifest.json"),
        legacy_rosters={inputs["expected_roster_sha256"]: scope.roster_path},
        exposure_authority=authority,
        expected_exposure_authority_sha256=pin(authority),
    )
    common: dict[str, Any] = {
        "context_directory": context,
        "expected_context_sha256": pin(context / "manifest.json"),
        "native_archive_directory": native_root,
    }
    capsule = tmp_path / "capsule"
    write_neotoma_ancillary_capsule(
        capsule,
        facet_captures=sources,
        linked_captures={captured.manifest_sha256: legacy},
        **common,
    )
    capsules = {pin(capsule / "manifest.json"): capsule}
    federation = tmp_path / "federation"
    write_neotoma_ancillary_federation(federation, capsule_sources=capsules, **common)
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        NeotomaLinkedAssociationInputs,
    )

    return {
        "inputs": NeotomaLinkedAssociationInputs(
            federation,
            pin(federation / "manifest.json"),
            context,
            common["expected_context_sha256"],
            native_root,
            pin(native_root / "manifest.json"),
            capsules,
        ),
        "evidence": evidence,
        "legacy": legacy,
        "capsule": capsule,
        "sources": sources,
        "native_payload": native,
    }


def false_native_pointer_state(evidence: Any, directory: Path) -> Any:
    """An independently anchored state whose claimed higher field has another native ID."""
    import shutil

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedEvidence,
    )

    shutil.copytree(evidence.directory, directory)
    header = json.loads((directory / "evidence-manifest.json").read_bytes())
    for descriptor in header["parts"]:
        old = descriptor["sha256"]
        path = directory / "proofs" / f"{old}.json"
        document = json.loads(path.read_bytes())
        for proof in document["proofs"]:
            if proof["target_kind"] == "taxon" and proof["native_id"] == 11:
                proof.update(
                    relation="source_reported_higher_taxon",
                    optional_higher_taxon=True,
                    json_pointer="/data/0/highertaxonid",
                )
        raw = json.dumps(document).encode()
        new = sha256(raw).hexdigest()
        path.unlink()
        (directory / "proofs" / f"{new}.json").write_bytes(raw)
        descriptor.update(sha256=new, bytes=len(raw))
        for target in header["targets"].values():
            for span in target["proof_ranges"]:
                if span["part_sha256"] == old:
                    span["part_sha256"] = new
    header["targets"]["taxon-11"]["has_direct_proof"] = False
    (directory / "evidence-manifest.json").write_text(json.dumps(header))
    return NeotomaLinkedEvidence(directory, pin(directory / "evidence-manifest.json"))
