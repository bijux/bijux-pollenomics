"""Validate source-bound field questions without conferring field authority."""

from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

LEADS = {
    "finjasjon": "Finjasjön",
    "ostra-ringsjon": "Östra Ringsjön",
    "havgardssjon": "Havgårdssjön",
    "bjaresjosjon": "Bjäresjösjön",
    "uppakra-lund": "Uppåkra/Lund",
}
THEMES = {
    "identity",
    "basin-and-sediment",
    "access",
    "landowner",
    "permits",
    "conservation-and-heritage",
    "hazards",
    "field-decision",
}
SOURCES = {
    "docs/report/countries/sweden/sweden_land_use_synthesis_v66.json",
    "docs/report/countries/sweden/sweden_lake_fieldwork_preparation_v66.json",
    "docs/report/countries/sweden/sweden_lake_evidence_richness_v66.json",
    "reports/science/bjaresjo-context/report.json",
    "reports/needed/source-requests.csv",
    "reports/needed/scientific-review.csv",
}
DECISIONS = {
    "not_received",
    "accepted_scoped",
    "accepted_with_conditions",
    "refused",
    "deferred_for_source",
}


def _file(root: Path, relative: str) -> Path:
    native = PurePosixPath(relative)
    path = root / relative
    if (
        native.is_absolute()
        or ".." in native.parts
        or "\\" in relative
        or not native.parts
        or str(native) != relative
        or not path.is_file()
        or not path.resolve().is_relative_to(root.resolve())
        or any(
            parent.is_symlink()
            for parent in [path, *path.parents]
            if parent != root.parent
        )
    ):
        raise ValueError("Field evidence path is unavailable or unsafe")
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _decision(root: Path, question: dict[str, Any]) -> None:
    status = question["decision_status"]
    if status not in DECISIONS or question["request_status"] not in {"unsent", "sent"}:
        raise ValueError("Unknown field request or decision state")
    if status == "not_received":
        if question["reviewer_assignment"] != "unassigned" or any(
            question[key] is not None
            for key in ["decision_date", "decision_evidence", "returned_fact"]
        ):
            raise ValueError("Unreceived field question contains a decision")
        return
    if question["reviewer_assignment"] in {"unassigned", "none", ""}:
        raise ValueError("Received field decision has no named resolver")
    if not isinstance(question["decision_date"], str):
        raise ValueError("Received field decision has no date")
    date.fromisoformat(question["decision_date"])
    evidence = question["decision_evidence"]
    if not isinstance(evidence, dict) or set(evidence) != {
        "path",
        "sha256",
        "resolver_qualification",
        "decision_scope",
        "remaining_conditions",
    }:
        raise ValueError("Returned field evidence is incomplete")
    if not all(_text(evidence[key]) for key in evidence):
        raise ValueError("Returned field evidence lacks scope or qualification")
    if _digest(_file(root, evidence["path"])) != evidence["sha256"] or not _text(
        question["returned_fact"]
    ):
        raise ValueError("Returned field fact is not bound to physical evidence")


