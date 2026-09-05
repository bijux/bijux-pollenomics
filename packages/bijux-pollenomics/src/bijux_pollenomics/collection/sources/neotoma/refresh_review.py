"""Deterministic baseline and refresh-drift review for Neotoma evidence."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path, PurePosixPath

from .lineage import LINEAGE_SCHEMA_VERSION
from bijux_pollenomics.evidence.sources.neotoma import (
    validate_neotoma_relational_materialization,
)
from .production import load_validated_neotoma_raw_archive

__all__ = [
    "build_neotoma_refresh_baseline",
    "build_neotoma_refresh_review",
    "render_neotoma_refresh_review_markdown",
    "write_neotoma_refresh_baseline",
    "write_neotoma_refresh_review",
]

BASELINE_SCHEMA_VERSION = "neotoma-refresh-baseline.v1"
REFRESH_REVIEW_SCHEMA_VERSION = "neotoma-refresh-review.v1"


def build_neotoma_refresh_baseline(
    *,
    raw_archive_root: Path,
    relational_root: Path,
    compact_geojson_path: Path,
    lineage_path: Path,
    raw_public_root: str = "data/neotoma/raw/neotoma_pollen_dataset_downloads",
    relational_public_root: str = "data/neotoma/relational",
    compact_public_path: str = "data/neotoma/normalized/nordic_pollen_sites.geojson",
    lineage_public_path: str = "data/neotoma/review/compact_relational_lineage.json",
) -> dict[str, object]:
    """Capture one validated candidate identity without approving a later refresh."""
    for role, path in (
        ("raw_archive", Path(raw_archive_root)),
        ("relational_detail", Path(relational_root)),
        ("compact_site_layer", Path(compact_geojson_path)),
        ("compact_lineage", Path(lineage_path)),
    ):
        if not path.exists():
            raise FileNotFoundError(f"Missing Neotoma baseline input {role}: {path}")

    raw_public_root = _safe_public_path(raw_public_root)
    relational_public_root = _safe_public_path(relational_public_root)
    compact_public_path = _safe_public_path(compact_public_path)
    lineage_public_path = _safe_public_path(lineage_public_path)
    raw_rows, source_snapshot_id = load_validated_neotoma_raw_archive(
        Path(raw_archive_root)
    )
    raw_manifest_path = Path(raw_archive_root) / "manifest.json"
    raw_manifest_bytes = _read_regular_file(raw_manifest_path)
    raw_manifest = _json_object(raw_manifest_bytes, "Neotoma raw manifest")
    parts = raw_manifest.get("parts")
    if not isinstance(parts, list):
        raise ValueError("Neotoma raw manifest parts must be a list")
    raw_part_digests: dict[str, str] = {}
    for part_value in parts:
        part = _mapping(part_value, "Neotoma raw part")
        filename = _safe_filename(
            _required_text(part.get("filename"), "Neotoma raw part filename")
        )
        raw_part_digests[filename] = hashlib.sha256(
            _read_regular_file(Path(raw_archive_root) / filename)
        ).hexdigest()

    relational_manifest = validate_neotoma_relational_materialization(
        Path(relational_root)
    )
    if relational_manifest.get("source_snapshot_id") != source_snapshot_id:
        raise ValueError("Raw and relational Neotoma source snapshot identities differ")
    compact_bytes = _read_regular_file(Path(compact_geojson_path))
    compact_payload = _json_object(compact_bytes, "Neotoma compact site layer")
    features = compact_payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Neotoma compact site layer features must be a list")
    lineage_bytes = _read_regular_file(Path(lineage_path))
    lineage = _json_object(lineage_bytes, "Neotoma compact lineage")
    if lineage.get("schema_version") != LINEAGE_SCHEMA_VERSION:
        raise ValueError("Unexpected Neotoma compact lineage schema")
    if lineage.get("status") != "complete":
        raise ValueError("Cannot baseline a refused Neotoma compact lineage")
    lineage_inputs = _mapping(lineage.get("input_artifacts"), "lineage inputs")
    lineage_compact = _mapping(
        lineage_inputs.get("compact_site_layer"), "lineage compact input"
    )
    lineage_relational = _mapping(
        lineage_inputs.get("relational_detail"), "lineage relational input"
    )
    if lineage_compact.get("sha256") != hashlib.sha256(compact_bytes).hexdigest():
        raise ValueError("Neotoma lineage does not bind the candidate compact layer")
    if lineage_relational.get("materialization_sha256") != relational_manifest.get(
        "materialization_sha256"
    ):
        raise ValueError("Neotoma lineage does not bind the candidate materialization")
    for field in ("source_snapshot_id", "build_id"):
        if lineage_relational.get(field) != relational_manifest.get(field):
            raise ValueError(f"Neotoma lineage does not bind candidate {field}")

    surfaces = _mapping(relational_manifest.get("surfaces"), "relational surfaces")
    counts = {
        "raw_download_rows": len(raw_rows),
        "raw_archive_parts": _non_negative_integer(
            raw_manifest.get("part_count"), "raw part_count"
        ),
        "raw_requested_datasets": _non_negative_integer(
            raw_manifest.get("requested_dataset_count"), "requested_dataset_count"
        ),
        "raw_downloaded_datasets": _non_negative_integer(
            raw_manifest.get("downloaded_dataset_count"),
            "downloaded_dataset_count",
        ),
        "compact_records": len(features),
        **{
            f"relational_{surface_name}": _non_negative_integer(
                _mapping(surface, surface_name).get("row_count"),
                f"{surface_name} row_count",
            )
            for surface_name, surface in sorted(surfaces.items())
        },
    }
    surface_schemas = {
        surface_name: _required_text(
            _mapping(surface, surface_name).get("schema_version"),
            f"{surface_name} schema_version",
        )
        for surface_name, surface in sorted(surfaces.items())
    }
    baseline: dict[str, object] = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "source_family": "neotoma",
        "input_artifacts": {
            "raw_archive": {
                "path": raw_public_root,
                "manifest_sha256": hashlib.sha256(raw_manifest_bytes).hexdigest(),
                "part_sha256": dict(sorted(raw_part_digests.items())),
            },
            "relational_detail": {
                "path": relational_public_root,
                "materialization_sha256": relational_manifest.get(
                    "materialization_sha256"
                ),
            },
            "compact_site_layer": {
                "path": compact_public_path,
                "sha256": hashlib.sha256(compact_bytes).hexdigest(),
            },
            "compact_lineage": {
                "path": lineage_public_path,
                "sha256": hashlib.sha256(lineage_bytes).hexdigest(),
            },
        },
        "identity": {
            "source_snapshot_id": source_snapshot_id,
            "raw_generated_on": raw_manifest.get("generated_on"),
            "build_id": relational_manifest.get("build_id"),
            "relational_materialization_sha256": relational_manifest.get(
                "materialization_sha256"
            ),
            "compact_sha256": hashlib.sha256(compact_bytes).hexdigest(),
            "lineage_sha256": hashlib.sha256(lineage_bytes).hexdigest(),
        },
        "schemas": {
            "relational_snapshot": relational_manifest.get(
                "relational_snapshot_schema_version"
            ),
            "relational_manifest": relational_manifest.get("schema_version"),
            "compact_lineage": lineage.get("schema_version"),
            "upstream_archive_contract": {
                "source": raw_manifest.get("source"),
                "endpoint_template": raw_manifest.get("endpoint_template"),
                "datasettype": raw_manifest.get("datasettype"),
                "part_count": raw_manifest.get("part_count"),
            },
            "surfaces": surface_schemas,
        },
        "counts": counts,
    }
    baseline["baseline_id"] = (
        "sha256:" + hashlib.sha256(_canonical_json(baseline)).hexdigest()
    )
    return baseline


def build_neotoma_refresh_review(
    prior: Mapping[str, object] | None,
    candidate: Mapping[str, object] | None,
    *,
    explanations: Mapping[str, str] | None = None,
    missing_reasons: list[str] | None = None,
) -> dict[str, object]:
    """Compare exact prior and candidate baselines or emit a refusal."""
    reasons = list(missing_reasons or [])
    if prior is None:
        reasons.append("missing_prior_baseline")
    if candidate is None:
        reasons.append("missing_candidate_baseline")
    if reasons:
        return {
            "schema_version": REFRESH_REVIEW_SCHEMA_VERSION,
            "source_family": "neotoma",
            "status": "refused",
            "refusal_reasons": sorted(set(reasons)),
            "prior_baseline_id": _optional_baseline_id(prior),
            "candidate_baseline_id": _optional_baseline_id(candidate),
            "change_count": 0,
            "unexplained_change_count": 0,
            "fixed_point": False,
            "baseline_update_permitted": False,
            "changes": [],
        }
    if prior is None or candidate is None:
        raise AssertionError("Neotoma baseline refusal did not terminate")
    _validate_baseline(prior, "prior")
    _validate_baseline(candidate, "candidate")
    normalized_explanations = {
        key: value.strip()
        for key, value in (explanations or {}).items()
        if key.strip() and value.strip()
    }
    changes: list[dict[str, object]] = []
    for section in ("identity", "schemas", "counts", "input_artifacts"):
        _collect_changes(
            changes,
            section=section,
            prior=_mapping(prior.get(section), f"prior {section}"),
            candidate=_mapping(candidate.get(section), f"candidate {section}"),
            explanations=normalized_explanations,
        )
    unexplained = sum(change["explanation"] is None for change in changes)
    fixed_point = not changes
    return {
        "schema_version": REFRESH_REVIEW_SCHEMA_VERSION,
        "source_family": "neotoma",
        "status": "fixed_point" if fixed_point else "review_required",
        "refusal_reasons": [],
        "prior_baseline_id": prior["baseline_id"],
        "candidate_baseline_id": candidate["baseline_id"],
        "change_count": len(changes),
        "unexplained_change_count": unexplained,
        "fixed_point": fixed_point,
        "zero_diff_proof": {
            "identity_equal": prior["identity"] == candidate["identity"],
            "schemas_equal": prior["schemas"] == candidate["schemas"],
            "counts_equal": prior["counts"] == candidate["counts"],
            "input_artifacts_equal": (
                prior["input_artifacts"] == candidate["input_artifacts"]
            ),
        },
        "baseline_update_permitted": fixed_point,
        "review_posture": (
            "no_refresh_drift"
            if fixed_point
            else "retain_prior_baseline_until_changes_are_explained_and_reviewed"
        ),
        "changes": changes,
    }


def write_neotoma_refresh_baseline(
    output_path: Path,
    *,
    raw_archive_root: Path,
    relational_root: Path,
    compact_geojson_path: Path,
    lineage_path: Path,
) -> Path:
    """Initialize an immutable refresh baseline; identical repeats are idempotent."""
    baseline = build_neotoma_refresh_baseline(
        raw_archive_root=raw_archive_root,
        relational_root=relational_root,
        compact_geojson_path=compact_geojson_path,
        lineage_path=lineage_path,
    )
    path = Path(output_path)
    content = _canonical_json(baseline)
    if path.exists():
        if _read_regular_file(path) == content:
            return path
        raise FileExistsError(
            "Neotoma refresh baseline already exists with different content; "
            "review drift before replacing it"
        )
    _write_atomic(path, content)
    return path


def write_neotoma_refresh_review(
    output_path: Path,
    *,
    baseline_path: Path,
    raw_archive_root: Path,
    relational_root: Path,
    compact_geojson_path: Path,
    lineage_path: Path,
    explanations: Mapping[str, str] | None = None,
    markdown_path: Path | None = None,
) -> Path:
    """Write the current baseline-to-candidate drift review atomically."""
    missing: list[str] = []
    prior: dict[str, object] | None = None
    candidate: dict[str, object] | None = None
    if Path(baseline_path).exists():
        prior = _json_object(
            _read_regular_file(Path(baseline_path)), "Neotoma prior baseline"
        )
    else:
        missing.append("missing_prior_baseline")
    candidate_inputs = (
        ("raw_archive", Path(raw_archive_root)),
        ("relational_detail", Path(relational_root)),
        ("compact_site_layer", Path(compact_geojson_path)),
        ("compact_lineage", Path(lineage_path)),
    )
    missing.extend(
        f"missing_candidate_{role}"
        for role, path in candidate_inputs
        if not path.exists()
    )
    if not any(reason.startswith("missing_candidate_") for reason in missing):
        candidate = build_neotoma_refresh_baseline(
            raw_archive_root=raw_archive_root,
            relational_root=relational_root,
            compact_geojson_path=compact_geojson_path,
            lineage_path=lineage_path,
        )
    review = build_neotoma_refresh_review(
        prior,
        candidate,
        explanations=explanations,
        missing_reasons=missing,
    )
    _write_atomic(Path(output_path), _canonical_json(review))
    if markdown_path is not None:
        _write_atomic(
            Path(markdown_path),
            render_neotoma_refresh_review_markdown(review).encode("utf-8"),
        )
    return Path(output_path)


def render_neotoma_refresh_review_markdown(payload: Mapping[str, object]) -> str:
    """Render the baseline comparison without treating review as approval."""
    changes = payload.get("changes")
    change_rows = changes if isinstance(changes, list) else []
    rendered = "\n".join(
        f"| `{change.get('change_id', '')}` | `{change.get('prior')}` | "
        f"`{change.get('candidate')}` | {change.get('explanation') or 'Unexplained'} |"
        for change in change_rows
        if isinstance(change, Mapping)
    )
    if not rendered:
        rendered = (
            "| None | — | — | Candidate is byte- and count-equivalent to baseline. |"
        )
    refusals = payload.get("refusal_reasons")
    refusal_values = refusals if isinstance(refusals, list) else []
    refusal_text = ", ".join(str(value) for value in refusal_values) or "none"
    return f"""# Neotoma refresh review

