# API Contracts

Repository API contracts live under `apis/<package>/v1/` for each public package.

Current package contract directories:

- `apis/bijux-pollenomics/v1`

Each package contract directory includes:

- `schema.yaml` as the source OpenAPI contract
- `pinned_openapi.json` as the frozen canonical JSON rendering
- `schema.hash` as the SHA-256 digest of the pinned JSON
