"""Investigate literal Exhult count concordance without physical-core admission.

Frozen scope: all108 cached workbook rows, all original dataset53994 samples,
unique numeric Sample/native-depth anchors only, exact unique taxon labels and
literal NISP only. Duplicate columns/anchors/variables and absent observations
remain unresolved; no aggregation, imputation, calendar conversion or chosen
chronology. Agreement is numerical concordance, not source independence,
historical-input authentication, ecological validity or LRA/rights admission.

The explicit-latin-headers profile is a separate post-exposure curation question:
only three fully specified presentation headers map to their literal Latin
names. Every other header is excluded, without general stripping or taxonomy.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from math import isfinite
from pathlib import Path
import subprocess
import sys
from typing import Any

from bijux_pollenomics.collection.sources.rootsi import authority
from bijux_pollenomics.collection.sources.rootsi.cells import decoding, inputs, models
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from . import exhult_cells

MEMBER = "rootsi/EXHU.xls"
RAW = "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json"
IDENTITIES = "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/inputs/source-identities.json"
WORKBOOK_SHA = "7448daf13d2b40eab5bf2cacd12a706e9c9a65b830c50bdd6816300fbc54fbe3"
RAW_SHA = "9cdcb2d394bc8ef23bf2b4b5e3f1f3ae5916aae16db71542c58f4b80a2dd1134"
CONSUMED = (
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/neotoma/exhult_count_correspondence.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/neotoma/exhult_cells.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/rootsi/cells/decoding.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/rootsi/cells/inputs.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/rootsi/cells/models.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/rootsi/authority.py",
)


def revision(repository: Path) -> str:
    """Require the consumed canonical modules to belong to the named Git commit."""

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(repository), *args], text=True
        ).strip()

    git("ls-files", "--error-unmatch", *CONSUMED)
    git("diff", "--exit-code", "HEAD", "--", *CONSUMED)
    for module, relative in (
        (sys.modules[__name__], CONSUMED[0]),
        (exhult_cells, CONSUMED[1]),
        (decoding, CONSUMED[2]),
        (inputs, CONSUMED[3]),
        (models, CONSUMED[4]),
        (authority, CONSUMED[5]),
    ):
        if Path(str(module.__file__)).resolve() != (repository / relative).resolve():
            raise ValueError("Consumed module is not canonical source")
    return git("rev-parse", "HEAD")


def load_workbook(source_store: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Bind one original workbook through its existing shared roster."""
    manifest = inputs.local_path(source_store / "manifest.json")
    if manifest.stat().st_size > 65536:
        raise ValueError("Workbook manifest exceeds bound")
    roster = json.loads(manifest.read_text())
    selected = [row for row in roster["members"] if row.get("archive_member") == MEMBER]
    if roster.get("archive_sha256") != authority.ARCHIVE_SHA256 or selected != [
        {"archive_member": MEMBER, "sha256": WORKBOOK_SHA, "bytes": 155136}
    ]:
        raise ValueError("Original Exhult workbook binding differs")
    payload = inputs.read_bytes(source_store / MEMBER, WORKBOOK_SHA, 155136)
    book = decoding.parser().open_workbook(file_contents=payload, formatting_info=True)
    try:
        sheets = book.sheets()
        if len(sheets) != 1 or sheets[0].nrows != 109 or sheets[0].ncols != 204:
            raise ValueError("Exhult workbook extent differs")
        return exhult_cells.workbook_rows(sheets[0]), {
            "workbook_bytes": len(payload),
            "workbook_sha256": WORKBOOK_SHA,
        }
    finally:
        book.release_resources()


def load_native(repository: Path) -> list[dict[str, Any]]:
    """Select exactly one original dataset; never assume its sample denominator."""
    identity = json.loads(inputs.local_path(repository / IDENTITIES).read_text())[
        "source_files"
    ][RAW]
    if identity != {"bytes": 24477671, "sha256": RAW_SHA}:
        raise ValueError("Existing raw source authority differs")
    raw = json.loads(inputs.read_bytes(repository / RAW, RAW_SHA, identity["bytes"]))
    return select_samples(raw)


