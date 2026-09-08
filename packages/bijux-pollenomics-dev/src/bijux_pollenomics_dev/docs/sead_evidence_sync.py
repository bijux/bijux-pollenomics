"""Synchronize public SEAD denominators from governed repository artifacts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Any, cast

START_MARKER = "<!-- sead-evidence:generated:start -->"
END_MARKER = "<!-- sead-evidence:generated:end -->"
FACT_KEY = "sead_archaeology_context"
DEFAULT_TARGETS = (
    Path("docs/public/pollenomics-data/sources/sead.md"),
    Path("docs/public/pollenomics-data/publications/sead-exports.md"),
)


class SeadEvidenceSyncError(ValueError):
    """Raised when governed SEAD evidence cannot be reconciled safely."""


@dataclass(frozen=True)
class SeadEvidenceFacts:
    """Exact, unit-aware SEAD facts used by public documentation."""

    source_run_id: str
    build_id: str
    source_table_count: int
    bbox_site_count: int
    assigned_site_count: int
    review_site_count: int
    unassigned_site_count: int
    country_site_counts: dict[str, int]
    map_feature_count: int
    chronology_claim_count: int
    comparable_claim_count: int
    context_only_claim_count: int
    refused_claim_count: int
    unresolved_claim_count: int
    observation_count: int
    taxon_relation_count: int
    dimension_relation_count: int
    eligible_event_count: int
    refused_event_count: int
    propagation_status: str
    propagation_reason_code: str


def _load_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SeadEvidenceSyncError(
            f"Cannot read governed JSON {path}: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise SeadEvidenceSyncError(f"Governed JSON must be an object: {path}")
    return cast(dict[str, Any], payload)


def _required_string(payload: dict[str, Any], key: str, owner: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise SeadEvidenceSyncError(f"{owner}.{key} must be a non-empty string")
    return value


def _required_count(payload: dict[str, Any], key: str, owner: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise SeadEvidenceSyncError(f"{owner}.{key} must be a non-negative integer")
    return value


def _required_object(payload: dict[str, Any], key: str, owner: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise SeadEvidenceSyncError(f"{owner}.{key} must be an object")
    return cast(dict[str, Any], value)


def _governing_manifest_path(repository_root: Path) -> Path:
    registry_path = repository_root / "data/source_fact_ownership_registry.json"
    registry = _load_object(registry_path)
    if not isinstance(registry.get("rows"), list):
        raise SeadEvidenceSyncError("source fact ownership registry must contain rows")
    rows = cast(list[Any], registry["rows"])
    if registry.get("row_count") != len(rows):
        raise SeadEvidenceSyncError("source fact ownership registry row count diverges")
    matches = [
        row for row in rows if isinstance(row, dict) and row.get("fact_key") == FACT_KEY
    ]
    if len(matches) != 1:
        raise SeadEvidenceSyncError(
            f"source fact ownership registry must define {FACT_KEY!r} exactly once"
        )
    relative = matches[0].get("governing_surface_path")
    if not isinstance(relative, str) or not relative:
        raise SeadEvidenceSyncError(f"{FACT_KEY} governing_surface_path is missing")
    path = (repository_root / relative).resolve()
    try:
        path.relative_to(repository_root.resolve())
    except ValueError as error:
        raise SeadEvidenceSyncError(
            f"{FACT_KEY} governing surface escapes the repository"
        ) from error
    if not path.is_file():
        raise SeadEvidenceSyncError(f"governing SEAD manifest is missing: {path}")
    return path


def load_sead_evidence_facts(repository_root: Path) -> SeadEvidenceFacts:
    """Load and reconcile SEAD facts from their declared authorities."""
    manifest_path = _governing_manifest_path(repository_root)
    manifest = _load_object(manifest_path)
    source_run_id = _required_string(manifest, "source_run_id", "manifest")
    build_id = _required_string(manifest, "build_id", "manifest")
    if Path(source_run_id).name != source_run_id:
        raise SeadEvidenceSyncError("manifest.source_run_id must be one path segment")
    acquisition_root = repository_root / "data/sead/raw/acquisitions" / source_run_id
    admission = _load_object(acquisition_root / "admission.json")
    chronology = _load_object(manifest_path.parent / "chronology_claims.json")
    observations = _load_object(
        manifest_path.parent / "source_native_observations.json"
    )
    relations = _load_object(manifest_path.parent / "observation_relation_index.json")
    events = _load_object(manifest_path.parent / "evidence_events.json")
    atlas = _load_object(
        repository_root
        / "docs/report/regions/nordic/nordic_map_publication_contract.json"
    )

    admission_run_id = _required_string(admission, "run_id", "admission")
    admission_build_id = _required_string(admission, "build_id", "admission")
    atlas_sead = _required_object(
        _required_object(atlas, "detail_projection", "atlas"),
        "sources",
        "atlas.detail_projection",
    ).get("sead")
    if not isinstance(atlas_sead, dict):
        raise SeadEvidenceSyncError(
            "atlas detail projection is missing its SEAD contract"
        )
    atlas_sead = cast(dict[str, Any], atlas_sead)
    identities = {
        "manifest": (source_run_id, build_id),
        "admission": (admission_run_id, admission_build_id),
        "atlas": (
            _required_string(atlas_sead, "source_run_id", "atlas.sead"),
            _required_string(atlas_sead, "build_id", "atlas.sead"),
        ),
    }
    if len(set(identities.values())) != 1:
        raise SeadEvidenceSyncError(f"SEAD run/build identities diverge: {identities}")
    for owner, payload in (
        ("chronology", chronology),
        ("observations", observations),
        ("relations", relations),
        ("events", events),
    ):
        if _required_string(payload, "source_run_id", owner) != source_run_id:
            raise SeadEvidenceSyncError(f"{owner} source run identity diverges")
    for owner, payload, key in (
        ("chronology", chronology, "source_build_id"),
        ("observations", observations, "build_id"),
        ("relations", relations, "build_id"),
    ):
        if _required_string(payload, key, owner) != build_id:
            raise SeadEvidenceSyncError(f"{owner} build identity diverges")

    country_accounting = _required_object(admission, "country_accounting", "admission")
    country_counts_payload = _required_object(
        country_accounting, "country_counts", "admission.country_accounting"
    )
    country_counts = {
        code: _required_count(country_counts_payload, code, "admission.country_counts")
        for code in ("SE", "DK", "NO", "FI")
    }
    assigned_site_count = _required_count(
        country_accounting, "admitted_site_count", "admission.country_accounting"
    )
    if sum(country_counts.values()) != assigned_site_count:
        raise SeadEvidenceSyncError("SEAD country site counts do not reconcile")
    table_counts = _required_object(admission, "table_counts", "admission")
    source_table_count = _required_count(manifest, "source_table_count", "manifest")
    if len(table_counts) != source_table_count:
        raise SeadEvidenceSyncError("SEAD source table count does not reconcile")

    chronology_comparability = _required_object(
        chronology, "comparability_counts", "chronology"
    )
    claim_count = _required_count(chronology, "claim_count", "chronology")
    comparable = _required_count(chronology_comparability, "comparable", "chronology")
    context_only = _required_count(
        chronology_comparability, "context_only", "chronology"
    )
    unresolved = _required_count(chronology_comparability, "unresolved", "chronology")
    refused_claims = _required_count(chronology_comparability, "refused", "chronology")
    if comparable + context_only + refused_claims + unresolved != claim_count:
        raise SeadEvidenceSyncError("SEAD chronology comparability does not reconcile")
    if _required_count(manifest, "chronology_claim_count", "manifest") != claim_count:
        raise SeadEvidenceSyncError("SEAD manifest chronology count diverges")

    observation_count = _required_count(
        observations, "observation_count", "observations"
    )
    event_denominator = _required_count(events, "observation_denominator", "events")
    eligible = _required_count(events, "eligible_event_count", "events")
    refused = _required_count(events, "refused_event_count", "events")
    if (
        observation_count != event_denominator
        or eligible + refused != observation_count
    ):
        raise SeadEvidenceSyncError("SEAD event disposition does not reconcile")
    if (
        _required_count(manifest, "observation_count", "manifest") != observation_count
        or _required_count(manifest, "eligible_event_count", "manifest") != eligible
        or _required_count(manifest, "refused_event_count", "manifest") != refused
    ):
        raise SeadEvidenceSyncError("SEAD manifest event accounting diverges")
    refusal_reasons = _required_object(events, "refusal_reason_counts", "events")
    if (
        _required_count(
            refusal_reasons, "source_classification_not_accepted", "events.refusals"
        )
        != observation_count
    ):
        raise SeadEvidenceSyncError("SEAD classification refusal is not exhaustive")

    atlas_observations = _required_count(
        atlas_sead, "source_observation_denominator", "atlas.sead"
    )
    atlas_claims = _required_count(atlas_sead, "source_claim_denominator", "atlas.sead")
    atlas_sites = _required_count(atlas_sead, "assigned_site_count", "atlas.sead")
    atlas_events = _required_count(
        atlas_sead, "source_event_refusal_denominator", "atlas.sead"
    )
    if (atlas_observations, atlas_claims, atlas_sites, atlas_events) != (
        observation_count,
        claim_count,
        assigned_site_count,
        refused,
    ):
        raise SeadEvidenceSyncError("SEAD evidence and atlas denominators diverge")
    atlas_country_counts = _required_object(
        atlas_sead, "country_site_counts", "atlas.sead"
    )
    expected_atlas_countries = {
        "Sweden": country_counts["SE"],
        "Denmark": country_counts["DK"],
        "Norway": country_counts["NO"],
        "Finland": country_counts["FI"],
    }
    if atlas_country_counts != expected_atlas_countries:
        raise SeadEvidenceSyncError("SEAD atlas country site counts diverge")
    map_feature_count = _required_count(
        atlas_sead, "source_feature_count", "atlas.sead"
    )
    if map_feature_count < assigned_site_count:
        raise SeadEvidenceSyncError("SEAD atlas feature count is below its site count")

    return SeadEvidenceFacts(
        source_run_id=source_run_id,
        build_id=build_id,
        source_table_count=source_table_count,
        bbox_site_count=_required_count(
            country_accounting, "bbox_site_count", "admission.country_accounting"
        ),
        assigned_site_count=assigned_site_count,
        review_site_count=_required_count(
            country_accounting, "review_site_count", "admission.country_accounting"
        ),
        unassigned_site_count=_required_count(
            country_accounting, "unassigned_site_count", "admission.country_accounting"
        ),
        country_site_counts=country_counts,
        map_feature_count=map_feature_count,
        chronology_claim_count=claim_count,
        comparable_claim_count=comparable,
        context_only_claim_count=context_only,
        refused_claim_count=refused_claims,
        unresolved_claim_count=unresolved,
        observation_count=observation_count,
        taxon_relation_count=_required_count(
            relations, "taxon_relation_count", "relations"
        ),
        dimension_relation_count=_required_count(
            relations, "dimension_relation_count", "relations"
        ),
        eligible_event_count=eligible,
        refused_event_count=refused,
        propagation_status=_required_string(
            atlas_sead, "propagation_status", "atlas.sead"
        ),
        propagation_reason_code=_required_string(
            atlas_sead, "propagation_reason_code", "atlas.sead"
        ),
    )


def render_sead_evidence_block(facts: SeadEvidenceFacts) -> str:
    """Render the canonical public snapshot block."""
    countries = facts.country_site_counts
    return "\n".join(
        (
            START_MARKER,
            (
                "The current governed full-evidence run is "
                f"`{facts.source_run_id}` (`{facts.build_id}`). Its denominators are:"
            ),
            "",
            "| Governed population | Count | Interpretation |",
            "| --- | ---: | --- |",
            f"| source tables | {facts.source_table_count:,} | complete captured relational table set |",
            f"| sites in the Nordic bounding-box review | {facts.bbox_site_count:,} | country-decision denominator |",
            f"| assigned four-country sites | {facts.assigned_site_count:,} | SE {countries['SE']:,}, DK {countries['DK']:,}, NO {countries['NO']:,}, FI {countries['FI']:,} |",
            f"| sites requiring country review | {facts.review_site_count:,} | retained outside assigned publication membership |",
            f"| unassigned sites | {facts.unassigned_site_count:,} | retained without a governed country assignment |",
            f"| atlas SEAD features | {facts.map_feature_count:,} | {facts.assigned_site_count:,} four-country site features plus {facts.map_feature_count - facts.assigned_site_count:,} Swedish chronology-discovery features; not a distinct-site count |",
            f"| chronology claims | {facts.chronology_claim_count:,} | {facts.comparable_claim_count:,} comparable, {facts.context_only_claim_count:,} context-only, {facts.refused_claim_count:,} refused by the numeric BP contract, {facts.unresolved_claim_count:,} unresolved |",
            f"| source-native observations | {facts.observation_count:,} | quantitative observation denominator |",
            f"| source-native taxon relations | {facts.taxon_relation_count:,} | preserved source taxonomy, not accepted cross-source classification |",
            f"| dimension relations | {facts.dimension_relation_count:,} | explicit source-native measurement dimensions |",
            f"| eligible / refused propagation events | {facts.eligible_event_count:,} / {facts.refused_event_count:,} | `{facts.propagation_status}`: `{facts.propagation_reason_code}` |",
            "",
            (
                "Site, feature, claim, observation, relation, and event counts are different units. "
                "The atlas may display SEAD chronology and source-native detail, but it must not "
                "turn the refused event population into migration or propagation evidence."
            ),
            END_MARKER,
        )
    )


def render_target_text(current_text: str, facts: SeadEvidenceFacts) -> str:
    """Replace one complete generated block without touching authored prose."""
    if current_text.count(START_MARKER) != 1 or current_text.count(END_MARKER) != 1:
        raise SeadEvidenceSyncError(
            "target must contain exactly one complete SEAD evidence block"
        )
    start = current_text.index(START_MARKER)
    end = current_text.index(END_MARKER, start) + len(END_MARKER)
    return current_text[:start] + render_sead_evidence_block(facts) + current_text[end:]


def synchronize_sead_evidence(
    repository_root: Path, *, check: bool
) -> tuple[Path, ...]:
    """Check or synchronize every public SEAD snapshot target."""
    facts = load_sead_evidence_facts(repository_root)
    changed: list[Path] = []
    for relative in DEFAULT_TARGETS:
        path = repository_root / relative
        current = path.read_text(encoding="utf-8")
        rendered = render_target_text(current, facts)
        if rendered == current:
            continue
        changed.append(relative)
        if check:
            continue
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", suffix=".sync"
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
                handle.write(rendered)
            os.replace(temporary_name, path)
        except BaseException:
            Path(temporary_name).unlink(missing_ok=True)
            raise
    if check and changed:
        rendered_paths = ", ".join(str(path) for path in changed)
        raise SeadEvidenceSyncError(
            f"SEAD public evidence blocks are stale: {rendered_paths}"
        )
    return tuple(changed)


def main(argv: list[str] | None = None) -> int:
    """Run the SEAD public-evidence synchronization command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        changed = synchronize_sead_evidence(
            arguments.repository_root.resolve(), check=arguments.check
        )
    except SeadEvidenceSyncError as error:
        parser.error(str(error))
    if changed:
        print("SEAD public evidence synchronized: " + ", ".join(map(str, changed)))
    else:
        print("SEAD public evidence current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
