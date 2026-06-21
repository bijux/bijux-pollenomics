from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import re
import unicodedata

from ..core import haversine_km
from ..data_downloader.models import ContextPointRecord

__all__ = [
    "DEFAULT_LAKE_EVIDENCE_RADII_KM",
    "LakeEvidenceBandScore",
    "LakeEvidenceCandidate",
    "LakeEvidenceRichnessAssessment",
    "LakeEvidenceRichnessReport",
    "build_sweden_lake_evidence_richness_report",
]

DEFAULT_LAKE_EVIDENCE_RADII_KM = (10, 20, 30, 40, 50)
_AGGREGATE_RADIUS_WEIGHTS = {10: 0.30, 20: 0.25, 30: 0.20, 40: 0.15, 50: 0.10}
_LAKE_NAME_TERMS = ("lake", "sjo", "sjon", "tjarn", "trask", "gol")
_WETLAND_TERMS = ("mosse", "mossen", "bog", "fen", "peat", "myr", "karr", "karret")


@dataclass(frozen=True)
class LakeEvidenceCandidate:
    """One Sweden lake candidate derived from pollen-basin context."""

    lake_name: str
    lake_token: str
    latitude: float
    longitude: float
    basin_posture: str
    direct_pollen_source_count: int
    direct_pollen_record_count: int
    time_aware_direct_pollen_records: int
    pollen_sources: tuple[str, ...]
    supporting_pollen_names: tuple[str, ...]
    direct_pollen_signal: float

    def as_dict(self) -> dict[str, object]:
        return {
            "lake_name": self.lake_name,
            "lake_token": self.lake_token,
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "basin_posture": self.basin_posture,
            "direct_pollen_source_count": self.direct_pollen_source_count,
            "direct_pollen_record_count": self.direct_pollen_record_count,
            "time_aware_direct_pollen_records": self.time_aware_direct_pollen_records,
            "pollen_sources": list(self.pollen_sources),
            "supporting_pollen_names": list(self.supporting_pollen_names),
            "direct_pollen_signal": self.direct_pollen_signal,
        }


@dataclass(frozen=True)
class LakeEvidenceBandScore:
    """One distance-band evidence view around a lake candidate."""

    radius_km: int
    band_rank: int
    total_score: float
    nearby_pollen_lake_count: int
    human_adna_locality_count: int
    human_adna_sample_count: int
    domesticated_animal_locality_count: int
    domesticated_animal_sample_count: int
    sead_site_count: int
    raa_density_site_count: int
    evidence_family_count: int
    nearby_pollen_signal: float
    human_signal: float
    animal_signal: float
    archaeology_signal: float
    diversity_signal: float

    def as_dict(self) -> dict[str, object]:
        return {
            "radius_km": self.radius_km,
            "band_rank": self.band_rank,
            "total_score": self.total_score,
            "nearby_pollen_lake_count": self.nearby_pollen_lake_count,
            "human_adna_locality_count": self.human_adna_locality_count,
            "human_adna_sample_count": self.human_adna_sample_count,
            "domesticated_animal_locality_count": self.domesticated_animal_locality_count,
            "domesticated_animal_sample_count": self.domesticated_animal_sample_count,
            "sead_site_count": self.sead_site_count,
            "raa_density_site_count": self.raa_density_site_count,
            "evidence_family_count": self.evidence_family_count,
            "signals": {
                "nearby_pollen": self.nearby_pollen_signal,
                "human_adna": self.human_signal,
                "domesticated_animal_adna": self.animal_signal,
                "archaeology": self.archaeology_signal,
                "evidence_diversity": self.diversity_signal,
            },
        }


@dataclass(frozen=True)
class LakeEvidenceRichnessAssessment:
    """Full multi-band evidence assessment for one Sweden lake candidate."""

    candidate: LakeEvidenceCandidate
    aggregate_rank: int
    aggregate_score: float
    band_scores: tuple[LakeEvidenceBandScore, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate": self.candidate.as_dict(),
            "aggregate_rank": self.aggregate_rank,
            "aggregate_score": self.aggregate_score,
            "band_scores": [score.as_dict() for score in self.band_scores],
        }


