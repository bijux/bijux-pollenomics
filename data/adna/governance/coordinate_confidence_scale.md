# Coordinate confidence scale

- `exact`: direct published coordinates or explicit archive coordinate pairs.
- `approximate`: named-place geocoding where the place is explicit but the archived source does not ship the exact point pair.
- `inferred`: indirect coordinate derivation retained only for non-public internal context.
- `withheld`: the repository refuses point-level mapping because the current geography is unresolved or region-only.
- `unknown`: legacy or foreign records where the confidence basis is not yet normalized.

Animal point publication is currently allowed only for rows whose coordinate provenance keeps an explicit basis and whose mapping posture is `mappable_point`.