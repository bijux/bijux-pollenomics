"""Screen complete native Neotoma sample series for first-observed readiness."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.analysis.propagation.event_estimation import GovernedSample

JsonObject = dict[str, object]
_SITES = ("12", "3009")
_PROFILES = ("native_default", "named_calibrated_alternative")
_SURFACES = (
    "sites",
    "samples",
    "age_claims",
    "observations",
    "variables",
    "collection_units",
    "datasets",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _native_records(
    root: Path,
    manifest: JsonObject,
    surface: str,
    ids: set[str],
    site_ids: set[str] | None = None,
) -> tuple[list[JsonObject], list[JsonObject]]:
    entry = cast(JsonObject, cast(JsonObject, manifest["surfaces"])[surface])
    key = cast(str, entry["id_field"])
    records: list[JsonObject] = []
    parts: list[JsonObject] = []
    for part in cast(list[JsonObject], entry["parts"]):
        path = root / cast(str, part["path"])
        digest = _sha(path)
        if digest != part["sha256"]:
            raise ValueError(f"Native Neotoma part digest mismatch: {path}")
        payload = json.loads(path.read_text())
        if (
            payload["build_id"] != manifest["build_id"]
            or payload["source_snapshot_id"] != manifest["source_snapshot_id"]
        ):
            raise ValueError(f"Native Neotoma part identity mismatch: {path}")
        if len(payload["rows"]) != part["row_count"]:
            raise ValueError(f"Native Neotoma row-count mismatch: {path}")
        records.extend(
            {**row, "source_part_number": part["part_number"]}
            if surface == "observations"
            else row
            for row in payload["rows"]
            if (
                row.get("site_id") in site_ids
                if site_ids is not None
                else row.get(key) in ids
            )
        )
        parts.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": digest,
                "part_number": part["part_number"],
                "row_count": part["row_count"],
            }
        )
    if len({row[key] for row in records}) != len(records):
        raise ValueError(f"Duplicate native Neotoma {surface} identity")
    if any(
        row.get("build_id") != manifest["build_id"]
        or row.get("source_snapshot_id") != manifest["source_snapshot_id"]
        for row in records
    ):
        raise ValueError(f"Native Neotoma {surface} row provenance mismatch")
    return records, parts


def _compare_export(
    native: list[JsonObject], exported: list[JsonObject], id_field: str
) -> None:
    actual = {row[id_field]: row for row in native}
    shown: dict[str, JsonObject] = {}
    for row in exported:
        row_id = cast(str, row[id_field])
        if row_id in shown and shown[row_id] != row:
            raise ValueError(f"Conflicting exported {id_field}: {row_id}")
        shown[row_id] = row
    if actual.keys() != shown.keys() or len(actual) != len(native):
        raise ValueError(f"Export/native {id_field} identity mismatch")
    for row_id, row in shown.items():
        for field, value in row.items():
            if field not in actual[row_id] or actual[row_id][field] != value:
                raise ValueError(
                    f"Export/native {id_field} field mismatch: {row_id}/{field}"
                )


def _reader_snapshot(
    repository: Path,
) -> tuple[JsonObject, dict[str, JsonObject], list[JsonObject]]:
    root = repository / "data/neotoma/relational"
    manifest = json.loads((root / "manifest.json").read_text())
    exports = {
        site: json.loads(
            (
                repository
                / f"docs/report/atlas/source-export/downloads/neotoma-site-{site}.pollen-series.json"
            ).read_text()
        )
        for site in _SITES
    }
    if manifest["source_family"] != "neotoma":
        raise ValueError("Native source family mismatch")
    for site, export in exports.items():
        provenance = cast(JsonObject, export["source_provenance"])
        semantics = cast(JsonObject, export["source_semantics"])
        feature_identity = cast(JsonObject, export["feature_identity"])
        if (
            export["schema_version"] != "source-pollen-record-export.v1"
            or export["record_id"] != f"neotoma:site:{site}"
            or export["record_scope"]
            != "complete_source_record_not_filtered_to_map_time_window"
            or semantics["classification_status"] != "not_accepted"
            or feature_identity["layer_key"] != "neotoma-pollen"
            or feature_identity["feature_key"] != f"evidence:{site}"
            or provenance["record_locator"]
            != f"surfaces/sites#site_id=neotoma:site:{site}"
            or provenance["observation_locator_contract"]
            != "surfaces/observations/part-{source_part_number:05d}.json#observation_id={observation_id}"
            or provenance["build_id"] != manifest["build_id"]
            or provenance["source_snapshot_id"] != manifest["source_snapshot_id"]
            or provenance["materialization_sha256"]
            != manifest["materialization_sha256"]
        ):
            raise ValueError(f"Export/native reader identity mismatch: {site}")
    ids: dict[str, set[str]] = {}
    ids["sites"] = {f"neotoma:site:{site}" for site in _SITES}
    for surface in (
        "samples",
        "age_claims",
        "observations",
        "variables",
        "collection_units",
        "datasets",
    ):
        id_field = cast(
            str,
            cast(JsonObject, cast(JsonObject, manifest["surfaces"])[surface])[
                "id_field"
            ],
        )
        export_key = (
            "chronology_claims"
            if surface == "age_claims"
            else "pollen_observations"
            if surface == "observations"
            else "source_variables"
            if surface == "variables"
            else surface
        )
        ids[surface] = {
            cast(str, row[id_field])
            for export in exports.values()
            for row in export[export_key]["records"]
        }
    identity: list[JsonObject] = []
    for surface in _SURFACES:
        native, parts = _native_records(
            root,
            manifest,
            surface,
            ids[surface],
            ids["sites"] if surface not in {"sites", "variables"} else None,
        )
        if surface == "observations":
            ids["variables"] = {cast(str, row["variable_id"]) for row in native}
        if surface != "sites":
            export_key = (
                "chronology_claims"
                if surface == "age_claims"
                else "pollen_observations"
                if surface == "observations"
                else "source_variables"
                if surface == "variables"
                else surface
            )
            id_field = cast(
                str,
                cast(JsonObject, cast(JsonObject, manifest["surfaces"])[surface])[
                    "id_field"
                ],
            )
            exported = [
                row
                for export in exports.values()
                for row in export[export_key]["records"]
            ]
            _compare_export(native, exported, id_field)
        identity.append(
            {
                "surface": surface,
                "selected_native_rows": len(native),
                "verified_parts": parts,
            }
        )
    return manifest, exports, identity


def _age_profile(
    claims: list[JsonObject],
    profile: str,
) -> JsonObject:
    selected = [
        row
        for row in claims
        if bool(row["is_default_chronology"]) == (profile == "native_default")
    ]
    if len(selected) != 1:
        return {
            "status": "refused",
            "reason_code": "selected_chronology_not_unique",
            "claims": claims,
            "selected_claim_ids": [row["chronology_claim_id"] for row in selected],
        }
    row = selected[0]
    return {
        "status": "selected",
        "claim": row,
        "selected_claim_ids": [row["chronology_claim_id"]],
    }


def _compact_age(age: JsonObject) -> JsonObject:
    claim = cast(JsonObject, age.get("claim", {}))
    fields = (
        "chronology_claim_id",
        "chronology_id",
        "source_age_type",
        "source_age_value",
        "source_age_unit",
        "calibration_status",
        "comparability_status",
        "younger_bp",
        "older_bp",
        "admission_reason",
        "refusal_reason",
        "is_default_chronology",
        "source_relation_path",
    )
    return {
        "status": age["status"],
        "selected_claim_ids": age["selected_claim_ids"],
        "reason_code": age.get("reason_code"),
        "claim": {field: claim[field] for field in fields} if claim else None,
    }


def _compact_observation(observation: JsonObject | None) -> JsonObject | None:
    if observation is None:
        return None
    fields = (
        "observation_id",
        "sample_id",
        "variable_id",
        "source_value",
        "source_unit",
        "source_denominator",
        "denominator_status",
        "detection_status",
        "unit_family",
        "source_part_number",
    )
    return {field: observation[field] for field in fields}


def _screen_inventory(
    site: str,
    variable: JsonObject,
    samples: list[JsonObject],
    observations: list[JsonObject],
    chronologies: dict[str, list[JsonObject]],
    profile: str,
    source_snapshot_id: str,
) -> JsonObject:
    variable_id = cast(str, variable["variable_id"])
    observed = {
        cast(str, row["sample_id"]): row
        for row in observations
        if row["variable_id"] == variable_id
    }
    ordered = sorted(samples, key=lambda row: -cast(float, row["source_depth"]))
    sample_rows: list[JsonObject] = []
    selected_ages: list[JsonObject] = []
    governed: list[GovernedSample] = []
    blockers: set[str] = set()
    if len(observed) != sum(row["variable_id"] == variable_id for row in observations):
        blockers.add("duplicate_feature_sample_observation")
    for position, sample in enumerate(ordered):
        sample_id = cast(str, sample["sample_id"])
        observation = observed.get(sample_id)
        age = _age_profile(chronologies.get(sample_id, []), profile)
        selected_ages.append(age)
        selected = cast(JsonObject, age.get("claim", {}))
        if observation is None:
            blockers.add("feature_sample_unreported")
        if age["status"] != "selected":
            blockers.add(cast(str, age["reason_code"]))
        else:
            if selected["comparability_status"] != "comparable":
                blockers.add("selected_chronology_not_comparable")
            if selected["comparability_status"] == "refused":
                blockers.add("selected_chronology_refused")
        if observation is not None:
            if (
                observation["source_unit"] != "NISP"
                or observation["unit_family"] != "count"
            ):
                blockers.add("native_measure_not_count")
            if observation["source_denominator"] is not None:
                blockers.add("unexpected_native_denominator")
            value = observation["source_value"]
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value <= 0
            ):
                blockers.add("native_positive_value_invalid")
            if (
                age["status"] == "selected"
                and value is not None
                and isinstance(value, (int, float))
                and not isinstance(value, bool)
                and value >= 0
                and selected["comparability_status"]
                in {"comparable", "context_only", "unresolved"}
            ):
                status = selected["comparability_status"]
                governed.append(
                    GovernedSample(
                        observation_id=cast(str, observation["observation_id"]),
                        source_record_id=sample_id,
                        source_family="neotoma",
                        source_snapshot_id=source_snapshot_id,
                        feature_key=variable_id,
                        site_id=f"neotoma:site:{site}",
                        collection_unit_id=cast(str, sample["collection_unit_id"]),
                        sequence_position=position,
                        value=cast(float, value),
                        measure_kind="count",
                        source_unit=cast(str, observation["source_unit"]),
                        measurement_semantics_id="neotoma-native-NISP-count",
                        chronology_claim_id=cast(str, selected["chronology_claim_id"]),
                        comparability_status=status,
                        younger_bp=cast(float | None, selected["younger_bp"])
                        if status == "comparable"
                        else None,
                        older_bp=cast(float | None, selected["older_bp"])
                        if status == "comparable"
                        else None,
                        source_age_value=cast(
                            float | None, selected["source_age_value"]
                        ),
                        source_age_unit=cast(str, selected["source_age_unit"]),
                    )
                )
        sample_rows.append(
            {
                "sample_id": sample_id,
                "observation": _compact_observation(observation),
            }
        )
    for older_age, younger_age in zip(selected_ages, selected_ages[1:], strict=False):
        if older_age["status"] != "selected" or younger_age["status"] != "selected":
            continue
        older = cast(JsonObject, older_age["claim"])
        younger = cast(JsonObject, younger_age["claim"])
        if (
            older["comparability_status"] == "comparable"
            and younger["comparability_status"] == "comparable"
            and cast(float, older["younger_bp"]) <= cast(float, younger["older_bp"])
        ):
            blockers.add("chronology_order_indeterminate")
    if variable["source_reported_name"] is None:
        blockers.add("source_variable_name_missing")
    blockers.add("accepted_taxon_mapping_not_available")
    return {
        "site_id": f"neotoma:site:{site}",
        "variable_id": variable_id,
        "source_reported_name": variable["source_reported_name"],
        "source_taxon_id": variable["source_taxon_id"],
        "source_semantics": variable["source_semantics"],
        "source_units": variable["source_units"],
        "threshold_profile_id": "reported_positive_v1",
        "chronology_profile": profile,
        "sample_universe_count": len(ordered),
        "reported_observation_count": len(observed),
        "governed_sample_inputs_count": len(governed),
        "complete_sample_observation_coverage": len(observed) == len(ordered),
        "sample_inventory": sample_rows,
        "blocker_codes": sorted(blockers),
        "estimator_invoked": False,
        "event": None,
        "status": "refused",
        "reason_code": next(
            reason
            for reason in (
                "feature_sample_unreported",
                "selected_chronology_not_unique",
                "selected_chronology_refused",
                "selected_chronology_not_comparable",
                "chronology_order_indeterminate",
                "native_measure_not_count",
                "unexpected_native_denominator",
                "native_positive_value_invalid",
                "accepted_taxon_mapping_not_available",
            )
            if reason in blockers
        ),
        "estimator_boundary": "taxon template requires accepted concept; single source variable cannot be relabeled whole:pollen",
    }


def build_neotoma_first_observed(repository: Path) -> JsonObject:
    manifest, exports, identity = _reader_snapshot(repository)
    attempts: list[JsonObject] = []
    sites: list[JsonObject] = []
    for site, export in exports.items():
        samples = cast(list[JsonObject], cast(JsonObject, export["samples"])["records"])
        observations = cast(
            list[JsonObject],
            cast(JsonObject, export["pollen_observations"])["records"],
        )
        variables = cast(
            list[JsonObject], cast(JsonObject, export["source_variables"])["records"]
        )
        claims = cast(
            list[JsonObject], cast(JsonObject, export["chronology_claims"])["records"]
        )
        bysample: dict[str, list[JsonObject]] = defaultdict(list)
        for claim in claims:
            bysample[cast(str, claim["subject_id"])].append(claim)
        siteattempts = [
            _screen_inventory(
                site,
                variable,
                samples,
                observations,
                bysample,
                profile,
                cast(str, manifest["source_snapshot_id"]),
            )
            for variable in variables
            for profile in _PROFILES
        ]
        inventories: list[JsonObject] = []
        for index, row in enumerate(siteattempts):
            inventory = cast(list[JsonObject], row.pop("sample_inventory"))
            row["sample_inventory_ref"] = f"{site}:{row['variable_id']}"
            if index % len(_PROFILES) == 0:
                inventories.append(
                    {
                        "sample_inventory_ref": row["sample_inventory_ref"],
                        "variable_id": row["variable_id"],
                        "rows": inventory,
                    }
                )
        attempts.extend(siteattempts)
        sites.append(
            {
                "site_id": export["record_id"],
                "title": export["title"],
                "sample_count": len(samples),
                "chronology_claim_count": len(claims),
                "observation_count": len(observations),
                "variable_count": len(variables),
                "attempt_count": len(siteattempts),
                "sample_universe": [
                    {
                        "sample_id": row["sample_id"],
                        "source_depth": row["source_depth"],
                        "collection_unit_id": row["collection_unit_id"],
                    }
                    for row in samples
                ],
                "chronology_claim_ledger": [
                    {
                        "sample_id": row["subject_id"],
                        **_compact_age(
                            {
                                "status": "selected",
                                "claim": row,
                                "selected_claim_ids": [row["chronology_claim_id"]],
                            }
                        ),
                    }
                    for row in claims
                ],
                "feature_sample_inventories": inventories,
                "full_coverage_variable_count": sum(
                    row["complete_sample_observation_coverage"] is True
                    for row in siteattempts
                    if row["chronology_profile"] == _PROFILES[0]
                ),
                "default_claim_statuses": dict(
                    Counter(
                        row["comparability_status"]
                        for row in claims
                        if row["is_default_chronology"]
                    )
                ),
                "alternative_claim_statuses": dict(
                    Counter(
                        row["comparability_status"]
                        for row in claims
                        if not row["is_default_chronology"]
                    )
                ),
            }
        )
    return {
        "schema_version": "neotoma-source-first-observed-readiness.v1",
        "source_identity": {
            "source_family": manifest["source_family"],
            "source_snapshot_id": manifest["source_snapshot_id"],
            "build_id": manifest["build_id"],
            "materialization_sha256": manifest["materialization_sha256"],
            "manifest_sha256": _sha(
                repository / "data/neotoma/relational/manifest.json"
            ),
            "verified_native_surfaces": identity,
            "export_sha256": {
                site: _sha(
                    repository
                    / f"docs/report/atlas/source-export/downloads/neotoma-site-{site}.pollen-series.json"
                )
                for site in _SITES
            },
        },
        "profiles": _PROFILES,
        "sites": sites,
        "attempts": attempts,
        "denominators": {
            "sites": len(sites),
            "variables": sum(cast(int, s["variable_count"]) for s in sites),
            "attempts": len(attempts),
            "full_coverage_attempts": sum(
                row["complete_sample_observation_coverage"] is True for row in attempts
            ),
            "refused": sum(row["status"] == "refused" for row in attempts),
            "events": sum(row["event"] is not None for row in attempts),
            "estimator_invocations": sum(
                row["estimator_invoked"] is True for row in attempts
            ),
            "blocker_counts": dict(
                Counter(
                    code
                    for row in attempts
                    for code in cast(list[str], row["blocker_codes"])
                )
            ),
        },
        "claims": {
            "real_source_rows_consumed": True,
            "source_chronology_profiles_separate": True,
            "missing_feature_observations_coerced_to_zero": False,
            "alternate_chronology_selected_for_publication": False,
            "unreviewed_taxon_concept_promoted": False,
            "first_observed_events_admitted": False,
            "scientific_accuracy_or_route_claim": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_neotoma_first_observed(args.repository.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    counts = cast(dict[str, object], report["denominators"])
    print(
        json.dumps(
            {
                "output": str(args.output),
                **{k: v for k, v in counts.items() if k != "blocker_counts"},
            }
        )
    )
    return 0 if counts["attempts"] == 256 and counts["events"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
