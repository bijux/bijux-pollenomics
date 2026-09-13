"""Private persisted AADR evidence members from exact governed raw release bytes."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.contracts import (
    SCHEMA_VERSION,
    boundary,
    canonical_bytes,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.projection import (
    iter_member_documents,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.validation import (
    validate_member_ownership,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    reconcile_aadr_panels,
)
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from ..inputs import load_aadr_release_inputs
from .inspection import AadrMemberInspection, inspect_aadr_member_bundle
from .publication import implementation_identity, new_staging, write_tables


def materialize_aadr_evidence_members(
    *, data_root: Path, version: str, output_root: Path
) -> AadrMemberInspection:
    """Publish a new private bundle only after exact raw replay, with no admission."""
    output, staging = new_staging(output_root, data_root=data_root)
    implementation = implementation_identity()
    inputs = load_aadr_release_inputs(data_root, version)
    reconciliation = reconcile_aadr_panels(inputs.source_tables)
    counts = validate_member_ownership(
        iter_member_documents(
            reconciliation, release_manifest_sha256=inputs.manifest_sha256
        ),
        release_manifest_sha256=inputs.manifest_sha256,
    )
    files = write_tables(
        staging,
        iter_member_documents(
            reconciliation, release_manifest_sha256=inputs.manifest_sha256
        ),
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "release_manifest": {
            "source_release": inputs.source_release,
            "logical_path": inputs.logical_manifest_path,
            "sha256": inputs.manifest_sha256,
            "byte_count": len(inputs.manifest_bytes),
        },
        "admission_boundary": boundary(),
        "files": files,
        "denominators": counts,
        "implementation": implementation,
    }
    content = canonical_bytes(manifest)
    with (staging / "manifest.json").open("xb") as stream:
        stream.write(content)
    inputs.verify_unchanged()
    if implementation_identity() != implementation:
        raise ValueError("AADR producer changed during materialization")
    del reconciliation, inputs
    digest = sha256(content).hexdigest()
    inspect_aadr_member_bundle(staging, expected_sha256=digest, data_root=data_root)
    publish_new_output_tree(final_output_root=output, staging_output_root=staging)
    return AadrMemberInspection._verified(output, content)
