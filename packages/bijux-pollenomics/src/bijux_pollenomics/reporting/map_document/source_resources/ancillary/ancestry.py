"""Project only explicitly selected recorded targets, never native body authority."""

from copy import deepcopy
from hashlib import sha256
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
    read_neotoma_taxon_chain_target,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
    encoded_json,
)

from ..archive_reference import _pinned
from .models import AtlasTaxonAncestryArchiveInput


def load_taxon_ancestry_metadata(
    reference: AtlasTaxonAncestryArchiveInput,
) -> dict[str, Any]:
    """Authenticate selected metadata through the maintained SDK reader per target."""
    header, _ = _pinned(
        reference.directory, "manifest.json", reference.expected_manifest_sha256
    )
    rows = []
    for kind, identity in reference.targets:
        selected = read_neotoma_taxon_chain_target(
            reference.directory,
            expected_manifest_sha256=reference.expected_manifest_sha256,
            kind=kind,
            native_id=identity,
            chain_sources=reference.chain_sources,
        )
        rows.append(
            {
                "target_key": f"{kind}-{identity}",
                "kind": kind,
                "native_id": identity,
                **selected,
            }
        )
    index = {"targets": rows}
    raw = encoded_json(index)
    return {
        "archive_kind": "taxon_ancestry",
        "archive_manifest_sha256": reference.expected_manifest_sha256,
        "manifest": {
            key: deepcopy(header[key])
            for key in (
                "schema_version",
                "baseline",
                "parent_chain_manifest_sha256",
                "new_capture_manifest_sha256s",
                "current_context_manifest_sha256",
                "current_native_archive_manifest_sha256",
                "scientific_admission",
            )
        },
        "index": index,
        "selected_index": {"bytes": len(raw), "sha256": sha256(raw).hexdigest()},
        "integrity_scope": "SELECTED_RECORDED_TARGETS_ONLY",
        "current_roles_revalidated": False,
        "native_source_fields_revalidated": False,
        "native_entity_bodies_opened": 0,
        "GET_authorized": False,
        "entity_body_hashes_verified": False,
        "native_profiles_verified": False,
        "source_assessments_replayed": False,
        "scientific_admission": "not_asserted",
        "selected_source_authority": "not_provided_by_metadata_projection",
        "source_epoch_semantics": "literal_capture_epochs_not_a_synchronized_snapshot",
        "native_dataset_version": "not_applicable_supporting_source_surface",
    }
