"""Authenticated author site geometry and pollen-count source axes."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
from math import asin, cos, isfinite, radians, sin, sqrt
from pathlib import Path
from typing import cast

from bijux_pollenomics.analysis.lra_validation.contracts import site_group_id

from ..observed_pollen_baseline import _checked, _csv

GRIDS = ("512", "562")
BUFFER_KM = 20.0
SOURCE_REVISION = "57ead2e2fcc493d099be4e5a3092fc396e1c3d3a"
SNAPSHOT_SHA256 = "48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb"
STATUS_FIELDS = (
    "block_grid_id",
    "target_site_id",
    "bin_id_bp",
    "status",
    "training_sites",
    "nearest_training_center_km",
    "nearest_training_basin_edge_km",
    "training_manifest_sha256",
)
PREDICTION_FIELDS = (
    "block_grid_id",
    "target_site_id",
    "bin_id_bp",
    "taxon",
    "predicted_fraction",
    "training_manifest_sha256",
)


@dataclass(frozen=True)
class SiteGeometry:
    """Source site label and basin geometry from the pinned author metadata."""

    site_id: str
    grid_id: str
    longitude: float
    latitude: float
    radius_m: float
    count_filename: str

    @property
    def record_id(self) -> str:
        return f"author:{self.site_id}"

    @property
    def group_id(self) -> str:
        return site_group_id((self.record_id,))


@dataclass(frozen=True)
class AuthorStudy:
    author: Path
    source_hashes: dict[str, str]
    source_manifest_sha256: str
    metadata_sha256: str
    crosswalk_sha256: str
    bins: list[str]
    taxa: list[str]
    prepared_taxa: list[str]
    sites: tuple[SiteGeometry, ...]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def _write_rows(
    path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]
) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _geometry(path: Path) -> tuple[SiteGeometry, ...]:
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != [
            "metadata",
            "filename",
            "SiteName",
            "model",
            "radius",
            "londd",
            "latdd",
            "LCGRID_ID",
        ]:
            raise ValueError("Author site metadata axis differs")
        raw = list(reader)
    sites = []
    for row in raw:
        radius = float(row["radius"])
        longitude = float(row["londd"])
        latitude = float(row["latdd"])
        if (
            row["metadata"] != "TRUE"
            or row["model"] not in {"1", "2"}
            or row["LCGRID_ID"] not in GRIDS
            or not row["filename"]
            or not isfinite(radius)
            or radius <= 0
            or not isfinite(longitude)
            or not isfinite(latitude)
            or not (-180 <= longitude <= 180 and -90 <= latitude <= 90)
        ):
            raise ValueError("Author site metadata lacks supported geometry")
        sites.append(
            SiteGeometry(
                row["filename"],
                row["LCGRID_ID"],
                longitude,
                latitude,
                radius,
                f"LRAready_{row['filename']}.csv",
            )
        )
    if len(sites) != 17 or len({site.site_id for site in sites}) != 17:
        raise ValueError("Author spatial cohort is incomplete or repeated")
    return tuple(sites)


def _study(author: Path, reference: Path) -> AuthorStudy:
    manifest_path = _checked(author.parent / "snapshot-manifest.json", SNAPSHOT_SHA256)
    snapshot = json.loads(manifest_path.read_text())
    if snapshot["schema_version"] != "v3-landclim-two-grid-snapshot.v1":
        raise ValueError("Author source snapshot profile differs")
    files = cast(dict[str, str], snapshot["files"])
    crosswalk_path = _checked(
        reference / "taxon-name-crosswalk.csv",
        files["reference/taxon-name-crosswalk.csv"],
    )
    crosswalk = _rows(crosswalk_path)
    taxa = [row["source"] for row in crosswalk]
    prepared = [row["prepared"] for row in crosswalk]
    if len(taxa) != 31 or len(set(taxa)) != 31 or len(set(prepared)) != 31:
        raise ValueError("Author pollen taxon axis differs")
    metadata_path = _checked(
        author / "site.metadata.csv", files["author/site.metadata.csv"]
    )
    lookup_path = _checked(author / "TWlookup.csv", files["author/TWlookup.csv"])
    lookup = _csv(lookup_path)
    if (
        lookup[0] != ["TW", "class"]
        or len(lookup) != 26
        or [row[0] for row in lookup[1:]] != [str(i) for i in range(1, 26)]
    ):
        raise ValueError("Author time-window axis differs")
    bins = [row[1] for row in lookup[1:]]
    if len(set(bins)) != 25:
        raise ValueError("Author time-window labels repeat")
    sites = _geometry(metadata_path)
    for grid in GRIDS:
        list_name = f"run.REVEALS.files/site.list.{grid}.csv"
        listed = (
            _checked(author / list_name, files[f"author/{list_name}"])
            .read_text()
            .splitlines()
        )
        if sorted(listed) != sorted(
            site.count_filename for site in sites if site.grid_id == grid
        ):
            raise ValueError("Author site metadata and prepared counts differ")
        if len(listed) < 2 or len(set(listed)) != len(listed):
            raise ValueError("Author grid lacks distinct site IDs")
    return AuthorStudy(
        author,
        files,
        _hash(manifest_path),
        _hash(metadata_path),
        _hash(crosswalk_path),
        bins,
        taxa,
        prepared,
        sites,
    )


def _distance_km(a: SiteGeometry, b: SiteGeometry) -> float:
    lon_a, lat_a, lon_b, lat_b = map(
        radians, (a.longitude, a.latitude, b.longitude, b.latitude)
    )
    angle = 2 * asin(
        sqrt(
            sin((lat_b - lat_a) / 2) ** 2
            + cos(lat_a) * cos(lat_b) * sin((lon_b - lon_a) / 2) ** 2
        )
    )
    return 6371.0088 * angle


def _edge_distance_km(a: SiteGeometry, b: SiteGeometry) -> float:
    return _distance_km(a, b) - (a.radius_m + b.radius_m) / 1000


def _buffered_training(
    sites: tuple[SiteGeometry, ...], target_grid: str, buffer_km: float = BUFFER_KM
) -> tuple[SiteGeometry, ...]:
    if not isfinite(buffer_km) or buffer_km < 0:
        raise ValueError("Spatial buffer must be finite and nonnegative")
    targets = [site for site in sites if site.grid_id == target_grid]
    training = [site for site in sites if site.grid_id != target_grid]
    if not targets or not training:
        raise ValueError("Spatial blocks require target and training sites")
    return tuple(
        site
        for site in training
        if all(_edge_distance_km(site, target) >= buffer_km for target in targets)
    )
