"""Compare the primary Solsø 1981 pollen profile with Neotoma source rows."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

SOURCE = Path("landclim/pangaea/solsoe/solsoe81-pollen-739834.txt")
SOURCE_SHA256 = "da790080493ccfe7e37ab16d154e438cfbeb7b0046bc41d7f24499572a0353d0"
DOI = "10.1594/PANGAEA.739834"
RELATIONAL = Path("data/neotoma/relational")
UNIT = "neotoma:collection-unit:4303"
SITE = "neotoma:site:3432"
PARAMETER = re.compile(r"^\t(.+?) \[#\] \(([^)]+)\) \* PI:")


def _identity(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data).hexdigest(),
    }


def _primary(data: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = data.decode("utf-8")
    if (
        DOI not in text
        or "Event(s):\tSOLSOE81" not in text
        or "Area: 2.5 ha." not in text
        or "Creative Commons Attribution-NonCommercial 3.0 Unported" not in text
        or "*/\n" not in text
    ):
        raise ValueError("Primary Solsø pollen citation, core or rights changed")
    metadata, table = text.split("*/\n", 1)
    parameters = [
        match.groups()
        for line in metadata.splitlines()
        if (match := PARAMETER.match(line)) is not None
    ]
    rows = list(csv.DictReader(table.splitlines(), delimiter="\t"))
    if len(parameters) != 147 or len(rows) != 66 or not rows:
        raise ValueError("Primary Solsø pollen dimensions changed")
    headers = list(rows[0])
    if (
        headers[0] != "Depth sed [m]"
        or len(headers) != 148
        or len({name for name, _ in parameters}) != 147
        or any(
            not header.startswith(short + " [#]")
            for header, (_, short) in zip(headers[1:], parameters, strict=True)
        )
    ):
        raise ValueError("Primary Solsø parameter or column order changed")
    depths = [Decimal(row[headers[0]]) * 100 for row in rows]
    if len(set(depths)) != 66 or any(value != int(value) for value in depths):
        raise ValueError("Primary Solsø sample depth is not unique centimetres")
    for row in rows:
        if any(not value.isdigit() for value in list(row.values())[1:]):
            raise ValueError("Primary Solsø pollen values must be integer counts")
    return [name for name, _ in parameters], rows


def _surface(
    repository: Path,
    manifest: dict[str, Any],
    surface: str,
    *,
    sample_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, object]]]:
    rows: list[dict[str, Any]] = []
    identities: list[dict[str, object]] = []
    for part in manifest["surfaces"][surface]["parts"]:
        path = repository / RELATIONAL / part["path"]
        raw = path.read_bytes()
        digest = sha256(raw).hexdigest()
        if digest != part["sha256"]:
            raise ValueError(f"Neotoma {surface} part hash differs from manifest")
        document = json.loads(raw)
        if len(document["rows"]) != part["row_count"]:
            raise ValueError(f"Neotoma {surface} part row count changed")
        rows.extend(
            row
            for row in document["rows"]
            if sample_ids is None or row["sample_id"] in sample_ids
        )
        identities.append(
            {
                "path": path.relative_to(repository).as_posix(),
                "bytes": len(raw),
                "sha256": digest,
            }
        )
    return rows, identities


def publish(
    repository: Path, source_root: Path
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Retain exact source-count lineage without approving a taxon ontology."""
    repository = repository.resolve()
    source_root = source_root.resolve()
    source_path = source_root / SOURCE
    source_data = source_path.read_bytes()
    if sha256(source_data).hexdigest() != SOURCE_SHA256:
        raise ValueError("Primary PANGAEA Solsø pollen bytes changed")
    names, primary = _primary(source_data)
    column_by_name = dict(zip(names, list(primary[0])[1:], strict=True))
    manifest_path = repository / RELATIONAL / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    samples, sample_inputs = _surface(repository, manifest, "samples")
    selected = [row for row in samples if row["collection_unit_id"] == UNIT]
    if len(selected) != 66 or {row["site_id"] for row in selected} != {SITE}:
        raise ValueError("Neotoma 1981 Solsø sample membership changed")
    by_depth = {Decimal(row["source_depth"]): row for row in selected}
    if len(by_depth) != 66:
        raise ValueError("Neotoma Solsø source depths are duplicated")
    source_depths = {Decimal(row["Depth sed [m]"]) * 100 for row in primary}
    if source_depths != set(by_depth):
        raise ValueError("Primary and Neotoma Solsø 1981 depths differ")
    sample_ids = {row["sample_id"] for row in selected}
    observations, observation_inputs = _surface(
        repository, manifest, "observations", sample_ids=sample_ids
    )
    by_sample: dict[str, dict[str, int]] = {sample_id: {} for sample_id in sample_ids}
    for row in observations:
        sample_id = row["sample_id"]
        if sample_id not in sample_ids:
            continue
        if (
            row["collection_unit_id"] != UNIT
            or row["site_id"] != SITE
            or row["source_unit"] != "NISP"
            or row["unit_family"] != "count"
        ):
            raise ValueError("Neotoma Solsø source observation role changed")
        name = row["source_reported_name"]
        value = row["source_value"]
        if name in by_sample[sample_id] or type(value) is not int or value <= 0:
            raise ValueError(
                "Neotoma Solsø source observation is duplicated or invalid"
            )
        by_sample[sample_id][name] = value
    neotoma_names = set.union(*(set(values) for values in by_sample.values()))
    unchanged = set(names) & neotoma_names
    source_only = sorted(set(names) - neotoma_names)
    neotoma_only = sorted(neotoma_names - set(names))
    if len(unchanged) != 129 or len(source_only) != 18 or len(neotoma_only) != 18:
        raise ValueError("Solsø source-name axes changed")
    paired = sorted(
        ((Decimal(row["Depth sed [m]"]) * 100, row) for row in primary),
        key=lambda item: item[0],
    )
    rename_candidates: list[dict[str, object]] = []
    mapping = {name: name for name in unchanged}
    for source_name in source_only:
        source_vector = [int(row[column_by_name[source_name]]) for _, row in paired]
        matches = [
            candidate
            for candidate in neotoma_only
            if source_vector
            == [
                by_sample[by_depth[depth]["sample_id"]].get(candidate, 0)
                for depth, _ in paired
            ]
        ]
        if len(matches) != 1:
            raise ValueError(
                "Solsø renamed source taxon lacks unique count fingerprint"
            )
        target = matches[0]
        mapping[source_name] = target
        rename_candidates.append(
            {
                "pangaea_parameter_name": source_name,
                "neotoma_source_reported_name": target,
                "positive_sample_count": sum(value > 0 for value in source_vector),
                "source_count_sum": sum(source_vector),
                "vector_equal_at_all_66_depths": True,
                "status": "numeric_source_name_candidate_not_ecological_approval",
            }
        )
    if len(set(mapping.values())) != 147 or len(mapping) != 147:
        raise ValueError("Solsø count-fingerprint mapping is not one-to-one")
    sample_rows: list[dict[str, object]] = []
    observed_cells = 0
    zero_cells = 0
    total_count = 0
    for depth, row in paired:
        sample = by_depth[depth]
        actual = by_sample[sample["sample_id"]]
        expected = {
            mapping[name]: int(row[column_by_name[name]])
            for name in names
            if int(row[column_by_name[name]]) > 0
        }
        if expected != actual:
            raise ValueError(f"Solsø count rows differ at depth {depth} cm")
        observed_cells += len(expected)
        zero_cells += len(names) - len(expected)
        total_count += sum(expected.values())
        sample_rows.append(
            {
                "depth_cm": int(depth),
                "neotoma_sample_id": sample["sample_id"],
                "positive_source_taxa": len(expected),
                "source_count_sum": sum(expected.values()),
                "positive_counts_equal": True,
            }
        )
    if observed_cells != 2881 or zero_cells != 6821 or total_count != 128653:
        raise ValueError("Solsø whole-profile count denominator changed")
    report: dict[str, object] = {
        "schema_version": "solsoe-primary-pollen-lineage.v1",
        "primary_doi": DOI,
        "primary_event": "SOLSOE81",
        "primary_profile_rows": len(primary),
        "primary_parameter_count": len(names),
        "primary_count_cells": len(primary) * len(names),
        "primary_positive_count_cells": observed_cells,
        "primary_zero_count_cells": zero_cells,
        "primary_total_count": total_count,
        "neotoma_1981_sample_count": len(selected),
        "neotoma_positive_observation_count": sum(
            len(value) for value in by_sample.values()
        ),
        "exact_same_name_parameter_count": len(unchanged),
        "numeric_rename_candidate_count": len(rename_candidates),
        "numeric_rename_candidates": rename_candidates,
        "all_source_sample_depths_match_exactly_cm": True,
        "all_positive_source_counts_match_exactly": True,
        "neotoma_zero_cells_are_sparse_absences": True,
        "author_79_sample_selection_identified": False,
        "author_chronology_identified": False,
        "lra_admitted_samples": 0,
        "interpretation": (
            "The primary EPD PANGAEA 1981 pollen profile and Neotoma 1981 "
            "collection unit have the same 66 depth rows and 2,881 positive "
            "NISP values. Eighteen source-name pairs are unique count-vector "
            "candidates, not qualified ecological-taxonomy approvals. The "
            "LandClim II 79-sample author selection and its chronology and "
            "age-specific basin are still unidentified."
        ),
        "source_rights": "PANGAEA CC BY-NC 3.0; primary raw text remains external",
        "inputs": [
            _identity(source_path, source_root),
            _identity(manifest_path, repository),
            *sample_inputs,
            *observation_inputs,
            _identity(
                repository
                / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/solsoe_pollen_lineage.py",
                repository,
            ),
        ],
    }
    return report, sample_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report, samples = publish(args.repository, args.source_root)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (args.output / "samples.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(samples[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(samples)
    print("66 Solsø 1981 samples and 2,881 source counts match Neotoma")


if __name__ == "__main__":
    main()
