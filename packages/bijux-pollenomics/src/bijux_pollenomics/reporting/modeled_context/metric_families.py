"""Source-evidenced metric families published by PANGAEA 937075."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final

RESULT_HEADER_EVIDENCE: Final = (
    "data/landclim/raw/landclim_ii_reveals_results.zip::"
    "LANDCLIMII.RV.means.JUN2021/TW1.RV.estimates.jun21.csv#header"
)
MAPPING_TABLE_EVIDENCE: Final = (
    "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"
)


@dataclass(frozen=True)
class MetricDefinition:
    """One source-spelled result metric and its available source definition."""

    key: str
    label: str
    source_label: str
    definition: str | None
    membership_evidence: str

    def as_dict(self) -> dict[str, object]:
        """Serialize without changing source spelling or nullable definitions."""
        return asdict(self)


@dataclass(frozen=True)
class MetricFamily:
    """A source-evidenced family of result-header metrics."""

    key: str
    label: str
    metrics: tuple[MetricDefinition, ...]
    membership_evidence: tuple[str, ...]
    default_metric_key: str

    def as_dict(self) -> dict[str, object]:
        """Serialize the ordered family contract for browser use."""
        return {
            "key": self.key,
            "label": self.label,
            "metric_count": len(self.metrics),
            "default_metric_key": self.default_metric_key,
            "membership_evidence": list(self.membership_evidence),
            "metrics": [metric.as_dict() for metric in self.metrics],
        }


def _metric(
    key: str,
    *,
    source_label: str | None = None,
    definition: str | None = None,
    evidence: str = MAPPING_TABLE_EVIDENCE,
) -> MetricDefinition:
    return MetricDefinition(
        key=key,
        label=source_label or key,
        source_label=source_label or key,
        definition=definition,
        membership_evidence=evidence,
    )


EXACT_TAXA: Final = (
    ("Abies.alba", "Abies alba"),
    ("Alnus.glutinosa", "Alnus glutinosa"),
    ("Amanranthaceae.Chenopodiaceae", "Amaranthaceae/Chenopodiaceae"),
    ("Artemisia", "Artemisia"),
    ("Betula", "Betula"),
    ("Buxus.sempervirens", "Buxus sempervirens"),
    ("Calluna.vulgaris", "Calluna vulgaris"),
    ("Carpinus.betulus", "Carpinus betulus"),
    ("Carpinus.orientalis", "Carpinus orientalis"),
    ("Castanea", "Castanea sativa"),
    ("Cerealia.t", "Cerealia-t"),
    ("Corylus.avellana", "Corylus avellana"),
    ("Cyperaceae", "Cyperaceae"),
    ("Ericaceae", "Ericaceae**"),
    ("Fagus.sylvatica", "Fagus sylvatica"),
    ("Filipendula", "Filipendula"),
    ("Fraxinus", "Fraxinus"),
    ("Juniperus", "Juniperus communis"),
    ("Phillyrea", "Phillyrea"),
    ("Picea", "Picea abies"),
    ("Pinus", "Pinus sylvestris"),
    ("Pistacia", "Pistacia"),
    ("Plantago.lanceolata.type", "Plantago lanceolata"),
    ("Poaceae", "Poaceae"),
    ("Quercus.deciduous", "Quercus deciduous t."),
    ("Quercus.evergreen", "Quercus evergreen t."),
    ("Rumex.acetosa.t", "Rumex acetosa-t"),
    ("Salix", "Salix"),
    ("Secale", "Secale cereale"),
    ("Tilia", "Tilia"),
    ("Ulmus", "Ulmus"),
)
EXACT_TAXON_KEYS: Final = tuple(key for key, _source_label in EXACT_TAXA)

PFT_DEFINITIONS: Final = (
    ("TBE1", "Shade-tolerant evergreen trees"),
    ("TBE2", "Shade-tolerant evergreen trees"),
    ("IBE", "Shade-intolerant evergreen trees"),
    ("MTBE", "Mediterranean shade-tolerant broadleaved evergreen trees"),
    ("TSE", "Tall shrub, evergreen"),
    ("MTSE", "Mediterranean broadleaved tall shrubs, evergreen"),
    ("IBS", "Shade-intolerant summer-green trees"),
    ("ISTS", None),
    ("TBS", "Shade-tolerant summer-green trees"),
    ("TSD", "Tall shrub, summer-green"),
    ("LSE", "Low shrub, broadleaved evergreen"),
    ("GL", "Grassland - all herbs"),
    ("AL", "Agricultural land - cereals"),
)

LAND_COVER_TYPE_DEFINITIONS: Final = (
    ("ET", "Evergreen trees"),
    ("ST", "Summer-green trees"),
    ("OL", "Open land"),
)

LAND_COVER_COMPONENT_KEYS: Final = {
    "ET": ("TBE1", "TBE2", "IBE", "MTBE", "TSE", "MTSE"),
    "ST": ("IBS", "ISTS", "TBS", "TSD"),
    "OL": ("LSE", "GL", "AL"),
}

METRIC_FAMILIES: Final = (
    MetricFamily(
        key="exact_taxa",
        label="Exact taxa / pollen-morphological types",
        metrics=tuple(
            _metric(key, source_label=source_label) for key, source_label in EXACT_TAXA
        ),
        membership_evidence=(RESULT_HEADER_EVIDENCE, MAPPING_TABLE_EVIDENCE),
        default_metric_key=EXACT_TAXON_KEYS[0],
    ),
    MetricFamily(
        key="source_pft_codes",
        label="Source plant-functional-type codes",
        metrics=tuple(
            _metric(
                key,
                definition=definition,
                evidence=(
                    MAPPING_TABLE_EVIDENCE
                    if definition is not None
                    else RESULT_HEADER_EVIDENCE
                ),
            )
            for key, definition in PFT_DEFINITIONS
        ),
        membership_evidence=(RESULT_HEADER_EVIDENCE, MAPPING_TABLE_EVIDENCE),
        default_metric_key=PFT_DEFINITIONS[0][0],
    ),
    MetricFamily(
        key="source_land_cover_types",
        label="Source land-cover types",
        metrics=tuple(
            _metric(
                key,
                source_label=f"{definition} ({key})",
                definition=definition,
            )
            for key, definition in LAND_COVER_TYPE_DEFINITIONS
        ),
        membership_evidence=(RESULT_HEADER_EVIDENCE, MAPPING_TABLE_EVIDENCE),
        default_metric_key="OL",
    ),
)

PANGAEA_METRIC_KEYS: Final = tuple(
    metric.key for family in METRIC_FAMILIES for metric in family.metrics
)

__all__ = [
    "EXACT_TAXA",
    "EXACT_TAXON_KEYS",
    "LAND_COVER_COMPONENT_KEYS",
    "LAND_COVER_TYPE_DEFINITIONS",
    "MAPPING_TABLE_EVIDENCE",
    "METRIC_FAMILIES",
    "PANGAEA_METRIC_KEYS",
    "PFT_DEFINITIONS",
    "RESULT_HEADER_EVIDENCE",
    "MetricDefinition",
    "MetricFamily",
]
