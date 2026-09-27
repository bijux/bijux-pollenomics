"""Paper labels and BioSample accessions must not be silently crosswalked."""

from __future__ import annotations

from copy import deepcopy

import pytest

from bijux_pollenomics_dev.source_completion.galician_cattle_review import derive


@pytest.fixture(scope="module")
def source_parts() -> tuple[
    str, str, dict[int, dict[str, str]], dict[int, dict[str, str]], str, dict[str, str]
]:
    dating = {15: {"C": "species"}}
    dating.update(
        {
            row: {
                "A": f"specimen-{row}",
                "C": "Bos primigenius" if row < 19 else "Bos taurus",
                "J": (f"Bp_({row - 14})" if row < 19 else f"Bt_({row - 14})")
                if row < 27
                else "-",
            }
            for row in range(16, 34)
        }
    )
    mapping = {1: {"A": "Sample"}}
    mapping.update(
        {row: {"A": f"Bp_{row}" if row < 5 else f"Bt_{row}"} for row in range(2, 13)}
    )
    archive = "study_accession\tsample_accession\tscientific_name\n" + "".join(
        f"PRJNA705960\tSAMN{row}\t{'Bos primigenius' if row < 5 else 'Bos taurus'}\n"
        for row in range(2, 13)
    )
    return (
        "10.1371/journal.pone.0249537 PRJNA705960",
        "The third author Johanna L. A. Paijmans",
        dating,
        mapping,
        archive,
        {f"SAMN{row}": f"Bp_{row}" if row < 5 else f"Bt_{row}" for row in range(2, 13)},
    )


def test_mixed_taxa_preserve_distinct_identity_units(
    source_parts: tuple[
        str,
        str,
        dict[int, dict[str, str]],
        dict[int, dict[str, str]],
        str,
        dict[str, str],
    ],
) -> None:
    report = derive(*source_parts)
    assert report["paper_specimen_rows"] == 18
    assert report["paper_sequenced_sample_labels"] == 11
    assert report["archive_biosample_accessions"] == 11
    assert report["paper_sequenced_species_counts"] == {
        "Bos primigenius": 3,
        "Bos taurus": 8,
    }
    assert report["source_catalog_species_conflict"] is True
    assert (
        report["sample_label_to_biosample_crosswalk_status"]
        == "resolved_by_source_owned_ena_biosample_alias"
    )
    assert len(report["sample_label_to_biosample_crosswalk"]) == 11


def test_archive_taxonomy_disagreement_refuses(
    source_parts: tuple[
        str,
        str,
        dict[int, dict[str, str]],
        dict[int, dict[str, str]],
        str,
        dict[str, str],
    ],
) -> None:
    article, correction, dating, mapping, archive, aliases = source_parts
    changed = archive.replace("Bos primigenius", "Bos taurus", 1)
    with pytest.raises(ValueError, match="taxon totals differ"):
        derive(article, correction, dating, mapping, changed, aliases)


def test_missing_bioproject_refuses(
    source_parts: tuple[
        str,
        str,
        dict[int, dict[str, str]],
        dict[int, dict[str, str]],
        str,
        dict[str, str],
    ],
) -> None:
    article, correction, dating, mapping, archive, aliases = source_parts
    with pytest.raises(ValueError, match="DOI or BioProject"):
        derive(
            article.replace("PRJNA705960", "PRJNA000000"),
            correction,
            dating,
            mapping,
            archive,
            aliases,
        )


def test_dating_species_header_change_refuses(
    source_parts: tuple[
        str,
        str,
        dict[int, dict[str, str]],
        dict[int, dict[str, str]],
        str,
        dict[str, str],
    ],
) -> None:
    article, correction, dating, mapping, archive, aliases = source_parts
    changed = deepcopy(dating)
    changed[15]["C"] = "unlabeled"
    with pytest.raises(ValueError, match="species column"):
        derive(article, correction, changed, mapping, archive, aliases)


def test_biosample_alias_change_refuses(
    source_parts: tuple[
        str,
        str,
        dict[int, dict[str, str]],
        dict[int, dict[str, str]],
        str,
        dict[str, str],
    ],
) -> None:
    article, correction, dating, mapping, archive, aliases = source_parts
    changed = deepcopy(aliases)
    changed["SAMN2"] = "unrelated"
    with pytest.raises(ValueError, match="does not match paper label"):
        derive(article, correction, dating, mapping, archive, changed)
