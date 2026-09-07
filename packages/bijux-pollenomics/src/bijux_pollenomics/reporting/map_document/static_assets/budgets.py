"""Size and responsiveness budgets for the static atlas transport."""

# The bootstrap carries the bounded 512-entry asset inventory, including two
# SHA-256 identities per entry. Keep enough room for that governed maximum while
# remaining well inside the total initial-load ceiling.
ATLAS_BOOTSTRAP_MAX_BYTES = 262_144
ATLAS_CHUNK_MAX_BYTES = 4_194_304
ATLAS_CHUNK_TARGET_BYTES = 2_097_152
# Compressed chunks can safely use more of the decoded-payload budget. The margin
# still bounds gzip/base64 overhead for an incompressible payload.
ATLAS_COMPRESSED_CHUNK_TARGET_BYTES = 3_140_000
# Preserve direct imports of the original detail-owned tuning name.
ATLAS_DETAIL_CHUNK_TARGET_BYTES = ATLAS_COMPRESSED_CHUNK_TARGET_BYTES
ATLAS_DOCUMENT_MAX_BYTES = 524_288
ATLAS_STATIC_ASSETS_MAX_BYTES = 134_217_728
ATLAS_STATIC_ASSETS_MAX_FILES = 512
ATLAS_INITIAL_MAX_REQUESTS = 4
ATLAS_INITIAL_MAX_BYTES = 1_048_576
ATLAS_INTERACTION_MAX_REQUESTS = 128
ATLAS_INTERACTION_MAX_BYTES = 67_108_864
ATLAS_FILTER_MAIN_THREAD_MAX_MS = 50
