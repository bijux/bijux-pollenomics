"""Fail-closed XML parsing with a narrowly governed JATS exception."""

from __future__ import annotations

import re

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]


class UnsafeXmlSourceError(ValueError):
    """Raised when XML contains a forbidden declaration or reference."""


_JATS_DOCTYPE = (
    rb"<!DOCTYPE[\t\n\r ]+article[\t\n\r ]+PUBLIC[\t\n\r ]+"
    rb'"-//NLM//DTD JATS \(Z39\.96\) Journal Archiving and Interchange DTD '
    rb'with MathML3 v1\.4 20241031//EN"[\t\n\r ]+'
    rb'"JATS-archivearticle1-4-mathml3\.dtd"[\t\n\r ]*>'
)
_JATS_PROLOG_RE = re.compile(
    rb"\A(?:\xef\xbb\xbf)?[\t\n\r ]*"
    rb"(?:<\?xml[\t\n\r ][^?]*\?>[\t\n\r ]*)?"
    rb"(?P<doctype>" + _JATS_DOCTYPE + rb")"
)
_DOCTYPE_MARKER = b"<!DOCTYPE"


def parse_hardened_xml(
    payload: bytes,
    *,
    permit_pinned_jats_doctype: bool = False,
) -> ET.Element:
    """Parse XML without DTD semantics, entity expansion, or external access.

    The captured Europe PMC article carries one pinned external JATS declaration.
    That exact declaration may be removed before parsing; its DTD is never loaded
    or applied. Every other DTD, including an internal subset, remains forbidden.
    """
    parse_payload = payload
    if _DOCTYPE_MARKER in payload:
        if not permit_pinned_jats_doctype:
            raise UnsafeXmlSourceError("DTD declarations are forbidden")
        match = _JATS_PROLOG_RE.match(payload)
        if match is None:
            raise UnsafeXmlSourceError("XML does not use the pinned JATS doctype")
        suffix = payload[match.end() :]
        if _DOCTYPE_MARKER in suffix:
            raise UnsafeXmlSourceError("Multiple DTD declarations are forbidden")
        start, end = match.span("doctype")
        parse_payload = payload[:start] + payload[end:]
    try:
        return ET.fromstring(
            parse_payload,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )
    except (
        ET.DTDForbidden,
        ET.EntitiesForbidden,
        ET.ExternalReferenceForbidden,
    ) as error:
        raise UnsafeXmlSourceError("Unsafe XML source payload") from error
