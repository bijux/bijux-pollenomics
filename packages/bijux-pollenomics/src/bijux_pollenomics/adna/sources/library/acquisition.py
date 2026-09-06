"""Fail-closed remote aDNA source capture."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from bijux_pollenomics.core.files import write_json
from bijux_pollenomics.core.http import validate_http_url
from bijux_pollenomics.adna.workflow.paths import (
    adna_source_library_root,
)
from bijux_pollenomics.adna.workflow.source_artifacts import (
    SourceArtifactContentDriftError,
    read_source_artifact_bytes,
    resolve_source_artifact_path,
    source_artifact_exists,
    write_source_artifact_bytes,
)
from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from .cache_control import _clear_source_library_caches
from .models import (
    SOURCE_LIBRARY_SCHEMA_VERSION,
    _CAPTURE_REFUSAL_SCHEMA_VERSION,
    _PendingSourceCapture,
    _RemoteArtifactSpec,
    _SourceCaptureAssessment,
    _SourceCaptureDisposition,
    _USER_AGENT,
)
from .specifications import (
    _expand_remote_assets,
    _paper_source_specs,
    _project_remote_assets,
)


def refresh_source_library(
    output_root: Path,
    *,
    downloader: Callable[[str], tuple[bytes, str]] | None = None,
) -> None:
    """Download or refresh local paper and supplementary artifacts."""
    _clear_source_library_caches()
    output_root = Path(output_root)
    downloader = _download_url if downloader is None else downloader
    source_root = adna_source_library_root(output_root)
    source_root.mkdir(parents=True, exist_ok=True)
    refusal_paths: list[Path] = []
    pending_captures: list[_PendingSourceCapture] = []
    retrieved_at_utc = (
        datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )

    for project in build_archive_project_catalog():
        project_dir = source_root / "projects" / project.project_accession
        try:
            payload, content_type = downloader(project.metadata_url)
        except (HTTPError, URLError, TimeoutError, ValueError):
            pass
        else:
            archive_path = project_dir / "archive_metadata.html"
            assessment = _assess_downloaded_source_capture(
                output_root=output_root,
                logical_path=archive_path,
                source_url=project.metadata_url,
                payload=payload,
                content_type=content_type,
            )
            if assessment.disposition is _SourceCaptureDisposition.REFUSED:
                if assessment.refusal_path is None:
                    raise RuntimeError("aDNA source refusal lacks an evidence path")
                refusal_paths.append(assessment.refusal_path)
                continue
            if assessment.disposition is _SourceCaptureDisposition.IDENTICAL_EXISTING:
                continue
            pending_captures.append(
                _PendingSourceCapture(
                    logical_path=archive_path,
                    payload=payload,
                    metadata={
                        "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
                        "source_url": project.metadata_url,
                        "artifact_kind": "archive_metadata_html",
                        "content_type": content_type,
                        "byte_size": len(payload),
                        "project_accession": project.project_accession,
                    },
                )
            )
        for asset in _project_remote_assets(project.project_accession):
            local_path = source_root / asset.relative_path
            try:
                payload, content_type = downloader(asset.source_url)
            except (HTTPError, URLError, TimeoutError, ValueError):
                continue
            assessment = _assess_downloaded_source_capture(
                output_root=output_root,
                logical_path=local_path,
                source_url=asset.source_url,
                payload=payload,
                content_type=content_type,
            )
            if assessment.disposition is _SourceCaptureDisposition.REFUSED:
                if assessment.refusal_path is None:
                    raise RuntimeError("aDNA source refusal lacks an evidence path")
                refusal_paths.append(assessment.refusal_path)
                continue
            if assessment.disposition is _SourceCaptureDisposition.IDENTICAL_EXISTING:
                continue
            pending_captures.append(
                _PendingSourceCapture(
                    logical_path=local_path,
                    payload=payload,
                    metadata={
                        "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
                        "source_url": asset.source_url,
                        "artifact_kind": asset.artifact_kind,
                        "content_type": content_type,
                        "byte_size": len(payload),
                        "project_accession": project.project_accession,
                        **_official_xml_receipt_metadata(
                            asset,
                            retrieved_at_utc=retrieved_at_utc,
                        ),
                    },
                )
            )

    for doi, spec in _paper_source_specs().items():
        for asset in _expand_remote_assets(spec, build_archive_project_catalog()):
            local_path = source_root / asset.relative_path
            try:
                payload, content_type = downloader(asset.source_url)
            except (HTTPError, URLError, TimeoutError, ValueError):
                continue
            assessment = _assess_downloaded_source_capture(
                output_root=output_root,
                logical_path=local_path,
                source_url=asset.source_url,
                payload=payload,
                content_type=content_type,
            )
            if assessment.disposition is _SourceCaptureDisposition.REFUSED:
                if assessment.refusal_path is None:
                    raise RuntimeError("aDNA source refusal lacks an evidence path")
                refusal_paths.append(assessment.refusal_path)
                continue
            if assessment.disposition is _SourceCaptureDisposition.IDENTICAL_EXISTING:
                continue
            pending_captures.append(
                _PendingSourceCapture(
                    logical_path=local_path,
                    payload=payload,
                    metadata={
                        "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
                        "source_url": asset.source_url,
                        "artifact_kind": asset.artifact_kind,
                        "content_type": content_type,
                        "byte_size": len(payload),
                        "paper_doi": doi,
                        **_official_xml_receipt_metadata(
                            asset,
                            retrieved_at_utc=retrieved_at_utc,
                        ),
                    },
                )
            )
    if refusal_paths:
        _clear_source_library_caches()
        relative_paths = sorted(
            str(path.relative_to(output_root)) for path in refusal_paths
        )
        raise ValueError(
            "aDNA source refresh refused capture(s): " + ", ".join(relative_paths)
        )
    _publish_source_captures(output_root, pending_captures)
    _clear_source_library_caches()


def _assess_downloaded_source_capture(
    *,
    output_root: Path,
    logical_path: Path,
    source_url: str,
    payload: bytes,
    content_type: str,
) -> _SourceCaptureAssessment:
    refusal_reason = _http_success_refusal_reason(payload, content_type)
    if refusal_reason is None:
        refusal_reason = _xml_capture_refusal_reason(
            logical_path=logical_path,
            payload=payload,
            content_type=content_type,
        )
    if refusal_reason is not None:
        refusal_path = _write_source_capture_refusal(
            output_root=output_root,
            logical_path=logical_path,
            source_url=source_url,
            payload=payload,
            content_type=content_type,
            reason_code=refusal_reason,
        )
        return _SourceCaptureAssessment(
            disposition=_SourceCaptureDisposition.REFUSED,
            refusal_path=refusal_path,
        )
    if source_artifact_exists(logical_path):
        existing_payload = read_source_artifact_bytes(logical_path)
        if existing_payload == payload:
            receipt_refusal = _official_source_receipt_refusal_reason(
                output_root=output_root,
                logical_path=logical_path,
            )
            if receipt_refusal is not None:
                refusal_path = _write_source_capture_refusal(
                    output_root=output_root,
                    logical_path=logical_path,
                    source_url=source_url,
                    payload=payload,
                    content_type=content_type,
                    reason_code=receipt_refusal,
                )
                return _SourceCaptureAssessment(
                    disposition=_SourceCaptureDisposition.REFUSED,
                    refusal_path=refusal_path,
                )
            return _SourceCaptureAssessment(
                disposition=_SourceCaptureDisposition.IDENTICAL_EXISTING
            )
        stored_path = resolve_source_artifact_path(logical_path)
        exc = SourceArtifactContentDriftError(
            logical_path=logical_path,
            stored_path=stored_path,
            existing_payload=existing_payload,
            candidate_payload=payload,
        )
        refusal_path = _write_source_capture_refusal(
            output_root=output_root,
            logical_path=logical_path,
            source_url=source_url,
            payload=payload,
            content_type=content_type,
            reason_code="content_drift",
            existing_sha256=exc.existing_sha256,
            existing_byte_size=exc.existing_byte_size,
            stored_path=exc.stored_path,
        )
        return _SourceCaptureAssessment(
            disposition=_SourceCaptureDisposition.REFUSED,
            refusal_path=refusal_path,
        )
    return _SourceCaptureAssessment(disposition=_SourceCaptureDisposition.NEW_CAPTURE)


def _publish_source_captures(
    output_root: Path, pending_captures: list[_PendingSourceCapture]
) -> None:
    captures_by_path: dict[Path, _PendingSourceCapture] = {}
    for pending in pending_captures:
        previous = captures_by_path.get(pending.logical_path)
        if previous is not None and previous != pending:
            raise ValueError(
                f"Conflicting aDNA refresh candidates for {pending.logical_path}"
            )
        captures_by_path[pending.logical_path] = pending
    for pending in captures_by_path.values():
        stored_path = write_source_artifact_bytes(pending.logical_path, pending.payload)
        metadata = {
            **pending.metadata,
            "content_sha256": hashlib.sha256(pending.payload).hexdigest(),
            "storage_byte_size": stored_path.stat().st_size,
            "storage_sha256": hashlib.sha256(stored_path.read_bytes()).hexdigest(),
            "storage_path": str(stored_path.relative_to(output_root)),
            "content_encoding": "gzip" if stored_path.suffix == ".gz" else None,
        }
        write_json(
            pending.logical_path.with_suffix(
                pending.logical_path.suffix + ".metadata.json"
            ),
            metadata,
        )


def _http_success_refusal_reason(payload: bytes, content_type: str) -> str | None:
    if not payload:
        return "empty_http_success_payload"
    head = payload[:262_144].lstrip().lower()
    looks_like_html = "text/html" in content_type.lower() or head.startswith(
        (b"<!doctype html", b"<html")
    )
    if not looks_like_html:
        return None
    markers = (
        b"<title>access denied",
        b"<h1>access denied",
        b"<title>attention required",
        b"<title>bad gateway",
        b"<title>service unavailable",
        b"cf-chl-captcha",
        b"cf-error-details",
        b"google.com/recaptcha/challengepage",
        b"recaptchachallengepageui",
        b"cookies must be enabled",
        b"the request could not be satisfied",
    )
    if any(marker in head for marker in markers):
        return "http_success_block_or_error_page"
    return None


def _xml_capture_refusal_reason(
    *, logical_path: Path, payload: bytes, content_type: str
) -> str | None:
    if logical_path.suffix.casefold() != ".xml":
        return None
    if "xml" not in content_type.casefold():
        return "xml_source_returned_non_xml_media_type"
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError:
        return "malformed_xml_source_payload"
    if "/ena_samples/" in logical_path.as_posix() and root.tag != "SAMPLE_SET":
        return "ena_sample_source_root_mismatch"
    if logical_path.name == "article_full_text.xml" and root.tag != "article":
        return "article_full_text_source_root_mismatch"
    path_text = logical_path.as_posix()
    if "/projects/PRJEB59481/ena_samples/" in path_text and logical_path.name.endswith(
        ".xml"
    ):
        try:
            from bijux_pollenomics.adna.projects.sample_master.tables.baltic_sheep.official_evidence import (  # noqa: PLC0415
                parse_baltic_sheep_ena_sample,
            )

            parse_baltic_sheep_ena_sample(
                payload,
                source_path=path_text,
                expected_accession=logical_path.stem,
            )
        except ValueError:
            return "ena_sample_source_semantic_mismatch"
    if (
        "/papers/10.1093-gbe-evae114/" in path_text
        and logical_path.name == "article_full_text.xml"
    ):
        try:
            from bijux_pollenomics.adna.projects.sample_master.tables.baltic_sheep.official_evidence import (  # noqa: PLC0415
                parse_baltic_sheep_article_chronology,
            )

            parse_baltic_sheep_article_chronology(payload, source_path=path_text)
        except ValueError:
            return "article_full_text_source_semantic_mismatch"
    return None


def _official_source_receipt_refusal_reason(
    *, output_root: Path, logical_path: Path
) -> str | None:
    path_text = logical_path.as_posix()
    is_baltic_ena = "/projects/PRJEB59481/ena_samples/" in path_text
    is_baltic_article = (
        "/papers/10.1093-gbe-evae114/" in path_text
        and logical_path.name == "article_full_text.xml"
    )
    if not is_baltic_ena and not is_baltic_article:
        return None
    try:
        repository_path = f"data/{logical_path.relative_to(output_root)}"
        from bijux_pollenomics.adna.projects.sample_master.tables.baltic_sheep.official_evidence import (  # noqa: PLC0415
            read_receipted_baltic_sheep_official_source,
        )

        read_receipted_baltic_sheep_official_source(
            output_root, repository_path=repository_path
        )
    except (OSError, ValueError):
        return "official_source_receipt_mismatch"
    return None


def _official_xml_receipt_metadata(
    asset: _RemoteArtifactSpec, *, retrieved_at_utc: str
) -> dict[str, object]:
    if asset.artifact_kind == "ena_sample_xml":
        accession = Path(asset.relative_path).stem
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
            "evidence_locators": [
                {
                    "claim_family": "sample_identity",
                    "locator": f"./SAMPLE[@accession='{accession}']",
                },
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
            ],
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


def _write_source_capture_refusal(
    *,
    output_root: Path,
    logical_path: Path,
    source_url: str,
    payload: bytes,
    content_type: str,
    reason_code: str,
    existing_sha256: str | None = None,
    existing_byte_size: int | None = None,
    stored_path: Path | None = None,
) -> Path:
    candidate_sha256 = hashlib.sha256(payload).hexdigest()
    if source_artifact_exists(logical_path) and existing_sha256 is None:
        existing_payload = read_source_artifact_bytes(logical_path)
        existing_sha256 = hashlib.sha256(existing_payload).hexdigest()
        existing_byte_size = len(existing_payload)
        stored_path = resolve_source_artifact_path(logical_path)
    refusal_path = logical_path.with_suffix(
        logical_path.suffix + f".capture-refusal-{candidate_sha256}.json"
    )
    record = {
        "schema_version": _CAPTURE_REFUSAL_SCHEMA_VERSION,
        "status": "refused",
        "reason_code": reason_code,
        "source_url": source_url,
        "logical_path": str(logical_path.relative_to(output_root)),
        "content_type": content_type,
        "candidate_sha256": candidate_sha256,
        "candidate_byte_size": len(payload),
        "existing_sha256": existing_sha256,
        "existing_byte_size": existing_byte_size,
        "existing_storage_path": (
            str(stored_path.relative_to(output_root))
            if stored_path is not None
            else None
        ),
    }
    record_bytes = json.dumps(record, indent=2, ensure_ascii=False).encode("utf-8")
    try:
        write_source_artifact_bytes(
            refusal_path,
            record_bytes,
            compress_html=False,
        )
    except SourceArtifactContentDriftError as exc:
        raise FileExistsError(
            f"Non-identical aDNA source refusal exists: {refusal_path}"
        ) from exc
    return refusal_path


def _download_url(url: str) -> tuple[bytes, str]:
    validate_http_url(url)
    request = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(request, timeout=60) as response:  # nosec B310
        payload = response.read()
        content_type = response.headers.get("Content-Type", "application/octet-stream")
    return payload, content_type
