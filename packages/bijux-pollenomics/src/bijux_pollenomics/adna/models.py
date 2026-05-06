from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ADNA_COORDINATE_CONFIDENCE",
    "ADNA_DATING_BASES",
    "AdnaChronology",
    "AdnaCoordinate",
    "AdnaLocalityIdentity",
    "AdnaLocalitySummary",
    "AdnaSampleIdentity",
    "AdnaSampleRecord",
]

ADNA_COORDINATE_CONFIDENCE = (
    "exact",
    "approximate",
    "inferred",
    "withheld",
    "unknown",
)
ADNA_DATING_BASES = (
    "bp_mean_and_stddev",
    "bp_window",
    "archaeological_period",
    "historical_attribution",
    "unknown",
)


@dataclass(frozen=True)
class AdnaCoordinate:
    """Typed coordinate contract for ancient-DNA records."""

    latitude: float | None
    longitude: float | None
    latitude_text: str
    longitude_text: str
    confidence: str = "unknown"


@dataclass(frozen=True)
class AdnaChronology:
    """Typed chronology contract for ancient-DNA records."""

    original_text: str
    time_start_bp: int | None
    time_end_bp: int | None
    time_mean_bp: int | None
    date_stddev_bp: str = ""
    dating_basis: str = "unknown"


@dataclass(frozen=True)
class AdnaSampleIdentity:
    """Canonical identity namespace for one normalized ancient-DNA sample."""

    namespace: str
    stable_token: str
    accession_lineage: tuple[str, ...]


@dataclass(frozen=True)
class AdnaLocalityIdentity:
    """Canonical shared locality anchor for species-aware ancient-DNA records."""

    namespace: str
    stable_token: str
    locality_text: str
    political_entity: str | None
    source_anchor_tokens: tuple[str, ...]


@dataclass(frozen=True)
class AdnaSampleRecord:
    """Species-aware normalized ancient-DNA sample record."""

    identity: AdnaSampleIdentity
    locality_identity: AdnaLocalityIdentity
    species_latin_name: str
    species_common_name: str
    source_family: str
    source_release: str
    record_modality: str
    review_strength: str
    provenance_quality: str
    master_id: str
    group_id: str
    locality: str | None
    political_entity: str | None
    coordinates: AdnaCoordinate
    publication: str
    year_first_published: str
    full_date: str
    chronology: AdnaChronology
    data_type: str
    molecular_sex: str
    datasets: tuple[str, ...]

    @property
    def genetic_id(self) -> str:
        return self.identity.stable_token

    @property
    def sample_namespace(self) -> str:
        return self.identity.namespace

    @property
    def accession_lineage(self) -> tuple[str, ...]:
        return self.identity.accession_lineage

    @property
    def locality_namespace(self) -> str:
        return self.locality_identity.namespace

    @property
    def locality_token(self) -> str:
        return self.locality_identity.stable_token

    @property
    def latitude(self) -> float | None:
        return self.coordinates.latitude

    @property
    def longitude(self) -> float | None:
        return self.coordinates.longitude

    @property
    def latitude_text(self) -> str:
        return self.coordinates.latitude_text

    @property
    def longitude_text(self) -> str:
        return self.coordinates.longitude_text

    @property
    def coordinate_confidence(self) -> str:
        return self.coordinates.confidence

    @property
    def date_mean_bp(self) -> str:
        return str(self.chronology.time_mean_bp) if self.chronology.time_mean_bp is not None else ""

    @property
    def date_stddev_bp(self) -> str:
        return self.chronology.date_stddev_bp

    @property
    def time_start_bp(self) -> int | None:
        return self.chronology.time_start_bp

    @property
    def time_end_bp(self) -> int | None:
        return self.chronology.time_end_bp

    @property
    def time_mean_bp(self) -> int | None:
        return self.chronology.time_mean_bp

    @property
    def time_label(self) -> str:
        return self.chronology.original_text

    @property
    def dating_basis(self) -> str:
        return self.chronology.dating_basis


@dataclass(frozen=True)
class AdnaLocalitySummary:
    """Species-aware locality summary derived from normalized ancient-DNA samples."""

    identity: AdnaLocalityIdentity
    species_latin_name: str
    species_common_name: str
    source_family: str
    source_releases: tuple[str, ...]
    record_modalities: tuple[str, ...]
    review_strengths: tuple[str, ...]
    provenance_qualities: tuple[str, ...]
    locality: str | None
    coordinates: AdnaCoordinate
    sample_count: int
    sample_ids: tuple[str, ...]
    datasets: tuple[str, ...]
    chronology: AdnaChronology
    sample_namespace: str

    @property
    def latitude(self) -> float | None:
        return self.coordinates.latitude

    @property
    def longitude(self) -> float | None:
        return self.coordinates.longitude

    @property
    def latitude_text(self) -> str:
        return self.coordinates.latitude_text

    @property
    def longitude_text(self) -> str:
        return self.coordinates.longitude_text

    @property
    def coordinate_confidence(self) -> str:
        return self.coordinates.confidence

    @property
    def locality_namespace(self) -> str:
        return self.identity.namespace

    @property
    def locality_token(self) -> str:
        return self.identity.stable_token

    @property
    def time_start_bp(self) -> int | None:
        return self.chronology.time_start_bp

    @property
    def time_end_bp(self) -> int | None:
        return self.chronology.time_end_bp

    @property
    def time_mean_bp(self) -> int | None:
        return self.chronology.time_mean_bp

    @property
    def time_label(self) -> str:
        return self.chronology.original_text

    @property
    def dating_basis(self) -> str:
        return self.chronology.dating_basis
