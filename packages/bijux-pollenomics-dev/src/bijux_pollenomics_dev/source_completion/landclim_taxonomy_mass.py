"""Measure Swedish native pollen counts against the authors' taxonomy lookup."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from .neotoma_parameter_mass import DATASETS, POLLEN, _identity

LOOKUP = Path("author/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv")
LOOKUP_SHA256 = "3a745f9b7606e5d0b59feaba2683b930c8d3990e4810f8217b69160a29a1b507"
EXCLUDED_TARGETS = frozenset({"zz.do not use", "aage.cal.BP"})
SIZE_VARIANT_CANDIDATES = {
    "Poaceae undiff. (<40 µm)": ("Poaceae undiff. <40um", "Poaceae"),
    "Poaceae undiff. (>40 µm)": ("Poaceae undiff. >40um", "Cerealia-t"),
}


def _lookup(path: Path) -> tuple[dict[str, str], int]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LOOKUP_SHA256:
        raise ValueError("LandClim author taxonomy lookup identity changed")
    rows = list(csv.DictReader(io.StringIO(raw.decode("latin-1"))))
    if len(rows) != 10788 or not rows or set(rows[0]) != {"oldvar", "RPP.LANDCLIMII"}:
        raise ValueError("LandClim author taxonomy lookup schema changed")
    mapping: dict[str, str] = {}
    for row in rows:
        source, target = row["oldvar"], row["RPP.LANDCLIMII"]
        if (
            not source
            or not target
            or (source in mapping and mapping[source] != target)
        ):
            raise ValueError("Ambiguous author taxonomy source name")
        mapping[source] = target
    if len(mapping) != 9731 or len(set(mapping.values()) - EXCLUDED_TARGETS) != 31:
        raise ValueError("LandClim author taxonomy target universe changed")
    return mapping, len(rows)


def _csv_text(rows: list[dict[str, object]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def publish(repository: Path, author_source_root: Path, output: Path) -> dict[str, Any]:
    """Retain author-assigned name mass without asserting numerical LRA admission."""
    repository = repository.resolve()
    lookup_path = author_source_root.resolve() / LOOKUP
    mapping, source_row_count = _lookup(lookup_path)
    for source_name, (witness_name, witness_target) in SIZE_VARIANT_CANDIDATES.items():
        if source_name in mapping or mapping.get(witness_name) != witness_target:
            raise ValueError("Author size-variant witness changed")
    config_path = repository / POLLEN / "config.json"
    exclusion_path = repository / POLLEN / "exclusions.csv"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["common_age_bin_ids"] != list(range(-1, 12)) or set(
        config["sites"]
    ) != set(DATASETS):
        raise ValueError("Swedish native pollen scope changed")

    excluded: dict[tuple[str, int], Counter[str]] = defaultdict(Counter)
    with exclusion_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            dataset = row["dataset_id"]
            if dataset not in DATASETS or int(row["excluded_nisp_count"]) < 0:
                raise ValueError("Unexpected Swedish source exclusion")
            excluded[(dataset, int(row["age_bin_index"]))][row["taxon_native"]] += int(
                row["excluded_nisp_count"]
            )

    inputs: list[dict[str, object]] = [
        {
            "source_root_role": "external_landclim_author_reference",
            "path": LOOKUP.as_posix(),
            "bytes": lookup_path.stat().st_size,
            "sha256": LOOKUP_SHA256,
        },
        _identity(config_path, repository),
        _identity(exclusion_path, repository),
    ]
    bins: list[dict[str, object]] = []
    sites: list[dict[str, object]] = []
    for dataset in DATASETS:
        prepared_path = repository / POLLEN / "prepared" / f"dataset-{dataset}.json"
        inputs.append(_identity(prepared_path, repository))
        prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
        if str(prepared["dataset_id"]) != dataset or str(prepared["site_id"]) != str(
            config["sites"][dataset]["site_id"]
        ):
            raise ValueError("Prepared Swedish pollen identity changed")
        totals: Counter[str] = Counter()
        targets: Counter[str] = Counter()
        size_variant_targets: Counter[str] = Counter()
        missing: Counter[str] = Counter()
        rejected: Counter[str] = Counter()
        for index in config["common_age_bin_ids"]:
            bin_source = prepared["bins"][str(index)]
            native: Counter[str] = Counter(bin_source["counts"])
            native.update(excluded[(dataset, index)])
            denominator = int(bin_source["all_nisp_count"])
            if sum(native.values()) != denominator or denominator <= 0:
                raise ValueError("Swedish native pollen bin does not close")
            status: Counter[str] = Counter()
            for name, count in native.items():
                target = mapping.get(name)
                if target is None:
                    status["unmapped"] += count
                    missing[name] += count
                    if name in SIZE_VARIANT_CANDIDATES:
                        status["size_variant_candidate"] += count
                        size_variant_targets[SIZE_VARIANT_CANDIDATES[name][1]] += count
                elif target in EXCLUDED_TARGETS:
                    status["author_excluded"] += count
                    rejected[name] += count
                else:
                    status["author_assigned"] += count
                    targets[target] += count
            if (
                status["author_assigned"]
                + status["author_excluded"]
                + status["unmapped"]
                != denominator
                or status["size_variant_candidate"] > status["unmapped"]
            ):
                raise ValueError("Swedish author taxonomy mass does not close")
            bins.append(
                {
                    "dataset_id": dataset,
                    "site_id": prepared["site_id"],
                    "site": prepared["site"],
                    "age_bin_index": index,
                    "all_native_nisp": denominator,
                    "author_assigned_nisp": status["author_assigned"],
                    "author_excluded_nisp": status["author_excluded"],
                    "unmapped_nisp": status["unmapped"],
                    "size_variant_candidate_nisp": status["size_variant_candidate"],
                    "author_assigned_fraction": round(
                        status["author_assigned"] / denominator, 6
                    ),
                    "lra_admitted": False,
                }
            )
            totals.update(status)
        total = (
            totals["author_assigned"] + totals["author_excluded"] + totals["unmapped"]
        )
        sites.append(
            {
                "dataset_id": dataset,
                "site_id": prepared["site_id"],
                "site": prepared["site"],
                "all_native_nisp": total,
                "author_assigned_nisp": totals["author_assigned"],
                "author_excluded_nisp": totals["author_excluded"],
                "unmapped_nisp": totals["unmapped"],
                "size_variant_candidate_nisp": totals["size_variant_candidate"],
                "size_variant_candidate_targets": dict(
                    sorted(size_variant_targets.items())
                ),
                "assigned_plus_size_candidate_fraction": round(
                    (totals["author_assigned"] + totals["size_variant_candidate"])
                    / total,
                    6,
                ),
                "author_assigned_fraction": round(totals["author_assigned"] / total, 6),
                "author_target_counts": dict(sorted(targets.items())),
                "leading_unmapped_names": [
                    {"name": name, "count": count}
                    for name, count in sorted(
                        missing.items(), key=lambda item: (-item[1], item[0])
                    )[:10]
                ],
                "leading_author_excluded_names": [
                    {"name": name, "count": count}
                    for name, count in sorted(
                        rejected.items(), key=lambda item: (-item[1], item[0])
                    )[:10]
                ],
            }
        )
    if len(bins) != 39:
        raise ValueError("Swedish author taxonomy screen is incomplete")
    csv_text = _csv_text(bins)
    report: dict[str, Any] = {
        "schema_version": "swedish-neotoma-landclim-author-taxonomy-mass.v1",
        "source_role": "author_lookup_candidate_screen",
        "source_lookup_rows": source_row_count,
        "source_lookup_distinct_names": len(mapping),
        "source_lookup_nonexcluded_targets": 31,
        "size_variant_candidates": [
            {
                "native_name": name,
                "author_witness_name": witness,
                "witness_target": target,
                "disposition": "source_witnessed_candidate_not_applied",
            }
            for name, (witness, target) in SIZE_VARIANT_CANDIDATES.items()
        ],
        "count_unit": "native_NISP",
        "common_bin_count": len(bins),
        "site_count": len(sites),
        "lra_admitted_samples": 0,
        "scientific_admission_allowed": False,
        "interpretation": (
            "Author lookup assignments preserve source-name and exclusion decisions. "
            "Two size-qualified BUS names have separate author-witnessed candidate "
            "targets; their counts remain in unmapped mass and are not applied. "
            "The screen does not establish a matched core, sample-time basin "
            "geometry, or LRA admission."
        ),
        "sites": sites,
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
    parser.add_argument("--author-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = publish(args.repository, args.author_source_root, args.output)
    print(f"{report['common_bin_count']} Swedish bins matched to author lookup targets")


if __name__ == "__main__":
    main()
