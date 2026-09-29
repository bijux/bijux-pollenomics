"""Source-specific attribution and evidence locators for official captures."""

from __future__ import annotations

from pathlib import Path

from .models import _RemoteArtifactSpec


def _official_source_receipt_metadata(
    asset: _RemoteArtifactSpec, *, retrieved_at_utc: str
) -> dict[str, object]:
    if asset.relative_path == "papers/10.1111-mec.17274/article.pdf":
        return {
            "published_article_doi": "10.1111/mec.17274",
            "repository_record": "https://nva.sikt.no/registration/0198cc66e16f-a743d6e1-054b-400e-a2c4-dd186a645095",
            "retrieved_at_utc": retrieved_at_utc,
            "license_name": "Creative Commons Attribution 4.0 International",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "evidence_locators": [
                {
                    "claim_family": "specimen_site_chronology",
                    "locator": "Table 1, published page 4",
                },
                {
                    "claim_family": "source_role",
                    "locator": "Data Availability Statement, published page 13",
                },
            ],
        }
    if asset.artifact_kind == "author_preprint_pdf":
        return {
            "preprint_doi": "10.1101/2023.09.21.558762",
            "retrieved_at_utc": retrieved_at_utc,
            "license_name": "Creative Commons Attribution 4.0 International",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "evidence_locators": [
                {
                    "claim_family": "specimen_site_chronology",
                    "locator": "Table 1, pp. 41–43",
                },
                {
                    "claim_family": "source_role",
                    "locator": "preprint DOI and version on each page",
                },
            ],
        }
    if asset.artifact_kind == "author_preprint_supplementary_xlsx":
        return {
            "preprint_doi": "10.1101/2023.09.21.558762",
            "preprint_version": "1",
            "retrieved_at_utc": retrieved_at_utc,
            "license_name": "Creative Commons Attribution 4.0 International",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "license_evidence_url": "https://api.biorxiv.org/details/biorxiv/10.1101/2023.09.21.558762/na",
            "published_appendix_equivalence": "unverified",
            "evidence_locators": [
                {
                    "claim_family": "specimen_site_chronology",
                    "locator": "Tabellenblatt1 rows 3-20, columns A-I",
                },
                {
                    "claim_family": "source_role",
                    "locator": "preprint supplementary listing, Table S3",
                },
            ],
        }
    if asset.artifact_kind == "ena_sample_xml":
        accession = Path(asset.relative_path).stem
        locators = [
            {
                "claim_family": "sample_identity",
                "locator": f"./SAMPLE[@accession='{accession}']",
            },
        ]
        if {"PRJEB41594", "PRJEB60484"} & set(Path(asset.relative_path).parts):
            locators.extend(
                (
                    {
                        "claim_family": "sample_alias",
                        "locator": f"./SAMPLE[@accession='{accession}']/@alias",
                    },
                    {
                        "claim_family": "sample_taxonomy",
                        "locator": "./SAMPLE/SAMPLE_ATTRIBUTES/SAMPLE_ATTRIBUTE[TAG='scientific_name']/VALUE",
                    },
                )
            )
        else:
            locators.extend(
                (
                    {
                        "claim_family": "sample_locality",
                        "locator": (
                            "./SAMPLE/SAMPLE_ATTRIBUTES/"
                            "SAMPLE_ATTRIBUTE[TAG='lat_lon']/VALUE"
                        ),
                    },
                    {
                        "claim_family": "sample_material",
                        "locator": "./SAMPLE/DESCRIPTION",
                    },
                )
            )
        return {
            "sample_accession": accession,
            "retrieved_at_utc": retrieved_at_utc,
            "license_name": "EMBL-EBI Terms of Use",
            "license_url": "https://www.ebi.ac.uk/about/terms-of-use/",
            "license_note": (
                "EMBL-EBI imposes no additional restriction on contributed "
                "scientific data beyond rights retained by the original data owner; "
                "attribution is expected."
            ),
            "evidence_locators": locators,
        }
    if asset.artifact_kind == "article_full_text_xml":
        return {
            "pmcid": "PMC11162877",
            "retrieved_at_utc": retrieved_at_utc,
            "license_name": "Creative Commons Attribution 4.0 International",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "evidence_locators": [
                {
                    "claim_family": "sample_chronology",
                    "locator": ".//table-wrap[@id='evae114-T1']",
                    "label": "Table 1: Overview of samples sequenced for this study",
                },
                {
                    "claim_family": "chronology_semantics",
                    "locator": (".//table-wrap[@id='evae114-T1']/table-wrap-foot"),
                    "label": "BP reference epoch and contextual-date footnote",
                },
                {
                    "claim_family": "license",
                    "locator": "./front/article-meta/permissions/license",
                },
            ],
        }
    return {}
