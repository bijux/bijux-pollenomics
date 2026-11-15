"""Literal source additions with independently fixed predecessor identities."""

from __future__ import annotations

RESOURCE_PUBLICATION_SPANS: dict[str, tuple[str, tuple[tuple[bytes, bytes], ...]]] = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/static_assets/asset_inventory.py": (
        "dccd61cc2a03bbd20d89a4ef95e397bafc1ed3bd2736bb430761f0f691391bab",
        (
            (
                (b'    "sequences",\n    "indexes",\n}\n\n'),
                (b'    "sequences",\n    "indexes",\n    "resources",\n}\n\n'),
            ),
            (
                (
                    b"    if domain not in _ASSET_DOMAINS:\n"
                    b'        raise ValueError("static atlas asset domain is invalid")\n'
                    b'    return "gzip_base64" if domain in {"nodes", "details", "provenance"} else "json"\n'
                    b"\n"
                    b"\n"
                ),
                (
                    b"    if domain not in _ASSET_DOMAINS:\n"
                    b'        raise ValueError("static atlas asset domain is invalid")\n'
                    b"    return (\n"
                    b'        "gzip_base64"\n'
                    b'        if domain in {"nodes", "details", "provenance", "resources"}\n'
                    b'        else "json"\n'
                    b"    )\n"
                    b"\n"
                    b"\n"
                ),
            ),
            (
                (
                    b"    if domain not in _ASSET_DOMAINS:\n"
                    b'        raise ValueError("static atlas asset domain is invalid")\n'
                    b'    return domain not in {"nodes", "details", "indexes"}\n'
                    b"\n"
                    b"\n"
                ),
                (
                    b"    if domain not in _ASSET_DOMAINS:\n"
                    b'        raise ValueError("static atlas asset domain is invalid")\n'
                    b'    return domain not in {"nodes", "details", "indexes", "resources"}\n'
                    b"\n"
                    b"\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/contracts.py": (
        "5674253433e951e2f06254c03437ba533574119f45dd2c548e3f9ba684d4c65d",
        (
            (
                (b"    }\n    if animal_chronology_context is not None:\n"),
                (
                    b"    }\n"
                    b'    resource_domain = static_assets.manifest["domains"].get("resources")\n'
                    b"    if resource_domain is not None:\n"
                    b'        map_publication_contract["source_resources"] = {\n'
                    b"            key: resource_domain[key]\n"
                    b"            for key in (\n"
                    b'                "catalogue_manifest_sha256",\n'
                    b'                "record_count",\n'
                    b'                "site_count",\n'
                    b'                "version_status_count",\n'
                    b'                "scientific_admission",\n'
                    b'                "numerical_atlas_denominator_changed",\n'
                    b"            )\n"
                    b"        }\n"
                    b"    if animal_chronology_context is not None:\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/published_reports.py": (
        "f4212c0fbd7c043d2475c1dcd04865c8bc8426db995d4f63bb8f7a069e1eac39",
        (
            (
                (
                    b")\n"
                    b"from ..models import CountryReport, MultiCountryMapReport, PublishedReportsReport\n"
                ),
                (
                    b")\n"
                    b"from ..map_document.source_resources import AtlasResourceCatalogueInput\n"
                    b"from ..models import CountryReport, MultiCountryMapReport, PublishedReportsReport\n"
                ),
            ),
            (
                (
                    b"    write_summary_json_fn: Callable[[Path, dict[str, object]], None],\n"
                    b") -> PublishedReportsReport:\n"
                ),
                (
                    b"    write_summary_json_fn: Callable[[Path, dict[str, object]], None],\n"
                    b"    source_resource_catalogue: AtlasResourceCatalogueInput | None = None,\n"
                    b") -> PublishedReportsReport:\n"
                ),
            ),
            (
                (b"        geography_scope=world_scope,\n    )\n"),
                (
                    b"        geography_scope=world_scope,\n"
                    b"        **(\n"
                    b'            {"source_resource_catalogue": source_resource_catalogue}\n'
                    b"            if source_resource_catalogue is not None\n"
                    b"            else {}\n"
                    b"        ),\n"
                    b"    )\n"
                ),
            ),
            (
                (b"            geography_scope=scope,\n        )\n"),
                (
                    b"            geography_scope=scope,\n"
                    b"            **(\n"
                    b'                {"source_resource_catalogue": source_resource_catalogue}\n'
                    b"                if source_resource_catalogue is not None\n"
                    b"                else {}\n"
                    b"            ),\n"
                    b"        )\n"
                ),
            ),
        ),
    ),
}
