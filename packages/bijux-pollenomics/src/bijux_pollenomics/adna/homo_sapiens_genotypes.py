from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import DEFAULT_AADR_VERSION, DEFAULT_DATA_ROOT
from .paths import ADNA_SPECIES_DIR

__all__ = [
    "HomoSapiensGenotypeArtifact",
    "HomoSapiensGenotypeContract",
    "build_homo_sapiens_genotype_contract",
]


@dataclass(frozen=True)
class HomoSapiensGenotypeArtifact:
    """One future genotype artifact that belongs under Homo sapiens only."""

    artifact_kind: str
    relative_path: str
    required_for_ingestion: bool
    currently_present: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "artifact_kind": self.artifact_kind,
            "relative_path": self.relative_path,
            "required_for_ingestion": self.required_for_ingestion,
            "currently_present": self.currently_present,
        }


@dataclass(frozen=True)
class HomoSapiensGenotypeContract:
    """Future-facing contract for Homo sapiens genotype ingestion ownership."""

    schema_version: str
    species_latin_name: str
    source_family: str
    source_release: str
    tracked_root: str
    required_artifacts: tuple[HomoSapiensGenotypeArtifact, ...]
    ingestion_ready: bool
    ingestion_blockers: tuple[str, ...]
    nonhuman_boundary: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_latin_name": self.species_latin_name,
            "source_family": self.source_family,
            "source_release": self.source_release,
            "tracked_root": self.tracked_root,
            "required_artifacts": [item.as_dict() for item in self.required_artifacts],
            "ingestion_ready": self.ingestion_ready,
            "ingestion_blockers": list(self.ingestion_blockers),
            "nonhuman_boundary": self.nonhuman_boundary,
        }


def build_homo_sapiens_genotype_contract(
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    version: str = DEFAULT_AADR_VERSION,
) -> HomoSapiensGenotypeContract:
    """Build the future genotype-ingestion contract for Homo sapiens."""
    tracked_root = (
        Path(data_root)
        / ADNA_SPECIES_DIR.removeprefix("data/")
        / "homo_sapiens"
        / "raw"
        / "aadr"
        / version
    )
    required_artifacts = tuple(
        HomoSapiensGenotypeArtifact(
            artifact_kind=kind,
            relative_path=f"{ADNA_SPECIES_DIR}/homo_sapiens/raw/aadr/{version}/{filename}",
            required_for_ingestion=True,
            currently_present=(tracked_root / filename).exists(),
        )
        for kind, filename in (
            ("geno", f"{version}.geno"),
            ("ind", f"{version}.ind"),
            ("snp", f"{version}.snp"),
        )
    )
    blockers = tuple(
        artifact.artifact_kind for artifact in required_artifacts if not artifact.currently_present
    )
    return HomoSapiensGenotypeContract(
        schema_version="homo-sapiens-genotype-contract.v1",
        species_latin_name="Homo sapiens",
        source_family="AADR",
        source_release=version,
        tracked_root=str(tracked_root),
        required_artifacts=required_artifacts,
        ingestion_ready=not blockers,
        ingestion_blockers=tuple(
            f"missing_{artifact_kind}_artifact" for artifact_kind in blockers
        ),
        nonhuman_boundary=(
            "These genotype artifacts belong only to Homo sapiens AADR ingestion. "
            "Non-human species must not mimic AADR .geno/.ind/.snp layout as a fake general model."
        ),
    )
