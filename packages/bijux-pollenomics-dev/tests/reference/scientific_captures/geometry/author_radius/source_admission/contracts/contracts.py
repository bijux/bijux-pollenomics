"""Keep complete prior-exposed radius science distinct from changed source identities."""

from __future__ import annotations

import ast
from copy import deepcopy
import csv
import io
from typing import Any

JsonObject = dict[str, Any]
EXPECTED = {
    "radius_report": "ad730572b453eff95328f83cd0848d05b8a9b3601f4b06027ba82962af248c6a",
    "radius_scores": "60bf6b4cc25bf94a9afbb241370d55e7be17239c20e25881b4cc862e452eb494",
    "direct_mae": "3a1f3835df417403ded587aa64a036edad50dfb244969c99ed45e70e58322dd5",
    "direct_hellinger": "7189523f2c5f5517c79f9b071f164bd1a480082a8cf3a0317940bcc8c9b1cf9f",
}
PRODUCER_SHA = "dba9fac988376d95da7b6aa802674828d410d2e70d0fcb839362084dc5d969e8"
OLD_EXPECTED = {
    **EXPECTED,
    "radius_report": "d2c10a128acb00425c5c785ce195ad245bcf1b428f0f4a4d75d0f7aa95f11129",
    "direct_mae": "623b0eb20e46e86fccbd48e840fa20e1882b89bf17ef3ef81c89e63c3a2c6f50",
    "direct_hellinger": "91255eda5f958f7072ea489dfc36201360b7aaa5f019e5f0c91f3e2a59830950",
}


def typed_equal(left: object, right: object) -> bool:
    """Preserve scalar types, ordered arrays and exact scientific numbers."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        assert isinstance(right, dict)
        return left.keys() == right.keys() and all(
            typed_equal(left[k], right[k]) for k in left
        )
    if isinstance(left, list):
        assert isinstance(right, list)
        return len(left) == len(right) and all(
            typed_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right)


def source_identity_only(original: bytes, proposed: bytes) -> None:
    """Permit the three reviewed hashes, with every other executable AST exact."""
    old, new = ast.parse(original), ast.parse(proposed)
    for tree, expected in [(old, OLD_EXPECTED), (new, EXPECTED)]:
        declarations = [
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "EXPECTED"
        ]
        assert len(declarations) == 1
        assert ast.literal_eval(declarations[0].value) == expected
        declarations[0].value = ast.Constant(None)
    assert ast.dump(old, include_attributes=False) == ast.dump(
        new, include_attributes=False
    )


def qualify_pairs(
    actual: JsonObject,
    historical: JsonObject,
    scores: bytes,
    original_scores: bytes,
    radius_rows: bytes,
    direct_rows: bytes,
    hellinger: JsonObject,
) -> JsonObject:
    """Compare every output value and independently join all three source factors."""
    expected = deepcopy(historical)
    assert expected["source_sha256"] == OLD_EXPECTED
    expected["source_sha256"] = EXPECTED
    expected["producer_sha256"] = PRODUCER_SHA
    assert typed_equal(actual, expected), "Paired science/type/order differs"
    assert scores == original_scores, "Paired CSV bytes differ"
    assert type(actual["matched_sites"]) is int and actual["matched_sites"] == 14
    assert type(actual["paired_rows"]) is int and actual["paired_rows"] == 126
    paired = list(csv.DictReader(io.StringIO(scores.decode())))
    radius = list(csv.DictReader(io.StringIO(radius_rows.decode())))
    direct = list(csv.DictReader(io.StringIO(direct_rows.decode())))
    hrows = hellinger["site_method_rows"]
    assert len(paired) == len(radius) == 126 and len(direct) == len(hrows) == 42
    maize = {(r["target_record_id"], r["method"]): r for r in direct}
    hindex = {(r["target_record_id"], r["method"]): r for r in hrows}
    assert len(maize) == len(hindex) == 42 and maize.keys() == hindex.keys()
    seen = set()
    for row, source in zip(paired, radius, strict=True):
        key = row["record_id"], row["method"]
        factor = float(row["radius_factor"])
        token = (*key, factor)
        assert token not in seen and factor in (0.8, 1.0, 1.2)
        seen.add(token)
        assert row["record_id"] != "author:BECKHAM"
        assert key == (source["record_id"], source["method"])
        assert factor == float(source["radius_factor"])
        d, h = maize[key], hindex[key]
        assert (
            row["observation_sha256"]
            == source["observation_sha256"]
            == d["target_raw_sha256"]
            == h["target_raw_sha256"]
        )
        assert int(source["observed_count"]) == h["observed_total_count"]
        assert d["lra_prediction_identity"] == h["lra_prediction_identity"]
        direct_mae, lra_mae = (
            float(d["direct_pollen_mae_fraction"]),
            float(source["mae_fraction"]),
        )
        direct_h, lra_h = (
            float(h["direct_pollen_hellinger"]),
            float(source["hellinger_distance"]),
        )
        assert float(row["direct_mae_fraction"]) == direct_mae
        assert float(row["lra_mae_fraction"]) == lra_mae
        assert float(row["direct_minus_lra_mae_fraction"]) == direct_mae - lra_mae
        assert float(row["direct_hellinger_distance"]) == direct_h
        assert float(row["lra_hellinger_distance"]) == lra_h
        assert float(row["direct_minus_lra_hellinger_distance"]) == direct_h - lra_h
    assert seen == {(*key, factor) for key in maize for factor in (0.8, 1.0, 1.2)}
    assert len({r["record_id"] for r in paired}) == 14
    return {
        "all_paired_scientific_values_types_orders_exact": True,
        "paired_CSV_byte_exact": True,
        "all_126_raw_observation_prediction_and_arithmetic_joins_exact": True,
        "paired_sites": 14,
        "paired_rows": 126,
        "radius_factors": [0.8, 1.0, 1.2],
        "excluded_site": "author:BECKHAM",
        "new_fit_forward_R_or_optimizer_executed": False,
        "scientific_or_official_release_acceptance": False,
        "scope": "Prior-exposed English fixed-vegetation radius comparison. Different direct/LRA training information remains explicit; no physical-radius, Nordic, vegetation-accuracy, ecological or source-rights claim.",
    }