@dataclass(frozen=True)
class LakeEvidenceRichnessReport:
    """Machine-readable Sweden lake evidence richness ranking."""

    schema_version: str
    country: str
    radii_km: tuple[int, ...]
    methodology: dict[str, object]
    candidate_count: int
    assessments: tuple[LakeEvidenceRichnessAssessment, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "country": self.country,
            "radii_km": list(self.radii_km),
            "candidate_count": self.candidate_count,
            "methodology": self.methodology,
            "assessments": [assessment.as_dict() for assessment in self.assessments],
        }


@dataclass(frozen=True)
class _PointEvidence:
    latitude: float
    longitude: float
    sample_count: int = 1


@dataclass(frozen=True)
class _DensityCell:
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float
    count: int


def build_sweden_lake_evidence_richness_report(
    *,
    context_root: Path,
    human_localities: Iterable[object],
    animal_localities: Iterable[dict[str, object]],
    radii_km: Sequence[int] = DEFAULT_LAKE_EVIDENCE_RADII_KM,
) -> LakeEvidenceRichnessReport:
    """Rank Sweden lake candidates by surrounding pollen, archaeology, and aDNA richness."""
    normalized_radii = tuple(sorted({int(radius) for radius in radii_km if int(radius) > 0}))
    pollen_points = _load_sweden_pollen_points(Path(context_root))
    candidates = _derive_lake_candidates(pollen_points)
    human_points = _extract_human_points(human_localities)
    animal_points = _extract_animal_points(animal_localities)
    sead_points = _load_sweden_context_points(
        Path(context_root) / "sead" / "normalized" / "nordic_environmental_sites.geojson",
        country="Sweden",
    )
    raa_cells = _load_sweden_density_cells(
        Path(context_root) / "raa" / "normalized" / "sweden_archaeology_density.geojson"
    )

    raw_scores: dict[str, dict[int, dict[str, int]]] = {
        candidate.lake_token: {
            radius: _build_raw_band_metrics(
                candidate,
                candidates,
                human_points,
                animal_points,
                sead_points,
                raa_cells,
                radius_km=radius,
            )
            for radius in normalized_radii
        }
        for candidate in candidates
    }
    maxima_by_radius = {
        radius: _build_band_maxima(raw_scores, radius_km=radius)
        for radius in normalized_radii
    }
    candidate_rows: list[dict[str, object]] = []
    for candidate in candidates:
        band_scores: list[LakeEvidenceBandScore] = []
        for radius in normalized_radii:
            raw = raw_scores[candidate.lake_token][radius]
            maxima = maxima_by_radius[radius]
            nearby_pollen_signal = _normalized_ratio(
                raw["nearby_pollen_lake_count"],
                maxima["nearby_pollen_lake_count"],
            )
            human_signal = _weighted_average(
                (
                    _normalized_ratio(
                        raw["human_adna_locality_count"],
                        maxima["human_adna_locality_count"],
                    ),
                    0.45,
                ),
                (
                    _normalized_ratio(
                        raw["human_adna_sample_count"],
                        maxima["human_adna_sample_count"],
                    ),
                    0.55,
                ),
            )
            animal_signal = _weighted_average(
                (
                    _normalized_ratio(
                        raw["domesticated_animal_locality_count"],
                        maxima["domesticated_animal_locality_count"],
                    ),
                    0.5,
                ),
                (
                    _normalized_ratio(
                        raw["domesticated_animal_sample_count"],
                        maxima["domesticated_animal_sample_count"],
                    ),
                    0.5,
                ),
            )
            archaeology_signal = _weighted_average(
                (
                    _normalized_ratio(raw["sead_site_count"], maxima["sead_site_count"]),
                    0.6,
                ),
                (
                    _normalized_ratio(
                        raw["raa_density_site_count"],
                        maxima["raa_density_site_count"],
                    ),
                    0.4,
                ),
            )
            diversity_signal = round(raw["evidence_family_count"] / 5.0, 4)
            total_score = round(
                candidate.direct_pollen_signal * 0.2
                + nearby_pollen_signal * 0.1
                + archaeology_signal * 0.25
                + human_signal * 0.2
                + animal_signal * 0.15
                + diversity_signal * 0.1,
                4,
            )
            band_scores.append(
                LakeEvidenceBandScore(
                    radius_km=radius,
                    band_rank=0,
                    total_score=total_score,
                    nearby_pollen_lake_count=raw["nearby_pollen_lake_count"],
                    human_adna_locality_count=raw["human_adna_locality_count"],
                    human_adna_sample_count=raw["human_adna_sample_count"],
                    domesticated_animal_locality_count=raw["domesticated_animal_locality_count"],
                    domesticated_animal_sample_count=raw["domesticated_animal_sample_count"],
                    sead_site_count=raw["sead_site_count"],
                    raa_density_site_count=raw["raa_density_site_count"],
                    evidence_family_count=raw["evidence_family_count"],
                    nearby_pollen_signal=nearby_pollen_signal,
                    human_signal=human_signal,
                    animal_signal=animal_signal,
                    archaeology_signal=archaeology_signal,
                    diversity_signal=diversity_signal,
                )
            )
        aggregate_score = round(
            sum(
                score.total_score
                * _AGGREGATE_RADIUS_WEIGHTS.get(score.radius_km, 0.0)
                for score in band_scores
            ),
            4,
        )
        candidate_rows.append(
            {
                "candidate": candidate,
                "aggregate_score": aggregate_score,
                "band_scores": tuple(band_scores),
            }
        )

    for radius in normalized_radii:
        ordered = sorted(
            candidate_rows,
            key=lambda row: (
                -_band_score_for_radius(
                    row["band_scores"],  # type: ignore[arg-type]
                    radius_km=radius,
                ).total_score,
                -row["aggregate_score"],  # type: ignore[arg-type]
                row["candidate"].lake_name,  # type: ignore[index]
            ),
        )
        for rank, row in enumerate(ordered, start=1):
            current_score = _band_score_for_radius(
                row["band_scores"],  # type: ignore[arg-type]
                radius_km=radius,
            )
            updated_scores = []
            for score in row["band_scores"]:  # type: ignore[assignment]
                if score.radius_km == radius:
                    updated_scores.append(
                        LakeEvidenceBandScore(
                            radius_km=score.radius_km,
                            band_rank=rank,
                            total_score=score.total_score,
                            nearby_pollen_lake_count=score.nearby_pollen_lake_count,
                            human_adna_locality_count=score.human_adna_locality_count,
                            human_adna_sample_count=score.human_adna_sample_count,
                            domesticated_animal_locality_count=score.domesticated_animal_locality_count,
                            domesticated_animal_sample_count=score.domesticated_animal_sample_count,
                            sead_site_count=score.sead_site_count,
                            raa_density_site_count=score.raa_density_site_count,
                            evidence_family_count=score.evidence_family_count,
                            nearby_pollen_signal=score.nearby_pollen_signal,
                            human_signal=score.human_signal,
                            animal_signal=score.animal_signal,
                            archaeology_signal=score.archaeology_signal,
                            diversity_signal=score.diversity_signal,
                        )
                    )
                else:
                    updated_scores.append(score)
            row["band_scores"] = tuple(updated_scores)

    ordered_candidates = sorted(
        candidate_rows,
        key=lambda row: (
            -row["aggregate_score"],  # type: ignore[arg-type]
            -_band_score_for_radius(
                row["band_scores"],  # type: ignore[arg-type]
                radius_km=normalized_radii[0],
            ).total_score,
            row["candidate"].lake_name,  # type: ignore[index]
        ),
    )
    assessments = tuple(
        LakeEvidenceRichnessAssessment(
            candidate=row["candidate"],  # type: ignore[arg-type]
            aggregate_rank=rank,
            aggregate_score=row["aggregate_score"],  # type: ignore[arg-type]
            band_scores=row["band_scores"],  # type: ignore[arg-type]
        )
        for rank, row in enumerate(ordered_candidates, start=1)
    )
    return LakeEvidenceRichnessReport(
        schema_version="sweden-lake-evidence-richness.v1",
        country="Sweden",
        radii_km=normalized_radii,
        candidate_count=len(assessments),
        methodology={
            "candidate_derivation": (
                "Candidates come from Sweden-scoped Neotoma and LandClim pollen "
                "points whose names or site descriptions identify lake-like basins. "
                "Wetland and ambiguous basins stay out of this ranking."
            ),
            "distance_bands": list(normalized_radii),
            "aggregate_radius_weights": {
                str(radius): _AGGREGATE_RADIUS_WEIGHTS.get(radius, 0.0)
                for radius in normalized_radii
            },
            "score_components": {
                "direct_pollen_signal": 0.2,
                "nearby_pollen_signal": 0.1,
                "archaeology_signal": 0.25,
                "human_adna_signal": 0.2,
                "domesticated_animal_signal": 0.15,
                "evidence_diversity_signal": 0.1,
            },
            "archaeology_note": (
                "SEAD contributes site-level point counts. RAÄ contributes coarse "
                "1-degree density cells, so the RAÄ term captures archaeology "
                "richness around the lake rather than precise site-by-site distance."
            ),
            "animal_note": (
                "Domesticated animal aDNA remains sparse in the current Sweden bundle. "
                "The ranking keeps that sparsity visible instead of inflating it."
            ),
        },
        assessments=assessments,
    )


