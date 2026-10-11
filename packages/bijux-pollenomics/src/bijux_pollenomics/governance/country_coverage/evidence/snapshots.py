"""Source-snapshot identity derivation."""

from __future__ import annotations

from collections.abc import Mapping

from ..constants import (
    EMPD2_SOURCE_ARTIFACT_SHA256,
    INPUT_PATHS,
    NFI_SOURCE_ARTIFACT_SHA256,
)
from ..decoding import (
    _object,
    _require_sha256_id,
    _required_text,
    _sha256,
    _sha256_id_from_raw,
)


def _source_snapshot_ids(
    collection: Mapping[str, object],
    documents: Mapping[str, Mapping[str, object]],
    input_bytes: Mapping[str, bytes],
) -> dict[str, str | None]:
    source_hashes = _object(collection.get("source_hashes"), "source hashes")
    result: dict[str, str | None] = {
        source: _sha256_id_from_raw(
            _required_text(_object(source_hashes[source], source), "snapshot_sha256"),
            f"{source} source snapshot",
        )
        for source in (
            "landclim",
            "neotoma",
            "sead",
            "raa",
            "boundaries",
            "svar",
            "aadr",
        )
    }
    result["neotoma"] = _require_sha256_id(
        _required_text(
            documents["data/neotoma/relational/reconciliation.json"],
            "source_snapshot_id",
        ),
        "Neotoma source snapshot",
    )
    result["sead"] = _require_sha256_id(
        _required_text(documents[INPUT_PATHS[5]], "acquisition_bundle_sha256"),
        "SEAD acquisition bundle",
    )
    result["animal_adna"] = f"sha256:{_sha256(input_bytes[INPUT_PATHS[14]])}"
    # No country projection exists; external archive custody remains separate.
    result["hyde"] = None
    result["empd2"] = f"sha256:{EMPD2_SOURCE_ARTIFACT_SHA256}"
    result["nfi"] = f"sha256:{NFI_SOURCE_ARTIFACT_SHA256}"
    return result
