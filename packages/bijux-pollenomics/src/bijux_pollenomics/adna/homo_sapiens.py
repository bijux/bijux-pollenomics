from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
import csv
import json
from pathlib import Path

from ..core.bp_time import build_bp_interval_label, midpoint_bp_year
from .homo_sapiens_schema import (
    resolve_homo_sapiens_schema,
    sample_time_interval,
    sample_time_label,
    sample_time_mean,
    schema_value,
)
from .locality import build_locality_identity
from .manifests import build_species_manifest
from .models import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaSampleIdentity,
    AdnaSampleRecord,
)
from .paths import ADNA_SPECIES_DIR
from .runtime import AdnaSampleQuery, AdnaSourceBundle, AdnaSpeciesRuntimeManifest

__all__ = [
    "build_homo_sapiens_runtime_manifest",
    "build_homo_sapiens_runtime_manifest_for_version_dir",
    "discover_homo_sapiens_anno_files",
    "iter_homo_sapiens_samples_from_anno",
    "load_homo_sapiens_country_samples",
    "load_homo_sapiens_samples",
]

HOMO_SAPIENS_REVIEW_STRENGTH = "curated_release_metadata"
HOMO_SAPIENS_PROVENANCE_QUALITY = "release_manifest_pinned"
HOMO_SAPIENS_RECORD_MODALITY = "metadata_only"


def build_homo_sapiens_runtime_manifest(
    *,
    data_root: Path,
    version: str,
) -> AdnaSpeciesRuntimeManifest:
    """Build the canonical Homo sapiens runtime manifest for AADR metadata support."""
    species_manifest = build_species_manifest("Homo sapiens")
    source_root = (
        Path(data_root)
        / ADNA_SPECIES_DIR.removeprefix("data/")
        / species_manifest.root_slug
        / "raw"
        / "aadr"
    )
    release_dir = source_root / version
    release_manifest = Path(data_root) / "aadr" / version / "release_manifest.json"
    dataset_names = _release_dataset_names(release_manifest, release_dir)
    return AdnaSpeciesRuntimeManifest(
        schema_version="adna-runtime-manifest.v1",
        species_manifest=species_manifest,
        source_bundles=(
            AdnaSourceBundle(
                source_family="AADR",
                source_release=version,
                bundle_kind="source_release",
                tracked_root=str(release_dir),
                release_manifest_path=str(release_manifest),
                dataset_names=dataset_names,
                record_modality=HOMO_SAPIENS_RECORD_MODALITY,
                review_strength=HOMO_SAPIENS_REVIEW_STRENGTH,
                provenance_quality=HOMO_SAPIENS_PROVENANCE_QUALITY,
            ),
        ),
        analysis_boundary=(
            "Homo sapiens runtime support is AADR metadata normalization only. "
            "This surface does not imply genotype-aware analysis."
        ),
        runtime_ready=True,
    )


def build_homo_sapiens_runtime_manifest_for_version_dir(
    version_dir: Path,
) -> AdnaSpeciesRuntimeManifest:
    """Build a Homo sapiens runtime manifest from one concrete version directory."""
    version_dir = Path(version_dir)
    if not version_dir.name:
        raise ValueError("A version directory is required for Homo sapiens runtime loading")
    species_manifest = build_species_manifest("Homo sapiens")
    release_manifest = version_dir / "release_manifest.json"
    return AdnaSpeciesRuntimeManifest(
        schema_version="adna-runtime-manifest.v1",
        species_manifest=species_manifest,
        source_bundles=(
            AdnaSourceBundle(
                source_family="AADR",
                source_release=version_dir.name,
                bundle_kind="source_release",
                tracked_root=str(version_dir),
                release_manifest_path=str(release_manifest),
                dataset_names=_release_dataset_names(release_manifest, version_dir),
                record_modality=HOMO_SAPIENS_RECORD_MODALITY,
                review_strength=HOMO_SAPIENS_REVIEW_STRENGTH,
                provenance_quality=HOMO_SAPIENS_PROVENANCE_QUALITY,
            ),
        ),
        analysis_boundary=(
            "Homo sapiens runtime support is AADR metadata normalization only. "
            "This surface does not imply genotype-aware analysis."
        ),
        runtime_ready=True,
    )


