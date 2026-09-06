from __future__ import annotations

from pathlib import Path
import stat


def _positive_int(value: object) -> int | None:
    parsed = _non_negative_int(value)
    return parsed if parsed is not None and parsed > 0 else None


def _non_negative_int(value: object) -> int | None:
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
        else None
    )


def _safe_relative_path(value: str) -> bool:
    path = Path(value)
    return (
        bool(path.parts)
        and not path.is_absolute()
        and ".." not in path.parts
        and "\\" not in value
    )


def _sha256_text(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _regular_non_symlink(path: Path) -> bool:
    try:
        path_stat = path.lstat()
    except OSError:
        return False
    return stat.S_ISREG(path_stat.st_mode) and not path.is_symlink()


def _materialization_status(
    *,
    support: str,
    evidence_paths: tuple[str, ...],
    present_evidence_paths: tuple[str, ...],
) -> str:
    if support == "unsupported":
        return "not_applicable"
    if not present_evidence_paths:
        return "missing"
    if any(path not in evidence_paths for path in present_evidence_paths):
        raise ValueError("present capability evidence exceeds the governed inventory")
    if len(present_evidence_paths) == len(evidence_paths):
        return "complete"
    return "partial"
