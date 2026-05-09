"""Species-owned aDNA contracts, runtime helpers, and tracked program surfaces."""

from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "ADNA_MODALITIES": ".definitions",
    "ADNA_SUPPORT_STATUSES": ".definitions",
    "AdnaSpeciesDefinition": ".definitions",
    "build_species_support_matrix": ".definitions",
    "resolve_species_definition": ".definitions",
    "BovineCombinedClaimRule": ".bovines",
    "BovineSpeciesSupportRow": ".bovines",
    "BovineSupportProgram": ".bovines",
    "build_bovine_support_program": ".bovines",
    "build_homo_sapiens_runtime_manifest": ".homo_sapiens",
    "build_homo_sapiens_runtime_manifest_for_version_dir": ".homo_sapiens",
    "discover_homo_sapiens_anno_files": ".homo_sapiens",
    "iter_homo_sapiens_samples_from_anno": ".homo_sapiens",
    "load_homo_sapiens_country_samples": ".homo_sapiens",
    "load_homo_sapiens_samples": ".homo_sapiens",
    "HomoSapiensGenotypeArtifact": ".homo_sapiens_genotypes",
    "HomoSapiensGenotypeContract": ".homo_sapiens_genotypes",
    "build_homo_sapiens_genotype_contract": ".homo_sapiens_genotypes",
    "resolve_homo_sapiens_schema": ".homo_sapiens_schema",
    "sample_time_interval": ".homo_sapiens_schema",
    "sample_time_label": ".homo_sapiens_schema",
    "sample_time_mean": ".homo_sapiens_schema",
    "schema_value": ".homo_sapiens_schema",
    "materialize_tracked_species_adna": ".tracked_data",
    "materialize_tracked_species_root": ".tracked_data",
    "tracked_species_slugs": ".tracked_data",
    "TRACKED_ADNA_SPECIES": ".tracked_species",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> object:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
