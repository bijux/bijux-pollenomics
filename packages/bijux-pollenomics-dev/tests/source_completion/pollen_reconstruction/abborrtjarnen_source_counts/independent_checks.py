"""Bind saved correspondence to retained originals and literal source metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .independent_controls import COLUMNS
from .independent_result import COMMENTS, check_comparison
from .independent_sources import original_rows

PROTOCOL = "reports/science/abborrtjarnen-source-counts/protocol.json"
ORIGINAL = "epd/pangaea/abbo-pollen-profile-pangaea-738429.tsv"
NATIVE = "neotoma/dataset-19913/2026-10-26T185139Z/dataset-19913.download.json"
METADATA = "neotoma/dataset-19913/2026-10-26T185139Z/dataset-19913.metadata.json"


def pinned_bodies(source_root: Path, pins: dict[str, Any]) -> dict[str, bytes]:
    """Read the three declared retained sources and check their byte identities."""
    if set(pins) != {ORIGINAL, NATIVE, METADATA}:
        raise ValueError("Independent retained source population differs")
    bodies = {}
    for relative, pin in pins.items():
        body = (source_root / relative).read_bytes()
        if (
            len(body) != pin["bytes"]
            or hashlib.sha256(body).hexdigest() != pin["sha256"]
        ):
            raise ValueError("Independent retained source identity changed")
        bodies[relative] = body
    return bodies


def verify_result(
    repository: Path, source_root: Path, result_path: Path
) -> dict[str, Any]:
    """Observe saved bytes only; do not call producer parsing or comparison."""
    protocol_body = (repository / PROTOCOL).read_bytes()
    protocol = json.loads(protocol_body)
    result_body = result_path.read_bytes()
    if len(result_body) > 16384:
        raise ValueError("Saved comparison exceeds its declared budget")
    result = json.loads(result_body)
    if protocol["original_table"] != ORIGINAL or protocol["current_native"] != NATIVE:
        raise ValueError("Declared original/native routes differ")
    pins = protocol["source_store_files"]
    bodies = pinned_bodies(source_root, pins)
    description, columns, _ = original_rows(bodies[ORIGINAL], COLUMNS)
    if len(columns) != 95:
        raise ValueError("Original full header population differs")
    required = (
        "Giesecke, Thomas (2010): Pollen profile ABBO, Abborrtjärnen, Sweden",
        "PANGAEA.738429",
        "2010-05-11",
        "CC-BY-NC-3.0",
        "DEPTH, sediment/rock [m]",
    )
    if any(token not in description for token in required):
        raise ValueError("Original source description differs")
    names = (
        "Betula",
        "Cyperaceae",
        "Juniperus communis",
        "Pinus sylvestris",
        "Poaceae",
    )
    abbreviations = ("Bet", "Cypae", "Jun.c", "Pin.s", "Poac")
    for name, abbreviation, comment in zip(names, abbreviations, COMMENTS, strict=True):
        lines = [
            line
            for line in description.splitlines()
            if f"{name} [#] ({abbreviation}) *" in line
        ]
        if len(lines) != 1 or lines[0].rsplit("* COMMENT:", 1)[-1].strip() != comment:
            raise ValueError("Original morphological parameter comment differs")
    checked = check_comparison(
        result,
        bodies[ORIGINAL],
        bodies[NATIVE],
        expected_reported=527,
        expected_samples=107,
    )
    if result[
        "schema_version"
    ] != "abborrtjarnen-original-count-correspondence.v1" or not re.fullmatch(
        r"[0-9a-f]{40}", result["source_commit"]
    ):
        raise ValueError("Saved source/version identity differs")
    if result["input_sha256"] != {
        f"source-store/{p}": pin["sha256"] for p, pin in pins.items()
    }:
        raise ValueError("Saved input identities differ")
    if result["original_source"] != {
        "doi": "10.1594/PANGAEA.738429",
        "archived_from": "European Pollen Database",
        "archive_date": "2010-05-11",
        "licence": "CC-BY-NC-3.0",
        "count_unit": "#",
    }:
        raise ValueError("Original source attribution/use scope differs")
    if result["native_source"] != {
        "dataset_id": 19913,
        "site_id": 13338,
        "collection_unit_id": 14910,
        "handle": "ABBO",
        "doi": "10.21233/2vzb-bg61",
        "count_unit": "NISP",
    }:
        raise ValueError("Native source attribution differs")
    if result["scope"] != "local_noncommercial_source_comparison_only":
        raise ValueError("Source comparison use scope differs")
    for key in ("model_fits", "age_draws_consumed", "counts_imputed"):
        if type(result[key]) is not int or result[key] != 0:
            raise ValueError("Source-only comparison acquired a numerical/model action")
    for key in (
        "source_measurements_changed",
        "species_or_morphotype_equivalence_claim",
        "independent_measurement_claim",
        "historical_core_admission_changed",
        "original_table_redistributed",
    ):
        if result[key] is not False:
            raise ValueError(
                "Comparison acquired unsupported scientific/source admission"
            )
    if (
        pinned_bodies(source_root, pins) != bodies
        or result_path.read_bytes() != result_body
        or (repository / PROTOCOL).read_bytes() != protocol_body
    ):
        raise ValueError("Consumed source/result bytes changed during observation")
    return {
        "status": "verified",
        "producer_source_commit": result["source_commit"],
        "result_sha256": hashlib.sha256(result_body).hexdigest(),
        **checked,
        "morphological_comments_checked": 5,
        "source_inputs_checked": len(bodies),
        "model_fits": 0,
    }


def main(entry: Path) -> None:
    """Run an explicit committed saved-result observation, outside fixture pytest."""
    import argparse
    import subprocess
    import time

    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "source-root", "result", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    helpers = entry.resolve().parent / "abborrtjarnen_source_counts"
    paths = [entry.resolve(), *sorted(helpers.glob("independent_*.py"))]
    relative = [str(path.relative_to(repository)) for path in paths]
    prefix = ["git", "-C", str(repository)]
    subprocess.run(
        [*prefix, "ls-files", "--error-unmatch", "--", *relative],
        check=True,
        capture_output=True,
    )
    revision = subprocess.check_output(
        [*prefix, "rev-parse", "HEAD"], text=True
    ).strip()
    subprocess.run(
        [*prefix, "diff", "--exit-code", revision, "--", *relative],
        check=True,
        capture_output=True,
    )
    output = args.output.absolute()
    if (
        output.exists()
        or not output.resolve().is_relative_to(repository / "artifacts")
        or any(p.is_symlink() for p in (output, *output.parents))
    ):
        raise ValueError("Observer output must be absent beneath repository artifacts")
    started = time.monotonic()
    checked = verify_result(
        repository,
        args.source_root.resolve(strict=True),
        args.result.resolve(strict=True),
    )
    checked["observer_source_commit"] = revision
    checked["elapsed_seconds"] = time.monotonic() - started
    subprocess.run(
        [*prefix, "diff", "--exit-code", revision, "--", *relative],
        check=True,
        capture_output=True,
    )
    if (
        subprocess.check_output([*prefix, "rev-parse", "HEAD"], text=True).strip()
        != revision
    ):
        raise ValueError("Observer source revision changed during observation")
    body = json.dumps(checked, indent=2, allow_nan=False) + "\n"
    if len(body.encode()) > 16384:
        raise ValueError("Independent verification output exceeds declared budget")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body)
    print(json.dumps(checked, sort_keys=True))
