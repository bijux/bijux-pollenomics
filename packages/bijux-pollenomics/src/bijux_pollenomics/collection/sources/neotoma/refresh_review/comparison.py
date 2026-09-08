from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, cast


def build_review(
    prior: Mapping[str, object] | None,
    candidate: Mapping[str, object] | None,
    *,
    explanations: Mapping[str, str] | None,
    missing_reasons: list[str] | None,
    schema_version: str,
    optional_baseline_id: Callable[[Mapping[str, object] | None], str | None],
    validate_baseline: Callable[[Mapping[str, object], str], None],
    parse_mapping: Callable[[object, str], Mapping[str, object]],
    collect_changes: Any,
) -> dict[str, object]:
    reasons = list(missing_reasons or [])
    if prior is None:
        reasons.append("missing_prior_baseline")
    if candidate is None:
        reasons.append("missing_candidate_baseline")
    if reasons:
        return {
            "schema_version": schema_version,
            "source_family": "neotoma",
            "status": "refused",
            "refusal_reasons": sorted(set(reasons)),
            "prior_baseline_id": optional_baseline_id(prior),
            "candidate_baseline_id": optional_baseline_id(candidate),
            "change_count": 0,
            "unexplained_change_count": 0,
            "fixed_point": False,
            "baseline_update_permitted": False,
            "changes": [],
        }
    if prior is None or candidate is None:
        raise AssertionError("Neotoma baseline refusal did not terminate")
    validate_baseline(prior, "prior")
    validate_baseline(candidate, "candidate")
    normalized_explanations = {
        key: value.strip()
        for key, value in (explanations or {}).items()
        if key.strip() and value.strip()
    }
    changes: list[dict[str, object]] = []
    for section in ("identity", "schemas", "counts", "input_artifacts"):
        collect_changes(
            changes,
            section=section,
            prior=parse_mapping(prior.get(section), f"prior {section}"),
            candidate=parse_mapping(candidate.get(section), f"candidate {section}"),
            explanations=normalized_explanations,
        )
    unexplained = sum(change["explanation"] is None for change in changes)
    fixed_point = not changes
    return {
        "schema_version": schema_version,
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
            "input_artifacts_equal": prior["input_artifacts"]
            == candidate["input_artifacts"],
        },
        "baseline_update_permitted": fixed_point,
        "review_posture": "no_refresh_drift"
        if fixed_point
        else "retain_prior_baseline_until_changes_are_explained_and_reviewed",
        "changes": changes,
    }


def collect_changes(
    changes: list[dict[str, object]],
    *,
    section: str,
    prior: Mapping[str, object],
    candidate: Mapping[str, object],
    explanations: Mapping[str, str],
    prefix: str = "",
    classify_change: Any,
    recurse: Any,
) -> None:
    for key in sorted(set(prior) | set(candidate)):
        change_path = f"{prefix}.{key}" if prefix else key
        prior_value = prior.get(key)
        candidate_value = candidate.get(key)
        if isinstance(prior_value, Mapping) and isinstance(candidate_value, Mapping):
            recurse(
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
            "change_kind": classify_change(
                section=section, prior=prior_value, candidate=candidate_value
            ),
            "prior": prior_value,
            "candidate": candidate_value,
            "explanation": explanations.get(change_id),
        }
        if (
            section == "counts"
            and _is_integer(prior_value)
            and _is_integer(candidate_value)
        ):
            change["delta"] = cast(int, candidate_value) - cast(int, prior_value)
        changes.append(change)


def change_kind(*, section: str, prior: object, candidate: object) -> str:
    if prior is None:
        return "added"
    if candidate is None:
        return "removed"
    if section == "counts" and _is_integer(prior) and _is_integer(candidate):
        return "increased" if cast(int, candidate) > cast(int, prior) else "decreased"
    return "changed"


def validate_baseline(
    value: Mapping[str, object],
    label: str,
    *,
    baseline_schema_version: str,
    required_text: Callable[[object, str], str],
    canonical_json: Callable[[object], bytes],
    parse_mapping: Callable[[object, str], Mapping[str, object]],
    hashlib_module: Any,
) -> None:
    if value.get("schema_version") != baseline_schema_version:
        raise ValueError(f"Unexpected {label} Neotoma baseline schema")
    if value.get("source_family") != "neotoma":
        raise ValueError(f"Unexpected {label} Neotoma baseline source family")
    baseline_id = required_text(value.get("baseline_id"), f"{label} baseline_id")
    identity_payload = dict(value)
    identity_payload.pop("baseline_id", None)
    expected_id = (
        "sha256:" + hashlib_module.sha256(canonical_json(identity_payload)).hexdigest()
    )
    if baseline_id != expected_id:
        raise ValueError(f"{label} Neotoma baseline_id does not match its content")
    for section in ("identity", "schemas", "counts", "input_artifacts"):
        parse_mapping(value.get(section), f"{label} {section}")


def optional_baseline_id(value: Mapping[str, object] | None) -> str | None:
    if value is None:
        return None
    baseline_id = value.get("baseline_id")
    return baseline_id if isinstance(baseline_id, str) else None


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
