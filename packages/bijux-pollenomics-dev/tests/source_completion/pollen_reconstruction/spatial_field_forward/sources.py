"""Independent original-byte, native identity and fixed nuisance-input checks."""

from __future__ import annotations

import csv
import gzip
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET
from zipfile import ZipFile

PROTOCOL = "reports/science/pollen-reconstruction/spatial-field-forward/protocol.json"
RAW = "data/neotoma/raw/neotoma_pollen_dataset_downloads/"
EXPECTED = {
    "BOKE": (54001, 28872, 39241, 38422, 52),
    "BUS": (53995, 28869, 39238, 38418, 69),
    "SOLSOE83": (4446, 3432, 4304, 25740, 26),
}
AXIS = ("Betula", "Ulmus")
WINDOWS = tuple((low, low + 500) for low in range(2700, 5700, 500))


def bound_files(root: Path, declarations: dict[str, Any]) -> dict[str, bytes]:
    """Read confined declared files and check their exact byte identities."""
    result = {}
    for relative, identity in declarations.items():
        path = root / relative
        assert not Path(relative).is_absolute() and ".." not in Path(relative).parts
        assert path.is_file() and not path.is_symlink()
        assert path.resolve().is_relative_to(root.resolve())
        body = path.read_bytes()
        assert (
            len(body) == identity["bytes"]
            and sha256(body).hexdigest() == identity["sha256"]
        )
        result[relative] = body
    return result


def workbook_cells(body: bytes, part: str) -> dict[str, str | None]:
    """Read literal worksheet cells while leaving formula cells unavailable."""
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with ZipFile(BytesIO(body)) as archive:
        strings = [
            "".join(node.itertext())
            for node in ET.fromstring(archive.read("xl/sharedStrings.xml"))
        ]
        cells = ET.fromstring(archive.read(part)).iter(namespace + "c")
        result: dict[str, str | None] = {}
        for cell in cells:
            if cell.find(namespace + "f") is not None:
                result[cell.attrib["r"]] = None
                continue
            value = cell.find(namespace + "v")
            token = None if value is None else value.text
            result[cell.attrib["r"]] = (
                strings[int(token)]
                if cell.get("t") == "s" and token is not None
                else token
            )
    return result


