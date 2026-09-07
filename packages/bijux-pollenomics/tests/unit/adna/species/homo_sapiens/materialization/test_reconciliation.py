"""Adversarial AADR panel-reconciliation tests."""

from pathlib import Path

from bijux_pollenomics.adna.species.homo_sapiens.materialization import (
    AadrSourceTable,
    load_aadr_source_table,
    reconcile_aadr_panels,
)

_HEADER = "\t".join(
    (
        "Genetic ID",
        "Method for Determining Date",
        "Date mean in BP",
        "Date standard deviation in BP",
        "Full Date",
        "Latitude",
        "Longitude",
    )
)


def _table(
    tmp_path: Path, dataset_name: str, rows: list[tuple[str, ...]]
) -> AadrSourceTable:
    source = _HEADER + "\n" + "\n".join("\t".join(row) for row in rows) + "\n"
    path = tmp_path / f"{dataset_name}.anno"
    path.write_text(source, encoding="utf-8")
    return load_aadr_source_table(path, source_release="v66", dataset_name=dataset_name)


def test_genetic_id_grouping_trims_only_outer_whitespace_and_accounts_for_all_rows(
    tmp_path: Path,
) -> None:
    table = _table(
        tmp_path,
        "ho",
        [
            (" ID-1 ", "Direct", "100", "10", "", "59", "18"),
            ("ID-1", "Direct", "100", "10", "", "59", "18"),
            ("id-1", "Direct", "100", "10", "", "59", "18"),
            ("ID  1", "Direct", "100", "10", "", "59", "18"),
            ("  ", "Direct", "100", "10", "", "59", "18"),
        ],
    )

    result = reconcile_aadr_panels((table,))

    assert result.dataset_names == ("ho",)
    assert [record.genetic_id for record in result.records] == ["ID  1", "ID-1", "id-1"]
    target = next(record for record in result.records if record.genetic_id == "ID-1")
    assert target.genetic_id_raw_values == (" ID-1 ", "ID-1")
    assert len(target.source_rows) == 2
    assert result.source_row_count == 5
    assert len(result.unkeyed_rows) == 1
    assert result.unkeyed_rows[0].genetic_id_raw == "  "
    assert result.unkeyed_rows[0].refusal_reason_code == "genetic_id_missing"
    assert result.unkeyed_rows[0].taxon_scope_status == "not_asserted_by_source"
    assert all(
        record.taxon_scope_status == "not_asserted_by_source"
        for record in result.records
    )


def test_semantically_equal_evidence_is_exact_without_discarding_raw_variants(
    tmp_path: Path,
) -> None:
    ho = _table(
        tmp_path,
        "ho",
        [("ID-1", "Direct", "100", "10", "100-80 BP", "59", "18")],
    )
    capture = _table(
        tmp_path,
        "1240k",
        [("ID-1", " direct ", "100.0", "10.0", "100-80 BP", "59.0", "18.00")],
    )

    [record] = reconcile_aadr_panels((ho, capture)).records

    assert record.coordinate_status == "exact"
    assert record.chronology_status == "exact"
    assert record.panel_status == "exact"
    assert record.reconciliation_status == "exact"
    assert len(record.coordinate_groups) == 2
    assert len(record.chronology_groups) == 2
    assert {group.evidence.latitude_raw for group in record.coordinate_groups} == {
        "59",
        "59.0",
    }
    assert {group.evidence.date_mean_bp_raw for group in record.chronology_groups} == {
        "100",
        "100.0",
    }


