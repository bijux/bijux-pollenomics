"""Restore exact multipart index readers and named optional-controller labels."""

from __future__ import annotations

from hashlib import sha256

_REFINEMENTS: dict[str, tuple[str, tuple[tuple[bytes, bytes], ...]]] = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py": (
        "945345f28035a9a5da795ca3110fe40bbd19015fe2f2f46b95d0bf4b0465d877",
        (
            (
                (
                    b"from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (\n"
                    b"    decode_index_bundle,\n"
                ),
                (
                    b"from bijux_pollenomics.reporting.map_document.static_assets.index_transport import (\n"
                    b"    decode_index_payloads,\n"
                ),
            ),
            (
                (
                    b"    indexes = decode_index_bundle(\n"
                    b'        chunk(next(row for row in inventory if row["domain"] == "indexes"))\n'
                ),
                (
                    b'    index_rows = [row for row in inventory if row["domain"] == "indexes"]\n'
                    b"    indexes = decode_index_payloads(\n"
                    b"        index_rows,\n"
                    b'        {str(row["asset_key"]): chunk(row) for row in index_rows},\n'
                    b"        manifest=manifest,\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source_detail_candidate.py": (
        "a3ba29b98b2b3efdbbe149a2498dcbd0471f309616010c788908bc171a8aab0d",
        (
            (
                (
                    b"from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (\n"
                    b"    decode_index_bundle,\n"
                ),
                (
                    b"from bijux_pollenomics.reporting.map_document.static_assets.index_transport import (\n"
                    b"    decode_index_payloads,\n"
                ),
            ),
            (
                (
                    b"    indexes = decode_index_bundle(\n"
                    b'        chunk(next(row for row in inventory if row["domain"] == "indexes"))\n'
                ),
                (
                    b'    index_rows = [row for row in inventory if row["domain"] == "indexes"]\n'
                    b"    indexes = decode_index_payloads(\n"
                    b"        index_rows,\n"
                    b'        {str(row["asset_key"]): chunk(row) for row in index_rows},\n'
                    b"        manifest=manifest,\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py": (
        "a7333ec7a5f4868019c940e7b64245a629ec16632847f6d3232e033a50bf07ad",
        (
            (
                (b'        ("Interactive evidence tools", path.name)\n'),
                (
                    b"        (\n"
                    b'            "Static atlas index transport"\n'
                    b'            if path.name.rsplit(".", 3)[-3] == "atlas-index-transport"\n'
                    b'            else "Interactive evidence tools",\n'
                    b"            path.name,\n"
                    b"        )\n"
                ),
            ),
        ),
    ),
}


def without_index_transport_refinement(name: str, current: bytes) -> bytes | None:
    """Restore only a fixed normal-Git predecessor before its existing owner law."""
    contract = _REFINEMENTS.get(name)
    if contract is None:
        return current
    predecessor_sha256, pairs = contract
    if not any(extension in current for _, extension in pairs):
        return current
    restored = current
    for prior, extension in pairs:
        if restored.count(extension) != 1:
            return None
        restored = restored.replace(extension, prior, 1)
    return restored if sha256(restored).hexdigest() == predecessor_sha256 else None
