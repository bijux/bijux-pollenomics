"""Independently join exact raw metadata to both genuine maintained publications."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve(strict=True) or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Physical absolute controller entry and ancestors required")
_entry_directory = _entry_path.parent
_expected_python = {
    "common_runner.py",
    "prepare.py",
    "run.py",
    "runtime_contracts.py",
    "check_contracts.py",
    "runtime_guarded_runner.py",
    "source_runtime.py",
    "observe.py",
    "execute_source.py",
    "contracts.py",
    "metadata.py",
}
_present_python = set()
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry before helper import")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory before helper import")
    if _entry.suffix in {".py", ".pyc", ".so", ".dylib", ".pyd"}:
        if _entry.name not in _expected_python:
            raise ValueError("Unexpected controller import before helper import")
        _present_python.add(_entry.name)
if _present_python != _expected_python:
    raise ValueError("Incomplete exact controller import namespace")
sys.path.insert(0, str(_entry_directory))
import contracts as c  # noqa: E402
import metadata as m  # noqa: E402


def provider_responses(record: dict[str, Any]) -> dict[int, bytes]:
    root = Path(record["root"])
    responses = {}
    for row in record["members"]:
        path = Path(row["path"])
        if path.name == "capture-manifest.json":
            continue
        relative = path.relative_to(root).as_posix()
        match = re.fullmatch(
            r"responses/dataset-([0-9]+)-publications[.]json", relative
        )
        c.require(match is not None, "Unknown provider response locator")
        assert match is not None
        token = int(match.group(1))
        c.require(token not in responses and token > 0, "Duplicate provider source ID")
        raw = path.read_bytes()
        c.require(c.pin(path) == row, "Root-authenticated provider raw bytes changed")
        m.provider_links(token, raw)
        responses[token] = raw
    return responses


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = c.load(args.plan)
    c.verify_inputs(plan)
    output = Path(plan["output"])
    c.require(
        plan["stage2_repository_view"] == str(output / "producer")
        and c.exact(
            plan["stage2_input_roles"],
            {
                "generated_attribution": str(
                    output / "producer" / c.REPORT / "report.json"
                ),
                "canonical_comparison_only": str(c.ROOT / c.REPORT / "report.json"),
            },
        ),
        "Stage2 generated/canonical input roles differ",
    )
    progress = c.load(output / "stage-progress.json")
    m.native_progress(progress, plan["stages"][:2])
    for actual, expected in zip(progress, plan["stages"][:2], strict=True):
        c.require(
            actual["id"] == expected["id"]
            and actual["argv"] == expected["argv"]
            and type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Maintained native stage binding/status differs",
        )
        for stream in ("stdout", "stderr"):
            c.require(
                c.sha(Path(actual[stream])) == actual[stream + "_sha256"],
                "Actual stage stream changed",
            )
    source_records = {}
    observed_origins = set()
    for kind in ("publication", "doi"):
        record = c.load(output / (kind + "-source-execution.json"))
        c.require(record["kind"] == kind, "Source receipt kind differs")
        stage = plan["stages"][0 if kind == "publication" else 1]
        c.require(
            record["actual_launcher_argv"] == [stage["argv"][0], *stage["argv"][3:]],
            "Source receipt actual launcher argv differs",
        )
        c.require(
            record["candidate"] == plan["candidate"]
            and c.exact(record["plan"], c.pin(args.plan))
            and c.exact(record["source"], plan["maintained_sources"][kind]),
            "Actual maintained source receipt binding differs",
        )
        c.require(
            type(record["source_exit"]) is int
            and record["source_exit"] == 0
            and type(record["metadata_exit"]) is int
            and record["metadata_exit"] == 0
            and record["metadata_error"] is None,
            "Native/source-metadata exits differ",
        )
        c.require(
            c.exact(
                record["counters"],
                {"LRA_implementation_function_calls": 0, "network_attempts": 0},
            ),
            "Source metadata crossed LRA/network boundary",
        )
        repository = c.ROOT if kind == "publication" else output / "producer"
        destination = (
            output
            / "producer"
            / c.REPORT
            / ("report.json" if kind == "publication" else "doi-review.json")
        )
        expected_argv = [
            str(c.ROOT / c.PRODUCERS[kind]),
            "--repository",
            str(repository),
            "--capture-root",
            plan["capture_sets"][kind]["root"],
            "--output",
            str(destination),
        ]
        c.require(
            record["executed_source_argv"] == expected_argv
            and c.exact(record["produced"], c.pin(destination)),
            "Actual maintained CLI/output differs",
        )
        if kind == "doi":
            c.require(
                c.exact(
                    record["stage2_generated_input"],
                    c.pin(output / "producer" / c.REPORT / "report.json"),
                ),
                "DOI source did not consume actual stage1 output",
            )
        else:
            c.require(
                record["stage2_generated_input"] is None,
                "Publication source input role differs",
            )
        pins = {row["path"]: row for row in plan["input_pins"]}
        c.require(
            record["first_party_origins"], "No observed maintained source origins"
        )
        for row in record["first_party_origins"]:
            native = {key: row[key] for key in ("path", "sha256", "bytes")}
            c.require(
                c.pin(Path(row["path"])) == native and pins.get(row["path"]) == native,
                "Observed first-party source origin changed",
            )
            observed_origins.add(row["path"])
        source_records[kind] = c.pin(output / (kind + "-source-execution.json"))
    current = provider_responses(plan["capture_sets"]["publication"])
    older = provider_responses(plan["capture_sets"]["older_publication"])
    c.require(
        len(current) == 169 and len(older) == 58,
        "Distinct provider capture populations differ",
    )
    publication_root = Path(plan["capture_sets"]["publication"]["root"])
    expected_publication = m.expected_publication(
        (c.ROOT / c.ENTITY).read_bytes(),
        (c.ROOT / c.DATASETS).read_bytes(),
        (c.ROOT / c.POLICY_REVIEW).read_bytes(),
        (publication_root / "capture-manifest.json").read_bytes(),
        current,
    )
    publication_file = output / "producer" / c.REPORT / "report.json"
    publication_raw = publication_file.read_bytes()
    c.require(
        m.exact(m.object_bytes(publication_raw), expected_publication),
        "Independent complete provider/source projection differs",
    )
    doi_root = Path(plan["capture_sets"]["doi"]["root"])
    doi_responses = {}
    for row in plan["capture_sets"]["doi"]["members"]:
        path = Path(row["path"])
        if path.name == "capture-manifest.json":
            continue
        relative = path.relative_to(doi_root).as_posix()
        c.require(
            re.fullmatch(r"responses/dataset-[0-9]+-doi-[12][.]json", relative)
            is not None
            and relative not in doi_responses,
            "Unknown/duplicate DataCite response locator",
        )
        c.require(c.pin(path) == row, "Root-authenticated DataCite raw bytes changed")
        doi_responses[relative] = path.read_bytes()
    c.require(len(doi_responses) == 26, "Exact26DataCite responses required")
    expected_doi = m.expected_doi(
        expected_publication,
        publication_raw,
        (doi_root / "capture-manifest.json").read_bytes(),
        doi_responses,
    )
    doi_file = output / "producer" / c.REPORT / "doi-review.json"
    c.require(
        m.exact(m.object_bytes(doi_file.read_bytes()), expected_doi),
        "Independent complete DOI/titles/landing/relations projection differs",
    )
    comparisons = []
    for name in ("report.json", "doi-review.json"):
        generated = output / "producer" / c.REPORT / name
        governed = c.ROOT / c.REPORT / name
        same_bytes = generated.read_bytes() == governed.read_bytes()
        same_values = m.exact(
            m.object_bytes(generated.read_bytes()),
            m.object_bytes(governed.read_bytes()),
        )
        comparisons.append(
            {
                "governed": c.pin(governed),
                "generated": c.pin(generated),
                "whole_byte_checker_exit": 0 if same_bytes else 2,
                "complete_ordered_typed_values_equal": same_values,
            }
        )
        c.require(
            same_bytes and same_values,
            "Current governed report bytes or full typed values differ",
        )
    c.verify_inputs(plan)
    overlap = set(current) & set(older)
    report = {
        "schema_version": "neotoma-current-publication-independent-review.v1",
        "actual_exit": 0,
        "candidate": plan["candidate"],
        "plan": c.pin(args.plan),
        "actual_maintained_stages": progress,
        "source_execution_receipts": source_records,
        "complete_provider_response_counts": {
            "current": len(current),
            "older_separate_epoch": len(older),
        },
        "DataCite_response_count": len(doi_responses),
        "current_older_overlapping_dataset_IDs": len(overlap),
        "overlap_raw_bytes_equal": sum(current[key] == older[key] for key in overlap),
        "overlap_complete_publication_projection_equal": sum(
            m.exact(
                m.provider_links(key, current[key]), m.provider_links(key, older[key])
            )
            for key in overlap
        ),
        "used_datasets": expected_publication["used_dataset_count"],
        "provider_publication_status_counts": expected_publication[
            "provider_publication_status_counts"
        ],
        "dataset_doi_status_counts": expected_publication["dataset_doi_status_counts"],
        "country_denominators": expected_publication["country_denominators"],
        "reviewed_DOI_pairs": expected_doi["reviewed_dataset_count"],
        "doi_pair_status_counts": expected_doi["doi_pair_status_counts"],
        "full_provider_source_field_order_and_native_values_checked": True,
        "all_DataCite_titles_landing_URLs_versions_relations_checked": True,
        "whole_product_comparisons": comparisons,
        "observed_first_party_source_origins": len(observed_origins),
        "original_acquisition_predecessor_06f08e_authenticated": False,
        "fresh_HTTP_or_rights_or_citation_selection_or_human_or_untouched_admission": False,
        "publication_ready": False,
        "lra_accepted_samples": 0,
    }
    c.dump(output / "independent-publication-review.json", report)
    print(
        json.dumps(
            {
                "actual_exit": 0,
                "independent_review": c.pin(
                    output / "independent-publication-review.json"
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
