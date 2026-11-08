"""Source-free counterexamples for the separately attributed DALMUT adjunct."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import hashlib
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.literal_window_support import (
    dalmutladdo_archival_counts as counts,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.regional_source_support import (
    TAXA,
    WINDOWS,
)


def fixture() -> tuple[dict[str, Any], bytes]:
    """Build an artificial 72-row shape, never a substitute for source pins."""
    window_by_id = {
        owner: list(edge)
        for edge, owners in zip(WINDOWS, counts.WINDOW_OWNERS, strict=True)
        for owner in owners
    }
    outside = [
        owner
        for owner in range(175353, 175425)
        if owner not in window_by_id and owner != 175354
    ]
    missing = set(counts.MISSING_WINDOW_OWNERS) | set(outside[:31])
    samples = []
    lines = []
    for index, owner in enumerate(range(175353, 175425)):
        absent = owner in missing
        taxa = []
        for axis, taxon in enumerate(TAXA):
            value = 3 if axis == 0 else 2
            taxa.append(
                {
                    **taxon,
                    "status": "missing_literal" if absent and axis == 1 else "measured",
                    "native_matches": []
                    if absent and axis == 1
                    else [
                        {
                            "datum_index": axis,
                            "native": {
                                "taxonid": taxon["taxon_id"],
                                "variablename": taxon["label"],
                                "value": value,
                                "units": "NISP",
                                "context": None,
                                "element": "pollen",
                                "elementtype": "pollen",
                            },
                        }
                    ],
                }
            )
        samples.append(
            {
                "sample_id": owner,
                "native_depth": 4.5 if index == 1 else index * 4,
                "window": window_by_id.get(owner),
                "taxa": taxa,
                "pollen_N": 10,
                "pollen_denominator_status": "complete",
            }
        )
        cells = ["UNREAD_OTHER_TAXON"] * 98
        cells[0] = str(Decimal(index * 4) / 100)
        cells[9], cells[93] = "3", "0" if absent else "2"
        # The unmatched row's target cells must never be interpreted.
        if index == 1:
            cells[9] = cells[93] = "UNREAD_UNMATCHED_TARGET"
        lines.append("\t".join(cells))
    headers = ["unread"] * 98
    for index, header in zip((0, 9, 93), counts.HEADERS, strict=True):
        headers[index] = header
    raw = (
        f"/* https://doi.org/{counts.DOI} */\n"
        + "\t".join(headers)
        + "\n"
        + "\n".join(lines)
        + "\n"
    ).encode()
    account = {
        "schema_version": "nordic-literal-core-support.v1",
        "key": "dalmutladdo",
        "identity": {
            "collection_unit_id": 14989,
            "dataset_id": 20034,
            "handle": "DALMUT",
            "site_id": 13388,
            "source_sample_count": 72,
        },
        "chronology": {"selected_chronology_id": 11601},
        "samples": samples,
        "windows": [
            {"window": list(edge), "sample_ids": list(owners)}
            for edge, owners in zip(WINDOWS, counts.WINDOW_OWNERS, strict=True)
        ],
    }
    return account, raw


def test_fixed_membership_source_attribution_and_exact_mixed_mass() -> None:
    account, raw = fixture()
    original = deepcopy(account)
    pairs = counts._correspondence(account, counts._table(raw))
    windows = counts._windows(account, pairs)
    assert account == original
    assert len(pairs) == 71 and 175354 not in pairs
    for row, owners, absent in zip(
        windows, counts.WINDOW_OWNERS, (4, 2, 2, 1, 1, 2), strict=True
    ):
        n = len(owners)
        panel = [3 * n, 2 * (n - absent)]
        assert row["sample_ids"] == list(owners)
        assert row["status"] == "supported"
        assert row["panel_counts"] == panel and row["panel_N"] == sum(panel)
        assert row["native_pollen_N"] == 10 * n
        assert row["mixed_source_literal_nonpanel_N"] == 10 * n - sum(panel)
        assert "pollen_N" not in row and "excluded_pollen_N" not in row
        assert [s["sample_id"] for s in row["source_cells"]] == list(owners)
        for sample in row["source_cells"]:
            assert sample["archival_row_index"] == sample["sample_id"] - 175353
            assert [c["column_index"] for c in sample["cells"]] == [9, 93]
            assert all(c["doi"] == counts.DOI for c in sample["cells"])
            assert sample["cells"][1]["native_status"] == (
                "missing_literal"
                if sample["sample_id"] in counts.MISSING_WINDOW_OWNERS
                else "measured"
            )


def test_all_shared_cells_precede_any_absent_token_inspection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account, raw = fixture()
    table = counts._table(raw)
    # Put a shared conflict last, after every absent native owner in input order.
    account["samples"][-1]["taxa"][0]["native_matches"][0]["native"]["value"] = 4
    forbidden = {
        sample["sample_id"] - 175353
        for sample in account["samples"]
        if sample["taxa"][1]["status"] == "missing_literal"
    }
    original = counts._archival_count

    def guarded(row: counts._ArchivalRow, axis: int) -> tuple[str, int]:
        assert not (axis == 1 and row.index in forbidden)
        return original(row, axis)

    monkeypatch.setattr(counts, "_archival_count", guarded)
    with pytest.raises(ValueError, match="Shared original/native count conflict"):
        counts._correspondence(account, table)


@pytest.mark.parametrize("token", ["", "NA", "?", "-1", "0.0", "1", "false"])
def test_absent_counterpart_requires_a_reported_integer_zero(token: str) -> None:
    account, raw = fixture()
    table = counts._table(raw)
    old = table[Decimal(0)]
    fields = old.line.split("\t")
    fields[93] = token
    table[Decimal(0)] = counts._ArchivalRow(
        old.index, old.depth_token_m, "\t".join(fields)
    )
    with pytest.raises(ValueError, match="integer|explicit zero"):
        counts._correspondence(account, table)


@pytest.mark.parametrize(
    "kind",
    [
        "owner",
        "duplicate_owner",
        "bool_owner",
        "depth",
        "duplicate_depth",
        "window",
        "taxon",
        "unit",
        "bool_count",
        "float_count",
        "negative_count",
        "duplicate_cell",
    ],
)
def test_owner_depth_literal_metadata_and_integer_contracts_refuse(kind: str) -> None:
    account, raw = fixture()
    sample = account["samples"][-1]
    native = sample["taxa"][0]["native_matches"][0]["native"]
    if kind == "owner":
        sample["sample_id"] = 999
    elif kind == "duplicate_owner":
        sample["sample_id"] = 175353
    elif kind == "bool_owner":
        sample["sample_id"] = True
    elif kind == "depth":
        sample["native_depth"] += 0.5
    elif kind == "duplicate_depth":
        sample["native_depth"] = 0
    elif kind == "window":
        account["samples"][19]["window"] = None
    elif kind == "taxon":
        native["taxonid"] = 4431
    elif kind == "unit":
        native["units"] = "%"
    elif kind == "bool_count":
        native["value"] = True
    elif kind == "float_count":
        native["value"] = 3.0
    elif kind == "negative_count":
        native["value"] = -1
    else:
        sample["taxa"][0]["native_matches"].append(
            deepcopy(sample["taxa"][0]["native_matches"][0])
        )
    with pytest.raises(ValueError):
        counts._correspondence(account, counts._table(raw))


@pytest.mark.parametrize(
    "kind",
    ["doi", "depth_unit", "count_header", "duplicate_depth", "row_width", "population"],
)
def test_archival_source_identity_shape_and_depth_contracts(kind: str) -> None:
    _, raw = fixture()
    lines = raw.decode().splitlines()
    if kind == "doi":
        lines[0] = "/* Different source */"
    elif kind == "depth_unit":
        lines[1] = lines[1].replace("Depth sed [m]", "Depth sed [cm]")
    elif kind == "count_header":
        lines[1] = lines[1].replace(
            "Bet [#] (Betula)", "B/C/M [#] (Betula/Corylus/Myrica)"
        )
    elif kind == "duplicate_depth":
        lines[-1] = "0\t" + lines[-1].split("\t", 1)[1]
    elif kind == "row_width":
        lines[-1] += "\textra"
    else:
        lines.pop()
    with pytest.raises(ValueError):
        counts._table("\n".join(lines).encode())


def test_missing_native_mass_stays_refused_and_panel_cannot_exceed_mass() -> None:
    account, raw = fixture()
    pairs = counts._correspondence(account, counts._table(raw))
    sample = account["samples"][19]
    sample["pollen_denominator_status"] = "refused_invalid_or_duplicate_pollen_rows"
    sample["pollen_N"] = None
    first = counts._windows(account, pairs)[0]
    assert first["status"] == "suppressed_full_mass"
    assert first["panel_N"] == 17 and first["native_pollen_N"] is None
    assert first["mixed_source_literal_nonpanel_N"] is None
    sample["pollen_denominator_status"], sample["pollen_N"] = "complete", 2
    with pytest.raises(ValueError, match="exceeds"):
        counts._windows(account, pairs)


def test_zero_panel_remains_explicitly_suppressed() -> None:
    account, raw = fixture()
    pairs = counts._correspondence(account, counts._table(raw))
    for owner in counts.WINDOW_OWNERS[0]:
        old = pairs[owner]
        fields = old.line.split("\t")
        fields[9] = fields[93] = "0"
        pairs[owner] = counts._ArchivalRow(
            old.index, old.depth_token_m, "\t".join(fields)
        )
    first = counts._windows(account, pairs)[0]
    assert first["status"] == "suppressed_zero_panel" and first["panel_counts"] == [
        0,
        0,
    ]
    assert first["native_pollen_N"] == first["mixed_source_literal_nonpanel_N"] == 50


@pytest.mark.parametrize(
    "bad", [None, "not bytes", bytearray(b"wrong"), b"wrong", bytes(133669)]
)
def test_public_api_never_accepts_unpinned_or_coerced_sources(bad: Any) -> None:
    with pytest.raises(ValueError, match="Exact frozen DALMUT source bytes"):
        counts.archival_window_counts(bad, b"wrong")


def test_public_api_rejects_wrong_archival_bytes_after_exact_native_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Exercise the second guard without adding a private source table fixture.
    native = bytes(133669)
    monkeypatch.setattr(counts, "NATIVE_SHA256", hashlib.sha256(native).hexdigest())
    with pytest.raises(ValueError, match="Exact frozen DALMUT source bytes"):
        counts.archival_window_counts(native, bytes(40251))