def _extract_human_points(localities: Iterable[object]) -> tuple[_PointEvidence, ...]:
    rows: list[_PointEvidence] = []
    for locality in localities:
        latitude = getattr(locality, "latitude", None)
        longitude = getattr(locality, "longitude", None)
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        sample_count = getattr(locality, "sample_count", 0)
        rows.append(
            _PointEvidence(
                latitude=float(latitude),
                longitude=float(longitude),
                sample_count=int(sample_count) if isinstance(sample_count, int) else 0,
            )
        )
    return tuple(rows)


def _extract_animal_points(
    animal_localities: Iterable[dict[str, object]],
) -> tuple[_PointEvidence, ...]:
    rows: list[_PointEvidence] = []
    for locality in animal_localities:
        latitude = locality.get("latitude")
        longitude = locality.get("longitude")
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        sample_count = locality.get("sample_count", 0)
        rows.append(
            _PointEvidence(
                latitude=float(latitude),
                longitude=float(longitude),
                sample_count=int(sample_count) if isinstance(sample_count, int) else 0,
            )
        )
    return tuple(rows)


def _load_sweden_pollen_points(context_root: Path) -> tuple[ContextPointRecord, ...]:
    paths = (
        context_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
        context_root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
    )
    records: list[ContextPointRecord] = []
    for path in paths:
        records.extend(_load_sweden_context_points(path, country="Sweden"))
    return tuple(records)


