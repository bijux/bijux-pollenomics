"""Trace author-example prepared taxon rows back to raw source headers."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import (
    EXCLUDED_TARGETS,
    LOOKUP,
    _lookup,
)

PARAMETERS = Path("author/run.REVEALS.files/av-RPP.all.landclimII.csv")
CROSSWALK = Path("reference/taxon-name-crosswalk.csv")
FORMAT_SCRIPT = Path("author/RV.file.format.LANDCLIMII.r")
GRIDS = {"512": 9, "562": 8}


def _rows(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def _identity(path: Path, root: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "source_root_role": "external_landclim_author_reference",
        "path": path.relative_to(root).as_posix(),
        "bytes": len(raw),
        "sha256": sha256(raw).hexdigest(),
    }


def publish(source_root: Path, output: Path) -> dict[str, object]:
    """Retain source-header support without inferring an observed-zero mask."""
    source_root = source_root.resolve()
    lookup, _ = _lookup(source_root / LOOKUP)
    parameter_rows = _rows(source_root / PARAMETERS)
    crosswalk_rows = _rows(source_root / CROSSWALK)
    targets = [row[0] for row in parameter_rows[1:]]
    if (
        parameter_rows[0] != ["A.series", "alpha", "vg"]
        or crosswalk_rows[0] != ["source", "prepared"]
        or len(targets) != 31
        or len(set(targets)) != 31
        or [row[0] for row in crosswalk_rows[1:]] != targets
        or len(set(row[1] for row in crosswalk_rows[1:])) != 31
    ):
        raise ValueError("Author target or prepared taxon axes changed")
    prepared_names = dict(crosswalk_rows[1:])
    inputs = [
        _identity(source_root / relative, source_root)
        for relative in (LOOKUP, PARAMETERS, CROSSWALK, FORMAT_SCRIPT)
    ]
    format_script = (source_root / FORMAT_SCRIPT).read_text(encoding="utf-8")
    if (
        "lookup$RPP.LANDCLIMII[match(names(poll.data), lookup$oldvar)]"
        not in format_script
        or "poll.joined[is.na(poll.joined)] <- 0" not in format_script
        or "trimws" in format_script
    ):
        raise ValueError("Retained author formatting source changed")
    rows: list[dict[str, object]] = []
    seen_sites: set[str] = set()
    for grid, expected_sites in GRIDS.items():
        site_list = Path(f"author/run.REVEALS.files/site.list.{grid}.csv")
        inputs.append(_identity(source_root / site_list, source_root))
        names = [item[0] for item in _rows(source_root / site_list)]
        if len(names) != expected_sites or len(set(names)) != expected_sites:
            raise ValueError("Author example site membership changed")
        for filename in names:
            if not filename.startswith("LRAready_") or not filename.endswith(".csv"):
                raise ValueError("Unexpected author prepared file name")
            site = filename.removeprefix("LRAready_").removesuffix(".csv")
            if site in seen_sites:
                raise ValueError("Author example site is duplicated across grids")
            seen_sites.add(site)
            raw_path = Path(f"author/input/{site}.csv")
            prepared_path = Path(f"author/run.REVEALS.files/{filename}")
            inputs.extend(
                _identity(source_root / relative, source_root)
                for relative in (raw_path, prepared_path)
            )
            raw_rows = _rows(source_root / raw_path)
            prepared_rows = _rows(source_root / prepared_path)
            header = raw_rows[0]
            if (
                header[0] not in {"depth", "sample"}
                or header[1] not in {"age.cal.BP", "age.cal.bp"}
                or len(prepared_rows) != 34
                or [row[0] for row in prepared_rows]
                != ["TW", "radius", "model", *prepared_names.values()]
                or any(len(row) != 26 for row in prepared_rows)
            ):
                raise ValueError("Author raw or prepared matrix schema changed")
            supported = {
                lookup[name]
                for name in header[2:]
                if name in lookup and lookup[name] not in EXCLUDED_TARGETS
            }
            if not supported <= set(targets):
                raise ValueError("Author lookup target is outside parameter axis")
            absent = [target for target in targets if target not in supported]
            row_by_name = {row[0]: row[1:] for row in prepared_rows[3:]}
            positive_without_literal_name = [
                {
                    "author_target": target,
                    "prepared_value_sum": sum(
                        float(value) for value in row_by_name[prepared_names[target]]
                    ),
                }
                for target in absent
                if any(
                    float(value) != 0 for value in row_by_name[prepared_names[target]]
                )
            ]
            whitespace_candidates = [
                {
                    "source_column_index": index,
                    "raw_header": name,
                    "trimmed_name": name.strip(),
                    "candidate_author_target": lookup[name.strip()],
                    "raw_column_sum": sum(
                        float(raw_row[index]) for raw_row in raw_rows[1:]
                    ),
                    "prepared_target_sum": sum(
                        float(value)
                        for value in row_by_name[prepared_names[lookup[name.strip()]]]
                    ),
                }
                for index, name in enumerate(header[2:], start=2)
                if name not in lookup
                and name.strip() != name
                and lookup.get(name.strip()) in targets
            ]
            for candidate in whitespace_candidates:
                candidate["sums_equal"] = (
                    candidate["raw_column_sum"] == candidate["prepared_target_sum"]
                )
            rows.append(
                {
                    "grid_id": grid,
                    "site_id": site,
                    "raw_sample_row_count": len(raw_rows) - 1,
                    "raw_source_taxon_column_count": len(header) - 2,
                    "raw_axis_headers": header[:2],
                    "duplicate_raw_source_names": {
                        name: count
                        for name, count in sorted(Counter(header[2:]).items())
                        if count > 1
                    },
                    "raw_author_target_count": len(supported),
                    "prepared_target_row_count": 31,
                    "prepared_target_without_raw_name_count": len(absent),
                    "targets_without_raw_source_name": absent,
                    "positive_prepared_targets_without_literal_raw_name": (
                        positive_without_literal_name
                    ),
                    "positive_prepared_without_raw_name_count": len(
                        positive_without_literal_name
                    ),
                    "whitespace_name_candidates": whitespace_candidates,
                    "raw_names_without_author_lookup": [
                        name for name in header[2:] if name not in lookup
                    ],
                    "all_targets_measured_admitted": False,
                }
            )
    return {
        "schema_version": "landclim-author-example-taxon-support.v1",
        "site_count": len(rows),
        "grid_site_counts": GRIDS,
        "author_target_count": len(targets),
        "raw_author_target_count_min": min(
            cast(int, row["raw_author_target_count"]) for row in rows
        ),
        "raw_author_target_count_max": max(
            cast(int, row["raw_author_target_count"]) for row in rows
        ),
        "total_prepared_target_rows_without_raw_source_name": sum(
            cast(int, row["prepared_target_without_raw_name_count"]) for row in rows
        ),
        "positive_prepared_target_rows_without_literal_raw_name": sum(
            cast(int, row["positive_prepared_without_raw_name_count"]) for row in rows
        ),
        "whitespace_name_candidate_count": sum(
            len(cast(list[object], row["whitespace_name_candidates"])) for row in rows
        ),
        "all_targets_measured_admitted": False,
        "reviewed_reveals_profile_admitted": False,
        "interpretation": (
            "Prepared matrices contain 31 target rows at every site. Most "
            "targets without an exact raw source-name lead have all-zero "
            "prepared rows, but one site's positive prepared targets also "
            "lack literal raw-name leads. Neither zero nor positive prepared "
            "rows establish a measured-taxon mask without the original "
            "counting semantics. The five whitespace-normalized WHH05 "
            "raw-name and count-sum matches have a separate retained "
            "R read.csv parser witness; the author formatter calls that "
            "parser before its literal name match."
        ),
        "inputs": inputs,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = publish(args.source_root, args.output)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{report['site_count']} author sites retain raw taxon-header support")


if __name__ == "__main__":
    main()
