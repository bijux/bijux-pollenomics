"""Qualify captured dataset DOI attribution without inventing primary papers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit


DOMAIN = Path(__file__).resolve().parent
DATASETS = {1438: 1400, 53969: 39224, 53970: 39224}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dataset_locator(value: str) -> int | None:
    """Read an explicit native dataset locator, without proximity/name inference."""
    parsed = urlsplit(value if "://" in value else "https://" + value)
    if parsed.hostname == "data.neotomadb.org":
        pattern = r"/(?:datasets/)?(\d+)(?:/index\.html)?/?"
    elif parsed.hostname == "api.neotomadb.org":
        pattern = r"/(?:v\d+(?:\.\d+)?/)?(?:data/)?(?:downloads|datasets)/(\d+)/?"
    else:
        return None
    match = re.fullmatch(pattern, parsed.path)
    return int(match.group(1)) if match else None


def registration_account(
    attributes: dict[str, Any], request: dict[str, Any]
) -> dict[str, Any]:
    """Keep registration assertions, rights and bibliographic evidence separate."""
    doi = attributes.get("doi")
    if not isinstance(doi, str) or doi.casefold() != request["native_doi"].casefold():
        raise ValueError("Registered DOI differs from native requested identifier")
    url = attributes.get("url")
    if not isinstance(url, str) or dataset_locator(url) != request["dataset_id"]:
        raise ValueError("Registration landing locator differs from native dataset")
    return {
        "native_dataset_id": request["dataset_id"],
        "native_collection_unit_id": DATASETS[request["dataset_id"]],
        "native_doi": request["native_doi"],
        "registered_doi": doi,
        "registered_landing_url": url,
        "title_records": attributes.get("titles", []),
        "creator_records": attributes.get("creators", []),
        "registration_publication_year": attributes.get("publicationYear"),
        "registration_dates": attributes.get("dates", []),
        "source_rights_declarations": attributes.get("rightsList", []),
        "related_identifier_assertions": attributes.get("relatedIdentifiers", []),
        "primary_journal_publication_admitted": False,
        "source_year_interpreted_as_sample_date_or_BP_epoch": False,
        "linked_identifiers_establish_byte_identical_pollen_counts": False,
        "scope": "Exact dataset DOI/landing identity and provider attribution declarations. A metadata identity relation does not authenticate raw count bytes, historical selection or a primary journal paper.",
    }


def qualify(source_root: Path) -> dict[str, Any]:
    """Verify the actual retained capture before interpreting any source field."""
    source_root = source_root.resolve(strict=True)
    pins = json.loads((DOMAIN / "source-custody.json").read_text())
    for name, pin in pins.items():
        path = source_root / name
        if (
            path.is_symlink()
            or not path.is_file()
            or not path.resolve().is_relative_to(source_root)
            or path.stat().st_size != pin["bytes"]
            or sha(path) != pin["sha256"]
        ):
            raise ValueError("Captured source custody differs: " + name)

    def read(name: str) -> Any:
        return json.loads((source_root / name).read_text())

    terminal = read("terminal.json")
    if (
        terminal["status"] != "passed"
        or type(terminal["native_exit_code"]) is not int
        or terminal["native_exit_code"] != 0
        or terminal["plan_sha256"] != sha(source_root / "plan.json")
        or not terminal["source_inputs_before_after_unchanged"]
        or not terminal["runtime_binary_before_after_unchanged"]
    ):
        raise ValueError("Actual native capture terminal is unqualified")
    capture = read("native/capture-result.json")
    expected = read("request-inventory.json")
    records = capture["records"]
    by_id = {row["id"]: row for row in records}
    if len(by_id) != len(records) or set(by_id) != {row["id"] for row in expected}:
        raise ValueError("Finite capture route inventory differs")
    accounts = []
    publication_rows = []
    for request in expected:
        record = by_id[request["id"]]
        if record["url"] != request["url"] or record["http_status"] != 200:
            raise ValueError("Actual native route/status differs")
        name = "native/" + record["body_file"]
        if sha(source_root / name) != record["body_sha256"] or (
            terminal["outputs"][name]["sha256"] != record["body_sha256"]
        ):
            raise ValueError("Response body/terminal identity differs")
        payload = read(name)
        if "native_doi" in request:
            account = registration_account(payload["data"]["attributes"], request)
            account["source_response_sha256"] = record["body_sha256"]
            accounts.append(account)
        else:
            if payload["status"] != "success" or not isinstance(payload["data"], list):
                raise ValueError("Native publication relation shape differs")
            if payload["data"]:
                raise ValueError(
                    "Previously unresolved publication relation changed; require primary-source review"
                )
            previous = (
                source_root
                / "inputs"
                / ("dataset-" + str(request["dataset_id"]) + "-publications.response")
            )
            publication_rows.append(
                {
                    "native_dataset_id": request["dataset_id"],
                    "native_collection_unit_id": DATASETS[request["dataset_id"]],
                    "source_url": request["url"],
                    "current_publication_rows": len(payload["data"]),
                    "current_response_sha256": record["body_sha256"],
                    "current_body_byte_equal_to_retained_previous_response": sha(
                        previous
                    )
                    == record["body_sha256"],
                }
            )
    if len(accounts) != 6 or len(publication_rows) != 3:
        raise ValueError("Exact unresolved source population differs")
    baseline = read("inputs/current-attribution.json")
    return {
        "schema_version": "nordic-dataset-attribution-followthrough.v1",
        "candidate": terminal["candidate"],
        "capture_terminal_sha256": sha(source_root / "terminal.json"),
        "capture_plan_sha256": terminal["plan_sha256"],
        "native_capture_exit": terminal["native_exit_code"],
        "source_population": {
            "native_datasets": 3,
            "distinct_native_collection_units": 2,
            "registered_dataset_DOIs": 6,
        },
        "native_publication_relations": publication_rows,
        "dataset_registration_accounts": accounts,
        "common_panel_primary_publication_scope_counts": baseline[
            "current_primary_publication_scope_counts"
        ],
        "baseline_primary_counts_changed": False,
        "new_primary_journal_publications_admitted": 0,
        "source_context": "All six exact DOI records bind the intended native dataset and retain creator, title, related identifiers, rights and registration-date declarations. All three native publication responses remain empty. Two Stentjärn datasets share collection unit 39224 and are not extra independent cores.",
        "scientific_limits": "Provider dataset-specific license declarations supplement current public analytical-use attribution. They do not authenticate historical workbook/private author-copy rights, original source revision, counted grain universe, chronology, basin geometry, qualified review or reproduction. DOI registration/publication years are provenance, not sample ages or age-reference epochs. Local Contexts notices remain alongside license declarations.",
        "next_source_resolution": "Obtain an explicit original-paper/reference association or source-owner declaration of unpublished status for dataset 1438 and datasets 53969/53970. Retain dataset DOI/creator/EPD credit meanwhile; no invented primary paper or correspondence is substituted.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = qualify(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
