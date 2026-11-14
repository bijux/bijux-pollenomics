"""Execute the source-qualified panel audit without granting physical admission."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .metadata import assess_metadata
from .source_reading import read_dataset
from .taxa import audit_native_window, audit_workbook_window, parameter_coverage

PROTOCOL = "reports/science/pollen-reconstruction/bokesjon-pilot/protocol.json"
SOURCE_DIRECTORY = "data/neotoma/raw/bokesjon-core-sources"


EXPECTED_IDENTITIES = {
    "BOKE": {
        "dataset_id": 54001,
        "site_id": 28872,
        "collection_unit_id": 39241,
        "chronology_id": 38422,
    },
    "KRAG": {
        "dataset_id": 23013,
        "site_id": 3204,
        "collection_unit_id": 16622,
        "chronology_id": 13366,
    },
}
EXPECTED_INPUTS = (
    "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json",
    "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-005.json",
    "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv",
    "data/validation/pollen-productivity/wieczorek-herzschuh-2020/continental-europe.csv",
) + tuple(
    f"{SOURCE_DIRECTORY}/{name}.json"
    for name in (
        "datacite-alternative-metadata",
        "datacite-dataset-metadata",
        "neotoma-dataset-metadata",
        "neotoma-geochronologic-download",
        "neotoma-geochronologic-metadata",
        "neotoma-site-metadata",
        "source",
    )
)
PRIVATE_HASHES = {
    "workbook": "d95da5626a877b340e365317769fa0ef39cf371687b84004a996c30353dc4bc4",
    "author_lookup": "3a745f9b7606e5d0b59feaba2683b930c8d3990e4810f8217b69160a29a1b507",
}


def validate_protocol(value: dict[str, Any]) -> None:
    """Refuse another cohort, window or unclassified raw input before access."""
    if (
        value.get("schema_version") != "bokesjon-pilot-source-protocol.v1"
        or value.get("window_cal_bp") != [2700, 3200]
        or value.get("identities") != EXPECTED_IDENTITIES
        or tuple(row["path"] for row in value["inputs"]) != EXPECTED_INPUTS
        or any(
            value["optional_private_sources"][key]["sha256"] != digest
            for key, digest in PRIVATE_HASHES.items()
        )
    ):
        raise ValueError("Scientific protocol does not match the declared pilot")


def _pin(path: Path) -> dict[str, Any]:
    body = path.read_bytes()
    return {
        "path": str(path),
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _csv(path: Path, encoding: str = "utf-8") -> list[dict[str, str]]:
    with path.open(newline="", encoding=encoding) as handle:
        return list(csv.DictReader(handle))


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def run(
    repository: Path,
    output: Path,
    *,
    workbook: Path | None = None,
    author_lookup: Path | None = None,
) -> Path:
    """Read committed inputs once, retain all dispositions and guard consumed bytes."""
    repository = repository.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    protocol = _json(repository / PROTOCOL)
    validate_protocol(protocol)
    inputs = [repository / row["path"] for row in protocol["inputs"]]
    for path, expected in zip(inputs, protocol["inputs"], strict=True):
        pin = _pin(path)
        if pin["bytes"] != expected["bytes"] or pin["sha256"] != expected["sha256"]:
            raise ValueError(f"Scientific source changed: {expected['path']}")
    for name, path in (("workbook", workbook), ("author_lookup", author_lookup)):
        if path is not None:
            if (
                _pin(path)["sha256"]
                != protocol["optional_private_sources"][name]["sha256"]
            ):
                raise ValueError(f"Private source identity changed: {name}")
            inputs.append(path)
    package = Path(__file__).parent
    code = [
        package / x
        for x in (
            "__init__.py",
            "__main__.py",
            "metadata.py",
            "workflow.py",
            "source_reading.py",
        )
    ]
    code += sorted((package / "taxa").glob("*.py"))
    code += [
        repository
        / (
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/"
            + name
        )
        for name in ("artifact_paths.py", "contracts.py")
    ]
    cells = (
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/rootsi/cells"
    )
    if workbook is not None:
        code += sorted(cells.glob("*.py"))
    guards = inputs + code + [repository / PROTOCOL]
    before = [_pin(p) for p in guards]
    relative = [str(p.relative_to(repository)) for p in code] + [PROTOCOL]
    git = ["git", "-C", str(repository)]
    subprocess.run(
        [*git, "ls-files", "--error-unmatch", "--", *relative],
        capture_output=True,
        check=True,
    )
    head = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(
        [*git, "diff", "--exit-code", head, "--", *relative],
        capture_output=True,
        check=True,
    )
    window = (int(protocol["window_cal_bp"][0]), int(protocol["window_cal_bp"][1]))
    raw_boke = read_dataset(inputs[0], 54001)
    raw_krag = read_dataset(inputs[1], 23013)
    native = {}
    for name, raw in (("BOKE", raw_boke), ("KRAG", raw_krag)):
        identity = protocol["identities"][name]
        native[name] = audit_native_window(
            raw,
            dataset_id=identity["dataset_id"],
            collection_unit_id=identity["collection_unit_id"],
            chronology_id=identity["chronology_id"],
            window=window,
        )
        if native[name]["site_id"] != identity["site_id"]:
            raise ValueError("Source site identity differs")
    retained = next(
        r["site"]
        for r in raw_boke["rows"]
        if r["site"]["dataset"]["datasetid"] == 54001
    )
    source = repository / SOURCE_DIRECTORY
    sources = {
        role: _json(source / name)
        for role, name in (
            ("site", "neotoma-site-metadata.json"),
            ("pollen", "neotoma-dataset-metadata.json"),
            ("geochronologic", "neotoma-geochronologic-metadata.json"),
            ("dating_download", "neotoma-geochronologic-download.json"),
        )
    }
    sources["doi_records"] = [
        _json(source / name)
        for name in (
            "datacite-dataset-metadata.json",
            "datacite-alternative-metadata.json",
        )
    ]
    metadata = assess_metadata(retained, sources)
    book = (
        audit_workbook_window(
            workbook,
            window=window,
            expected_sha256=protocol["optional_private_sources"]["workbook"]["sha256"],
        )
        if workbook is not None
        else None
    )
    lookup = _csv(author_lookup, "latin-1") if author_lookup is not None else None
    parameters = {
        name: parameter_coverage(
            value,
            _csv(inputs[2]),
            _csv(inputs[3]),
            workbook_audit=book if name == "BOKE" else None,
            author_lookup_rows=lookup,
        )
        for name, value in native.items()
    }
    if (
        before != [_pin(p) for p in guards]
        or subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
        != head
    ):
        raise ValueError("Consumed inputs or source epoch changed during execution")
    output.mkdir()
    _write(output / "metadata.json", metadata)
    _write(output / "native-taxa.json", native)
    _write(output / "parameters.json", parameters)
    if book is not None:
        _write(output / "private-workbook.json", book)
    _write(
        output / "result.json",
        {
            "schema_version": "bokesjon-pilot-source-result.v1",
            "status": "source_audit_complete_scientific_admission_open",
            "calculation_source_commit": head,
            "protocol": protocol,
            "consumed_pins": before,
            "runtime": {"executable": sys.executable, "python": sys.version},
            "products": [_pin(p) for p in sorted(output.glob("*.json"))],
            "scientific_admission": False,
            "independent_measured_pairs": 0,
            "engine_calls": 0,
        },
    )
    if (
        before != [_pin(p) for p in guards]
        or subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
        != head
    ):
        raise ValueError("Consumed source or epoch changed during serialization")
    return output
