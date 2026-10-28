# Temporal metadata transport

`TemporalSemantics` keeps its existing `temporal-semantics.v1` fields. Callers may
supply `source_metadata` to `build_temporal_semantics` or the dataclass to retain
explicit source assertions such as `reference_epoch`, `calibration_status`,
`age_type`, `model`, `method`, laboratory identifiers, or claim provenance. These
fields serialize alongside the existing fields and survive
`normalize_temporal_semantics_payload` unchanged. Explicit JSON null remains null;
omitted metadata stays omitted and means that the source did not declare it.
No epoch, calibration, model, or method is inferred from numeric BP values.

Metadata must contain finite JSON values with string object keys. Nested objects
and lists are copied, and metadata cannot replace canonical computed fields.
Invalid metadata raises `ValueError`. Metadata retention does not establish
comparability or authorize a conversion between source age types. Existing
precision, comparability, and refusal fields continue to govern numeric use.

Schema-less legacy input remains accepted. An explicit unsupported schema version
is retained, its supplied source metadata survives, and its normalized numeric
support is refused with `unsupported_temporal_semantics_schema`; it is never
silently labelled as the current schema.

The external context reader is a separate source-text intake. It accepts explicit
numeric text, preserves source properties, and projects only exact, nonnegative
integer BP years within the browser safe integer range. Fractional, unsafe,
nonfinite, reversed, and partial values retain named refusal instead of rounding
into a present-day observation. Declared contextual or refused semantics cannot
become numeric support merely because external properties contain numbers.
Canonical map payload readers accept actual finite, nonnegative JSON numbers;
they do not coerce strings or booleans. Analytical fractional intervals remain
supported by the canonical interval algebra.
