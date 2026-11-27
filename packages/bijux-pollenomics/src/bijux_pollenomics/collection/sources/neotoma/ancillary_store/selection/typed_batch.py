"""All-or-nothing typed facet reads under one bounded source operation."""

from collections.abc import Mapping
from functools import partial
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.errors.cleanup import add_cleanup_note

from ...capture.facets.assessment import assess_http as facet_assessment
from ...capture.facets.profiles import qualify_neotoma_facet_body
from ...capture.receipts import _read
from ...capture.resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits
from ...resource_catalogue.source_projection import _same
from ..context.seals import context_seals
from .access import _result
from .batch import prepare_neotoma_preflight_batch
from .preflight import _prepared_facet_access

_MAX_ITEMS = 128
_MAX_BODIES = 64 * 1024 * 1024


def _cleanup_message(error: BaseException) -> str:
    return f"Facet batch cleanup failed: {error}"


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
) -> tuple[dict[str, Any], ...]:
    """Return fully qualified selected bodies only after the whole operation passes.

    Metadata caching never owns native entity buffers. Physical drift checks are
    operation-local and do not establish an atomic snapshot or scientific admission.
    """
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
                prepared.append((access, facet, receipt, bound, member, size, path))
                total += size
            for access, facet, receipt, bound, member, size, path in prepared:
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
                results.append({**result, "source_qualification": qualified})
            batch.close()
        except BaseException as error:
            try:
                batch._abort()
            except BaseException as cleanup_error:
                add_cleanup_note(error, partial(_cleanup_message, cleanup_error))
            raise
    return tuple(results)
