# Calendar age relations

`bijux_pollenomics.core.temporal_relations.compare_bp_intervals` returns a typed
pair relation: `OVERLAPPING`, `LEFT_YOUNGER`, `LEFT_OLDER`, or `NOT_COMPARABLE`.
BP direction is younger/lower to older/higher. The result retains both original
`BpInterval` values and both supplied `TemporalComparisonBasis` objects. An
overlap retains its exact closed support; separated intervals retain their
nonnegative separation in years. Touching endpoints overlap, including genuine
zero and fractional calendar-year bounds.

Each source comparison needs an explicit basis for each operand: age type,
reference epoch as an integer calendar CE year, and numeric comparability
posture. Only the exact `calendar_bp` age type is supported. The reference epochs
must agree; they are never inferred from the label BP, a publication year, or
numeric bounds. Numeric caveats and mixed-support postures remain attached to
the result through their original basis objects.

Missing intervals, missing bases, unknown or unsupported age types, different
epochs, contextual postures, and source refusals return `NOT_COMPARABLE` with a
reason. They produce neither an overlap nor a numeric separation. Radiocarbon
or other age systems need their own governed source interpretation or
transformation before entering this calendar-year API. No conversion,
calibration, source authentication, or scientific acceptance occurs here.

The existing `closed_bp_intervals_overlap` boolean API keeps its interval-algebra
contract. Its caller already supplies canonical interval values, and it delegates
to the same typed algebra classifier. It has no source metadata and establishes
no source comparability. Source-aware callers must use the explicit comparison
API after retaining their original source assertions and establishing the
required basis. A missing date must not enter the boolean API as a fabricated
zero-width interval.

The relation dataclasses are typed returned values, not untrusted JSON decoders
or source authenticators. Their constructors do not establish source provenance.
The interval class stays in `core.temporal_semantics`; the relation module owns
pair classification. A local import in the established boolean helper keeps
this dependency direction without moving the interval type or changing its
import identity.

Closed nonnegative calendar intervals do not replace half-open scientific bins,
signed calendar-support profiles, raw source assertions, source coverage hulls,
or immutable native reference implementations. Those consumers retain their
own explicit boundary and admission rules. Reusing the classifier requires
proving that those rules agree, including exact boundaries and non-comparable
inputs; matching numeric field names is insufficient.
