from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ArticleSampleEvidence", "resolve_article_sample_evidence"]


@dataclass(frozen=True)
class ArticleSampleEvidence:
    """A sample identity, locality, and chronology linked by a primary article."""

    accession: str
    sample_label: str
    locality_text: str
    political_entity: str
    chronology_text: str
    source_path: str
    source_locator: str
    source_excerpt: str


_DOG_ARTICLE = "adna/governance/source_library/papers/10.1038-ncomms16082/article.html"
_CAMEL_ARTICLE = (
    "adna/governance/source_library/papers/10.1111-1755-0998.12551/article.html"
)


def _dog(
    accession: str,
    sample_label: str,
    locality_text: str,
    chronology_text: str,
    source_excerpt: str,
) -> ArticleSampleEvidence:
    return ArticleSampleEvidence(
        accession=accession,
        sample_label=sample_label,
        locality_text=locality_text,
        political_entity="Germany",
        chronology_text=chronology_text,
        source_path=_DOG_ARTICLE,
        source_locator="Results: Archaeological samples and ancient DNA sequencing; Data availability",
        source_excerpt=source_excerpt,
    )


def _camel(
    accession: str,
    sample_label: str,
    locality_text: str,
    political_entity: str,
    chronology_text: str,
    source_excerpt: str,
) -> ArticleSampleEvidence:
    return ArticleSampleEvidence(
        accession=accession,
        sample_label=sample_label,
        locality_text=locality_text,
        political_entity=political_entity,
        chronology_text=chronology_text,
        source_path=_CAMEL_ARTICLE,
        source_locator="Materials and methods; Data accessibility",
        source_excerpt=source_excerpt,
    )


_ARTICLE_SAMPLE_EVIDENCE = {
    row.accession: row
    for row in (
        _dog(
            "SRS1407453",
            "HXH",
            "Herxheim",
            "5223-5040 BCE",
            "SRS1407453 maps to HXH; the article identifies Herxheim and gives a calibrated BCE interval.",
        ),
        _dog(
            "KX379528",
            "CTC",
            "Cherry Tree Cave",
            "2900-2632 BCE",
            "KX379528 maps respectively to CTC; the article identifies Cherry Tree Cave and gives a calibrated BCE interval.",
        ),
        _dog(
            "KX379529",
            "HXH",
            "Herxheim",
            "5223-5040 BCE",
            "KX379529 maps respectively to HXH; the article identifies Herxheim and gives a calibrated BCE interval.",
        ),
        _camel(
            "KU605068",
            "Palm152",
            "Palmyra",
            "Syria",
            "1650-2050 BP",
            "KU605068 maps to Palm152 from Palmyra, dated by the article to 100 BCE-300 CE.",
        ),
        _camel(
            "KU605069",
            "Palm157",
            "Palmyra",
            "Syria",
            "1650-2050 BP",
            "KU605069 maps to Palm157 from Palmyra, dated by the article to 100 BCE-300 CE.",
        ),
        _camel(
            "KU605070",
            "Palm171",
            "Palmyra",
            "Syria",
            "1650-2050 BP",
            "KU605070 maps to Palm171 from Palmyra, dated by the article to 100 BCE-300 CE.",
        ),
        _camel(
            "KU605071",
            "SAG2",
            "Sagalassos",
            "Turkey",
            "1250-1500 BP",
            "KU605071 maps to SAG2 from Sagalassos, dated by the article to 450-700 CE.",
        ),
        _camel(
            "KU605072",
            "Drom439",
            "Qatar-Jordan border",
            "Qatar and Jordan",
            "0 BP (modern comparator)",
            "The article identifies KU605072 as a modern comparator from the Qatar-Jordan border.",
        ),
        _camel(
            "KU605073",
            "Drom795",
            "Saudi Arabia",
            "Saudi Arabia",
            "0 BP (modern comparator)",
            "The article identifies KU605073 as a modern comparator from Saudi Arabia.",
        ),
        _camel(
            "KU605074",
            "Drom796",
            "Saudi Arabia",
            "Saudi Arabia",
            "0 BP (modern comparator)",
            "The article identifies KU605074 as a modern comparator from Saudi Arabia.",
        ),
        _camel(
            "KU605075",
            "Drom797",
            "Saudi Arabia",
            "Saudi Arabia",
            "0 BP (modern comparator)",
            "The article identifies KU605075 as a modern comparator from Saudi Arabia.",
        ),
        _camel(
            "KU605076",
            "Drom801A",
            "Austria",
            "Austria",
            "0 BP (modern comparator)",
            "The article identifies KU605076 as a modern comparator from Austria.",
        ),
        _camel(
            "KU605077",
            "Drom802",
            "Dubai",
            "United Arab Emirates",
            "0 BP (modern comparator)",
            "The article identifies KU605077 as a modern comparator from Dubai, United Arab Emirates.",
        ),
        _camel(
            "KU605078",
            "Drom806",
            "Kenya",
            "Kenya",
            "0 BP (modern comparator)",
            "The article identifies KU605078 as a modern comparator from Kenya.",
        ),
        _camel(
            "KU605079",
            "Drom816",
            "Sudan",
            "Sudan",
            "0 BP (modern comparator)",
            "The article identifies KU605079 as a modern comparator from Sudan.",
        ),
        _camel(
            "KU605080",
            "Drom820",
            "Pakistan",
            "Pakistan",
            "0 BP (modern comparator)",
            "The article identifies KU605080 as a modern comparator from Pakistan.",
        ),
    )
}


def resolve_article_sample_evidence(
    accession: str,
) -> ArticleSampleEvidence | None:
    """Return primary-article evidence for one archive-native accession."""
    return _ARTICLE_SAMPLE_EVIDENCE.get(accession)
