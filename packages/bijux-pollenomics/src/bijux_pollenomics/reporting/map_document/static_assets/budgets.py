"""Size and responsiveness budgets for the static atlas transport."""

ATLAS_BOOTSTRAP_MAX_BYTES = 65_536
ATLAS_CHUNK_MAX_BYTES = 4_194_304
ATLAS_CHUNK_TARGET_BYTES = 2_097_152
# Compressed detail chunks can safely use more of the decoded-payload budget than
# JSON node chunks, whose script wrapper expands quotes and escape sequences.
# The margin also bounds gzip/base64 overhead for an incompressible detail payload.
ATLAS_DETAIL_CHUNK_TARGET_BYTES = 3_140_000
ATLAS_DOCUMENT_MAX_BYTES = 524_288
ATLAS_STATIC_ASSETS_MAX_BYTES = 134_217_728
ATLAS_STATIC_ASSETS_MAX_FILES = 512
ATLAS_INITIAL_MAX_REQUESTS = 4
ATLAS_INITIAL_MAX_BYTES = 1_048_576
ATLAS_INTERACTION_MAX_REQUESTS = 128
ATLAS_INTERACTION_MAX_BYTES = 67_108_864
ATLAS_FILTER_MAIN_THREAD_MAX_MS = 50
