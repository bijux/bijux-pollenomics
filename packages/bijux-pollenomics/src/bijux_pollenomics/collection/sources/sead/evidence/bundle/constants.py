from __future__ import annotations

from typing import Final


EVIDENCE_BUNDLE_SCHEMA_VERSION: Final = "sead-source-native-evidence-bundle.v1"


OBSERVATION_SCHEMA_VERSION: Final = "sead-source-native-observation.v1"


RELATION_INDEX_SCHEMA_VERSION: Final = "sead-evidence-relation-index.v1"


EVENT_BUNDLE_SCHEMA_VERSION: Final = "sead-evidence-event-bundle.v1"


EVIDENCE_MANIFEST_SCHEMA_VERSION: Final = "sead-evidence-materialization-manifest.v1"


MULTIPART_SCHEMA_VERSION: Final = "sead-evidence-multipart.v1"


_MAX_GOVERNED_FILE_BYTES: Final = 50 * 1024 * 1024


_PART_TARGET_BYTES: Final = 12 * 1024 * 1024


_OBSERVATION_TABLES: Final = (
    ("tbl_abundances", "abundance_id", "abundance"),
    ("tbl_analysis_taxon_counts", "analysis_taxon_count_id", "value"),
    ("tbl_analysis_values", "analysis_value_id", "analysis_value"),
    ("tbl_measured_values", "measured_value_id", "measured_value"),
)


_ANALYSIS_VALUE_COMPONENTS: Final = (
    "tbl_analysis_numerical_values",
    "tbl_analysis_integer_values",
    "tbl_analysis_categorical_values",
    "tbl_analysis_boolean_values",
)


_ABUNDANCE_COMPONENTS: Final = (
    "tbl_abundance_ident_levels",
    "tbl_abundance_modifications",
    "tbl_abundance_properties",
)


_DIMENSION_RELATION_TABLES: Final = (
    (
        "tbl_analysis_value_dimensions",
        "analysis_value_dimension_id",
        "analysis_value_id",
        "analysis_value",
    ),
    (
        "tbl_measured_value_dimensions",
        "measured_value_dimension_id",
        "measured_value_id",
        "measured_value",
    ),
    (
        "tbl_analysis_entity_dimensions",
        "analysis_entity_dimension_id",
        "analysis_entity_id",
        "analysis_entity",
    ),
    (
        "tbl_sample_dimensions",
        "sample_dimension_id",
        "physical_sample_id",
        "physical_sample",
    ),
    (
        "tbl_sample_group_dimensions",
        "sample_group_dimension_id",
        "sample_group_id",
        "sample_group",
    ),
)