def _load_sweden_context_points(
    path: Path,
    *,
    country: str,
) -> tuple[ContextPointRecord, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    records: list[ContextPointRecord] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue
        if str(properties.get("country", "")).strip() != country:
            continue
        coordinates = geometry.get("coordinates", [])
        if (
            geometry.get("type") != "Point"
            or not isinstance(coordinates, list)
            or len(coordinates) < 2
        ):
            continue
        longitude, latitude = coordinates[0], coordinates[1]
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        popup_rows = tuple(
            (
                str(item.get("label", "")),
                str(item.get("value", "")),
            )
            for item in properties.get("popup_rows", [])
            if isinstance(item, dict)
        )
        records.append(
            ContextPointRecord(
                source=str(properties.get("source", "")),
                layer_key=str(properties.get("layer_key", "")),
                layer_label=str(properties.get("layer_label", "")),
                category=str(properties.get("category", "")),
                country=str(properties.get("country", "")),
                record_id=str(properties.get("record_id", "")),
                name=str(properties.get("name", "")),
                latitude=float(latitude),
                longitude=float(longitude),
                geometry_type=str(properties.get("geometry_type", "Point")),
                subtitle=str(properties.get("subtitle", "")),
                description=str(properties.get("description", "")),
                source_url=str(properties.get("source_url", "")),
                record_count=int(properties.get("record_count", 1) or 1),
                popup_rows=popup_rows,
                time_start_bp=_optional_int(properties.get("time_start_bp")),
                time_end_bp=_optional_int(properties.get("time_end_bp")),
                time_mean_bp=_optional_int(properties.get("time_mean_bp")),
                time_label=str(properties.get("time_label", "")),
                temporal_semantics=properties.get("temporal_semantics")
                if isinstance(properties.get("temporal_semantics"), dict)
                else None,
            )
        )
    return tuple(records)


def _load_sweden_density_cells(path: Path) -> tuple[_DensityCell, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cells: list[_DensityCell] = []
    for feature in payload.get("features", []):
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        if not isinstance(geometry, dict) or not isinstance(properties, dict):
            continue
        if geometry.get("type") != "Polygon":
            continue
        rings = geometry.get("coordinates", [])
        if not isinstance(rings, list) or not rings:
            continue
        ring = rings[0]
        if not isinstance(ring, list) or not ring:
            continue
        latitudes = [
            float(coordinate[1])
            for coordinate in ring
            if isinstance(coordinate, list)
            and len(coordinate) >= 2
            and isinstance(coordinate[0], (int, float))
            and isinstance(coordinate[1], (int, float))
        ]
        longitudes = [
            float(coordinate[0])
            for coordinate in ring
            if isinstance(coordinate, list)
            and len(coordinate) >= 2
            and isinstance(coordinate[0], (int, float))
            and isinstance(coordinate[1], (int, float))
        ]
        if not latitudes or not longitudes:
            continue
        cells.append(
            _DensityCell(
                min_latitude=min(latitudes),
                max_latitude=max(latitudes),
                min_longitude=min(longitudes),
                max_longitude=max(longitudes),
                count=int(properties.get("count", 0) or 0),
            )
        )
    return tuple(cells)


def _derive_lake_candidates(
    pollen_points: Iterable[ContextPointRecord],
) -> tuple[LakeEvidenceCandidate, ...]:
    clusters: list[dict[str, object]] = []
    for point in pollen_points:
        basin_posture = _resolve_basin_posture(point.name, point.description)
        if basin_posture != "lake_basin":
            continue
        name_token = _normalize_text(point.name)
        matched_cluster: dict[str, object] | None = None
        for cluster in clusters:
            distance_km = haversine_km(
                latitude_a=point.latitude,
                longitude_a=point.longitude,
                latitude_b=cluster["latitude"],  # type: ignore[arg-type]
                longitude_b=cluster["longitude"],  # type: ignore[arg-type]
            )
            if distance_km <= 1.5 or (
                name_token == cluster["name_token"] and distance_km <= 5.0
            ):
                matched_cluster = cluster
                break
        if matched_cluster is None:
            clusters.append(
                {
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                    "name_token": name_token,
                    "canonical_name": point.name,
                    "canonical_source": point.layer_key,
                    "basin_posture": basin_posture,
                    "points": [point],
                }
            )
            continue
        matched_cluster["points"].append(point)  # type: ignore[index]
        if _prefer_pollen_name(
            candidate_name=point.name,
            candidate_source=point.layer_key,
            current_name=matched_cluster["canonical_name"],  # type: ignore[arg-type]
            current_source=matched_cluster["canonical_source"],  # type: ignore[arg-type]
        ):
            matched_cluster["canonical_name"] = point.name
            matched_cluster["canonical_source"] = point.layer_key

    candidates: list[LakeEvidenceCandidate] = []
    for cluster in clusters:
        points = tuple(cluster["points"])  # type: ignore[arg-type]
        canonical_name = str(cluster["canonical_name"])
        average_latitude = sum(point.latitude for point in points) / len(points)
        average_longitude = sum(point.longitude for point in points) / len(points)
        pollen_sources = tuple(sorted({point.layer_key for point in points}))
        supporting_names = tuple(sorted({point.name for point in points}))
        direct_pollen_signal = round(
            _weighted_average(
                (
                    min(1.0, len(pollen_sources) / 2.0),
                    0.35,
                ),
                (
                    min(1.0, len(points) / 4.0),
                    0.25,
                ),
                (
                    _time_aware_ratio(points),
                    0.2,
                ),
                (
                    1.0,
                    0.2,
                ),
            ),
            4,
        )
        candidates.append(
            LakeEvidenceCandidate(
                lake_name=canonical_name,
                lake_token=_build_lake_token(
                    canonical_name,
                    latitude=average_latitude,
                    longitude=average_longitude,
                ),
                latitude=average_latitude,
                longitude=average_longitude,
                basin_posture=str(cluster["basin_posture"]),
                direct_pollen_source_count=len(pollen_sources),
                direct_pollen_record_count=len(points),
                time_aware_direct_pollen_records=sum(
                    1
                    for point in points
                    if point.time_start_bp is not None and point.time_end_bp is not None
                ),
                pollen_sources=pollen_sources,
                supporting_pollen_names=supporting_names,
                direct_pollen_signal=direct_pollen_signal,
            )
        )
    return tuple(sorted(candidates, key=lambda candidate: candidate.lake_name))


def _build_raw_band_metrics(
    candidate: LakeEvidenceCandidate,
    candidates: Sequence[LakeEvidenceCandidate],
    human_points: Sequence[_PointEvidence],
    animal_points: Sequence[_PointEvidence],
    sead_points: Sequence[ContextPointRecord],
    raa_cells: Sequence[_DensityCell],
    *,
    radius_km: int,
) -> dict[str, int]:
    nearby_pollen_lake_count = sum(
        1
        for other in candidates
        if other.lake_token != candidate.lake_token
        and _distance_between_candidates(candidate, other) <= radius_km
    )
    human_locality_count = 0
    human_sample_count = 0
    for point in human_points:
        if (
            haversine_km(
                latitude_a=candidate.latitude,
                longitude_a=candidate.longitude,
                latitude_b=point.latitude,
                longitude_b=point.longitude,
            )
            <= radius_km
        ):
            human_locality_count += 1
            human_sample_count += point.sample_count
    animal_locality_count = 0
    animal_sample_count = 0
    for point in animal_points:
        if (
            haversine_km(
                latitude_a=candidate.latitude,
                longitude_a=candidate.longitude,
                latitude_b=point.latitude,
                longitude_b=point.longitude,
            )
            <= radius_km
        ):
            animal_locality_count += 1
            animal_sample_count += point.sample_count
    sead_site_count = sum(
        1
        for point in sead_points
        if haversine_km(
            latitude_a=candidate.latitude,
            longitude_a=candidate.longitude,
            latitude_b=point.latitude,
            longitude_b=point.longitude,
        )
        <= radius_km
    )
    raa_density_site_count = sum(
        cell.count
        for cell in raa_cells
        if _distance_to_density_cell(candidate, cell) <= radius_km
    )
    evidence_family_count = 1 + sum(
        1
        for has_evidence in (
            nearby_pollen_lake_count > 0,
            human_locality_count > 0,
            animal_locality_count > 0,
            sead_site_count > 0 or raa_density_site_count > 0,
        )
        if has_evidence
    )
    return {
        "nearby_pollen_lake_count": nearby_pollen_lake_count,
        "human_adna_locality_count": human_locality_count,
        "human_adna_sample_count": human_sample_count,
        "domesticated_animal_locality_count": animal_locality_count,
        "domesticated_animal_sample_count": animal_sample_count,
        "sead_site_count": sead_site_count,
        "raa_density_site_count": raa_density_site_count,
        "evidence_family_count": evidence_family_count,
    }


def _build_band_maxima(
    raw_scores: dict[str, dict[int, dict[str, int]]],
    *,
    radius_km: int,
) -> dict[str, int]:
    keys = (
        "nearby_pollen_lake_count",
        "human_adna_locality_count",
        "human_adna_sample_count",
        "domesticated_animal_locality_count",
        "domesticated_animal_sample_count",
        "sead_site_count",
        "raa_density_site_count",
    )
    return {
        key: max(
            raw_scores[lake_token][radius_km][key] for lake_token in raw_scores
        )
        for key in keys
    }


def _resolve_basin_posture(name: str, description: str) -> str:
    normalized_name = _normalize_text(name)
    normalized_description = _normalize_text(description)
    if any(term in normalized_name or term in normalized_description for term in _LAKE_NAME_TERMS):
        return "lake_basin"
    if any(term in normalized_name or term in normalized_description for term in _WETLAND_TERMS):
        return "wetland_basin"
    return "ambiguous_basin"


def _prefer_pollen_name(
    *,
    candidate_name: str,
    candidate_source: str,
    current_name: str,
    current_source: str,
) -> bool:
    if current_source != "neotoma-pollen" and candidate_source == "neotoma-pollen":
        return True
    if current_source == candidate_source and len(candidate_name) > len(current_name):
        return True
    return False


def _build_lake_token(name: str, *, latitude: float, longitude: float) -> str:
    return (
        f"sweden_lake:{_normalize_text(name)}:"
        f"{round(latitude, 4)}:{round(longitude, 4)}"
    )


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode(
        "ascii"
    )
    compact = re.sub(r"[^a-z0-9]+", "", normalized.casefold())
    return compact


def _time_aware_ratio(points: Sequence[ContextPointRecord]) -> float:
    if not points:
        return 0.0
    time_aware = sum(
        1 for point in points if point.time_start_bp is not None and point.time_end_bp is not None
    )
    return round(time_aware / len(points), 4)


def _distance_between_candidates(
    left: LakeEvidenceCandidate, right: LakeEvidenceCandidate
) -> float:
    return haversine_km(
        latitude_a=left.latitude,
        longitude_a=left.longitude,
        latitude_b=right.latitude,
        longitude_b=right.longitude,
    )


def _distance_to_density_cell(
    candidate: LakeEvidenceCandidate, cell: _DensityCell
) -> float:
    nearest_latitude = min(
        max(candidate.latitude, cell.min_latitude),
        cell.max_latitude,
    )
    nearest_longitude = min(
        max(candidate.longitude, cell.min_longitude),
        cell.max_longitude,
    )
    return haversine_km(
        latitude_a=candidate.latitude,
        longitude_a=candidate.longitude,
        latitude_b=nearest_latitude,
        longitude_b=nearest_longitude,
    )


def _normalized_ratio(value: int, maximum: int) -> float:
    if maximum <= 0:
        return 0.0
    return round(value / maximum, 4)


def _weighted_average(*pairs: tuple[float, float]) -> float:
    numerator = sum(value * weight for value, weight in pairs)
    denominator = sum(weight for _, weight in pairs)
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _band_score_for_radius(
    band_scores: Sequence[LakeEvidenceBandScore],
    *,
    radius_km: int,
) -> LakeEvidenceBandScore:
    for score in band_scores:
        if score.radius_km == radius_km:
            return score
    raise ValueError(f"Missing band score for radius {radius_km}")


def _optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None
