"""Account for Neotoma sample membership in the four-country pollen study."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
from hashlib import sha256
import json
import math
from pathlib import Path


SAMPLE_PART = Path("data/neotoma/relational/surfaces/samples/part-00001.json")
MANIFEST = Path("data/neotoma/relational/manifest.json")
POLLEN_SCREEN = Path("docs/report/source-relations/neotoma/pollen-screen/report.json")
SWEDISH_SAMPLES = Path(
    "docs/report/pollen-reconstruction/swedish-native-sequences/samples.json"
)
SWEDISH_DESIGN = Path(
    "docs/report/pollen-reconstruction/swedish-direct-pollen/config.json"
)
SWEDISH_PREDICTIONS = Path(
    "docs/report/regions/nordic/swedish-author-target-pollen/predictions/predictions-SE.json.gz"
)
METADATA = {
    country: Path(
        "docs/report/regions/nordic/"
        + (
            "swedish-author-target-pollen"
            if country == "SE"
            else "author-target-pollen"
        )
        + f"/inputs/metadata-{country}.json.gz"
    )
    for country in ("DK", "FI", "NO", "SE")
}
FIELDS = (
    "sample_id",
    "country_code",
    "site_id",
    "dataset_id",
    "source_row_index",
    "membership",
    "study_metadata_path",
)


def _identity(repository: Path, relative: Path) -> dict[str, object]:
    data = (repository / relative).read_bytes()
    return {
        "path": relative.as_posix(),
        "bytes": len(data),
        "sha256": sha256(data).hexdigest(),
    }


def _neotoma_id(kind: str, value: object) -> str:
    text = str(value)
    suffix = text.rsplit(":", 1)[-1]
    if not suffix.isdecimal() or (":" in text and text != f"neotoma:{kind}:{suffix}"):
        raise ValueError(f"Unexpected {kind} identity: {text}")
    return f"neotoma:{kind}:{suffix}"


def build(repository: Path, output: Path) -> dict[str, object]:
    """Join every source sample to frozen study metadata without reading outcomes."""
    repository = repository.resolve()
    manifest = json.loads((repository / MANIFEST).read_text(encoding="utf-8"))
    part_entry = manifest["surfaces"]["samples"]["parts"]
    if (
        len(part_entry) != 1
        or part_entry[0]["path"] != "surfaces/samples/part-00001.json"
    ):
        raise ValueError("Source sample partition changed")
    inputs = [_identity(repository, MANIFEST), _identity(repository, SAMPLE_PART)]
    if inputs[1]["sha256"] != part_entry[0]["sha256"]:
        raise ValueError("Sample part differs from the source manifest")
    source = json.loads((repository / SAMPLE_PART).read_text(encoding="utf-8"))
    rows = source["rows"]
    if (
        source["row_count"] != len(rows)
        or part_entry[0]["row_count"] != len(rows)
        or manifest["surfaces"]["samples"]["row_count"] != len(rows)
        or source["build_id"] != manifest["build_id"]
        or source["source_snapshot_id"] != manifest["source_snapshot_id"]
    ):
        raise ValueError("Source sample counts or snapshot identity changed")
    inputs.append(_identity(repository, POLLEN_SCREEN))
    screen = json.loads((repository / POLLEN_SCREEN).read_text(encoding="utf-8"))
    screen_rows = screen["sample_decisions"]
    if (
        len(screen_rows) != len(rows)
        or screen["normalized_build_id"] != manifest["build_id"]
        or screen["source_snapshot_id"] != manifest["source_snapshot_id"]
    ):
        raise ValueError("Pollen screen source population changed")
    screen_by_id = {item["sample_id"]: item for item in screen_rows}
    if len(screen_by_id) != len(rows):
        raise ValueError("Pollen screen sample identities are duplicated")

    selected: dict[str, tuple[str, str, str]] = {}
    study_sites: dict[str, tuple[str, str]] = {}
    for country, relative in METADATA.items():
        inputs.append(_identity(repository, relative))
        with gzip.open(repository / relative, "rt", encoding="utf-8") as stream:
            metadata = json.load(stream)
        if metadata["country"] != country:
            raise ValueError(f"Study metadata country changed: {country}")
        count = 0
        for site in metadata["sites"]:
            site_id = _neotoma_id("site", site["site_id"])
            if site["country"] != country or site_id in study_sites:
                raise ValueError(f"Study site ownership changed: {site_id}")
            study_sites[site_id] = (country, relative.as_posix())
            for raw_sample in site["candidate_sample_ids"]:
                sample_id = _neotoma_id("sample", raw_sample)
                if sample_id in selected:
                    raise ValueError(f"Duplicate selected sample: {sample_id}")
                selected[sample_id] = (country, site_id, relative.as_posix())
                count += 1
        if "candidate_samples" in metadata and metadata["candidate_samples"] != count:
            raise ValueError(f"Study sample count changed: {country}")

    source_ids: set[str] = set()
    decisions: list[dict[str, object]] = []
    counts: Counter[tuple[str, str]] = Counter()
    screen_counts: Counter[tuple[str, str, str]] = Counter()
    same_site_reasons: Counter[tuple[str, str]] = Counter()
    selected_screen_refusals: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        sample_id = row["sample_id"]
        if sample_id in source_ids:
            raise ValueError(f"Duplicate source sample: {sample_id}")
        source_ids.add(sample_id)
        country = row["country_code"]
        if country not in (*METADATA, "UNASSIGNED"):
            raise ValueError(f"Unexpected source country: {country}")
        site_id = row["site_id"]
        if sample_id in selected:
            selected_country, selected_site, metadata_path = selected[sample_id]
            if (country, site_id) != (selected_country, selected_site):
                raise ValueError(f"Selected source ownership differs: {sample_id}")
            membership = "selected_for_author_target_study"
        elif country == "UNASSIGNED":
            membership = "unresolved_source_country"
            metadata_path = ""
        elif site_id in study_sites:
            if study_sites[site_id][0] != country:
                raise ValueError(f"Study site source country differs: {site_id}")
            membership = "same_site_not_selected"
            metadata_path = study_sites[site_id][1]
        else:
            membership = "outside_study_sites"
            metadata_path = ""
        screened = screen_by_id.get(sample_id)
        if (
            screened is None
            or any(
                screened[key] != row[key]
                for key in ("country_code", "site_id", "dataset_id")
            )
            or screened["source_locator"]["row_index"] != index
        ):
            raise ValueError(f"Pollen screen sample lineage differs: {sample_id}")
        status = screened["screen_status"]
        if status not in ("necessary_candidate", "refused"):
            raise ValueError(f"Unexpected pollen screen status: {sample_id}")
        screen_counts[(country, membership, status)] += 1
        if membership == "same_site_not_selected":
            if status != "refused" or not screened["reason_codes"]:
                raise ValueError(f"Same-site screen decision changed: {sample_id}")
            for reason in screened["reason_codes"]:
                same_site_reasons[(country, reason)] += 1
        if membership == "selected_for_author_target_study" and status == "refused":
            selected_screen_refusals.append(
                {
                    "sample_id": sample_id,
                    "country_code": country,
                    "screen_reason_codes": screened["reason_codes"],
                }
            )
        counts[(country, membership)] += 1
        decisions.append(
            {
                "sample_id": sample_id,
                "country_code": country,
                "site_id": site_id,
                "dataset_id": row["dataset_id"],
                "source_row_index": index,
                "membership": membership,
                "study_metadata_path": metadata_path,
            }
        )
    if not set(selected).issubset(source_ids):
        raise ValueError("Selected study sample absent from source population")
    for relative in (SWEDISH_SAMPLES, SWEDISH_DESIGN, SWEDISH_PREDICTIONS):
        inputs.append(_identity(repository, relative))
    native_samples = json.loads(
        (repository / SWEDISH_SAMPLES).read_text(encoding="utf-8")
    )
    native_by_id = {
        _neotoma_id("sample", row["sample_id"]): row for row in native_samples
    }
    swedish_selected = {
        sample_id for sample_id, owner in selected.items() if owner[0] == "SE"
    }
    if (
        len(native_by_id) != len(native_samples)
        or set(native_by_id) != swedish_selected
    ):
        raise ValueError("Swedish source sample membership changed")
    design = json.loads((repository / SWEDISH_DESIGN).read_text(encoding="utf-8"))
    width = design["age_bin_width_cal_bp"]
    if type(width) is not int or width <= 0:
        raise ValueError("Swedish age bin width changed")
    with gzip.open(repository / SWEDISH_PREDICTIONS, "rt", encoding="utf-8") as stream:
        frozen = json.load(stream)
    if frozen["country"] != "SE":
        raise ValueError("Swedish prediction country changed")
    predicted_bins = {(row["site_id"], row["bin_id"]) for row in frozen["predictions"]}
    refused_by_bin = {
        (row["site_id"], row["bin_id"]): row["reason"] for row in frozen["refusals"]
    }
    refused_bins = set(refused_by_bin)
    if len(refused_by_bin) != len(frozen["refusals"]):
        raise ValueError("Swedish prediction refusals are duplicated")
    if predicted_bins & refused_bins:
        raise ValueError("Swedish prediction and refusal bins overlap")
    refusal_age_context: list[dict[str, object]] = []
    for item in selected_screen_refusals:
        sample_id = str(item["sample_id"])
        native = native_by_id[sample_id]
        age = native["calibrated_age_bp"]
        site_id = native["site_id"]
        bin_id = math.floor(age / width)
        if (
            age >= 0
            or site_id != selected[sample_id][1].rsplit(":", 1)[-1]
            or (site_id, bin_id) not in refused_bins
            or (site_id, bin_id) in predicted_bins
        ):
            raise ValueError(f"Swedish age/refusal support changed: {sample_id}")
        refusal_age_context.append(
            {
                "sample_id": sample_id,
                "site_id": site_id,
                "calibrated_age_bp": age,
                "nominal_bin_id": bin_id,
                "frozen_prediction_status": "refused",
                "frozen_prediction_reason": refused_by_bin[(site_id, bin_id)],
            }
        )
    decisions.sort(key=lambda row: int(str(row["sample_id"]).rsplit(":", 1)[-1]))
    output.mkdir(parents=True)
    csv_path = output / "decisions.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(decisions)
    result = {
        "schema_version": "neotoma-author-target-study-membership.v2",
        "source_build_id": manifest["build_id"],
        "source_snapshot_id": manifest["source_snapshot_id"],
        "source_sample_count": len(rows),
        "selected_sample_count": len(selected),
        "study_site_count": len(study_sites),
        "counts": [
            {"country_code": country, "membership": membership, "samples": number}
            for (country, membership), number in sorted(counts.items())
        ],
        "screen_status_counts": [
            {
                "country_code": country,
                "membership": membership,
                "screen_status": status,
                "samples": number,
            }
            for (country, membership, status), number in sorted(screen_counts.items())
        ],
        "same_site_screen_reason_occurrences": [
            {"country_code": country, "reason_code": reason, "samples": number}
            for (country, reason), number in sorted(same_site_reasons.items())
        ],
        "selected_screen_refusals": selected_screen_refusals,
        "selected_screen_refusal_age_context": refusal_age_context,
        "inputs": inputs,
        "decisions": _identity(output, Path("decisions.csv")),
        "limits": (
            "Membership describes four prior-exposed observed-pollen study input "
            "sets. Pollen-screen reasons describe source prerequisites, not a "
            "proven study-selection cause. Unassigned source country is unresolved; "
            "no LRA, ecological or source-rights admission follows."
        ),
    }
    (output / "report.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("Output destination must be absent")
    build(args.repository, args.output)


if __name__ == "__main__":
    main()
