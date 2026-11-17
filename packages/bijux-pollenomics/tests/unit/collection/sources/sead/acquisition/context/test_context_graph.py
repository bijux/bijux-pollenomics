"""Independent generated graph, receipt and physical publication challenges."""

from copy import deepcopy
from email.message import Message
from hashlib import sha256
import io
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.context import (
    SeadContextLimits,
    SeadContextSite,
    acquire_unresolved_sead_context,
    publication,
    read_sead_context,
    transport,
)
from bijux_pollenomics.collection.sources.sead.acquisition.context.workflow import (
    CONTEXT_PLANS,
    ContextCollector,
)

SITES = (
    SeadContextSite(2, "c3e38c42-36ad-40dd-8958-436ad141d108", "review"),
    SeadContextSite(3441, "12ae88cc-a58f-4093-8afd-8cbdf1d95795", "unassigned"),
)


def graph():
    values = {
        "tbl_sites": [{"site_id": s.site_id, "site_uuid": s.site_uuid} for s in SITES],
        "tbl_sample_groups": [
            {"sample_group_id": 11, "site_id": 2},
            {"sample_group_id": 12, "site_id": 3441},
        ],
        "tbl_physical_samples": [
            {"physical_sample_id": 21, "sample_group_id": 11},
            {"physical_sample_id": 22, "sample_group_id": 12},
        ],
        "tbl_analysis_entities": [
            {"analysis_entity_id": 31, "physical_sample_id": 21, "dataset_id": 41},
            {"analysis_entity_id": 32, "physical_sample_id": 22, "dataset_id": 42},
        ],
        "tbl_analysis_entity_ages": [
            {
                "analysis_entity_age_id": 51,
                "analysis_entity_id": 31,
                "chronology_id": 9001,
                "age": 0,
                "age_older": 13.25,
            }
        ],
        "tbl_geochronology": [
            {
                "geochron_id": 61,
                "analysis_entity_id": 32,
                "dating_lab_id": 9002,
                "dating_uncertainty_id": 91,
                "age": 145.125,
            }
        ],
        "tbl_dendro_dates": [
            {
                "dendro_date_id": 71,
                "analysis_entity_id": 31,
                "age_type_id": 81,
                "dating_uncertainty_id": None,
                "dendro_lookup_id": 9003,
                "season_id": None,
            }
        ],
        "tbl_analysis_values": [{"analysis_value_id": 101, "analysis_entity_id": 31}],
        "tbl_analysis_dating_ranges": [
            {
                "analysis_dating_range_id": 111,
                "analysis_value_id": 101,
                "age_type_id": 82,
                "dating_uncertainty_id": 91,
                "low_value": 0,
                "high_value": 125.5,
            }
        ],
        "tbl_relative_dates": [
            {
                "relative_date_id": 121,
                "analysis_entity_id": 32,
                "relative_age_id": 131,
                "method_id": 141,
                "dating_uncertainty_id": 92,
            }
        ],
        "tbl_age_types": [{"age_type_id": 81}, {"age_type_id": 82}],
        "tbl_relative_ages": [
            {"relative_age_id": 131, "cal_age_older": 0, "c14_age_younger": 37.5}
        ],
        "tbl_relative_age_refs": [
            {"relative_age_ref_id": 151, "relative_age_id": 131, "biblio_id": 211}
        ],
        "tbl_dating_uncertainty": [
            {"dating_uncertainty_id": 91},
            {"dating_uncertainty_id": 92},
        ],
        "tbl_methods": [{"method_id": 141}],
        "tbl_datasets": [
            {"dataset_id": 41, "biblio_id": 211},
            {"dataset_id": 42, "biblio_id": 212},
        ],
        "tbl_site_references": [
            {"site_reference_id": 171, "site_id": 3441, "biblio_id": 211}
        ],
        "tbl_sample_group_references": [
            {"sample_group_reference_id": 181, "sample_group_id": 11, "biblio_id": 212}
        ],
        "tbl_biblio": [{"biblio_id": 211}, {"biblio_id": 212}],
    }
    return {
        p.table: [
            dict.fromkeys(p.projection.split(",")) | row for row in values[p.table]
        ]
        for p in CONTEXT_PLANS
    }


