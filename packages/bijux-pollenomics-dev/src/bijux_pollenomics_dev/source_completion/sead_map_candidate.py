"""Audit the built Nordic SEAD map against its governed source and browser replay."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, cast

from bijux_pollenomics.core.filesystem import read_regular_file
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)
from bijux_pollenomics_dev.docs.sead_evidence_sync import synchronize_sead_evidence

COUNTRIES = {"Denmark": "DK", "Finland": "FI", "Norway": "NO", "Sweden": "SE"}
SITE_LAYER = "sead-sites"
RECORD_LAYER = "sweden-archaeology-site-discovery"
REPORT = Path("docs/report/source-relations/sead/map-candidate")
HISTORICAL_SOURCE = Path("data/sead/normalized/nordic_environmental_sites.geojson")
HISTORICAL_LINEAGE = Path("data/sead/normalized/source_lineage.json")
HISTORICAL_INTERVALS = Path(
    "docs/report/source-relations/sead/interval-sets/report.json"
)
HISTORICAL_CUSTODY = Path(
    "docs/report/source-relations/sead/public-custody/report.json"
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def validate_historical_browser_binding(
    candidate: Path, generation_bytes: bytes, browser: dict[str, Any]
) -> None:
    """Require an explicitly candidate-bound browser receipt for v2 audits."""
    generation = json.loads(generation_bytes)
    if not isinstance(generation, dict):
        raise ValueError("SEAD historical browser generation differs")
    served = browser.get("served_files_sha256")
    if (
        browser.get("schema_version") != "atlas-nordic-source-browser-verification.v2"
        or browser.get("candidate_generation_sha256") != _sha(generation_bytes)
        or browser.get("candidate_build_id") != generation.get("candidate_build_id")
        or browser.get("source_atlas_build_id")
        != generation.get("source_atlas_build_id")
        or not isinstance(generation.get("candidate_build_id"), str)
        or not isinstance(generation.get("source_atlas_build_id"), str)
        or browser.get("status") != "PASS"
        or browser.get("runtime_errors") != []
        or not isinstance(served, dict)
        or "index.html" not in served
        or not any(isinstance(path, str) and ".atlas-nodes." in path for path in served)
        or not any(
            isinstance(path, str) and ".atlas-details." in path for path in served
        )
    ):
        raise ValueError("SEAD historical browser receipt is unbound")
    for name, expected in served.items():
        if not isinstance(name, str) or not name or "\\" in name:
            raise ValueError("SEAD historical browser served path differs")
        relative = Path(name)
        if relative.is_absolute() or any(
            part in {".", ".."} for part in relative.parts
        ):
            raise ValueError("SEAD historical browser served path differs")
        payload = read_regular_file(candidate / relative, max_bytes=64 * 1024 * 1024)
        if not isinstance(expected, str) or _sha(payload) != expected:
            raise ValueError("SEAD historical browser served bytes differ")
    html = read_regular_file(
        candidate / "index.html", max_bytes=64 * 1024 * 1024
    ).decode()
    match = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    if (
        match is None
        or json.loads(match.group(1)).get("build_id")
        != generation["candidate_build_id"]
    ):
        raise ValueError("SEAD historical browser candidate build differs")
    records = generation.get("source_records")
    tables = browser.get("chronology_tables")
    if (
        not isinstance(records, list)
        or len(records) != 8
        or any(
            not isinstance(row, dict) or not isinstance(row.get("record_id"), str)
            for row in records
        )
        or not isinstance(tables, list)
        or len(tables) != 16
    ):
        raise ValueError("SEAD historical browser record inventory differs")
    by_id = {row["record_id"]: row for row in records}
    if len(by_id) != 8:
        raise ValueError("SEAD historical browser record identity differs")
    seen: set[tuple[int, str]] = set()
    for row in tables:
        if (
            not isinstance(row, dict)
            or type(row.get("width")) is not int
            or row.get("width") not in {390, 1440}
            or not isinstance(row.get("record_id"), str)
            or row["record_id"] not in by_id
        ):
            raise ValueError("SEAD historical browser chronology identity differs")
        identity = (row["width"], row["record_id"])
        if identity in seen:
            raise ValueError("SEAD historical browser chronology identity differs")
        seen.add(identity)
        chronology = by_id[row["record_id"]].get("chronology")
        if not isinstance(chronology, dict):
            raise ValueError("SEAD historical browser chronology differs")
        expected_rows = chronology.get("records")
        if isinstance(expected_rows, list):
            if row.get("all_source_cells_equal") is not True or row.get("rows") != len(
                expected_rows
            ):
                raise ValueError("SEAD historical browser chronology differs")
        elif (
            row.get("status") != "unavailable"
            or row.get("reason_code") != chronology.get("reason_code")
            or row.get("source_null_not_zero") is not True
        ):
            raise ValueError("SEAD historical browser chronology differs")
    if seen != {(width, key) for width in (390, 1440) for key in by_id}:
        raise ValueError("SEAD historical browser chronology inventory differs")


def validate_historical_input_bindings(
    source_bytes: bytes,
    lineage_bytes: bytes,
    interval_bytes: bytes,
    custody_bytes: bytes,
    pins: tuple[str, str, str, str],
    source_count: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate caller-selected identities, without attesting producer execution."""
    payloads = (source_bytes, lineage_bytes, interval_bytes, custody_bytes)
    if any(
        not isinstance(pin, str)
        or len(pin) != 64
        or any(c not in "0123456789abcdef" for c in pin)
        for pin in pins
    ) or any(_sha(payload) != pin for payload, pin in zip(payloads, pins, strict=True)):
        raise ValueError("SEAD historical input digest differs")
    documents = [json.loads(payload) for payload in payloads]
    if any(not isinstance(document, dict) for document in documents):
        raise ValueError("SEAD historical input document differs")
    source, lineage, intervals, custody = documents
    source_sha, lineage_sha, _, _ = pins
    run_id = "sead-full-evidence-39bfff6a-ce80714e"
    build_id = "sha256:ce80714e4c9e9974b24913e5da50f49854670ed642879c1ca5076499e1d56725"
    bundle_sha = (
        "sha256:fdcda26e7de9a09383b0d9aae7ab7f9e8846c7cbf05513da17fdb8e329331ba9"
    )
    membership = {
        "purpose": "historical_admission_cohort",
        "authority_id": "sha256:e67d7e498df146bcdd65c398f67cdf2372298258288bcba9af734486fa2fe8d0",
        "artifact_digest": "sha256:bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f",
    }
    interval_hashes = intervals.get("input_hashes")
    lineage_hashes = lineage.get("normalized_surface_sha256")
    refresh = lineage.get("refresh_input_sha256")
    custody_hashes = custody.get("inputs_sha256")
    posture = {
        "record_intervals_are_distinct": True,
        "site_display_envelope_is_analytic_interval": False,
        "qualified_or_contextual_claims_admitted": False,
        "event_propagation_approved": False,
    }
    if (
        lineage.get("schema_version") != "sead-normalized-surface-lineage.v2"
        or lineage.get("source_run_id") != run_id
        or lineage.get("build_id") != build_id
        or lineage.get("acquisition_manifest_sha256")
        != "6fc2428046d148f9ce6c158f982afbbbbaea39de2132850a4fb8f41acf8a4c14"
        or lineage.get("parent_admission_sha256")
        != "168ad1efe6fa68cdb7789246a6cce16670377cdbacd14d1673beaab8ddd1ebd1"
        or lineage.get("acquisition_bundle_sha256") != bundle_sha
        or lineage.get("country_membership") != membership
        or not isinstance(lineage_hashes, dict)
        or lineage_hashes.get("normalized/nordic_environmental_sites.geojson")
        != source_sha
        or not isinstance(refresh, dict)
        or refresh.get("boundary/normalized/nordic_country_boundaries.geojson")
        != membership["artifact_digest"].removeprefix("sha256:")
        or refresh.get("evidence/evidence_materialization_manifest.json")
        != "383151443d04da5a6e127ea2e4344b4b10bb210137dd1d13b77e50dbfae93508"
        or intervals.get("schema_version") != "sead-interval-set-review.v1"
        or intervals.get("source_run_id") != run_id
        or intervals.get("source_build_id") != build_id
        or intervals.get("analytic_posture") != posture
        or not isinstance(interval_hashes, dict)
        or interval_hashes.get("site_geojson_sha256") != source_sha
        or interval_hashes.get("claim_index_sha256")
        != "b9accf421059eebf95b75a8c22fd237f4d51991fbc868e79530d20a694e6cd21"
        or custody.get("schema_version") != "sead-public-source-custody.v1"
        or custody.get("source_run_id") != run_id
        or custody.get("acquisition_bundle_sha256") != bundle_sha
        or custody.get("raw_and_public_site_count") != source_count
        or custody.get("excluded_decision_count") != 126
        or custody.get("excluded_status_counts") != {"review": 103, "unassigned": 23}
        or not isinstance(custody_hashes, dict)
        or custody_hashes.get(HISTORICAL_SOURCE.as_posix()) != source_sha
        or custody_hashes.get(HISTORICAL_LINEAGE.as_posix()) != lineage_sha
        or custody_hashes.get(
            "docs/report/regions/nordic/nordic_environmental_sites.geojson"
        )
        != source_sha
    ):
        raise ValueError("SEAD historical source, interval or custody identity differs")
    return source, intervals