def load_homo_sapiens_country_samples(
    manifest: AdnaSpeciesRuntimeManifest, country: str
) -> tuple[list[AdnaSampleRecord], Counter[str]]:
    """Compatibility helper for country-scoped Homo sapiens sample loading."""
    return load_homo_sapiens_samples(
        manifest=manifest,
        query=AdnaSampleQuery(political_entity=country),
    )


def load_homo_sapiens_samples(
    *,
    manifest: AdnaSpeciesRuntimeManifest,
    query: AdnaSampleQuery | None = None,
) -> tuple[list[AdnaSampleRecord], Counter[str]]:
    """Load normalized Homo sapiens AADR samples via the species runtime manifest."""
    if manifest.species.latin_name != "Homo sapiens":
        raise ValueError(
            "Homo sapiens AADR loader cannot be used for species "
            f"{manifest.species.latin_name}"
        )
    bundle = _single_human_bundle(manifest)
    normalized_query = query.normalized() if query is not None else AdnaSampleQuery()
    combined: dict[str, AdnaSampleRecord] = {}
    dataset_counts: Counter[str] = Counter()

    for anno_path in discover_homo_sapiens_anno_files(Path(bundle.tracked_root)):
        dataset_name = anno_path.parent.name
        for sample in iter_homo_sapiens_samples_from_anno(
            anno_path,
            dataset_name=dataset_name,
            source_release=bundle.source_release,
            source_family=bundle.source_family,
            record_modality=bundle.record_modality,
            review_strength=bundle.review_strength,
            provenance_quality=bundle.provenance_quality,
        ):
            if not _sample_matches_query(sample, normalized_query):
                continue
            dataset_counts[dataset_name] += 1
            existing = combined.get(sample.genetic_id)
            if existing is None:
                combined[sample.genetic_id] = sample
                continue
            combined[sample.genetic_id] = merge_duplicate_samples(existing, sample)

    samples = sorted(
        combined.values(),
        key=lambda sample: (
            sample.locality.casefold(),
            sample.master_id.casefold(),
            sample.genetic_id.casefold(),
        ),
    )
    return samples, dataset_counts


def discover_homo_sapiens_anno_files(release_dir: Path) -> list[Path]:
    """Find all governed AADR anno files inside the Homo sapiens runtime surface."""
    files = sorted(path for path in release_dir.glob("*/*.anno") if path.is_file())
    if not files:
        raise FileNotFoundError(f"No .anno files found under {release_dir}")
    return files