def original_inputs(repository: Path, source_root: Path) -> dict[str, Any]:
    """Check pinned source identities and reconstruct declared core inputs."""
    protocol_body = (repository / PROTOCOL).read_bytes()
    protocol = json.loads(protocol_body)
    assert protocol["projected_axis"] == list(AXIS)
    assert protocol["native_taxon_ids"] == [29, 310]
    assert (
        tuple(
            zip(
                protocol["window_edges_native_bp"][:-1],
                protocol["window_edges_native_bp"][1:],
                strict=True,
            )
        )
        == WINDOWS
    )
    public = bound_files(repository, protocol["repository_files"])
    original = bound_files(source_root, protocol["source_store_files"])
    manifest = json.loads(public[RAW + "manifest.json"])
    baseline = json.loads(public["data/neotoma/review/relational_baseline.json"])[
        "input_artifacts"
    ]["raw_archive"]
    assert (
        sha256(public[RAW + "manifest.json"]).hexdigest() == baseline["manifest_sha256"]
    )
    metadata = workbook_cells(
        public["data/landclim/raw/landclim_ii_site_metadata.xlsx"],
        "xl/worksheets/sheet2.xml",
    )
    assert (metadata["B1"], metadata["D1"]) == ("csvfilename", "siteradius")
    readme = workbook_cells(
        public["data/landclim/raw/landclim_ii_site_metadata.xlsx"],
        "xl/worksheets/sheet1.xml",
    )
    assert (readme["A6"], readme["B6"]) == (
        "siteradius",
        "radius of the site in meters",
    )
    saved_dk = json.loads(
        gzip.decompress(
            public[
                "docs/report/regions/nordic/author-target-pollen/inputs/metadata-DK.json.gz"
            ]
        )
    )
    declarations = {row["id"]: row for row in protocol["cores"]}
    assert set(declarations) == set(EXPECTED)
    cores = {}
    for part in sorted({row["part"] for row in declarations.values()}):
        body = public[RAW + part]
        assert sha256(body).hexdigest() == baseline["part_sha256"][part]
        rows = json.loads(body)["rows"]
        assert len(rows) == next(
            row["row_count"] for row in manifest["parts"] if row["filename"] == part
        )
        for row in rows:
            site = row["site"]
            unit, dataset = site["collectionunit"], site["collectionunit"]["dataset"]
            name = next(
                (
                    name
                    for name, spec in EXPECTED.items()
                    if spec[0] == dataset["datasetid"]
                ),
                None,
            )
            if name is None:
                continue
            assert name not in cores
            declaration = declarations[name]
            expected = EXPECTED[name]
            assert (
                tuple(
                    declaration[field]
                    for field in (
                        "dataset_id",
                        "site_id",
                        "collection_unit_id",
                        "chronology_id",
                        "native_samples",
                    )
                )
                == expected
            )
            assert (
                dataset["datasetid"],
                site["siteid"],
                unit["collectionunitid"],
                unit["handle"],
                len(dataset["samples"]),
            ) == (expected[0], expected[1], expected[2], name, expected[4])
            chronology = [
                item["chronology"]
                for item in unit["chronologies"]
                if item["chronology"]["chronologyid"] == expected[3]
            ]
            assert (
                len(chronology) == 1
                and chronology[0]["chronology"]["modelagetype"]
                == "Calibrated radiocarbon years BP"
            )
            geometry = json.loads(site["geography"])
            assert geometry["crs"]["properties"]["name"] == "EPSG:4326"
            if name == "SOLSOE83":
                assert geometry["type"] == "Polygon"
                ring = geometry["coordinates"][0]
                assert ring[:4] == [
                    [8.61199, 56.12781],
                    [8.61483, 56.12781],
                    [8.61483, 56.12911],
                    [8.61199, 56.12911],
                ]
                saved = next(
                    item["coordinate"]
                    for item in saved_dk["sites"]
                    if item["site_id"] == "neotoma:site:3432"
                )
                assert declaration["analysis_centre_lon_lat"] == [
                    saved["longitude"],
                    saved["latitude"],
                ]
            else:
                assert geometry["type"] == "Point"
                assert (
                    declaration["analysis_centre_lon_lat"]
                    == geometry["coordinates"][:2]
                )
            assert (
                unit["gpslocation"]["latitude"]
                is unit["gpslocation"]["longitude"]
                is None
            )
            locator = declaration["metadata_row"]
            assert (
                metadata[f"B{locator}"] == declaration["metadata_code"]
                and metadata[f"C{locator}"] == "lake"
            )
            radius = metadata[f"D{locator}"]
            assert radius is not None and float(radius) == declaration["radius_m"]
            cores[name] = {"spec": declaration, "site": site}
    assert set(cores) == set(EXPECTED)
    parameters = list(
        csv.DictReader(
            StringIO(
                public[
                    "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"
                ].decode("utf-8-sig")
            )
        )
    )
    vectors = []
    for name, expected_parameter in zip(
        AXIS, ((5.106, 0.303, 0.024), (1.27, 0.05, 0.032)), strict=True
    ):
        selected = [
            row
            for row in parameters
            if row["Plant taxa/Pollen-morphological types"] == name
        ]
        assert len(selected) == 1
        match = re.fullmatch(r"([0-9.]+) \(([0-9.]+)\)", selected[0]["PPE (SD)"])
        assert match is not None
        values = float(match[1]), float(match[2]), float(selected[0]["FSP (m/s)"])
        assert values == expected_parameter
        vectors.append(values)
    return {
        "protocol": protocol,
        "cores": cores,
        "parameters": vectors,
        "public": public,
        "original": original,
    }