def validate(root: Path, record: dict[str, Any]) -> dict[str, int]:
    """Check record custody and completeness; acceptance still needs reviewers."""
    expected_fields = {
        "schema_version",
        "prepared_on",
        "fact_observation_date",
        "scope",
        "current_governed_candidate_count",
        "current_candidate_refusal",
        "source_pins",
        "preserved_registers",
        "leads",
        "questions",
        "decision_import_boundary",
    }
    if set(record) != expected_fields:
        raise ValueError("Named field record fields differ")
    if record.get("schema_version") != "swedish-named-field-questions.v1":
        raise ValueError("Unknown named field question schema")
    date.fromisoformat(record["prepared_on"])
    if record["fact_observation_date"] is not None:
        raise ValueError("A preparation date cannot become a field observation")
    pins = record["source_pins"]
    if (
        not isinstance(pins, list)
        or len(pins) != len(SOURCES)
        or {pin["path"] for pin in pins} != SOURCES
    ):
        raise ValueError("Field source population differs")
    for pin in pins:
        if (
            set(pin) != {"path", "sha256"}
            or _digest(_file(root, pin["path"])) != pin["sha256"]
        ):
            raise ValueError("Field source bytes changed")
    synthesis = json.loads(
        _file(
            root, "docs/report/countries/sweden/sweden_land_use_synthesis_v66.json"
        ).read_text()
    )
    preparation = json.loads(
        _file(
            root,
            "docs/report/countries/sweden/sweden_lake_fieldwork_preparation_v66.json",
        ).read_text()
    )
    ranking = json.loads(
        _file(
            root, "docs/report/countries/sweden/sweden_lake_evidence_richness_v66.json"
        ).read_text()
    )
    if (
        preparation["row_count"] != 0
        or preparation["rows"]
        or ranking["candidate_count"] != 0
        or ranking["methodology"]["refusal_reason"] != "governing_svar_registry_missing"
    ):
        raise ValueError("Current candidate posture changed; review the field dossier")
    if (
        record["current_governed_candidate_count"] != 0
        or record["current_candidate_refusal"] != "governing_svar_registry_missing"
    ):
        raise ValueError("A named lead cannot become an admitted candidate")
    expected_registers = {
        "reports/needed/source-requests.csv": {
            "row_count": 18,
            "request_status": "unsent",
        },
        "reports/needed/scientific-review.csv": {
            "row_count": 36,
            "review_decision": "not_received",
        },
    }
    if record["preserved_registers"] != expected_registers:
        raise ValueError("Preserved register accounting differs")
    leads = record["leads"]
    if len(leads) != 5 or {lead["lead_id"] for lead in leads} != set(LEADS):
        raise ValueError("Named field lead population differs")
    identities: dict[str, Any] = {}
    for lead in leads:
        if (
            lead["requested_name"] != LEADS[lead["lead_id"]]
            or lead["rank"] is not None
            or lead["governed_field_candidate"] is not False
            or lead["selection_status"] != "unranked_user_lead"
            or lead["field_decision"] != "not_received"
        ):
            raise ValueError("Field lead has unsupported ranking or decision")
        identity = lead["modern_reference"]
        if lead["lead_id"] == "uppakra-lund":
            if (
                any(
                    identity[key] is not None
                    for key in [
                        "source_path",
                        "json_pointer",
                        "retained_registry_id",
                        "retained_registry_name",
                        "source_url",
                    ]
                )
                or identity["identity_status"] != "physical_study_object_unresolved"
            ):
                raise ValueError("Uppåkra/Lund identity is unresolved")
        else:
            matches = [
                (index, row)
                for index, row in enumerate(synthesis["target_decisions"])
                if row["requested_name"] == lead["requested_name"]
            ]
            if len(matches) != 1:
                raise ValueError("Named modern reference is not unique")
            index, native = matches[0]
            expected = {
                "source_path": "docs/report/countries/sweden/sweden_land_use_synthesis_v66.json",
                "json_pointer": f"/target_decisions/{index}",
                "retained_registry_id": native["registry_id"],
                "retained_registry_name": native["registry_name"],
                "source_url": native["source_url"],
                "identity_status": "retained_modern_reference_only",
                "physical_core_identity": "not_established",
            }
            if identity != expected:
                raise ValueError("Retained modern source identity differs")
        if identity["physical_core_identity"] != "not_established":
            raise ValueError("Modern identity cannot establish a pollen core")
        identities[lead["lead_id"]] = identity
    questions = record["questions"]
    expected_pairs = {(lead, theme) for lead in LEADS for theme in THEMES}
    if (
        len(questions) != 40
        or {(q["lead_id"], q["theme"]) for q in questions} != expected_pairs
        or len({q["question_id"] for q in questions}) != 40
    ):
        raise ValueError("Individual field question coverage differs")
    for question in questions:
        if (
            question["question_id"]
            != f"field-{question['lead_id']}-{question['theme']}"
            or question["source_identity"] != identities[question["lead_id"]]
        ):
            raise ValueError("Field question identity differs")
        if not all(
            _text(question[key])
            for key in [
                "requested_fact",
                "responsible_external_resolver",
                "reopening_condition",
                "scope_limit",
            ]
        ):
            raise ValueError(
                "Field question lacks fact, resolver or reopening condition"
            )
        _decision(root, question)
    for relative, field, value, count in [
        ("reports/needed/source-requests.csv", "status", "unsent", 18),
        ("reports/needed/scientific-review.csv", "review_decision", "not_received", 36),
    ]:
        with _file(root, relative).open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != count or any(row[field] != value for row in rows):
            raise ValueError(
                "Existing source/review posture changed; review exact replies"
            )
    return {
        "named_leads": 5,
        "questions": 40,
        "received_field_records": sum(
            q["decision_status"] != "not_received" for q in questions
        ),
        "governed_candidates": 0,
    }


def main(argv: list[str] | None = None) -> None:
    """Read a bounded field-question dossier without changing any source."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--questions", type=Path, required=True)
    args = parser.parse_args(argv)
    record = json.loads(args.questions.read_text())
    print(json.dumps(validate(args.repository.resolve(), record), sort_keys=True))


if __name__ == "__main__":
    main()