This generated review compares a retained governed baseline with the current candidate. It records drift but does not authorize replacing a changed baseline.

- Status: `{payload.get("status", "refused")}`
- Fixed point: `{str(payload.get("fixed_point", False)).lower()}`
- Changes: `{payload.get("change_count", 0)}`
- Unexplained changes: `{payload.get("unexplained_change_count", 0)}`
- Refusal reasons: `{refusal_text}`
- Baseline update permitted by this automated check: `{str(payload.get("baseline_update_permitted", False)).lower()}`

| Change | Prior | Candidate | Explanation |
| --- | --- | --- | --- |
{rendered}
"""


def _collect_changes(
    changes: list[dict[str, object]],
    *,
    section: str,
    prior: Mapping[str, object],
    candidate: Mapping[str, object],
    explanations: Mapping[str, str],
    prefix: str = "",
) -> None:
    for key in sorted(set(prior) | set(candidate)):
        change_path = f"{prefix}.{key}" if prefix else key
        prior_value = prior.get(key)
        candidate_value = candidate.get(key)
        if isinstance(prior_value, Mapping) and isinstance(candidate_value, Mapping):
            _collect_changes(
                changes,
                section=section,
                prior=prior_value,
                candidate=candidate_value,
                explanations=explanations,
                prefix=change_path,
            )
            continue
        if prior_value == candidate_value:
            continue
        change_id = f"{section}:{change_path}"
        change: dict[str, object] = {
            "change_id": change_id,
            "section": section,
            "field": change_path,
            "change_kind": _change_kind(
                section=section,
                prior=prior_value,
                candidate=candidate_value,
            ),
            "prior": prior_value,
            "candidate": candidate_value,
            "explanation": explanations.get(change_id),
        }
        if (
            section == "counts"
            and isinstance(prior_value, int)
            and not isinstance(prior_value, bool)
            and isinstance(candidate_value, int)
            and not isinstance(candidate_value, bool)
        ):
            change["delta"] = candidate_value - prior_value
        changes.append(change)


def _change_kind(*, section: str, prior: object, candidate: object) -> str:
    if prior is None:
        return "added"
    if candidate is None:
        return "removed"
    if (
        section == "counts"
        and isinstance(prior, int)
        and not isinstance(prior, bool)
        and isinstance(candidate, int)
        and not isinstance(candidate, bool)
    ):
        return "increased" if candidate > prior else "decreased"
    return "changed"


def _validate_baseline(value: Mapping[str, object], label: str) -> None:
    if value.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise ValueError(f"Unexpected {label} Neotoma baseline schema")
    if value.get("source_family") != "neotoma":
        raise ValueError(f"Unexpected {label} Neotoma baseline source family")
    baseline_id = _required_text(value.get("baseline_id"), f"{label} baseline_id")
    identity_payload = dict(value)
    identity_payload.pop("baseline_id", None)
    expected_id = (
        "sha256:" + hashlib.sha256(_canonical_json(identity_payload)).hexdigest()
    )
    if baseline_id != expected_id:
        raise ValueError(f"{label} Neotoma baseline_id does not match its content")
    for section in ("identity", "schemas", "counts", "input_artifacts"):
        _mapping(value.get(section), f"{label} {section}")


def _optional_baseline_id(value: Mapping[str, object] | None) -> str | None:
    if value is None:
        return None
    baseline_id = value.get("baseline_id")
    return baseline_id if isinstance(baseline_id, str) else None


def _write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError(f"Neotoma review output cannot use symlinks: {path}")
    candidate = path.parent / f".{path.name}.candidate"
    if candidate.exists() or candidate.is_symlink():
        raise FileExistsError(f"Neotoma review candidate path exists: {candidate}")
    try:
        with candidate.open("xb") as stream:
            stream.write(content)
        candidate.replace(path)
    finally:
        if candidate.exists():
            candidate.unlink()


def _read_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Neotoma review input is not a regular file: {path}")
    return path.read_bytes()


def _json_object(content: bytes, label: str) -> dict[str, object]:
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON for {label}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"JSON must be an object for {label}")
    return payload


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Expected object for {label}")
    return value


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected non-empty text for {label}")
    return value


def _non_negative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Expected non-negative integer for {label}")
    return value


def _safe_filename(value: str) -> str:
    candidate = PurePosixPath(value)
    if len(candidate.parts) != 1 or value in {"", ".", ".."}:
        raise ValueError(f"Unsafe Neotoma raw filename: {value!r}")
    return value


def _safe_public_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Unsafe Neotoma public path: {value!r}")
    return candidate.as_posix()


def _canonical_json(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
