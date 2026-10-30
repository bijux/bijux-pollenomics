"""Transport the exact admitted Nordic scalar reference without numerical replay."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject
from .scalar_reference import validated_scalar_reference_account

OWNER = (
    "pollen-reconstruction/nordic-static-basin-scenarios/wind-scalar-reference-account"
)
PRODUCT = "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/wind-scalar-reference.json"
SHA256 = "9d4321222932cec85c0e10dc03d9234d5e5fcbe0a2e8fddea7b4f0c1ad03ac24"
BYTES = 32502


def validated_nordic_wind_reference(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Require one separate exact owner and reviewed product; preserve old captures."""
    return validated_scalar_reference_account(
        repository,
        tracked_by_path,
        owners,
        owner_id=OWNER,
        product=PRODUCT,
        sha256=SHA256,
        size=BYTES,
        schema="nordic-wind-scalar-reference-public-account.v1",
        label="Nordic wind reference",
        scope="Exact independently admitted46scalar numerical-reference account only. Original33d4 baseline/1413 savedwind/cc29 reference/54feb canonicaladoption identities and executedartifact overlays remain distinct; publication HEAD is not a rerun. Original22 Nordic captures and their owner remain unchanged. Transport confers no new moment/R execution, source rights, empirical wind, historical, field, human or whole scientific acceptance.",
    )
