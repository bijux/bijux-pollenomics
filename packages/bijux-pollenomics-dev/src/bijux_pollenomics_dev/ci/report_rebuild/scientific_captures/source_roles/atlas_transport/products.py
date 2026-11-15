"""Restore exact regional-draw presentation declarations before prior source law."""

from __future__ import annotations

from hashlib import sha256

_REFINEMENTS: dict[str, tuple[str, tuple[tuple[bytes, bytes], ...]]] = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py": (
        "756bd56ee1af690979287ee4759897814b89b44d6bc3bc72d256deb49026438f",
        (
            (
                (b""),
                (
                    b"from ...analysis.lra.inputs.regional_draw_love import REGIONAL_DRAW_LOVE_REQUEST_SCHEMA\n"
                ),
            ),
            (
                (b""),
                (
                    b'    supplied_draws = request["schema_version"] == "lra-regional-draw-love-request.v1"\n'
                    b"    estimate_scope = (\n"
                    b'        "<p>This local LOVE result uses supplied regional-cover draws in fractions, "\n'
                    b'        "not measured regional pollen. Local cover is in fractions. This report "\n'
                    b'        "retains the complete original numerical tables below and in downloads; "\n'
                    b'        "typed estimate rows and a geographic map are unavailable for this profile. "\n'
                    b'        "The saved request retains the draw-source binding, seed and configuration. "\n'
                    b'        "Values retain original CSV decimal text; N/A remains missing. q10/q90 are "\n'
                    b'        "method quantiles, not total uncertainty or held-out predictive intervals.</p>"\n'
                    b"        if supplied_draws\n"
                    b'        else "<p>REVEALS cover: percent. LOVE cover: fraction. "\n'
                    b'        "Values retain original CSV decimal text; N/A remains missing. q10/q90 are method "\n'
                    b'        "quantiles, not total uncertainty or held-out predictive intervals.</p>"\n'
                    b"    )\n"
                    b"    compatibility = (\n"
                    b'        manifest.get("scientific_identity", {})\n'
                    b'        .get("engine_scientific_manifest", {})\n'
                    b'        .get("compatibility_mode")\n'
                    b"    )\n"
                    b'    if compatibility == "analytical-love-clip-and-renormalize":\n'
                    b"        estimate_scope += (\n"
                    b'            "<p>Declared LOVE cover assumption: negative cover is set to zero and "\n'
                    b'            "each draw is normalized to a total of one before summaries. The raw equation "\n'
                    b'            "summaries and outlier diagnostics remain in the downloaded product. "\n'
                    b'            "This assumption does not establish true taxon absence or field accuracy.</p>"\n'
                    b"        )\n"
                ),
            ),
            (
                (
                    b'            + "<h2>Native estimates</h2><p>REVEALS cover: percent. LOVE cover: fraction. "\n'
                    b'            "Values retain original CSV decimal text; N/A remains missing. q10/q90 are method "\n'
                    b'            "quantiles, not total uncertainty or held-out predictive intervals.</p>"\n'
                    b'            "<table><thead><tr><th>Role</th><th>Site</th><th>Taxon</th><th>Statistic</th>"\n'
                ),
                (
                    b'            + "<h2>Native estimates</h2>"\n'
                    b"            + estimate_scope\n"
                    b'            + "<table><thead><tr><th>Role</th><th>Site</th><th>Taxon</th><th>Statistic</th>"\n'
                ),
            ),
            (
                (b"        Draft202012Validator(REQUEST_SCHEMA).validate(request)\n"),
                (
                    b"        schema = (\n"
                    b"            REGIONAL_DRAW_LOVE_REQUEST_SCHEMA\n"
                    b'            if request.get("schema_version") == "lra-regional-draw-love-request.v1"\n'
                    b"            else REQUEST_SCHEMA\n"
                    b"        )\n"
                    b"        Draft202012Validator(schema).validate(request)\n"
                ),
            ),
            (
                (b""),
                (
                    b'                "compatibility_mode": manifest.get("scientific_identity", {})\n'
                    b'                .get("engine_scientific_manifest", {})\n'
                    b'                .get("compatibility_mode"),\n'
                ),
            ),
        ),
    ),
}


def without_regional_product_refinement(name: str, current: bytes) -> bytes | None:
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
