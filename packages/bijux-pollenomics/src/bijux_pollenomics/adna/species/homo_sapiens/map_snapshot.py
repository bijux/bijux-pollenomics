"""Hold one AADR annotation capture and runtime manifest for country queries."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics.adna.domain.models import AdnaSampleRecord
from bijux_pollenomics.adna.workflow.runtime import (
    AdnaSampleQuery,
    AdnaSpeciesRuntimeManifest,
)

from .loading import load_homo_sapiens_samples, single_human_bundle
from .release import (
    capture_release_inputs,
    discover_homo_sapiens_anno_files,
    release_cache_key,
)


def _manifest_sha256(manifest: AdnaSpeciesRuntimeManifest) -> str:
    payload = json.dumps(
        manifest.as_dict(),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class AadrMapSnapshot:
    """Held annotation bytes and runtime manifest, without source-admission claims."""

    manifest: AdnaSpeciesRuntimeManifest
    runtime_manifest_sha256: str
    captured: tuple[tuple[str, bytes], ...]
    expected_sha256: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if (
            self.manifest.species.latin_name != "Homo sapiens"
            or _manifest_sha256(self.manifest) != self.runtime_manifest_sha256
        ):
            raise ValueError("AADR runtime manifest differs")
        bundle = single_human_bundle(self.manifest)
        root = Path(bundle.tracked_root)
        if (
            type(self.captured) is not tuple
            or not self.captured
            or type(self.expected_sha256) is not tuple
            or any(type(pair) is not tuple or len(pair) != 2 for pair in self.captured)
            or any(
                type(pair) is not tuple or len(pair) != 2
                for pair in self.expected_sha256
            )
        ):
            raise ValueError("AADR annotation capture must use immutable pairs")
        observed = []
        for path, body in self.captured:
            if not isinstance(path, str) or type(body) is not bytes:
                raise ValueError("AADR captured annotation differs")
            try:
                relative = Path(path).relative_to(root).as_posix()
            except ValueError as exc:
                raise ValueError("AADR annotation path differs") from exc
            parts = Path(relative).parts
            if (
                len(parts) != 2
                or any(part in {".", ".."} for part in parts)
                or Path(relative).suffix != ".anno"
            ):
                raise ValueError("AADR annotation path differs")
            observed.append((relative, hashlib.sha256(body).hexdigest()))
        if tuple(path for path, _ in self.captured) != tuple(
            str(path) for path in discover_homo_sapiens_anno_files(root)
        ):
            raise ValueError("AADR annotation inventory or order differs")
        if tuple(observed) != self.expected_sha256 or len(
            {x[0] for x in observed}
        ) != len(observed):
            raise ValueError("AADR annotation identities differ")

    def identity(self) -> dict[str, Any]:
        """Report held file and runtime-manifest identities without byte provenance for its source file."""
        if _manifest_sha256(self.manifest) != self.runtime_manifest_sha256:
            raise ValueError("AADR runtime manifest changed")
        return {
            "schema_version": "aadr-map-annotation-inputs.v1",
            "posture": "captured_annotation_bytes_and_runtime_manifest_not_release_manifest_bytes_or_admission",
            "runtime_manifest_sha256": self.runtime_manifest_sha256,
            "annotations": [{"path": p, "sha256": h} for p, h in self.expected_sha256],
        }

    def load_country(self, country: str) -> tuple[list[AdnaSampleRecord], Counter[str]]:
        """Query a held release using the ordinary country deduplication owner."""
        if not isinstance(country, str) or not country.strip():
            raise ValueError("AADR map country must be nonblank")
        from . import (
            _CAPTURED_RELEASE,
            _cached_country_records,
            _cached_release_samples,
            sample_matches_query,
        )

        if _manifest_sha256(self.manifest) != self.runtime_manifest_sha256:
            raise ValueError("AADR runtime manifest changed")
        key = release_cache_key(single_human_bundle(self.manifest), self.captured)
        token = _CAPTURED_RELEASE.set(self.captured)
        try:
            return load_homo_sapiens_samples(
                manifest=self.manifest,
                query=AdnaSampleQuery(political_entity=country),
                cache_key=key,
                release_loader=_cached_release_samples,
                country_loader=_cached_country_records,
                sample_matcher=sample_matches_query,
            )
        finally:
            _CAPTURED_RELEASE.reset(token)


def capture_aadr_map_snapshot(
    manifest: AdnaSpeciesRuntimeManifest, expected_sha256: Mapping[str, str]
) -> AadrMapSnapshot:
    """Sequentially capture all caller-pinned annotations and the runtime manifest."""
    if manifest.species.latin_name != "Homo sapiens":
        raise ValueError("AADR capture requires Homo sapiens")
    if not expected_sha256 or any(
        not isinstance(k, str)
        or not isinstance(v, str)
        or re.fullmatch(r"[0-9a-f]{64}", v) is None
        for k, v in expected_sha256.items()
    ):
        raise ValueError("AADR annotation pins differ")
    bundle = single_human_bundle(manifest)
    root = Path(bundle.tracked_root)
    captured = capture_release_inputs(bundle)
    observed = tuple(
        (Path(path).relative_to(root).as_posix(), hashlib.sha256(body).hexdigest())
        for path, body in captured
    )
    if dict(observed) != dict(expected_sha256) or len(observed) != len(expected_sha256):
        raise ValueError("AADR annotation inventory or digest differs")
    return AadrMapSnapshot(manifest, _manifest_sha256(manifest), captured, observed)


def validate_aadr_map_inputs(
    snapshot: AadrMapSnapshot,
    version: str,
    countries: tuple[str, ...],
    samples: tuple[AdnaSampleRecord, ...],
    counts: dict[str, int],
) -> None:
    """Bind the published samples and counts to the exact held country queries."""
    if type(snapshot) is not AadrMapSnapshot:
        raise ValueError("AADR snapshot must be an exact captured snapshot")
    if single_human_bundle(snapshot.manifest).source_release != version:
        raise ValueError("AADR snapshot release differs")
    country_rows = {country: snapshot.load_country(country)[0] for country in countries}
    if {
        country: len(rows) for country, rows in country_rows.items()
    } != counts or tuple(
        row for country in countries for row in country_rows[country]
    ) != samples:
        raise ValueError("AADR map samples differ from captured country queries")