def validate_historical_site_projection(
    source: dict[str, Any], features: list[dict[str, Any]], intervals: dict[str, Any]
) -> int:
    """Reconcile every historical source site's displayed bounds with atlas nodes."""
    rows = source.get("features")
    if source.get("type") != "FeatureCollection" or not isinstance(rows, list):
        raise ValueError("SEAD historical site GeoJSON differs")
    source_sites: dict[str, dict[str, Any]] = {}
    for row in rows:
        if (
            not isinstance(row, dict)
            or row.get("type") != "Feature"
            or not isinstance(row.get("properties"), dict)
        ):
            raise ValueError("SEAD historical site feature differs")
        site = row["properties"]
        raw_id = site.get("record_id")
        if not isinstance(raw_id, str) or not raw_id or raw_id in source_sites:
            raise ValueError("SEAD historical site identity differs")
        start, end = site.get("time_start_bp"), site.get("time_end_bp")
        if (start is None) != (end is None) or (
            start is not None
            and (
                type(start) is not int
                or type(end) is not int
                or start < 0
                or end < start
            )
        ):
            raise ValueError("SEAD historical site bounds differ")
        if not all(
            isinstance(site.get(key), str) and site[key]
            for key in ("site_uuid", "country")
        ):
            raise ValueError("SEAD historical site identity differs")
        source_sites[raw_id] = site
    seen: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError("SEAD historical atlas feature differs")
        identifier = feature.get("record_id")
        if not isinstance(identifier, str) or not identifier.startswith("sead:site:"):
            raise ValueError("SEAD historical atlas identity differs")
        site_id = identifier.removeprefix("sead:site:")
        if site_id in seen or site_id not in source_sites:
            raise ValueError("SEAD historical atlas identity differs")
        seen.add(site_id)
        site = source_sites[site_id]
        if any(
            feature.get(key) != site.get(key)
            or type(feature.get(key)) is not type(site.get(key))
            for key in ("site_uuid", "country", "time_start_bp", "time_end_bp")
        ):
            raise ValueError("SEAD historical atlas site fields differ")
    if seen != set(source_sites):
        raise ValueError("SEAD historical atlas site set differs")
    denominators = intervals.get("denominators")
    if not isinstance(denominators, dict):
        raise ValueError("SEAD historical interval denominators differ")
    total = denominators.get("exported_sites")
    dated = denominators.get("sites_with_display_envelope")
    untimed = sum(site.get("time_start_bp") is None for site in source_sites.values())
    if (
        type(total) is not int
        or type(dated) is not int
        or total != len(source_sites)
        or not 0 <= dated <= total
        or untimed != total - dated
    ):
        raise ValueError("SEAD historical interval denominators differ")
    return untimed


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _chunk(directory: Path, row: dict[str, Any]) -> dict[str, Any]:
    path = directory / row["path"]
    payload = path.read_bytes()
    if _sha(payload) != row["sha256"]:
        raise ValueError(f"Built atlas chunk hash changed: {row['path']}")
    return decode_chunk_script(
        payload,
        expected_asset_key=row["asset_key"],
        expected_payload_sha256=row["payload_sha256"],
        expected_payload_encoding=row["payload_encoding"],
        expected_decoded_byte_count=row.get("decoded_byte_count"),
    )


