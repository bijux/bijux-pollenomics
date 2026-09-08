"""Source-value parsing for Scandinavian aurochs reconciliation."""

from __future__ import annotations

from pathlib import PurePosixPath
import re
from typing import Final

_BP_INTERVAL_RE: Final = re.compile(r"(?P<older>\d+)-(?P<younger>\d+)")
_MITOCHONDRIAL_DATE_RE: Final = re.compile(
    r"(?P<mean>\d+(?:\.\d+)?) \((?P<younger>\d+)-(?P<older>\d+)\)"
)


def _parse_calibrated_bp_interval(value: str, label: str) -> tuple[int, int]:
    match = _BP_INTERVAL_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"PRJEB75467 {label} calibrated BP interval is invalid")
    younger = int(match.group("younger"))
    older = int(match.group("older"))
    if younger > older:
        raise ValueError(f"PRJEB75467 {label} calibrated BP interval direction drift")
    return younger, older


def _parse_mitochondrial_date(value: str, label: str) -> tuple[int, int, float]:
    match = _MITOCHONDRIAL_DATE_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"PRJEB75467 {label} mitochondrial date is invalid")
    younger = int(match.group("younger"))
    older = int(match.group("older"))
    mean = float(match.group("mean"))
    if younger > mean or mean > older:
        raise ValueError(f"PRJEB75467 {label} mitochondrial date ordering drift")
    return younger, older, mean


def _submitted_basenames(value: str) -> tuple[str, ...]:
    return tuple(
        PurePosixPath(part.strip()).name for part in value.split(";") if part.strip()
    )


def _basename_has_label(basename: str, label: str) -> bool:
    if not basename.startswith(label):
        return False
    suffix = basename[len(label) :]
    return not suffix or suffix[0] in "_-." or suffix == "\n"
