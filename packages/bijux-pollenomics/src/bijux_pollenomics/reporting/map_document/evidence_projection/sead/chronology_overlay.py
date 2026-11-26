"""Apply owner-produced historical chronology corrections to copied Atlas claims."""

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .models import ClaimIndex


@dataclass(frozen=True)
class HistoricalChronologyRequest:
    """Select a historical boundary authority and pinned corrected lineage."""

    country_authority_root: Path
    lineage_sha256: str

    def __post_init__(self) -> None:
        if (
            not self.country_authority_root.is_absolute()
            or len(self.lineage_sha256) != 64
            or any(c not in "0123456789abcdef" for c in self.lineage_sha256)
        ):
            raise ValueError("SEAD historical chronology request differs")


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    except (ValueError, TypeError) as error:
        raise ValueError("SEAD derived chronology JSON differs") from error


def apply_overlay(claims: ClaimIndex, overlay: Mapping[str, object]) -> ClaimIndex:
    """Validate an owner result and copy only its permitted derived fields."""
    original: dict[str, Mapping[str, object]] = {}
    for row in claims.rows:
        claim_id = row.get("chronology_claim_id")
        if not isinstance(claim_id, str) or not claim_id or claim_id in original:
            raise ValueError("SEAD derived chronology claim identity differs")
        original[claim_id] = row
    if (
        type(overlay.get("claim_count")) is not int
        or overlay.get("claim_count") != len(original)
        or overlay.get("claim_id_set_sha256")
        != hashlib.sha256(_canonical(sorted(original))).hexdigest()
    ):
        raise ValueError("SEAD derived chronology claim set differs")
    raw = overlay.get("changes")
    if (
        not isinstance(raw, list)
        or type(overlay.get("changed_claim_count")) is not int
        or overlay.get("changed_claim_count") != len(raw)
    ):
        raise ValueError("SEAD derived chronology change count differs")
    changes: dict[str, Mapping[str, object]] = {}
    for change in raw:
        if not isinstance(change, dict) or set(change) != {
            "chronology_claim_id",
            "time_start_bp",
            "time_end_bp",
            "original_interval_orientation",
        }:
            raise ValueError("SEAD derived chronology fields differ")
        claim_id = change.get("chronology_claim_id")
        if (
            not isinstance(claim_id, str)
            or claim_id not in original
            or claim_id in changes
            or not isinstance(change.get("original_interval_orientation"), str)
        ):
            raise ValueError("SEAD derived chronology change identity differs")
        _canonical(change)
        changes[claim_id] = change
    result: list[Mapping[str, object]] = []
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in claims.rows:
        claim_id = row["chronology_claim_id"]
        if not isinstance(claim_id, str):
            raise ValueError("SEAD derived chronology claim identity differs")
        change = changes.get(claim_id)
        revised = dict(row)
        if change is not None:
            age = row.get("source_age_value")
            if (
                not isinstance(age, dict)
                or "time_start_bp" not in age
                or "time_end_bp" not in age
            ):
                raise ValueError("SEAD derived chronology source age differs")
            revised["source_age_value"] = {
                **age,
                "time_start_bp": change["time_start_bp"],
                "time_end_bp": change["time_end_bp"],
            }
            revised["original_interval_orientation"] = change[
                "original_interval_orientation"
            ]
        site = revised.get("source_site_id")
        if not isinstance(site, str) or not site:
            raise ValueError("SEAD derived chronology site differs")
        grouped[site].append(revised)
        result.append(revised)
    return ClaimIndex(
        rows=result, by_site=grouped, country_counts=claims.country_counts.copy()
    )
