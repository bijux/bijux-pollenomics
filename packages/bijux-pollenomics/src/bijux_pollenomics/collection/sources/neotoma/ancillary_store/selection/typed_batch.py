"""All-or-nothing typed facet reads under one bounded source operation."""

from collections.abc import Mapping
from functools import partial
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.errors.cleanup import add_cleanup_note

from ...capture.facets.assessment import assess_http as facet_assessment
from ...capture.facets.models import SCOPED_FACET_SCHEMA
from ...capture.facets.profiles import qualify_neotoma_facet_body
from ...capture.receipts import _read, _utc
from ...capture.resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
)
from ...resource_catalogue.source_projection import _same
from ..context.seals import context_seals
from .access import _result
from .batch import prepare_neotoma_preflight_batch
from .preflight import _prepared_facet_access

_MAX_ITEMS = 128
_MAX_BODIES = 64 * 1024 * 1024
_SCOPED_DECLARATIONS_PROFILE = "neotoma-scoped-facet-declarations.v1"


def _cleanup_message(error: BaseException) -> str:
    return f"Facet batch cleanup failed: {error}"


def _source_declarations(access: Any, receipt: dict[str, Any]) -> dict[str, Any]:
    """Copy only checked scoped capture and current-use declarations."""
    capture = access.capture["document"]
    dataset = access.resource.dataset_id
    role = access.parents[dataset]["effective_scope_role"]
    if (
        capture["schema_version"] != SCOPED_FACET_SCHEMA
        or access.row.get("capture_parent_scope_verification")
        != "authenticated_original_parent_scope"
        or role not in DEVELOPMENT_ROLES
        or access.row.get("current_use_role") != role
        or access.entry.get("parent_scope_role") != role
    ):
        raise ValueError("Scoped facet declarations require authenticated scoped roles")
    capture_start, capture_end = (
        capture["capture_utc_start"],
        capture["capture_utc_end"],
    )
    request_start, request_end = receipt["utc_start"], receipt["utc_end"]
    if (
        not _utc(capture_start)
        <= _utc(request_start)
        <= _utc(request_end)
        <= _utc(capture_end)
    ):
        raise ValueError("Scoped facet declaration timing differs")
    url = receipt["requested_url"]
    if not isinstance(url, str) or url != access.request.url:
        raise ValueError("Scoped facet declaration request differs")
    return {
        "schema_version": _SCOPED_DECLARATIONS_PROFILE,
        "capture_utc_start": capture_start,
        "capture_utc_end": capture_end,
        "request_utc_start": request_start,
        "request_utc_end": request_end,
        "request_url": url,
        "original_parent_scope": "authenticated_original_parent_scope",
        "original_scope_role": access.entry["parent_scope_role"],
        "current_scope_role": role,
        "scientific_admission": "not_asserted",
    }


def read_neotoma_ancillary_facets(
    directory: Path,
    *,
    requests: tuple[tuple[str, int, str], ...],
    expected_manifest_sha256: str,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    source_declarations_profile: str | None = None,
) -> tuple[dict[str, Any], ...]:
    """Return fully qualified selected bodies only after the whole operation passes.

    Metadata caching never owns native entity buffers. The optional scoped
    declarations profile returns checked capture/request time and scope role
    declarations only for scoped captures; legacy captures are refused by that
    profile. These declarations do not independently attest acquisition, rights,
    scientific admission, or an atomic snapshot.
    """
    if source_declarations_profile is not None and (
        type(source_declarations_profile) is not str
        or source_declarations_profile != _SCOPED_DECLARATIONS_PROFILE
    ):
        raise ValueError("Unsupported scoped facet declarations profile")
    if not isinstance(requests, tuple) or not 0 < len(requests) <= _MAX_ITEMS:
        raise ValueError("Typed facet batch selection count is invalid")
    for item in requests:
        if (
            not isinstance(item, tuple)
            or len(item) != 3
            or not isinstance(item[0], str)
            or type(item[1]) is not int
            or item[1] <= 0
            or not isinstance(item[2], str)
        ):
            raise ValueError("Typed facet batch request is malformed")
    if len({item[0] for item in requests}) != len(requests):
        raise ValueError("Typed facet batch has duplicate observations")
    options: dict[str, Any] = {
        "expected_manifest_sha256": expected_manifest_sha256,
        "expected_context_sha256": expected_context_sha256,
        "expected_native_archive_sha256": expected_native_archive_sha256,
        "context_directory": context_directory,
        "native_archive_directory": native_archive_directory,
        "capsule_sources": capsule_sources,
        "limits": limits,
    }
    results: list[dict[str, Any]] = []
    total = 0
    with context_seals(options) as guard:
        batch = prepare_neotoma_preflight_batch(directory, **options)
        batch.__enter__()
        try:
            metadata, scope = batch._active()
            prepared = []
            for observation_id, dataset_id, facet in requests:
                batch._parts.validate()
                guard.check()
                access = _prepared_facet_access(
                    metadata,
                    scope,
                    observation_id=observation_id,
                    dataset_id=dataset_id,
                    facet=facet,
                )
                receipt, bound = access.response
                declarations = (
                    _source_declarations(access, receipt)
                    if source_declarations_profile is not None
                    else None
                )
                reference = access.entry["attempts"][-1]
                member = access.capture["descriptor"]["files"][reference["body_file"]]
                size = member["bytes"]
                if (
                    type(size) is not int
                    or size < 0
                    or size > bound
                    or total + size > _MAX_BODIES
                ):
                    raise ValueError("Typed facet batch body budget differs")
                path = access.capture["directory"] / reference["body_file"]
                batch._parts.seal(path, size)
                prepared.append(
                    (access, facet, receipt, bound, member, size, path, declarations)
                )
                total += size
            for (
                access,
                facet,
                receipt,
                bound,
                member,
                size,
                path,
                declarations,
            ) in prepared:
                guard.check()
                batch._parts.validate()
                body = _read(path, bound + 1)
                batch._parts.validate()
                guard.check()
                if len(body) != size or sha256(body).hexdigest() != member["sha256"]:
                    raise ValueError("Typed facet batch body identity differs")
                assessed = facet_assessment(receipt, access.request, body, bound)
                if not _same(
                    {key: access.entry.get(key) for key in assessed}, assessed
                ):
                    raise ValueError("Typed facet batch source assessment differs")
                result = _result(access.row, body, receipt, linked=False)
                if result["terminal_status"] != "received_complete_unqualified_facet":
                    raise ValueError(
                        "Typed facet source is not a complete successful entity"
                    )
                qualified = qualify_neotoma_facet_body(
                    access.resource,
                    facet,
                    body,
                    expected_body_sha256=result["body_sha256"],
                )
                batch._parts.validate()
                guard.check()
                if qualified["qualification_status"] != "qualified_source_schema":
                    raise ValueError(
                        "Selected facet native source schema is unqualified"
                    )
                output = {**result, "source_qualification": qualified}
                if declarations is not None:
                    output["source_declarations"] = declarations
                results.append(output)
            batch.close()
        except BaseException as error:
            try:
                batch._abort()
            except BaseException as cleanup_error:
                add_cleanup_note(error, partial(_cleanup_message, cleanup_error))
            raise
    return tuple(results)