def iter_homo_sapiens_samples_from_anno(
    path: Path,
    *,
    dataset_name: str,
    source_release: str,
    source_family: str,
    record_modality: str,
    review_strength: str,
    provenance_quality: str,
) -> Iterable[AdnaSampleRecord]:
    """Yield normalized Homo sapiens sample records from one AADR anno file."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        schema = resolve_homo_sapiens_schema(reader.fieldnames or ())
        for row in reader:
            genetic_id = _clean_text(schema_value(row, schema, "genetic_id"))
            latitude_text = _clean_text(schema_value(row, schema, "latitude"))
            longitude_text = _clean_text(schema_value(row, schema, "longitude"))
            if not genetic_id or not latitude_text or not longitude_text:
                continue
            try:
                latitude = float(latitude_text)
                longitude = float(longitude_text)
            except ValueError:
                continue
            time_interval = sample_time_interval(row, schema)
            yield AdnaSampleRecord(
                identity=AdnaSampleIdentity(
                    namespace="homo_sapiens:aadr_genetic_id",
                    stable_token=genetic_id,
                    accession_lineage=(
                        "species:Homo sapiens",
                        f"source:{source_family}",
                        f"release:{source_release}",
                        f"dataset:{dataset_name}",
                        f"genetic_id:{genetic_id}",
                    ),
                ),
                locality_identity=build_locality_identity(
                    species_name="Homo sapiens",
                    source_family=source_family,
                    locality_text=_clean_text(schema_value(row, schema, "locality"))
                    or "Unspecified locality",
                    political_entity=_clean_text(
                        schema_value(row, schema, "political_entity")
                    ),
                    latitude_text=latitude_text,
                    longitude_text=longitude_text,
                ),
                species_latin_name="Homo sapiens",
                species_common_name="human",
                source_family=source_family,
                source_release=source_release,
                record_modality=record_modality,
                review_strength=review_strength,
                provenance_quality=provenance_quality,
                master_id=_clean_text(schema_value(row, schema, "master_id")),
                group_id=_clean_text(schema_value(row, schema, "group_id")),
                locality=_clean_text(schema_value(row, schema, "locality"))
                or "Unspecified locality",
                political_entity=_clean_text(
                    schema_value(row, schema, "political_entity")
                ),
                coordinates=AdnaCoordinate(
                    latitude=latitude,
                    longitude=longitude,
                    latitude_text=latitude_text,
                    longitude_text=longitude_text,
                    confidence="unknown",
                ),
                publication=_clean_text(schema_value(row, schema, "publication")),
                year_first_published=_clean_text(
                    schema_value(row, schema, "year_first_published")
                ),
                full_date=_clean_text(schema_value(row, schema, "full_date")),
                chronology=AdnaChronology(
                    original_text=sample_time_label(row, schema),
                    time_start_bp=time_interval[0] if time_interval is not None else None,
                    time_end_bp=time_interval[1] if time_interval is not None else None,
                    time_mean_bp=sample_time_mean(row, schema),
                    date_stddev_bp=_clean_text(
                        schema_value(row, schema, "date_stddev_bp")
                    ),
                    dating_basis=_dating_basis(row, schema, time_interval),
                ),
                data_type=_clean_text(schema_value(row, schema, "data_type")),
                molecular_sex=_clean_text(schema_value(row, schema, "molecular_sex")),
                datasets=(dataset_name,),
            )


def merge_duplicate_samples(
    existing: AdnaSampleRecord, sample: AdnaSampleRecord
) -> AdnaSampleRecord:
    """Merge duplicate Homo sapiens AADR rows across datasets."""
    merged_datasets = tuple(sorted(set(existing.datasets) | set(sample.datasets)))
    merged_interval = merge_sample_time_interval(existing, sample)
    return AdnaSampleRecord(
        identity=AdnaSampleIdentity(
            namespace=existing.sample_namespace,
            stable_token=existing.genetic_id,
            accession_lineage=tuple(
                dict.fromkeys(existing.accession_lineage + sample.accession_lineage)
            ),
        ),
        locality_identity=existing.locality_identity,
        species_latin_name=existing.species_latin_name,
        species_common_name=existing.species_common_name,
        source_family=existing.source_family,
        source_release=existing.source_release,
        record_modality=existing.record_modality,
        review_strength=existing.review_strength,
        provenance_quality=existing.provenance_quality,
        master_id=_pick_value(existing.master_id, sample.master_id),
        group_id=_pick_value(existing.group_id, sample.group_id),
        locality=_pick_value(existing.locality, sample.locality),
        political_entity=_pick_value(existing.political_entity, sample.political_entity),
        coordinates=AdnaCoordinate(
            latitude=existing.latitude,
            longitude=existing.longitude,
            latitude_text=_pick_value(existing.latitude_text, sample.latitude_text),
            longitude_text=_pick_value(existing.longitude_text, sample.longitude_text),
            confidence=_pick_value(
                existing.coordinate_confidence, sample.coordinate_confidence
            )
            or "unknown",
        ),
        publication=_pick_value(existing.publication, sample.publication),
        year_first_published=_pick_value(
            existing.year_first_published, sample.year_first_published
        ),
        full_date=_pick_value(existing.full_date, sample.full_date),
        chronology=AdnaChronology(
            original_text=_pick_time_label(existing, sample, merged_interval),
            time_start_bp=merged_interval[0] if merged_interval is not None else None,
            time_end_bp=merged_interval[1] if merged_interval is not None else None,
            time_mean_bp=_mean_bp_from_samples(existing, sample, merged_interval),
            date_stddev_bp=_pick_value(existing.date_stddev_bp, sample.date_stddev_bp),
            dating_basis=_pick_value(existing.dating_basis, sample.dating_basis)
            or "unknown",
        ),
        data_type=_pick_value(existing.data_type, sample.data_type),
        molecular_sex=_pick_value(existing.molecular_sex, sample.molecular_sex),
        datasets=merged_datasets,
    )


def merge_sample_time_interval(
    left: AdnaSampleRecord, right: AdnaSampleRecord
) -> tuple[int, int] | None:
    """Merge two sample intervals into one BP span."""
    intervals = [
        interval
        for interval in (
            (left.time_start_bp, left.time_end_bp)
            if left.time_start_bp is not None and left.time_end_bp is not None
            else None,
            (right.time_start_bp, right.time_end_bp)
            if right.time_start_bp is not None and right.time_end_bp is not None
            else None,
        )
        if interval is not None
    ]
    if not intervals:
        return None
    return (min(start for start, _ in intervals), max(end for _, end in intervals))


def _release_dataset_names(
    release_manifest_path: Path, release_dir: Path
) -> tuple[str, ...]:
    if not release_manifest_path.exists():
        return tuple(
            sorted(
                path.name
                for path in release_dir.iterdir()
                if path.is_dir() and any(path.glob("*.anno"))
            )
        )
    payload = json.loads(release_manifest_path.read_text(encoding="utf-8"))
    anno_files = payload.get("anno_files", [])
    if not isinstance(anno_files, list):
        return ()
    names = {
        str(row.get("dataset_name", "")).strip()
        for row in anno_files
        if isinstance(row, dict) and str(row.get("dataset_name", "")).strip()
    }
    return tuple(sorted(names))


def _single_human_bundle(manifest: AdnaSpeciesRuntimeManifest) -> AdnaSourceBundle:
    if len(manifest.source_bundles) != 1:
        raise ValueError("Homo sapiens runtime manifest must expose exactly one source bundle")
    return manifest.source_bundles[0]


def _sample_matches_query(sample: AdnaSampleRecord, query: AdnaSampleQuery) -> bool:
    if query.political_entity and sample.political_entity.casefold() != query.political_entity.casefold():
        return False
    if query.locality_token and sample.locality_token != query.locality_token:
        return False
    if query.dataset_names and not set(sample.datasets).intersection(query.dataset_names):
        return False
    if query.modalities and sample.record_modality not in query.modalities:
        return False
    if query.provenance_qualities and sample.provenance_quality not in query.provenance_qualities:
        return False
    if query.review_strengths and sample.review_strength not in query.review_strengths:
        return False
    if query.time_start_bp is not None or query.time_end_bp is not None:
        if sample.time_start_bp is None or sample.time_end_bp is None:
            return False
        if query.time_start_bp is not None and sample.time_end_bp < query.time_start_bp:
            return False
        if query.time_end_bp is not None and sample.time_start_bp > query.time_end_bp:
            return False
    return True


def _pick_value(left: str, right: str) -> str:
    return left or right


def _mean_bp_from_samples(
    left: AdnaSampleRecord,
    right: AdnaSampleRecord,
    merged_interval: tuple[int, int] | None,
) -> int | None:
    for value in (left.time_mean_bp, right.time_mean_bp):
        if value is not None:
            return value
    if merged_interval is None:
        return None
    return midpoint_bp_year(merged_interval[0], merged_interval[1])


def _pick_time_label(
    left: AdnaSampleRecord,
    right: AdnaSampleRecord,
    merged_interval: tuple[int, int] | None,
) -> str:
    for value in (left.time_label, right.time_label, left.full_date, right.full_date):
        if _clean_text(value):
            return _clean_text(value)
    if merged_interval is None:
        return ""
    return build_bp_interval_label(merged_interval[0], merged_interval[1])


def _dating_basis(
    row: Mapping[str, str],
    schema: Mapping[str, str | None],
    time_interval: tuple[int, int] | None,
) -> str:
    if time_interval is not None and _clean_text(schema_value(row, schema, "date_stddev_bp")):
        return "bp_mean_and_stddev"
    if time_interval is not None:
        return "bp_window"
    if _clean_text(schema_value(row, schema, "full_date")):
        return "archaeological_period"
    return "unknown"


def _clean_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip()
