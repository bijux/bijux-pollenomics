"""Public static-atlas identities and safe release naming."""

import re
from dataclasses import dataclass
from pathlib import Path

_SAFE_RELEASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


@dataclass(frozen=True)
class StaticAtlasAssets:
    """Materialized static-atlas manifest and immutable asset paths."""

    manifest_path: Path
    manifest: dict[str, object]
    asset_paths: tuple[Path, ...]

    @property
    def script_tags(self) -> str:
        """Return no eager tags; the runtime applies protocol-aware integrity first."""
        return ""


def validate_atlas_release_id(version: str) -> None:
    """Reject release identifiers that are unsafe in paths or script contexts."""
    if not isinstance(version, str) or not _SAFE_RELEASE_ID.fullmatch(version):
        raise ValueError("atlas version must be a safe release identifier")


__all__ = ["StaticAtlasAssets", "validate_atlas_release_id"]
