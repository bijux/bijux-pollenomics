from __future__ import annotations

from collections.abc import Callable

from .models import NeotomaProductionConfig


def build_id(
    *,
    source_snapshot_id: str,
    boundary_authority_id: str,
    config: NeotomaProductionConfig,
    canonical_digest: Callable[[object], str],
) -> str:
    aliases = sorted([list(item) for item in config.raw_country_aliases])
    identity = {
        "schema": "neotoma-relational-build-identity.v1",
        "source_snapshot_id": source_snapshot_id,
        "boundary_authority_id": boundary_authority_id,
        "producer": {"id": config.producer_id, "version": config.producer_version},
        "config": {
            "schema": config.config_schema,
            "rows_per_part": config.rows_per_part,
            "proximity_tolerance": config.proximity_tolerance,
            "raw_country_aliases": aliases,
        },
    }
    return f"sha256:{canonical_digest(identity)}"