def _built_layers(
    repository: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, list[dict[str, Any]]], int]:
    directory = repository / "docs/report/regions/nordic"
    html = (directory / "nordic_map.html").read_text()
    match = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    if match is None:
        raise ValueError("Built Nordic map has no static bootstrap")
    manifest = json.loads(match.group(1))
    inventory = normalize_asset_inventory(manifest["assets"])
    provenance = _chunk(
        directory, next(row for row in inventory if row["domain"] == "provenance")
    )
    layers = {
        entry["layer"]["key"]: entry["layer"]
        for entry in provenance["layers"]
        if entry["layer"]["key"] in {SITE_LAYER, RECORD_LAYER}
    }
    if set(layers) != {SITE_LAYER, RECORD_LAYER}:
        raise ValueError("Built SEAD layers are missing")
    features: dict[str, list[dict[str, Any]]] = {key: [] for key in layers}
    for row in inventory:
        layer_key = row.get("layer_key")
        if (
            row["domain"] == "nodes"
            and isinstance(layer_key, str)
            and layer_key in features
        ):
            nodes = _chunk(directory, row)["features"]
            if len(nodes) != row["record_count"]:
                raise ValueError("Built SEAD node count differs from manifest")
            features[layer_key].extend(nodes)
    edge_row = next(row for row in inventory if row["domain"] == "edges")
    edge_count = len(_chunk(directory, edge_row)["records"])
    return manifest, layers, features, edge_count


