"""Exact-inventory intake for the pinned SpatioCompoMixed export set."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from ..quarantine import IntakeRefusal
from .authority import (
    FILE_AUTHORITIES,
    KNOWN_REFUSED_RELATIVE_PATH,
    SOURCE_DIRECTORY,
    SOURCE_PERIODS,
)
from .models import (
    ModeledHumanLandUseSlice,
    SliceRefusal,
    SpatioCompoHumanLandUseCollection,
)
from .normalization import normalize_export_file


def normalize_spatiocompo_human_land_use(
    source_root: Path,
) -> SpatioCompoHumanLandUseCollection:
    """Normalize nine complete slices and retain the known corrupt slice refusal."""
    source_root = Path(source_root)
    data_root = source_root / SOURCE_DIRECTORY
    expected_paths = {authority.relative_path for authority in FILE_AUTHORITIES}
    actual_paths = (
        {path.relative_to(source_root).as_posix() for path in data_root.iterdir()}
        if data_root.is_dir() and not data_root.is_symlink()
        else set()
    )
    if actual_paths != expected_paths:
        raise IntakeRefusal(
            "spatiocompo_export_inventory_mismatch",
            f"missing={sorted(expected_paths - actual_paths)}; "
            f"unlisted={sorted(actual_paths - expected_paths)}",
        )
    slices: list[ModeledHumanLandUseSlice] = []
    refusals: list[SliceRefusal] = []
    expected_grid: frozenset[tuple[Decimal, Decimal]] | None = None
    for authority in FILE_AUTHORITIES:
        try:
            source_slice = normalize_export_file(
                source_root / authority.relative_path,
                authority,
                expected_grid=expected_grid,
            )
        except IntakeRefusal as exc:
            if (
                authority.relative_path != KNOWN_REFUSED_RELATIVE_PATH
                or exc.reason_code != "upstream_spatiocompo_slice_known_corrupt"
            ):
                raise
            refusals.append(
                SliceRefusal(
                    relative_path=authority.relative_path,
                    period_key=authority.period.key,
                    model_variant=authority.variant.key,
                    reason_code=exc.reason_code,
                    detail=str(exc),
                )
            )
            continue
        if expected_grid is None:
            expected_grid = frozenset(
                (cell.longitude_claim, cell.latitude_claim)
                for cell in source_slice.cells
            )
        slices.append(source_slice)
    refused_paths = {refusal.relative_path for refusal in refusals}
    if refused_paths != {KNOWN_REFUSED_RELATIVE_PATH}:
        raise IntakeRefusal(
            "unexpected_spatiocompo_refusal_set", repr(sorted(refused_paths))
        )
    return SpatioCompoHumanLandUseCollection(
        periods_oldest_to_present=tuple(period.label for period in SOURCE_PERIODS),
        slices=tuple(slices),
        refusals=tuple(refusals),
    )


__all__ = ["normalize_spatiocompo_human_land_use"]
