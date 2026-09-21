"""Render a source-bound, label-free EMPD2–NFI reference review sheet."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Any, cast


def _digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _cell(value: object) -> str:
    if value is None:
        return "∅"
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def render_review(
    dossier_path: Path,
    dossier_sha256: str,
    spatial_path: Path,
    spatial_sha256: str,
    guide_path: Path,
    guide_sha256: str,
) -> str:
    """Render only candidate source facts; leave scientific decisions pending."""
    for path, expected in (
        (dossier_path, dossier_sha256),
        (spatial_path, spatial_sha256),
        (guide_path, guide_sha256),
    ):
        if _digest(path) != expected:
            raise ValueError("review_parent_digest_mismatch")
    if not guide_path.read_bytes().startswith(b"%PDF-"):
        raise ValueError("guide_not_pdf")
    dossier = cast(dict[str, Any], json.loads(dossier_path.read_text()))
    spatial = cast(dict[str, Any], json.loads(spatial_path.read_text()))
    rows = dossier.get("rows")
    if (
        dossier.get("schema_version") != "empd2-nfi-source-dossier.v1"
        or dossier.get("spatial_report_sha256") != spatial_sha256
        or dossier.get("scientific_admission") != "candidate_only"
        or dossier.get("independent_vegetation_pair_count") != 0
        or not isinstance(rows, list)
        or len(rows) != dossier.get("selected_lead_count")
        or len(rows) != 16
        or spatial.get("schema_version") != "empd2-nfi-spatial-feasibility.v2"
        or spatial.get("scientific_admission") != "candidate_only"
    ):
        raise ValueError("review_parent_posture_mismatch")
    lines = [
        "---",
        "title: EMPD2–NFI candidate reference review",
        "audience: scientific reviewer",
        "type: reference review",
        "status: proposed; no scientific admission",
        "owner: bijux-pollenomics-docs",
        "last_reviewed: 2026-09-21",
        "---",
        "",
        "# EMPD2–NFI candidate reference review",
        "",
        "This sheet lists **16 source-review leads, zero admitted vegetation–pollen pairs**.",
        "It is generated from pinned source artifacts and contains no NFI tree measurements.",
        "A distance-selected NFI row is a lead, not a temporal match or a vegetation footprint.",
        "Review decisions require named evidence and a qualified reviewer; blank or silent review is not approval.",
        "",
        f"- EMPD2 source dossier SHA-256: `{dossier_sha256}`",
        f"- Unrounded WGS84 spatial report SHA-256: `{spatial_sha256}`",
        f"- [Official SLU NFI calibration guide](https://www.slu.se/globalassets/slu.se/om-slu/organisation/institutioner/skoglig-resurshushallning/riksskogstaxeringen/dokument/dokument/info-data-for-calibration.pdf) SHA-256: `{guide_sha256}`. It declares CC0 1.0 for this temporary forest-plot subset and says it cannot support geographic-area totals or means.",
        "",
        "## Source leads within 1 km",
        "",
        "`NULL` below is the source's literal text; `∅` means an absent field. Distances are displayed rounded to 0.01 m only; selection used unrounded values. Source age is not a collection year. Publication counts are source links, not identity decisions.",
        "",
        "| EMPD2 sample | Source agebp | Age code | Source context/type | Nearest NFI year | Distance m | Publications | Neotoma identity flag | Collection note cue |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    seen: set[str] = set()
    cue_count = 0
    cue_leads: list[str] = []
    for item in sorted(rows, key=lambda row: row["spatial_lead"]["pollen_sample"]):
        lead = item["spatial_lead"]
        source = item["source_metadata_excluding_vegdescription"]
        name = lead["pollen_sample"]
        if name in seen or name != source["samplename"]:
            raise ValueError("review_sample_identity_mismatch")
        seen.add(name)
        if (
            lead.get("pair_admission") != "candidate_only"
            or lead.get("distance_m_wgs84", 1001) > 1000
        ):
            raise ValueError("review_spatial_candidate_mismatch")
        if item.get("independent_vegetation_pair_admission") is not False:
            raise ValueError("review_admission_mismatch")
        cues = item.get("collection_time_source_note")
        cue_count += cues is not None
        if cues is not None:
            if cues != source.get("notes"):
                raise ValueError("review_collection_note_mismatch")
            cue_leads.append(
                f"`{_cell(name)}` has the source note “{_cell(cues)}”; its distance-selected NFI row carries {_cell(lead['nfi_year'])} and lies {lead['distance_m_wgs84']:.2f} m away."
            )
        identity_flag = (
            "unresolved"
            if "cross_source_identity_unresolved" in lead["pollen_review_reason_codes"]
            else "none recorded"
        )
        lines.append(
            "| "
            + " | ".join(
                (
                    _cell(name),
                    _cell(source["agebp"]),
                    _cell(source["ageuncertainty"]),
                    _cell(source["samplecontext"])
                    + " / "
                    + _cell(source["sampletype"]),
                    _cell(lead["nfi_year"]),
                    f"{lead['distance_m_wgs84']:.2f}",
                    _cell(item["publication_link_count"]),
                    identity_flag,
                    "source note; review" if cues is not None else "none recorded",
                )
            )
            + " |"
        )
    if cue_count != dossier.get("samples_with_collection_note_cues"):
        raise ValueError("review_collection_cue_denominator_mismatch")
    lines.extend(
        [
            "",
            "## Immediate source review",
            "",
            *cue_leads,
            "A source note and a matching NFI year do not establish matched collection time. Lake sediment and a forest plot have different support. Cross-database identity flags remain unresolved proximity hypotheses.",
            "",
            "For each proposed reference, a qualified reviewer must record: exact collection date and age-type evidence; physical sample/core and cross-database identity; position datum and uncertainty; basin footprint and a defensible point/plot versus regional estimand; compatible measured vegetation variables/units and observation time; taxon/PPE decision; independence and leakage group; and a documented eligible/refused outcome with reason. The benchmark also needs a predeclared minimum independent site/block count, non-null error thresholds and a blind label store before test access.",
            "",
            "**Current decision: candidate preparation only. 0/16 paired references admitted. No model accuracy or superiority result.**",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dossier", "spatial", "guide", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("dossier", "spatial", "guide"):
        parser.add_argument(f"--{name}-sha256", required=True)
    args = parser.parse_args()
    content = render_review(
        args.dossier,
        args.dossier_sha256,
        args.spatial,
        args.spatial_sha256,
        args.guide,
        args.guide_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stage: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=args.output.parent,
            prefix=".review-",
            delete=False,
        ) as stream:
            stage = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(stage, args.output)
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)
    print(
        json.dumps(
            {
                "candidate_rows": 16,
                "admitted_pairs": 0,
                "sha256": sha256(content.encode()).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
