"""Transport the exact admitted regional-cutoff scalar account without numerical replay."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject
from .scalar_reference import validated_scalar_reference_account

OWNER = "pollen-reconstruction/nordic-static-basin-scenarios/regional-cutoff-scalar-reference-account"
PRODUCT = "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/regional-cutoff-scalar-reference.json"
SHA256 = "ba9b1718770f630b8ac9136d45c0a4de66fccc0be3644737d3159f845f1a2167"
BYTES = 52268


def validated_regional_cutoff_reference(
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
        schema="nordic-regional-cutoff-scalar-reference-public-account.v1",
        label="Nordic cutoff reference",
        scope="Exact independently admitted 46-factor regional-cutoff scalar account only. Original baseline source, saved cutoff execution, independent reference execution and later canonical source adoption remain distinct; publication HEAD is not a rerun. The original Nordic source captures, panels, age/count support and owners remain unchanged. Transport confers no new R or moment execution, measured or source-qualified extent range, asymptotic convergence, source rights, historical or field validity, human review or whole scientific acceptance.",
    )
