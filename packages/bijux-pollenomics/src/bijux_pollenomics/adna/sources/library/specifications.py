"""Curated aDNA paper and supplementary source specifications."""

from __future__ import annotations

from bijux_pollenomics.adna.workflow.paths import (
    ADNA_SOURCE_LIBRARY_DIR,
)
from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from .models import AdnaSourceBundleManifest, _PaperSourceSpec, _RemoteArtifactSpec


def _paper_source_specs() -> dict[str, _PaperSourceSpec]:
    return {
        "10.1038/s42003-021-02794-8": _PaperSourceSpec(
            doi="10.1038/s42003-021-02794-8",
            article_source_url="https://www.nature.com/articles/s42003-021-02794-8",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s42003-021-02794-8/article.pdf",
            article_kind="article_pdf",
            article_note="Nature article PDF is directly downloadable and anchors sheep project metadata plus supplementary sample tables.",
            supplementary_assets=(
                _RemoteArtifactSpec(
                    artifact_kind="supplementary_pdf",
                    label="supplementary note 1",
                    source_url="https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02794-8/MediaObjects/42003_2021_2794_MOESM1_ESM.pdf",
                    relative_path="papers/10.1038-s42003-021-02794-8/supplementary/42003_2021_2794_MOESM1_ESM.pdf",
                    remote_note="Nature supplementary PDF discovered from article page.",
                ),
                _RemoteArtifactSpec(
                    artifact_kind="supplementary_pdf",
                    label="supplementary note 2",
                    source_url="https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02794-8/MediaObjects/42003_2021_2794_MOESM2_ESM.pdf",
                    relative_path="papers/10.1038-s42003-021-02794-8/supplementary/42003_2021_2794_MOESM2_ESM.pdf",
                    remote_note="Nature supplementary PDF discovered from article page.",
                ),
                _RemoteArtifactSpec(
                    artifact_kind="supplementary_pdf",
                    label="supplementary note 3",
                    source_url="https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02794-8/MediaObjects/42003_2021_2794_MOESM3_ESM.pdf",
                    relative_path="papers/10.1038-s42003-021-02794-8/supplementary/42003_2021_2794_MOESM3_ESM.pdf",
                    remote_note="Nature supplementary PDF discovered from article page.",
                ),
                _RemoteArtifactSpec(
                    artifact_kind="supplementary_zip",
                    label="supplementary data zip",
                    source_url="https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02794-8/MediaObjects/42003_2021_2794_MOESM4_ESM.zip",
                    relative_path="papers/10.1038-s42003-021-02794-8/supplementary/42003_2021_2794_MOESM4_ESM.zip",
                    remote_note="Nature supplementary data bundle discovered from article page.",
                ),
                _RemoteArtifactSpec(
                    artifact_kind="supplementary_pdf",
                    label="supplementary note 5",
                    source_url="https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02794-8/MediaObjects/42003_2021_2794_MOESM5_ESM.pdf",
                    relative_path="papers/10.1038-s42003-021-02794-8/supplementary/42003_2021_2794_MOESM5_ESM.pdf",
                    remote_note="Nature supplementary PDF discovered from article page.",
                ),
            ),
        ),
        "10.1038/s41562-021-01083-y": _PaperSourceSpec(
            doi="10.1038/s41562-021-01083-y",
            article_source_url="https://www.nature.com/articles/s41562-021-01083-y",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41562-021-01083-y/article.html",
            article_kind="article_html",
            article_note="Nature Human Behaviour article page is archived as the accessible paper surface.",
        ),
        "10.1038/s41586-021-04018-9": _PaperSourceSpec(
            doi="10.1038/s41586-021-04018-9",
            article_source_url="https://www.nature.com/articles/s41586-021-04018-9",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41586-021-04018-9/article.html",
            article_kind="article_html",
            article_note="Nature article page is archived because direct PDF automation is inconsistent.",
        ),
        "10.1038/s41586-024-08112-6": _PaperSourceSpec(
            doi="10.1038/s41586-024-08112-6",
            article_source_url="https://www.nature.com/articles/s41586-024-08112-6",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41586-024-08112-6/article.html",
            article_kind="article_html",
            article_note="Nature article page is archived as the accessible paper surface.",
        ),
        "10.1038/s41598-024-54296-2": _PaperSourceSpec(
            doi="10.1038/s41598-024-54296-2",
            article_source_url="https://www.nature.com/articles/s41598-024-54296-2",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41598-024-54296-2/article.html",
            article_kind="article_html",
            article_note="Scientific Reports article page is archived as the accessible paper surface.",
        ),
        "10.1038/ncomms16082": _PaperSourceSpec(
            doi="10.1038/ncomms16082",
            article_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5520058/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-ncomms16082/article.html",
            article_kind="article_html",
            article_note="PMC full-text HTML is archived for the dog paper.",
        ),
        "10.1093/gbe/evae114": _PaperSourceSpec(
            doi="10.1093/gbe/evae114",
            article_source_url="https://academic.oup.com/gbe/article/doi/10.1093/gbe/evae114/7682331",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1093-gbe-evae114/article.html",
            article_kind="article_html",
            article_note="Publisher article page is archived where accessible; OUP bot protection can still block richer downloads.",
            additional_assets=(
                _RemoteArtifactSpec(
                    artifact_kind="article_full_text_xml",
                    label="Europe PMC full-text XML",
                    source_url=(
                        "https://www.ebi.ac.uk/europepmc/webservices/rest/"
                        "PMC11162877/fullTextXML"
                    ),
                    relative_path=("papers/10.1093-gbe-evae114/article_full_text.xml"),
                    remote_note=(
                        "Official open-access full text supplies Table 1 sample "
                        "chronology and its BP/context footnotes."
                    ),
                ),
            ),
        ),
        "10.1093/gbe/evaf181": _PaperSourceSpec(
            doi="10.1093/gbe/evaf181",
            article_source_url="https://academic.oup.com/gbe/article/doi/10.1093/gbe/evaf181/8317779",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1093-gbe-evaf181/article.html",
            article_kind="article_html",
            article_note="Publisher article page is archived where accessible; OUP bot protection can still block richer downloads.",
        ),
        "10.1111/1755-0998.12551": _PaperSourceSpec(
            doi="10.1111/1755-0998.12551",
            article_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5324683/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1111-1755-0998.12551/article.html",
            article_kind="article_html",
            article_note="PMC full-text HTML is archived for the camel paper.",
        ),
        "10.1126/science.aam5298": _PaperSourceSpec(
            doi="10.1126/science.aam5298",
            article_source_url="https://pubmed.ncbi.nlm.nih.gov/28450643/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aam5298/article.html",
            article_kind="article_html",
            article_note="PubMed landing page is archived because publisher automation is blocked.",
            parsing_status="full_paper_download_blocked",
        ),
        "10.1126/science.aao3297": _PaperSourceSpec(
            doi="10.1126/science.aao3297",
            article_source_url="https://pubmed.ncbi.nlm.nih.gov/29472442/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aao3297/article.html",
            article_kind="article_html",
            article_note="PubMed landing page is archived because publisher automation is blocked.",
            parsing_status="full_paper_download_blocked",
        ),
        "10.1126/science.aav1002": _PaperSourceSpec(
            doi="10.1126/science.aav1002",
            article_source_url="https://pubmed.ncbi.nlm.nih.gov/31296769/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aav1002/article.html",
            article_kind="article_html",
            article_note="PubMed landing page is archived because publisher automation is blocked.",
            parsing_status="full_paper_download_blocked",
        ),
        "10.1126/science.adt2642": _PaperSourceSpec(
            doi="10.1126/science.adt2642",
            article_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC7618505/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.adt2642/article.html",
            article_kind="article_html",
            article_note="PMC full-text HTML is archived for the cat dispersal paper.",
            supplement_required=True,
        ),
        "10.1073/pnas.1901169116": _PaperSourceSpec(
            doi="10.1073/pnas.1901169116",
            article_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6717267/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1073-pnas.1901169116/article.html",
            article_kind="article_html",
            article_note="PMC full-text HTML is archived for the pig turnover paper.",
        ),
        "10.1016/j.cell.2019.03.049": _PaperSourceSpec(
            doi="10.1016/j.cell.2019.03.049",
            article_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6547883/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.cell.2019.03.049/article.html",
            article_kind="article_html",
            article_note="PMC full-text HTML is archived for the horse time-series paper.",
        ),
        "10.1016/j.isci.2025.113771": _PaperSourceSpec(
            doi="10.1016/j.isci.2025.113771",
            article_source_url="https://linkinghub.elsevier.com/retrieve/pii/S2589004225020322",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.isci.2025.113771/article.html",
            article_kind="article_html",
            article_note="Elsevier article landing page is archived as the accessible paper surface.",
        ),
        "10.1016/j.xgen.2025.101099": _PaperSourceSpec(
            doi="10.1016/j.xgen.2025.101099",
            article_source_url="https://linkinghub.elsevier.com/retrieve/pii/S2666979X25003556",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.xgen.2025.101099/article.html",
            article_kind="article_html",
            article_note="Elsevier article landing page is archived as the accessible paper surface.",
        ),
        "10.24272/j.issn.2095-8137.2025.080": _PaperSourceSpec(
            doi="10.24272/j.issn.2095-8137.2025.080",
            article_source_url="https://www.zoores.ac.cn/en/article/doi/10.24272/j.issn.2095-8137.2025.080",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.24272-j.issn.2095-8137.2025.080/article.html",
            article_kind="article_html",
            article_note="Publisher article page is archived for the goat paper.",
        ),
    }