class Page(io.BytesIO):
    status = 200

    def __init__(self, url, rows):
        super().__init__(json.dumps(rows, allow_nan=False).encode())
        self.url, self.read_sizes = url, []

    def read(self, size=-1):
        self.read_sizes.append(size)
        return super().read(size)


class Source:
    def __init__(self, rows=None, *, eof416=False, foreign=None):
        self.rows = graph() if rows is None else rows
        self.eof416, self.foreign = eof416, foreign
        self.calls, self.responses, self.error_streams = [], [], []

    def __call__(self, url, **kwargs):
        table = urlsplit(url).path.rsplit("/", 1)[-1]
        plan = next(p for p in CONTEXT_PLANS if p.table == table)
        query = parse_qs(urlsplit(url).query)
        assert query["select"] == [plan.projection]
        ids = [int(v) for v in query[plan.filter_field][0][4:-1].split(",")]
        assert ids == sorted(set(ids))
        rows = [deepcopy(r) for r in self.rows[table] if r[plan.filter_field] in ids]
        if self.foreign == table:
            rows = deepcopy(self.rows[table])
        start, end = map(int, kwargs["headers"]["Range"].split("-"))
        self.calls.append({"table": table, "ids": ids, "offset": start})
        if self.eof416 and start >= len(rows):
            headers = Message()
            headers["Content-Range"] = "*/" + str(len(rows))
            stream = io.BytesIO(b"generated EOF error entity")
            self.error_streams.append(stream)
            raise HTTPError(url, 416, "generated exact EOF", headers, stream)
        response = Page(url, rows[start : end + 1])
        self.responses.append(response)
        return response


def collector(source, **limits):
    return ContextCollector(
        sites=SITES,
        run_id="independent-context",
        parent_run_id="generated-parent",
        build_id="generated-build",
        opener=source,
        limits=SeadContextLimits(**limits),
    )


def acquire(output, private, source, **limits):
    return acquire_unresolved_sead_context(
        output,
        recovery_root=private,
        sites=SITES,
        run_id="independent-context",
        parent_run_id="generated-parent",
        build_id="generated-build",
        opener=source,
        limits=SeadContextLimits(**limits),
    )


def test_exact_approved_plan_and_generated_graph_roundtrip(tmp_path):
    authority = Path(
        "/Users/bijan/bijux/bijux-pollenomics/artifacts/data-collection-audit/sead-context-source-review/reconciliation/review-context-packet-plan.json"
    )
    raw = authority.read_bytes()
    assert (
        sha256(raw).hexdigest()
        == "15cd5ce47fd5db19ed2ec1a1b955c951b7e478e3b63461db8764542a7509846e"
    )
    expected = json.loads(raw)["tables"]
    assert [
        (
            p.table,
            p.primary_key,
            p.projection,
            p.filter_field,
            [(d.table, d.field) for d in p.dependencies],
        )
        for p in CONTEXT_PLANS
    ] == [
        (
            r["table"],
            r["primary_key"],
            r["projection"],
            r["filter_field"],
            [(d["table"], d["field"]) for d in r["dependencies"]],
        )
        for r in expected
    ]
    source = Source()
    path = acquire(tmp_path / "output", tmp_path / "private", source)
    manifest = read_sead_context(
        path.parent, expected_manifest_sha256=sha256(path.read_bytes()).hexdigest()
    )
    assert (
        manifest["country_admission"] is manifest["ecological_event_admission"] is False
    )
    assert manifest["sites"] == [
        {
            "site_id": s.site_id,
            "site_uuid": s.site_uuid,
            "membership_status": s.membership_status,
        }
        for s in SITES
    ]
    assert all(response.closed for response in source.responses)
    for plan in CONTEXT_PLANS:
        body = json.loads(
            (path.parent / "payloads" / (plan.table + ".json")).read_bytes()
        )
        assert body["rows"] == graph()[plan.table]
    biblios = [r for r in source.calls if r["table"] == "tbl_biblio"]
    assert all(r["ids"] == [211, 212] for r in biblios)