def _run_time_filter(
    repository: Path, features: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    html = (
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html"
    ).read_text()
    start = html.index("function finiteTimeValue")
    end = html.index("function pointFeatureInTimeWindow", start)
    helpers = html[start:end]
    site = next(
        feature
        for feature in features[SITE_LAYER]
        if feature["record_id"] == "sead:site:3840"
    )
    unresolved = next(
        feature
        for feature in features[SITE_LAYER]
        if feature["record_id"] == "sead:site:6468"
    )
    zero = next(
        feature for feature in features[SITE_LAYER] if feature.get("time_start_bp") == 0
    )
    records = [
        feature
        for feature in features[RECORD_LAYER]
        if feature["record_id"] == "sead:site:3840"
    ]
    if len(records) != 11:
        raise ValueError("Disjoint-site regression no longer has 11 source records")
    js = (
        "const TIME_HAS_DATA=true; let timeStartBp=84,timeIntervalYears=20;\n"
        "function timeWindowEndBp(){return timeStartBp+timeIntervalYears}\n"
        "function timeFilterUsesFullExtent(){return false}\n"
        + helpers
        + "\nconst input=JSON.parse(require('node:fs').readFileSync(0,'utf8'));\n"
        "const recordLayer={applies_time_filter:true,semantic_role:'source_chronology_context'};\n"
        "const siteLayer={applies_time_filter:false};\n"
        "const gap=input.records.filter(x=>featureInTimeWindow(recordLayer,x));\n"
        "timeStartBp=82;timeIntervalYears=0;\n"
        "const dated=input.records.filter(x=>featureInTimeWindow(recordLayer,x));\n"
        "timeStartBp=0;timeIntervalYears=0;\n"
        "console.log(JSON.stringify({gap_record_count:gap.length,at_82_record_count:dated.length,"
        "zero_site_status:featureTimeAdmission(input.zero).status,"
        "zero_site_in_test_window:featureInTimeWindow(recordLayer,input.zero),"
        "unresolved_site_status:featureTimeAdmission(input.unresolved).status,"
        "unresolved_site_in_test_window:featureInTimeWindow(recordLayer,input.unresolved),"
        "site_layer_applies_time_filter:siteLayer.applies_time_filter,"
        "site_hull_visible_as_context:featureInTimeWindow(siteLayer,input.site)}));\n"
    )
    result = subprocess.run(
        ["node", "-e", js],
        input=json.dumps(
            {"site": site, "unresolved": unresolved, "zero": zero, "records": records}
        ),
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    observed = cast(dict[str, Any], json.loads(result.stdout))
    expected = {
        "gap_record_count": 0,
        "at_82_record_count": 2,
        "zero_site_status": "valid",
        "zero_site_in_test_window": True,
        "unresolved_site_status": "contextual",
        "unresolved_site_in_test_window": False,
        "site_layer_applies_time_filter": False,
        "site_hull_visible_as_context": True,
    }
    if observed != expected:
        raise ValueError(f"Built SEAD time-filter behavior differs: {observed}")
    return observed


def audit(
    repository: Path,
    candidate: Path,
    browser_receipt: Path,
    *,
    historical_site_sha256: str | None = None,
    historical_lineage_sha256: str | None = None,
    historical_interval_sha256: str | None = None,
    historical_custody_sha256: str | None = None,
) -> dict[str, Any]:
    """Check exact built payloads, governed denominators and browser detail outcome."""
    options = (
        historical_site_sha256,
        historical_lineage_sha256,
        historical_interval_sha256,
        historical_custody_sha256,
    )
    if any(value is not None for value in options) and not all(
        value is not None for value in options
    ):
        raise ValueError("Historical map audit pins must be supplied together")
    historical = all(value is not None for value in options)
    repository = repository.resolve()
    manifest, layers, features, edge_count = _built_layers(repository)
    site_features, record_features = features[SITE_LAYER], features[RECORD_LAYER]
    source = repository / "docs/report/source-relations/sead"
    country = _read_json(source / "country-coverage/report.json")
    claims = _read_json(source / "chronology-country-accounting/report.json")
    if historical:
        pins = cast(tuple[str, str, str, str], options)
        selected = tuple(
            read_regular_file(repository / path, max_bytes=64 * 1024 * 1024)
            for path in (
                HISTORICAL_SOURCE,
                HISTORICAL_LINEAGE,
                HISTORICAL_INTERVALS,
                HISTORICAL_CUSTODY,
            )
        )
        site_source, intervals = validate_historical_input_bindings(
            selected[0], selected[1], selected[2], selected[3], pins, len(site_features)
        )
        map_copy = read_regular_file(
            repository
            / "docs/report/regions/nordic/nordic_environmental_sites.geojson",
            max_bytes=64 * 1024 * 1024,
        )
        if map_copy != selected[0]:
            raise ValueError("SEAD historical map copy differs from selected source")
        expected_site_untimed = validate_historical_site_projection(
            site_source, site_features, intervals
        )
    else:
        intervals = _read_json(source / "interval-sets/report.json")
        expected_site_untimed = 1219
    contract = _read_json(
        repository / "docs/report/regions/nordic/nordic_map_publication_contract.json"
    )
    synchronize_sead_evidence(repository, check=True)
    map_prose = (
        repository / "docs/report/regions/nordic/nordic_map_publication_contract.md"
    ).read_text()
    handbook = (
        repository / "docs/public/pollenomics-data/sources/sead-handbook.md"
    ).read_text()
    if not all(
        phrase in map_prose
        for phrase in (
            "Site envelopes summarize source chronology and are not dated events or interval evidence.",
            "| `2069` |",
            "| `8799` |",
        )
    ) or not all(
        phrase in handbook
        for phrase in (
            "| assigned four-country sites | 2,069 |",
            "| Swedish numeric chronology features | 7,244 |",
            "| chronology claims | 25,109 |",
        )
    ):
        raise ValueError(
            "Public SEAD map narrative no longer matches governed counts or posture"
        )
    if historical:
        generation_bytes = read_regular_file(
            candidate / "generation.json", max_bytes=64 * 1024 * 1024
        )
        browser_bytes = read_regular_file(browser_receipt, max_bytes=64 * 1024 * 1024)
        generation = json.loads(generation_bytes)
        browser = json.loads(browser_bytes)
        if not isinstance(browser, dict):
            raise ValueError("SEAD historical browser receipt differs")
        validate_historical_browser_binding(candidate, generation_bytes, browser)
    else:
        generation = _read_json(candidate / "generation.json")
        browser = _read_json(browser_receipt)
    source_id = country["source_run_id"]
    if {
        claims["source_run_id"],
        intervals["source_run_id"],
        contract["detail_projection"]["sources"]["sead"]["source_run_id"],
    } != {source_id}:
        raise ValueError("SEAD report and map source runs differ")
    counts = Counter(feature["country"] for feature in site_features)
    expected_counts = {
        next(
            name for name, code in COUNTRIES.items() if code == row["country_code"]
        ): row["governed_assigned_sites"]
        for row in country["country_rows"]
    }
    if (
        counts != expected_counts
        or len(site_features) != intervals["denominators"]["exported_sites"]
    ):
        raise ValueError("Built SEAD site and governed country counts differ")
    site_untimed = sum(
        feature.get("time_start_bp") is None and feature.get("time_end_bp") is None
        for feature in site_features
    )
    record_untimed = sum(
        feature.get("time_start_bp") is None and feature.get("time_end_bp") is None
        for feature in record_features
    )
    record_numeric = len(record_features) - record_untimed
    if (len(record_features), record_numeric, record_untimed, site_untimed) != (
        8799,
        intervals["denominators"]["exported_record_intervals"],
        1555,
        expected_site_untimed,
    ):
        raise ValueError("Built SEAD chronology display denominators differ")
    if any(feature["country"] != "Sweden" for feature in record_features):
        raise ValueError("Swedish discovery layer gained unsupported country scope")
    if (
        layers[SITE_LAYER]["applies_time_filter"]
        or layers[SITE_LAYER]["default_enabled"]
        or not layers[RECORD_LAYER]["applies_time_filter"]
    ):
        raise ValueError("Built SEAD layer visibility/time posture differs")
    rows_by_key = {row["key"]: row for row in contract["layer_rows"]}
    for key in (SITE_LAYER, RECORD_LAYER):
        if (
            layers[key]["coverage_label"] != rows_by_key[key]["coverage_label"]
            or layers[key]["count"] != rows_by_key[key]["count"]
        ):
            raise ValueError("Built SEAD layer and public contract prose/count differ")
    if (
        "not dated events or interval evidence"
        not in layers[SITE_LAYER]["coverage_label"]
    ):
        raise ValueError("Site hull is not explicitly identified as context")
    if (
        country["eligible_evidence_event_count"],
        contract["detail_projection"]["sources"]["sead"]["eligible_event_count"],
    ) != (0, 0):
        raise ValueError("SEAD ecological event count gained admission")
    if any(
        row["eligible_evidence_events"] or row["propagation_eligible_sites"]
        for row in country["country_rows"]
    ):
        raise ValueError("SEAD country event eligibility changed")
    if (
        contract["detail_projection"]["sources"]["sead"]["propagation_status"]
        != "refused"
        or edge_count != 0
    ):
        raise ValueError("Built map has accepted SEAD propagation")
    if (
        browser["status"] != "PASS"
        or browser["runtime_errors"]
        or len(browser["chronology_tables"]) != 16
    ):
        raise ValueError("Four-country browser detail replay did not pass")
    if (
        generation["source_atlas_build_id"] != manifest["build_id"]
        or not generation["selected_source_record_equality"]
    ):
        raise ValueError("Browser candidate does not match built Nordic map")
    if len(generation["source_records"]) != 8 or set(generation["countries"]) != set(
        COUNTRIES
    ):
        raise ValueError("Browser candidate lacks a four-country source detail pair")
    time_filter = _run_time_filter(repository, features)
    return {
        "schema_version": "sead-built-map-candidate-audit.v2"
        if historical
        else "sead-built-map-candidate-audit.v1",
        **(
            {
                "historical_input_sha256": {
                    HISTORICAL_SOURCE.as_posix(): pins[0],
                    HISTORICAL_LINEAGE.as_posix(): pins[1],
                    HISTORICAL_INTERVALS.as_posix(): pins[2],
                    HISTORICAL_CUSTODY.as_posix(): pins[3],
                },
                "historical_input_posture": "caller-pinned identities and site identity, country and time-bound correspondence; no producer execution, scientific admission or comprehensive browser qualification is inferred",
            }
            if historical
            else {}
        ),
        "status": "PASS",
        "source_run_id": source_id,
        "source_release_status": contract["detail_projection"]["sources"]["sead"][
            "acquisition_release_status"
        ],
        "published_atlas_build_id": manifest["build_id"],
        "browser_candidate_build_id": generation["candidate_build_id"],
        "browser_status": browser["status"],
        "browser_chronology_table_checks": len(browser["chronology_tables"]),
        "browser_runtime_error_count": len(browser["runtime_errors"]),
        "public_evidence_sync_status": "current",
        "site_count": len(site_features),
        "site_country_counts": dict(sorted(counts.items())),
        "site_untimed_count": site_untimed,
        "record_count": len(record_features),
        "record_numeric_count": record_numeric,
        "record_unresolved_count": record_untimed,
        "reviewed_claim_count": claims["claim_count"],
        "eligible_ecological_event_count": 0,
        "built_accepted_edge_count": edge_count,
        "cross_border_propagation_posture": "refused_zero_eligible_events_all_four_countries",
        "time_filter_regression": time_filter,
        "source_sha256": {
            str(path.relative_to(repository)): _sha(path.read_bytes())
            for path in (
                source / "country-coverage/report.json",
                source / "chronology-country-accounting/report.json",
                *(() if historical else (source / "interval-sets/report.json",)),
                repository / "docs/report/regions/nordic/nordic_map.html",
                repository
                / "docs/report/regions/nordic/nordic_map_publication_contract.json",
                repository
                / "docs/report/regions/nordic/nordic_map_publication_contract.md",
                repository / "docs/public/pollenomics-data/sources/sead.md",
                repository / "docs/public/pollenomics-data/sources/sead-handbook.md",
                repository
                / "docs/public/pollenomics-data/publications/sead-exports.md",
                repository
                / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html",
                Path(__file__).resolve(),
            )
        },
        "browser_receipt_sha256": _sha(
            browser_bytes if historical else browser_receipt.read_bytes()
        ),
        "candidate_generation_sha256": _sha(
            generation_bytes
            if historical
            else (candidate / "generation.json").read_bytes()
        ),
    }


def main() -> None:
    """Write a governed result for an actual built and browser-checked candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--browser-receipt", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--historical-site-sha256")
    parser.add_argument("--historical-lineage-sha256")
    parser.add_argument("--historical-interval-sha256")
    parser.add_argument("--historical-custody-sha256")
    args = parser.parse_args()
    historical = any(
        value is not None
        for value in (
            args.historical_site_sha256,
            args.historical_lineage_sha256,
            args.historical_interval_sha256,
            args.historical_custody_sha256,
        )
    )
    if historical and (
        args.output is None
        or args.output.exists()
        or args.output.is_symlink()
        or not args.output.resolve().is_relative_to(
            args.repository.resolve() / "artifacts"
        )
    ):
        raise ValueError("Historical map audit requires an absent artifact output")
    result = audit(
        args.repository,
        args.candidate,
        args.browser_receipt,
        historical_site_sha256=args.historical_site_sha256,
        historical_lineage_sha256=args.historical_lineage_sha256,
        historical_interval_sha256=args.historical_interval_sha256,
        historical_custody_sha256=args.historical_custody_sha256,
    )
    output = args.output or args.repository / REPORT
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (output / "README.md").write_text(
        "# SEAD built map candidate\n\n"
        f"The {'inspected' if historical else 'published'} Nordic atlas build `{result['published_atlas_build_id']}` and the "
        f"browser candidate `{result['browser_candidate_build_id']}` agree on the "
        f"retained four-country SEAD source details. The browser replay checked "
        f"{result['browser_chronology_table_checks']} chronology tables at two widths "
        f"with {result['browser_runtime_error_count']} runtime errors. "
        "The public SEAD evidence blocks and map layer prose/counts match the "
        "governed sources. The [machine report](report.json) binds the checked "
        "source and map bytes.\n\n"
        f"The built site layer contains {result['site_count']:,} context points, including "
        f"{result['site_untimed_count']:,} without numeric site envelopes. "
        f"The Swedish discovery layer contains {result['record_count']:,} features: "
        f"{result['record_numeric_count']:,} numeric record intervals and "
        f"{result['record_unresolved_count']:,} unresolved context records. "
        "A live run of the map's time-filter functions excluded every site 3840 "
        "record from the 84–104 BP gap and admitted the two 82 BP records at 82 BP; "
        "a source-backed 0 BP site envelope remained numeric while an unresolved "
        "site remained outside the test time window. The optional site inventory "
        "ignores the time filter because its envelopes are display context.\n\n"
        f"The source review contains {result['reviewed_claim_count']:,} typed chronology "
        "claims and zero eligible ecological events across Denmark, Finland, Norway "
        "and Sweden. The built atlas contains zero accepted propagation edges. "
        "Cross-border candidate materialization is therefore refused for lack of "
        "admissible event endpoints; a national border is not a rejection rule. "
        f"The pinned acquisition release status is `{result['source_release_status']}`. "
        "Site envelopes do not establish occupation, arrival or propagation.\n\n"
        + (
            "The v2 browser receipt contract binds the candidate generation and "
            "served bytes; the current retained browser verifier does not emit "
            "that schema. Caller-pinned, self-reported receipt bytes do not "
            "independently attest producer or browser execution. Historical "
            "inputs and the output remain separately qualified.\n\n"
            if historical
            else ""
        )
        + (
            "## Reproduce\n\n"
            "A historical v2 replay requires separately qualified source, lineage, "
            "interval and custody SHA-256 values and an independently qualified "
            "candidate-bound v2 browser receipt. The current v1 browser verifier "
            "cannot produce that receipt. Supply all four `--historical-*-sha256` "
            "options and an absent output under `artifacts/`.\n"
            if historical
            else (
                "## Reproduce\n\n"
                "From the repository root, run the existing retained-source candidate and "
                "browser verifier, then this audit with their output paths:\n\n"
                "```sh\n"
                "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m "
                "bijux_pollenomics_dev.ci.atlas_browser.nordic_source_candidate "
                "--repository . --destination artifacts/sead-map-candidate/source-display\n"
                "node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic-country.mjs "
                "artifacts/sead-map-candidate/source-display artifacts/sead-map-candidate/browser "
                "'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'\n"
                "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m "
                "bijux_pollenomics_dev.source_completion.sead_map_candidate "
                "--repository . --candidate artifacts/sead-map-candidate/source-display "
                "--browser-receipt artifacts/sead-map-candidate/browser/receipt.json\n"
                "```\n\n"
                "Use absent artifact destinations for a replay. The browser result is a bounded "
                "retained-source detail check; it does not certify event-level ecology, "
                "source release, hosted deployment or all browser engines.\n"
            )
        )
    )
    print(
        json.dumps({"status": result["status"], "output": str(output / "report.json")})
    )


if __name__ == "__main__":
    main()