def _paper_source_spec(doi: str) -> _PaperSourceSpec:
    try:
        return _paper_source_specs()[doi]
    except KeyError as exc:
        raise KeyError(f"Missing paper source spec for DOI: {doi}") from exc


def _expand_remote_assets(
    spec: _PaperSourceSpec,
    catalog: tuple[AdnaArchiveProject, ...],
) -> tuple[_RemoteArtifactSpec, ...]:
    article_relative = spec.article_local_path.split(f"{ADNA_SOURCE_LIBRARY_DIR}/", 1)[
        1
    ]
    assets = [
        _RemoteArtifactSpec(
            artifact_kind=spec.article_kind,
            label="article source",
            source_url=spec.article_source_url,
            relative_path=article_relative,
            remote_note=spec.article_note,
        ),
        _RemoteArtifactSpec(
            artifact_kind="paper_metadata_json",
            label="crossref metadata",
            source_url=f"https://api.crossref.org/works/{spec.doi}",
            relative_path=f"papers/{_doi_slug(spec.doi)}/crossref.json",
            remote_note="Crossref metadata snapshot preserves DOI and title even when publisher downloads are blocked.",
        ),
    ]
    project = next(
        (
            item
            for item in catalog
            if item.paper_linkage is not None
            and item.paper_linkage.doi == spec.doi
            and item.paper_linkage.pubmed_id is not None
        ),
        None,
    )
    project_linkage = None if project is None else project.paper_linkage
    if project_linkage is not None and project_linkage.pubmed_id is not None:
        assets.append(
            _RemoteArtifactSpec(
                artifact_kind="paper_metadata_json",
                label="pubmed abstract",
                source_url=(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                    f"?db=pubmed&id={project_linkage.pubmed_id}&retmode=xml"
                ),
                relative_path=f"papers/{_doi_slug(spec.doi)}/pubmed.xml",
                remote_note="PubMed XML snapshot provides publisher-independent citation and abstract metadata.",
            )
        )
    assets.extend(spec.additional_assets)
    assets.extend(spec.supplementary_assets)
    return tuple(assets)


