"""Source-snapshot identity derivation."""

from __future__ import annotations

from collections.abc import Mapping

from ..constants import INPUT_PATHS
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
) -> dict[str, str]:
    source_hashes = _object(collection.get("source_hashes"), "source hashes")
    result = {
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
    return result
