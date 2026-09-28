"""Measure literal LandClim parameter-name mass in Swedish source pollen bins."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

PARAMETERS = Path(
    "docs/report/source-relations/neotoma/parameter-candidates/report.json"
)
POLLEN = Path("docs/report/pollen-reconstruction/swedish-direct-pollen")
DATASETS = ("19913", "53995", "54001")


def _identity(path: Path, repository: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(repository).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _csv_text(rows: list[dict[str, object]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def publish(repository: Path, output: Path) -> dict[str, object]:
    """Preserve native NISP denominators and unapproved literal-name leads."""
    repository = repository.resolve()
    parameter_path = repository / PARAMETERS
    config_path = repository / POLLEN / "config.json"
    exclusion_path = repository / POLLEN / "exclusions.csv"
    parameters = json.loads(parameter_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if (
        parameters["parameter_row_count"] != 31
        or parameters["exact_name_parameter_count"] != 20
        or parameters["lra_accepted_samples"] != 0
        or parameters["scientific_admission_allowed"] is not False
        or config["common_age_bin_ids"] != list(range(-1, 12))
        or set(config["sites"]) != set(DATASETS)
    ):
        raise ValueError("Parameter or Swedish pollen scope changed")

    literal_names: set[str] = set()
    for parameter in parameters["rows"]:
        if parameter["literal_name_match_status"] != "exact_unreviewed_candidate":
            continue
        if any(
            concept["source_unit"] == "NISP"
            and concept["review_state"] == "needs_discussion"
            for concept in parameter["source_concepts"]
        ):
            literal_names.add(parameter["parameter_source_name"])
    if len(literal_names) != 20:
        raise ValueError("Native NISP literal parameter set changed")

    excluded: dict[tuple[str, int], Counter[str]] = defaultdict(Counter)
    with exclusion_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            dataset = row["dataset_id"]
            if dataset not in DATASETS:
                raise ValueError("Unexpected Swedish dataset in excluded pollen")
            count = int(row["excluded_nisp_count"])
            if count < 0:
                raise ValueError("Negative native pollen count")
            excluded[(dataset, int(row["age_bin_index"]))][row["taxon_native"]] += count

    rows: list[dict[str, object]] = []
    site_rows: list[dict[str, object]] = []
    inputs = [
        _identity(parameter_path, repository),
        _identity(config_path, repository),
        _identity(exclusion_path, repository),
    ]
    for dataset in DATASETS:
        prepared_path = repository / POLLEN / "prepared" / f"dataset-{dataset}.json"
        inputs.append(_identity(prepared_path, repository))
        prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
        if (
            str(prepared["dataset_id"]) != dataset
            or str(prepared["site_id"]) != config["sites"][dataset]["site_id"]
        ):
            raise ValueError("Prepared Swedish pollen site identity changed")
        total = matched = shared = 0
        unmatched: Counter[str] = Counter()
        for index in config["common_age_bin_ids"]:
            native: Counter[str] = Counter(prepared["bins"][str(index)]["counts"])
            native.update(excluded[(dataset, index)])
            bin_row = prepared["bins"][str(index)]
            denominator = int(bin_row["all_nisp_count"])
            if sum(native.values()) != denominator or denominator <= 0:
                raise ValueError("Swedish native pollen bin does not close")
            candidate_count = sum(
                count for name, count in native.items() if name in literal_names
            )
            shared_count = int(bin_row["closed_nisp_count"])
            if shared_count != sum(bin_row["counts"].values()):
                raise ValueError("Swedish direct-pollen subcomposition changed")
            unmatched.update(
                {
                    name: count
                    for name, count in native.items()
                    if name not in literal_names
                }
            )
            rows.append(
                {
                    "dataset_id": dataset,
                    "site_id": prepared["site_id"],
                    "site": prepared["site"],
                    "age_bin_index": index,
                    "younger_cal_bp": index * 500,
                    "older_cal_bp_exclusive": (index + 1) * 500,
                    "all_native_nisp": denominator,
                    "literal_parameter_name_nisp": candidate_count,
                    "unmatched_name_nisp": denominator - candidate_count,
                    "literal_parameter_name_fraction": round(
                        candidate_count / denominator, 6
                    ),
                    "direct_16_taxon_nisp": shared_count,
                    "direct_16_taxon_fraction": round(shared_count / denominator, 6),
                    "lra_admitted": False,
                }
            )
            total += denominator
            matched += candidate_count
            shared += shared_count
        site_rows.append(
            {
                "dataset_id": dataset,
                "site_id": prepared["site_id"],
                "site": prepared["site"],
                "common_bin_count": 13,
                "all_native_nisp": total,
                "literal_parameter_name_nisp": matched,
                "literal_parameter_name_fraction": round(matched / total, 6),
                "direct_16_taxon_nisp": shared,
                "direct_16_taxon_fraction": round(shared / total, 6),
                "leading_unmatched_native_names": [
                    {"name": name, "count": count}
                    for name, count in sorted(
                        unmatched.items(), key=lambda item: (-item[1], item[0])
                    )[:10]
                ],
            }
        )
    if len(rows) != 39:
        raise ValueError("Swedish common-bin screen is incomplete")
    csv_text = _csv_text(rows)
    report: dict[str, Any] = {
        "schema_version": "swedish-neotoma-parameter-mass.v1",
        "source_role": "literal_name_candidate_screen",
        "count_unit": "native_NISP",
        "denominator": "all native NISP pollen counts in each source age bin",
        "candidate_parameter_name_count": len(literal_names),
        "common_bin_count": len(rows),
        "site_count": len(site_rows),
        "lra_admitted_samples": 0,
        "scientific_admission_allowed": False,
        "interpretation": (
            "Exact text equality is an unreviewed lead, not taxon equivalence, "
            "PPE/FSP applicability, complete pollen denominator or LRA admission. "
            "The prior-exposed direct-pollen 16-taxon response is a separate subcomposition."
        ),
        "sites": site_rows,
        "inputs": inputs,
        "bins_csv_sha256": hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "bins.csv").write_text(csv_text, encoding="utf-8")
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = publish(args.repository, args.output)
    print(
        f"{report['common_bin_count']} Swedish pollen bins retain literal "
        "parameter-name mass without LRA admission"
    )


if __name__ == "__main__":
    main()