def _project_remote_assets(project_accession: str) -> tuple[_RemoteArtifactSpec, ...]:
    if project_accession != "PRJEB59481":
        return ()
    return tuple(
        _RemoteArtifactSpec(
            artifact_kind="ena_sample_xml",
            label=f"ENA sample XML {accession}",
            source_url=f"https://www.ebi.ac.uk/ena/browser/api/xml/{accession}",
            relative_path=(f"projects/PRJEB59481/ena_samples/{accession}.xml"),
            remote_note=(
                "Official ENA biological-sample record supplies exact sample "
                "identity, source-native lat_lon, taxonomy, and material wording."
            ),
        )
        for accession in (
            "SAMEA112960291",
            "SAMEA112960292",
            "SAMEA112960293",
            "SAMEA112960294",
            "SAMEA112960295",
        )
    )


def _paper_required(archive_status: str) -> bool:
    return archive_status in {
        "paper_pinned_core",
        "archive_verified_needs_paper_pinning",
        "comparator_only",
    }


def _supplement_required(project: AdnaArchiveProject) -> bool:
    if project.paper_linkage is None or project.paper_linkage.doi is None:
        return False
    spec = _paper_source_spec(project.paper_linkage.doi)
    return spec.supplement_required or bool(spec.supplementary_assets)


def _derive_ingestion_status(bundle: AdnaSourceBundleManifest) -> str:
    if bundle.blockers:
        return "blocked"
    if bundle.supplement_required:
        return "paper_and_supplement_archived"
    if bundle.paper_required:
        return "paper_source_archived"
    return "archive_metadata_sufficient"


def _doi_slug(doi: str) -> str:
    return doi.lower().replace("/", "-")
