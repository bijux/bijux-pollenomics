from __future__ import annotations

CAPABILITY_DIMENSIONS = (
    "site_identity",
    "coordinates",
    "four_country_coverage",
    "within_site_hierarchy",
    "numeric_chronology",
    "chronology_uncertainty",
    "relative_chronology",
    "taxon_identity",
    "native_ecological_class",
    "derived_pollen_group",
    "derived_ecological_role",
    "crop_cereal_resolution",
    "quantitative_observation",
    "observation_unit",
    "dataset_provenance",
    "pollen_propagation_event",
    "non_pollen_context",
)


SEAD_ADMITTED_ACQUISITION_ADMISSION = (
    "data/sead/raw/acquisitions/sead-full-evidence-39bfff6a-ce80714e/admission.json"
)


_SEAD_RUN_ID = "sead-full-evidence-39bfff6a-ce80714e"


_SEAD_SCOPE_ID = (
    "sha256:39bfff6abd80041dc01c554711b2a57daf6ee68e1757e3515668a18874ffb7d7"
)


_SEAD_BUILD_ID = (
    "sha256:ce80714e4c9e9974b24913e5da50f49854670ed642879c1ca5076499e1d56725"
)


_SEAD_ACQUISITION_MANIFEST_SHA256 = (
    "6fc2428046d148f9ce6c158f982afbbbbaea39de2132850a4fb8f41acf8a4c14"
)


_SEAD_ACQUISITION_BUNDLE_SHA256 = (
    "sha256:fdcda26e7de9a09383b0d9aae7ab7f9e8846c7cbf05513da17fdb8e329331ba9"
)


_SEAD_ADMISSION_SHA256 = (
    "69f93b6bd34e457bedc4047077024de1beefc900142f45051fab60dce03751ea"
)


_SEAD_PARENT_ADMISSION_SHA256 = (
    "168ad1efe6fa68cdb7789246a6cce16670377cdbacd14d1673beaab8ddd1ebd1"
)


_SEAD_COUNTRY_DECISIONS_SHA256 = (
    "e08c2fa2f70d9a3491b95a87b81c992ec3902051aa6e30c35dbcb0f86e214528"
)


_SEAD_EVIDENCE_MANIFEST_SHA256 = (
    "c6c709ddcdadf736f157636874e0cebfb152f90d83d0b90a25e3cfd9dfed1510"
)


_SEAD_NORMALIZED_ROOT = f"data/sead/normalized/acquisitions/{_SEAD_RUN_ID}"


SEAD_NORMALIZED_EVIDENCE_MANIFEST = (
    f"{_SEAD_NORMALIZED_ROOT}/evidence_materialization_manifest.json"
)


SEAD_NORMALIZED_OBSERVATIONS = (
    f"{_SEAD_NORMALIZED_ROOT}/source_native_observations.json"
)


SEAD_NORMALIZED_RELATIONS = f"{_SEAD_NORMALIZED_ROOT}/observation_relation_index.json"


SEAD_NORMALIZED_EVIDENCE_EVENTS = f"{_SEAD_NORMALIZED_ROOT}/evidence_events.json"


_SEAD_NORMALIZED_CHRONOLOGY = f"{_SEAD_NORMALIZED_ROOT}/chronology_claims.json"


NEOTOMA_CLASSIFICATION_EVIDENCE = "data/neotoma/review/classification_evidence.json"


NEOTOMA_PROPAGATION_EVIDENCE = "data/neotoma/derived/pollen_propagation_evidence.json"


_SUPPORT_STATUSES = frozenset({"supported", "partial", "unsupported"})


_MATERIALIZATION_STATUSES = frozenset(
    {"complete", "partial", "missing", "not_applicable"}
)


_NORMATIVE_CONTRACT_ID = "bijux-pollenomics-source-capability-matrix"


_NORMATIVE_CONTRACT_VERSION = "1.0.0"


_NORMATIVE_SOURCE_KEYS = (
    "animal_adna",
    "boundaries",
    "landclim",
    "neotoma",
    "raa",
    "sead",
    "svar",
)
