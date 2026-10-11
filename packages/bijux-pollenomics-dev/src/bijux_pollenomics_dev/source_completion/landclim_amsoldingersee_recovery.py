"""Replay the bounded Amsoldingersee publication-input source refusal."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

CUSTODY = Path(
    "docs/report/maintenance/artifact-retention/landclim-amsoldingersee-custody.json"
)
AUTHOR_SITES_SHA256 = "72949e9e3faf417be0b7425fc111a9638b37c4a38aab8f8d82e0c3d8739da2de"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _objects(value: Any) -> Any:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


def _scalars(value: Any, key: str) -> set[str]:
    return {
        str(row[key])
        for row in _objects(value)
        if key in row and not isinstance(row[key], (dict, list))
    }


def _candidate(source_root: Path, dataset_id: int) -> dict[str, Any]:
    parent = source_root / "capture"
    if dataset_id != 3875:
        parent /= "siblings001"
    suffix = "" if dataset_id == 3875 else f"-{dataset_id}"
    paths = {
        name: parent / f"{name}{suffix}.raw"
        for name in ("dataset", "download", "chronologies")
    }
    metadata, download, chronology = (
        json.loads(paths[name].read_text()) for name in paths
    )
    site = metadata["data"][0]["site"]
    entry = site["datasets"][0]
    sample_ids = _scalars(download, "sampleid")
    units = Counter(str(row["units"]) for row in _objects(download) if "units" in row)
    elements = Counter(
        str(row["elementtype"]) for row in _objects(download) if "elementtype" in row
    )
    return {
        "dataset_id": dataset_id,
        "site_id": site["siteid"],
        "collection_handle": site["handle"],
        "sample_id_count": len(sample_ids),
        "age_range_as_reported": entry.get("agerange"),
        "chronology_ids": sorted(_scalars(chronology, "chronologyid")),
        "age_types": sorted(
            _scalars(download, "agetype") | _scalars(chronology, "agetype")
        ),
        "chronology_record_count": len(chronology.get("data", [])),
        "observation_units": dict(units),
        "element_types": dict(elements),
        "publication_code_e69_present": any(
            b"E#69" in path.read_bytes() for path in paths.values()
        ),
        "source_sha256": {name: _sha(path) for name, path in paths.items()},
    }


def build(repository: Path, source_root: Path, output: Path) -> dict[str, Any]:
    """Recheck exact private captures before using their observed source fields."""
    repository, source_root = repository.resolve(), source_root.resolve()
    custody = json.loads((repository / CUSTODY).read_text())
    assert custody["schema_version"] == "landclim-amsoldingersee-source-custody.v1"
    private_prefix = Path(custody["private_source_root"])
    captured: dict[str, str] = {}
    for item in custody["files"]:
        relative = Path(item["private_path"]).relative_to(private_prefix)
        path = source_root / relative
        if path.stat().st_size != item["bytes"] or _sha(path) != item["sha256"]:
            raise ValueError(f"Amsoldingersee source custody changed: {relative}")
        captured[relative.as_posix()] = item["sha256"]
    if len(captured) != 47:
        raise ValueError("Amsoldingersee source custody file set changed")

    response_paths: set[str] = set()
    for receipt_name, parent in (
        ("capture/receipt.json", "capture"),
        ("capture/siblings001/receipt.json", "capture/siblings001"),
    ):
        receipt = json.loads((source_root / receipt_name).read_text())
        if receipt["read_set_unchanged"] is not True:
            raise ValueError("Amsoldingersee source capture was not stable")
        rows = receipt["responses"]
        for row in rows if isinstance(rows, list) else rows.values():
            response_relative = f"{parent}/{Path(row['raw_path']).name}"
            if (
                row["http_status"] != 200
                or row["truncated"] is not False
                or row["failure"] is not None
                or row["raw_sha256"] != captured[response_relative]
            ):
                raise ValueError(
                    f"Amsoldingersee source capture invalid: {response_relative}"
                )
            response_paths.add(response_relative)
    if len(response_paths) != 11:
        raise ValueError("Amsoldingersee source response set changed")

    author_sites = source_root.parent / "author-reference/author/site.metadata.csv"
    if _sha(author_sites) != AUTHOR_SITES_SHA256:
        raise ValueError("LandClim author example site metadata changed")
    examples = list(csv.DictReader(author_sites.open(newline="")))
    example_keys = {
        value for row in examples for value in (row["filename"], row["SiteName"])
    }
    publication = json.loads(
        (source_root / "capture/selected-publication-row.json").read_text()
    )
    fields = {row["column"]: row["raw"] for row in publication["values"]}
    if (
        publication["source_locator"]
        != "landclim_ii_site_metadata.xlsx#LANDCLIMII metadata file!1059"
        or fields["SiteName"] != "Amsoldingersee"
        or fields["csvfilename"] != "E#69"
        or fields["nPollenSamples"] != "23"
        or fields["chronologySource"] != "Authors chronology"
        or len(examples) != 17
    ):
        raise ValueError("Amsoldingersee publication selection changed")
    site = json.loads((source_root / "capture/sites.raw").read_text())["data"][0]
    candidates = [
        _candidate(source_root, dataset_id) for dataset_id in (3873, 3874, 3875)
    ]
    if site["siteid"] != 2973 or {row["site_id"] for row in candidates} != {2973}:
        raise ValueError("Amsoldingersee candidate site changed")
    if any(row["publication_code_e69_present"] for row in candidates):
        raise ValueError("E#69 appeared in the captured candidate sources")

    report = {
        "schema_version": "landclim-amsoldingersee-source-review.v1",
        "source_capture_date": "2026-09-21",
        "publication_locator": publication["source_locator"],
        "publication_fields": {
            key: fields[key]
            for key in (
                "SiteName",
                "csvfilename",
                "Country",
                "nPollenSamples",
                "chronologySource",
                "DataRestricted/NotRestriced",
            )
        },
        "outside_author_example_set": (
            fields["csvfilename"] not in example_keys
            and fields["SiteName"] not in example_keys
        ),
        "site_id": site["siteid"],
        "candidates": candidates,
        "denominators": {
            "selected_publication_rows": 1,
            "candidate_core_count": len(candidates),
            "candidate_with_23_current_sample_ids": sum(
                row["sample_id_count"] == 23 for row in candidates
            ),
            "candidate_with_exact_e69_bridge": 0,
            "candidate_with_authenticated_author_chronology": 0,
            "reproduction_ready": 0,
        },
        "admission": "refused_historical_input_identity",
        "required_next_source": (
            "Source-owner E#69-to-core mapping, exact historical 23-sample count revision, "
            "author age-depth output, and authenticated taxon/PFT transformation"
        ),
        "input_sha256": {
            "private_capture_custody": _sha(repository / CUSTODY),
            "author_example_site_metadata": AUTHOR_SITES_SHA256,
        },
    }
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    return report


def main() -> None:
    """Run the CLI to replay the bounded Amsoldingersee publication-input source refusal."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.repository, args.source_root, args.output)


if __name__ == "__main__":
    main()