def test_foreign_site_UUID_refuses_before_dependency_or_second_page():
    rows = graph()
    rows["tbl_sites"][0]["site_uuid"] = SITES[1].site_uuid
    source = Source(rows)
    with pytest.raises(ValueError, match="UUID"):
        collector(source, page_size=1).acquire()
    assert source.calls == [{"table": "tbl_sites", "ids": [2, 3441], "offset": 0}]


def test_foreign_intermediate_owner_refuses_before_page_or_descendant():
    rows = graph()
    rows["tbl_physical_samples"][0]["sample_group_id"] = 999
    source = Source(rows, foreign="tbl_physical_samples")
    with pytest.raises(ValueError, match="owner"):
        collector(source, page_size=1).acquire()
    assert len([r for r in source.calls if r["table"] == "tbl_physical_samples"]) == 1
    assert not any(r["table"] == "tbl_analysis_entities" for r in source.calls)


@pytest.mark.parametrize("invalid_key", [True, "41"])
def test_invalid_declared_outgoing_key_refuses_before_next_page(tmp_path, invalid_key):
    rows = graph()
    rows["tbl_analysis_entities"][0]["dataset_id"] = invalid_key
    source = Source(rows)
    with pytest.raises(ValueError, match="source key"):
        collector(source, page_size=1).acquire()
    pages = [r for r in source.calls if r["table"] == "tbl_analysis_entities"]
    (tmp_path / "outgoing-native-key-proof.json").write_text(
        json.dumps(
            {
                "invalid_key": invalid_key,
                "analysis_entity_pages": pages,
                "total_source_requests": len(source.calls),
                "chronology_related_requests_after_invalid_page": [
                    r
                    for r in source.calls
                    if r["table"]
                    in {
                        "tbl_analysis_entity_ages",
                        "tbl_geochronology",
                        "tbl_dendro_dates",
                        "tbl_relative_dates",
                    }
                ],
            },
            indent=2,
        )
        + "\n"
    )
    assert len(pages) == 1


def test_literal_null_FK_causes_empty_identity_record_without_request():
    rows = graph()
    for row in rows["tbl_analysis_entities"]:
        row["dataset_id"] = None
    source = Source(rows)
    value = collector(source)
    value.acquire()
    assert not any(r["table"] == "tbl_datasets" for r in source.calls)
    assert (
        value.receipts["tbl_datasets"]["completion_basis"]
        == "empty_dependency_identity_set"
    )
    assert all(r["dataset_id"] is None for r in value.tables["tbl_analysis_entities"])


def test_missing_lookup_has_EOF_evidence_and_no_invented_row():
    rows = graph()
    rows["tbl_analysis_entities"][0]["dataset_id"] = 701
    source = Source(rows)
    value = collector(source)
    result = value.acquire()
    assert result["country_admission"] is result["ecological_event_admission"] is False
    assert value.receipts["tbl_datasets"]["requested_ids"] == [42, 701]
    assert [r["dataset_id"] for r in value.tables["tbl_datasets"]] == [42]
    assert value.tables["tbl_analysis_entities"][0]["dataset_id"] == 701
    assert (
        value.receipts["tbl_datasets"]["completion_basis"]
        == "all_dependency_batches_source_eof"
    )


