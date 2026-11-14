"""Declared metadata capture populations, bounds and immutable HTTP results."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

_BASE = "https://api.neotomadb.org/v2.0/data"
_SCHEMA = "neotoma-metadata-http-capture.v1"
_HEADERS = (
    ("Host", "api.neotomadb.org"),
    ("Accept", "application/json"),
    ("Accept-Encoding", "identity"),
    ("User-Agent", "bijux-pollenomics"),
    ("Connection", "close"),
)


@dataclass(frozen=True)
class NeotomaMetadataPlan:
    """Declare pollen inventory queries and an independent known-site census."""

    inventory_bbox: tuple[float, float, float, float] | None = None
    inventory_limits: tuple[int, ...] = ()
    site_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class NeotomaMetadataLimits:
    """Finite transport and pagination bounds, also enforced during replay."""

    max_requests: int = 256
    max_pages_per_inventory: int = 8
    max_response_bytes: int = 2 * 1024 * 1024
    max_total_bytes: int = 16 * 1024 * 1024
    timeout_seconds: float = 45.0


DEFAULT_METADATA_LIMITS = NeotomaMetadataLimits()


@dataclass(frozen=True)
class NeotomaMetadataResponse:
    """One complete or bounded partial HTTP entity before any JSON parsing."""

    final_url: str
    http_status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes
    body_complete: bool = True


@dataclass(frozen=True)
class NeotomaMetadataCapture:
    """Verified source bodies and metadata populations from a completed capture."""

    manifest_sha256: str
    inventory_rows: dict[int, list[dict[str, object]]]
    site_responses: dict[int, bytes]
    request_count: int
    response_bytes: int


@dataclass(frozen=True)
class _Request:
    name: str
    role: str
    endpoint: str
    parameters: dict[str, str]
    site_id: int | None = None

    @property
    def url(self) -> str:
        return (
            _BASE
            + self.endpoint
            + ("?" + urlencode(self.parameters) if self.parameters else "")
        )