def test_complementary_evidence_remains_separate_and_is_never_synthesized(
    tmp_path: Path,
) -> None:
    numeric = _table(
        tmp_path,
        "ho",
        [("ID-1", "Direct", "100", "10", "", "", "")],
    )
    textual = _table(
        tmp_path,
        "1240k",
        [("ID-1", "", "", "", "100-80 BP", "59", "18")],
    )

    [record] = reconcile_aadr_panels((numeric, textual)).records

    assert record.coordinate_status == "complementary"
    assert record.chronology_status == "complementary"
    assert record.reconciliation_status == "complementary"
    assert len(record.chronology_groups) == 2
    assert not any(
        group.evidence.date_mean_bp.parsed_value is not None
        and group.evidence.full_date.tokens
        for group in record.chronology_groups
    )


def test_conflicting_atomic_pairs_and_signed_dates_are_not_first_wins_or_unioned(
    tmp_path: Path,
) -> None:
    first = _table(
        tmp_path,
        "ho",
        [("ID-1", "Direct", "100", "10", "120-80 BP", "59", "18")],
    )
    second = _table(
        tmp_path,
        "1240k",
        [("ID-1", "Direct", "-25", "10", "-30--20 BP", "60", "19")],
    )

    [record] = reconcile_aadr_panels((first, second)).records

    assert record.coordinate_status == "conflict"
    assert record.chronology_status == "conflict"
    assert record.reconciliation_status == "conflict"
    assert {
        (group.evidence.latitude, group.evidence.longitude)
        for group in record.coordinate_groups
    } == {(59.0, 18.0), (60.0, 19.0)}
    assert (59.0, 19.0) not in {
        (group.evidence.latitude, group.evidence.longitude)
        for group in record.coordinate_groups
    }
    assert {group.evidence.date_mean_bp.sign for group in record.chronology_groups} == {
        "negative",
        "positive",
    }
    assert all(
        not group.evidence.scientifically_admitted for group in record.chronology_groups
    )


def test_partial_coordinate_pair_cannot_complete_another_atomic_pair(
    tmp_path: Path,
) -> None:
    partial = _table(
        tmp_path,
        "ho",
        [("ID-1", "", "", "", "", "59", "")],
    )
    point = _table(
        tmp_path,
        "1240k",
        [("ID-1", "", "", "", "", "59", "18")],
    )

    [record] = reconcile_aadr_panels((partial, point)).records

    assert record.coordinate_status == "conflict"
    assert {group.evidence.status for group in record.coordinate_groups} == {
        "admitted",
        "partial",
    }


def test_every_dimension_group_links_back_to_every_retained_source_row(
    tmp_path: Path,
) -> None:
    ho = _table(
        tmp_path,
        "ho",
        [
            ("ID-1", "Direct", "100", "10", "", "59", "18"),
            ("ID-1", "Direct", "100", "10", "", "59", "18"),
        ],
    )
    capture = _table(
        tmp_path,
        "1240k",
        [("ID-1", "Direct", "100", "10", "", "59", "18")],
    )

    [record] = reconcile_aadr_panels((ho, capture)).records
    expected_keys = sorted(link.key for link in record.source_rows)

    assert (
        sorted(
            link.key for group in record.coordinate_groups for link in group.source_rows
        )
        == expected_keys
    )
    assert (
        sorted(
            link.key for group in record.chronology_groups for link in group.source_rows
        )
        == expected_keys
    )
    assert all(
        row.taxon_scope_status == "not_asserted_by_source"
        for table in (ho, capture)
        for row in table.rows
    )


def test_reconciliation_is_independent_of_panel_iteration_order(tmp_path: Path) -> None:
    ho = _table(
        tmp_path,
        "ho",
        [("ID-2", "Context", "200", "20", "", "60", "19")],
    )
    capture = _table(
        tmp_path,
        "1240k",
        [("ID-1", "Modern", "0", "0", "", "59", "18")],
    )

    forward = reconcile_aadr_panels((ho, capture))
    reverse = reconcile_aadr_panels((capture, ho))

    assert forward == reverse
    assert forward.dataset_names == ("1240k", "ho")
    assert all(record.panel_status == "complementary" for record in forward.records)
    assert all(
        record.reconciliation_status == "complementary" for record in forward.records
    )
