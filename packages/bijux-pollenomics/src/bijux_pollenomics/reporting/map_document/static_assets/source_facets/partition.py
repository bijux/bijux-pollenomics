"""Pack literal source labels together while retaining original feature positions."""

from collections.abc import Mapping


def native_taxon(value: object) -> int:
    """Use the existing source taxon identifier domain without changing its bytes."""
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and value.isascii() and value.isdigit():
        return int(value)
    raise ValueError("Source facet native taxon identifier is invalid")


def order_source_features(
    layer: Mapping[str, object],
    features: list[tuple[int, dict[str, object]]],
) -> list[tuple[int, dict[str, object]]]:
    """Only physical delivery order changes; original indexes remain authoritative."""
    if (
        layer.get("semantic_role") != "source_chronology_context"
        or layer.get("node_level") != "source_taxon"
    ):
        return features
    return sorted(
        features,
        key=lambda item: (native_taxon(item[1].get("source_taxon_id")), item[0]),
    )
