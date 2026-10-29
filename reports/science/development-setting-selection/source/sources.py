"""Authenticate saved prediction/score populations without reading outer outcomes."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import stat
from typing import Any

Json = dict[str, Any]


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def decode(body: bytes) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> Json:
        result: Json = {}
        for key, value in pairs:
            require(key not in result, "Duplicate scientific JSON member")
            result[key] = value
        return result

    def invalid(value: str) -> None:
        raise ValueError("Nonfinite JSON: " + value)

    return json.loads(body, object_pairs_hook=unique, parse_constant=invalid)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def checked(root: Path, reference: Json) -> bytes:
    path: Path = root / reference["path"]
    require(
        path.is_absolute()
        and ".." not in path.parts
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Independent normalized input required",
    )
    info = path.lstat()
    require(
        stat.S_ISREG(info.st_mode)
        and info.st_nlink == 1
        and type(reference["bytes"]) is int
        and info.st_size == reference["bytes"] <= 256 * 1024**2,
        "Exact bounded regular input required",
    )
    body: bytes = path.read_bytes()
    require(
        hashlib.sha256(body).hexdigest() == reference["sha256"],
        "Declared saved input changed: " + str(path),
    )
    return body


def load(root: Path, protocol: Json) -> Json:
    """Read inner scores and prediction freezes only; hash outer reports unopened."""
    for row in protocol["maintained_sources"]:
        checked(root, row)
    experiment = decode(checked(root, protocol["experiment"]))
    records = [site["record_id"] for site in experiment["sites"]]
    require(
        sorted(records) == protocol["records"]
        and experiment["baselines"] == protocol["baselines"],
        "Original site/baseline population changed",
    )
    require(
        all(
            not site["identity_keys"]
            and site["record_id"] == "author:" + site["site_id"]
            for site in experiment["sites"]
        ),
        "This admitted original population has changed identity authority",
    )
    groups = {record: "site-group:" + digest([record]) for record in records}
    require(groups == protocol["groups"], "Admitted original group identity differs")
    declarations = decode(checked(root, protocol["forecast"]))
    require(
        len(declarations["grid"]) == 16
        and [r["id"] for r in declarations["grid"]] == protocol["declared_setting_ids"],
        "Exact original sixteen settings required",
    )
    rows: dict[tuple[str, str, str, str], Json] = {}
    outer: dict[tuple[str, str, str], Json] = {}
    inner_evidence = []
    duplicate_rows, duplicate_slots = 0, 0
    for axis in protocol["axes"]:
        authority = decode(checked(root, axis["authority"]))
        require(
            authority["independent_semantics"]["approved"] is True
            and authority["independent_semantics"]["scientific_saved_products_admitted"]
            is True
            and authority["source_candidate"] == axis["source_candidate"],
            "Independently admitted saved axis required",
        )
        for role, reference in (
            ("inner-scores.json", axis["inner_scores"]),
            ("candidate-prediction-freeze.json", axis["candidate_freeze"]),
            ("report.json", axis["report"]),
        ):
            require(
                authority["raw_trace_products"]["evaluation:" + role]
                == {k: reference[k] for k in ("sha256", "bytes")},
                "Axis raw trace/report identity differs",
            )
        # Byte custody may authenticate a saved outer report before selection;
        # no JSON deserialization of that report occurs until after freeze.
        checked(root, axis["report"])
        scores = decode(checked(root, axis["inner_scores"]))
        freeze = decode(checked(root, axis["candidate_freeze"]))
        slots = freeze["slots"]
        methods = axis["methods"]
        require(
            len(scores) == len(methods) * 630 and len(slots) == len(methods) * 675,
            "Complete saved axis populations required",
        )
        by_slot = {}
        for slot in slots:
            key = (
                slot["kind"],
                slot["outer_target"],
                slot["target"],
                slot["method"],
                slot["baseline"],
            )
            require(
                key not in by_slot
                and key[3] in methods
                and key[4] in protocol["baselines"]
                and slot["status"] in ("predicted", "refused"),
                "Unknown/duplicate frozen prediction",
            )
            by_slot[key] = slot
            target, heldout = slot["target"], slot["outer_target"]
            expected_train = set(records) - {target, heldout}
            fold = slot["fold"]
            require(
                target in records
                and heldout in records
                and set(fold["train_record_ids"]) == expected_train
                and fold["test_record_ids"] == [target]
                and set(fold["train_group_ids"]) == {groups[r] for r in expected_train}
                and fold["test_group_ids"] == [groups[target]],
                "Frozen whole-group fold population differs",
            )
            if key[0] == "outer":
                require(target == heldout, "Outer target identity differs")
                outer_key = (methods[key[3]], key[4], heldout)
                if outer_key in outer:
                    require(
                        outer[outer_key] == slot,
                        "Shared nominal outer prediction changed",
                    )
                    duplicate_slots += 1
                else:
                    outer[outer_key] = slot
            else:
                require(
                    key[0] == "inner" and target != heldout,
                    "Unknown prediction context",
                )
        seen = set()
        for row in scores:
            key = (
                "inner",
                row["outer_target"],
                row["inner_target"],
                row["method"],
                row["baseline"],
            )
            require(
                key in by_slot and key not in seen,
                "Exact unique inner-score/frozen-prediction join required",
            )
            seen.add(key)
            source = by_slot[key]
            require(
                row["prediction_sha256"] == digest(source)
                and row["status"]
                == ("scored" if source["status"] == "predicted" else "refused")
                and row["inner_train_record_ids"] == source["fold"]["train_record_ids"]
                and row["inner_train_group_ids"] == source["fold"]["train_group_ids"],
                "Stored score/freeze ancestry or prediction hash differs",
            )
            normalized_key = (
                methods[row["method"]],
                row["baseline"],
                row["outer_target"],
                row["inner_target"],
            )
            if normalized_key in rows:
                require(
                    rows[normalized_key] == row,
                    "Shared nominal inner metrics/prediction identity changed",
                )
                duplicate_rows += 1
            else:
                rows[normalized_key] = row
                inner_evidence.append(
                    {
                        "candidate_id": normalized_key[0],
                        "spatial_id": normalized_key[1],
                        "original_row": row,
                        "source": axis["inner_scores"],
                        "row_sha256": digest(row),
                    }
                )
        require(
            seen == {key for key in by_slot if key[0] == "inner"},
            "Missing saved inner score/refusal",
        )
    require(
        len(rows) == 4410
        and len(outer) == 315
        and duplicate_rows == 630
        and duplicate_slots == 45,
        "Exact seven physical profiles with strict nominal deduplication required",
    )
    catalogue = protocol["catalogue"]
    pair_ids = [(p["candidate_id"], p["spatial_id"]) for p in catalogue]
    saved = {
        (p["candidate_id"], p["spatial_id"])
        for p in catalogue
        if p["eligibility"] == "saved_prediction"
    }
    physical = {(key[0], key[1]) for key in rows}
    aliases = [p for p in catalogue if p["eligibility"] == "source_equivalent_alias"]
    require(
        len(pair_ids) == len(set(pair_ids)) == 32
        and saved == physical
        and len(saved) == 21,
        "Exact declared physical candidate/spatial pairs required",
    )
    require(
        len(aliases) == 3
        and all(
            p["candidate_id"] == "local-support-500m"
            and p["source_candidate_id"] == "gpm-neutral-fixed-start"
            and p["spatial_id"] in protocol["baselines"]
            and p["evidence"] == protocol["auxiliary"]["ring_support"]
            for p in aliases
        ),
        "Exact source-equivalent aliases/provenance required",
    )
    auxiliary = qualify_auxiliary(root, protocol)
    return {
        "records": records,
        "groups": groups,
        "inner_rows": rows,
        "outer_slots": outer,
        "inner_evidence": inner_evidence,
        "auxiliary": auxiliary,
        "shared_nominal_inner_rows": duplicate_rows,
        "shared_nominal_outer_slots": duplicate_slots,
    }


def qualify_auxiliary(root: Path, protocol: Json) -> Json:
    evidence = {
        name: decode(checked(root, row)) for name, row in protocol["auxiliary"].items()
    }
    ring, analytical, clr, de = (
        evidence[k] for k in ("ring_support", "analytical", "clr", "de")
    )
    require(
        ring["approved"] is True
        and ring["source_derived_equivalence_admitted"] is True
        and ring["actual_exit"] == 0
        and ring["summary"]["equal_selected_covers"] == 39
        and ring["summary"]["nominal_probability_value_projections"] == 675
        and ring["summary"]["new_prediction_manifests_executed"] is False,
        "Exact conditional source-equivalence alias proof required",
    )
    require(
        analytical["approved"] is True
        and analytical["scientific_saved_products_admitted"] is True
        and analytical["summary"]["ring_dispositions"] == 78
        and analytical["summary"]["raw_closed_composition_rings"] == 0,
        "Actual analytical prerequisite failure required",
    )
    require(
        clr["approved"] is True
        and clr["scientific_saved_products_admitted"] is True
        and clr["summary"]["actual_expected_domain_refusals"] == 450
        and clr["summary"]["successful_ridge_solves"] == 0,
        "Actual CLR domain refusal required",
    )
    require(
        de["approved"] is True
        and de["scientific_saved_products_admitted"] is True
        and de["summary"]["requests"] == 39
        and de["summary"]["refused_rings"] == 78
        and de["summary"]["accepted_rings"] == 0,
        "Actual nonconverged DE prerequisite failure required",
    )
    require(
        evidence["de_execution"]["actual_exit"] == 0
        and evidence["de_source_review"]["approved"] is True
        and evidence["de_source_review"]["source_manifest_sha256"]
        == "6732cdae89752a7592e640e803798aeb2fb783b2ef8fbd7a6307b34505f802c2",
        "Independent DE observation execution/source approval required",
    )
    require(
        evidence["legacy"]["approved"] is True
        and evidence["legacy"]["summary"]["request_refusals"] == 39,
        "Legacy diagnostic exclusion evidence required",
    )
    return evidence


def outcomes(
    root: Path,
    protocol: Json,
    frozen: list[Json],
    eligible: Any,
    before_decode: Callable[[Json], None],
) -> Json:
    """Call only after fifteen chosen prediction/refusal hashes persist on disk."""
    all_scores: dict[tuple[str, str, str], Json] = {}
    dispositions: dict[tuple[str, str, str], Json] = {}
    for axis in protocol["axes"]:
        before_decode(axis["report"])
        report = decode(checked(root, axis["report"]))
        require(
            report["candidate_freeze"] == axis["candidate_freeze"],
            "Original report/freeze identity differs",
        )
        methods = axis["methods"]
        expected = {
            (method, baseline, target)
            for method in methods
            for baseline in protocol["baselines"]
            for target in protocol["records"]
        }
        seen_dispositions, seen_scores = set(), set()
        for row in report["candidate_dispositions"]:
            original_key = (row["method"], row["baseline"], row["outer_target"])
            require(
                original_key in expected and original_key not in seen_dispositions,
                "Unique exact saved outer disposition grid required",
            )
            seen_dispositions.add(original_key)
            key = (methods[row["method"]], row["baseline"], row["outer_target"])
            require(
                row["status"] in ("predicted", "refused"),
                "Unknown original outer disposition",
            )
            if key in dispositions:
                require(
                    dispositions[key] == row, "Shared nominal outer refusal differs"
                )
            dispositions[key] = row
        require(
            seen_dispositions == expected,
            "Complete original outer disposition population required",
        )
        for row in report["candidate_scores"]:
            original_key = (row["method"], row["baseline"], row["outer_target"])
            require(
                original_key in expected and original_key not in seen_scores,
                "Unique exact saved outer score identity required",
            )
            seen_scores.add(original_key)
            key = (methods[row["method"]], row["baseline"], row["outer_target"])
            require(
                eligible({"status": "scored", "metrics": row}),
                "Valid saved outer metric required",
            )
            if key in all_scores:
                require(all_scores[key] == row, "Shared nominal outer outcome differs")
            all_scores[key] = row
    require(
        len(dispositions) == 315
        and all(
            (key in all_scores) == (row["status"] == "predicted")
            for key, row in dispositions.items()
        ),
        "Complete physical outer failure/score population required",
    )
    selected = []
    for slot in frozen:
        pair = slot["selected_pair"]
        if pair is None or slot["status"] == "refused":
            selected.append(
                {
                    "outer_target": slot["outer_target"],
                    "status": "refused",
                    "metrics": None,
                }
            )
            continue
        key = (pair["source_candidate_id"], pair["spatial_id"], slot["outer_target"])
        require(
            key in all_scores, "Chosen frozen prediction has no admitted saved outcome"
        )
        selected.append(
            {
                "outer_target": slot["outer_target"],
                "selected_pair": pair,
                "status": "reused_saved_score",
                "original_score": all_scores[key],
            }
        )
    return {
        "selected": selected,
        "all_physical_candidate_scores": list(all_scores.values()),
        "all_physical_candidate_dispositions": list(dispositions.values()),
        "new_scoring_calls": 0,
        "scope": "Reuse independently admitted saved direct-pollen metrics after the new choice/prediction freeze; no target count object or model/scoring API is read or called.",
    }