def select_samples(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep site, collection unit and dataset identity distinct at native selection."""
    selected = [
        row["site"]
        for row in raw["rows"]
        if row["site"].get("collectionunit", {}).get("dataset", {}).get("datasetid")
        == 53994
    ]
    if raw.get("part_number") != 8 or len(selected) != 1:
        raise ValueError("Native dataset selection differs")
    site = selected[0]
    unit = site["collectionunit"]
    if (
        site["siteid"] != 28868
        or unit["collectionunitid"] != 39237
        or unit["dataset"]["datasetid"] != 53994
    ):
        raise ValueError("Native site or collection unit differs")
    samples: list[dict[str, Any]] = unit["dataset"]["samples"]
    ids = [sample["sampleid"] for sample in samples]
    if not samples or len(ids) != len(set(ids)):
        raise ValueError("Native sample IDs are empty or repeated")
    return samples


def render_csv(rows: list[dict[str, Any]]) -> str:
    """Keep row summaries and sparse exceptions, rather than another count matrix."""
    fields = list(dict.fromkeys(key for row in rows for key in row))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: json.dumps(
                    _literal(value),
                    ensure_ascii=False,
                    allow_nan=False,
                    separators=(",", ":"),
                )
                for key, value in row.items()
            }
        )
    return stream.getvalue()


def _literal(value: Any) -> Any:
    """Represent refused nonfinite cached values explicitly in valid JSON cells."""
    if isinstance(value, float) and not isfinite(value):
        return {"nonfinite_float": repr(value)}
    if isinstance(value, list):
        return [_literal(item) for item in value]
    if isinstance(value, dict):
        return {key: _literal(item) for key, item in value.items()}
    return value


def run(
    repository: Path, source_store: Path, output: Path, *, profile: str = "literal"
) -> None:
    """Run the committed bounded source comparison and preserve honest terminal scope."""
    output = require_absent_artifact_output(repository, output)
    source = revision(repository)
    rows, workbook = load_workbook(source_store)
    samples = load_native(repository)
    correspondence, summary = exhult_cells.compare(rows, samples, profile=profile)
    csv_text = render_csv(correspondence)
    report = (
        f"# Exhult {profile} count correspondence\n\n"
        f"Source commit: `{source}`. Reproduction template: `python -B -m "
        "bijux_pollenomics_dev.source_completion.neotoma.exhult_count_correspondence "
        f"--repository . --source-store SHARED_ROTSI_WORKBOOKS --output ARTIFACT_OUTPUT --profile {profile}`.\n\n"
        f"Original workbook `{MEMBER}`: {workbook['workbook_bytes']} bytes, SHA256 `{WORKBOOK_SHA}`. "
        f"Native dataset 53994/site 28868/unit 39237: `{RAW}`, 24477671 bytes, SHA256 `{RAW_SHA}`.\n\n"
        + "\n".join(
            f"- {key}: `{json.dumps(value, sort_keys=True)}`"
            for key, value in summary.items()
        )
        + "\n\nThe CSV preserves each workbook row and every native sample not uniquely paired. "
        "Only unique finite numeric anchors and unique literal taxon names with NISP units are compared. "
        "The explicit-latin-headers profile uses only the three complete header pairs listed above; "
        "all other unique headers are unassessed, not missing native observations. Duplicate columns remain excluded. "
        "It is a post-exposure curation comparison, not untouched evaluation or biological taxonomy approval. "
        "Native-only labels in that profile mean labels outside the selected panel, not ecological absence. "
        "Workbook Sample is not authenticated as depth or a unit. Ages retain the literal AD/BC header "
        "and native chronology metadata separately; no calendar conversion, chronology choice or age equivalence is made. "
        "Cached formula origin is unavailable. Missing rows remain distinct from explicit zero. "
        "Non-NISP observations and ambiguous variables are excluded from paired mass. "
        "Numerical concordance cannot establish physical core identity, source independence, historical "
        "input identity, basin radius applicability, source permission or LRA admission.\n"
    )
    if len(csv_text.encode()) + len(report.encode()) > 4 * 1024**2:
        raise ValueError("Correspondence output exceeds 4 MiB bound")
    if revision(repository) != source:
        raise ValueError("Consumed source revision changed")
    # Recheck only the two raw assets, without decoding them again.
    inputs.read_bytes(source_store / MEMBER, WORKBOOK_SHA, 155136)
    inputs.read_bytes(repository / RAW, RAW_SHA, 24477671)
    output.mkdir(parents=True, exist_ok=False)
    (output / "correspondence.csv").write_text(csv_text)
    (output / "REPORT.md").write_text(report)


def main() -> int:
    """Compare the shared original sources without copying them."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--profile", choices=("literal", "explicit-latin-headers"), default="literal"
    )
    args = parser.parse_args()
    run(
        args.repository.absolute(), args.source_store, args.output, profile=args.profile
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