def test_exact_HTTP416_EOF_closes_error_streams_without_absence_claim():
    source = Source(eof416=True)
    value = collector(source)
    result = value.acquire()
    assert result["status"] == "complete_context_only"
    assert all(s.closed for s in source.error_streams)
    assert all(
        r["pagination"]["pages"][-1]["eof"]["kind"] == "unsatisfied_range"
        for r in value.query_receipts
    )


def test_response_cap_refuses_before_real_decode_and_next_request(monkeypatch):
    calls = []
    real = transport.decode

    def decode(raw):
        calls.append(len(raw))
        return real(raw)

    monkeypatch.setattr(transport, "decode", decode)
    source = Source()
    value = collector(source, response_bytes=16)
    with pytest.raises(ValueError, match="byte budget"):
        value.acquire()
    assert calls == [] and len(source.calls) == 1
    assert value.transport.byte_count == 17 and source.responses[0].closed
    assert source.responses[0].read_sizes == [17]


def test_private_packet_pin_refuses_before_any_payload_read(tmp_path, monkeypatch):
    from bijux_pollenomics.core.filesystem import BoundedInputTree

    path = acquire(tmp_path / "output", tmp_path / "private", Source())
    names = []
    real = BoundedInputTree.read

    def read(tree, member, *args, **kwargs):
        names.append(Path(member).name)
        return real(tree, member, *args, **kwargs)

    monkeypatch.setattr(BoundedInputTree, "read", read)
    with pytest.raises(ValueError, match="independent authority"):
        read_sead_context(path.parent, expected_manifest_sha256="0" * 64)
    assert names == ["manifest.json"]


def test_partial_stream_primary_survives_close_failure_and_retains_bytes(tmp_path):
    primary = OSError("generated partial source primary")

    class Broken(Page):
        def read(self, size=-1):
            if self.tell():
                raise primary
            return super().read(min(size, 7))

        def close(self):
            first = not self.closed
            super().close()
            if first:
                raise RuntimeError("generated secondary close")

    def opener(url, **kwargs):
        return Broken(url, graph()["tbl_sites"])

    with pytest.raises(OSError) as caught:
        acquire(tmp_path / "output", tmp_path / "private", opener)
    assert caught.value is primary
    assert not (tmp_path / "output").exists()
    manifests = list((tmp_path / "private").glob("*/candidate/manifest.json"))
    assert len(manifests) == 1
    value = json.loads(manifests[0].read_bytes())
    assert value["status"] == "partial_context_only"
    assert (manifests[0].parent / "responses/0001.json").stat().st_size == 7
    assert any("close failed" in n for n in primary.__notes__)


def test_original_destination_parent_checked_inside_attachment_boundary(
    tmp_path, monkeypatch
):
    parent = tmp_path / "destination-parent"
    parent.mkdir()
    (parent / "original.txt").write_text("ORIGINAL")
    displaced = tmp_path / "held-original-parent"
    fired = []
    real = publication.publish_owned_replacement

    def swap(writer, **kwargs):
        fired.append(True)
        parent.rename(displaced)
        parent.mkdir()
        (parent / "foreign.txt").write_text("FOREIGN")
        return real(writer, **kwargs)

    monkeypatch.setattr(publication, "publish_owned_replacement", swap)
    result, error = None, None
    try:
        result = acquire(parent / "output", tmp_path / "private", Source())
    except ValueError as caught:
        error = caught
    (tmp_path / "parent-attachment-proof.json").write_text(
        json.dumps(
            {
                "fault_fired": bool(fired),
                "returned_manifest": None if result is None else str(result),
                "error": None if error is None else str(error),
                "foreign_final_published": (parent / "output/manifest.json").is_file(),
                "foreign_namespace": sorted(p.name for p in parent.iterdir()),
            },
            indent=2,
        )
        + "\n"
    )
    assert fired == [True]
    assert {p.name for p in parent.iterdir()} == {"foreign.txt"}
    assert error is not None
    assert (displaced / "original.txt").read_text() == "ORIGINAL"
