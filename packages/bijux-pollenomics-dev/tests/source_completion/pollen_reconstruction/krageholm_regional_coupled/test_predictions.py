"""Closed-product controls for all method dispositions and quantitative lineage."""

from copy import deepcopy
from pathlib import Path

import pytest

from . import predictions as observer
from .fixtures import prediction_fixture, write_product
from .lineage import digest
from .predictions import check_prediction
from .reading import decode
from .test_native_fits import TOLERANCE


@pytest.mark.parametrize("refused", [False, True])
def test_closed_prediction_products_keep_all_successes_and_signed_refusals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, refused: bool
) -> None:
    pin, context, native, _ = prediction_fixture(tmp_path, refused=refused)
    monkeypatch.setattr(observer, "check_batches", lambda *args: native)
    result = check_prediction(tmp_path, pin, context, TOLERANCE)
    assert len(result["dispositions"]) == 9
    assert len(result["predictions"]) == (6 if refused else 9)
    assert result["native_negative_final_covers"] == int(refused)
    for available in result["predictions"].values():
        assert tuple(map(float, available["pollen"])) == (0.625, 0.375)


def test_host_canonical_aliases_preserve_source_declaration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pin, context, native, _ = prediction_fixture(tmp_path)
    before = deepcopy(context["experiment"]["sites"])
    saved = decode((Path(pin["directory"]) / "experiment.json").read_bytes())
    assert before[0]["identity_keys"] == ["site:BOKE", "collection:BOKE"]
    assert saved["source_catalogue"][0]["identity_keys"] == [
        "collection:BOKE",
        "site:BOKE",
    ]
    assert type(context["experiment"]["local_support_radius_m"]) is int
    assert type(saved["local_support_radius_m"]) is float
    monkeypatch.setattr(observer, "check_batches", lambda *args: native)
    assert len(check_prediction(tmp_path, pin, context, TOLERANCE)["predictions"]) == 9
    assert context["experiment"]["sites"] == before


@pytest.mark.parametrize(
    "corruption",
    ["source_duplicate", "missing", "foreign", "duplicate", "uncanonical_order"],
)
def test_alias_membership_and_canonical_serialization_refuse_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    pin, context, native, science = prediction_fixture(tmp_path)
    monkeypatch.setattr(observer, "check_batches", lambda *args: native)
    members = {
        path.name: decode(path.read_bytes())
        for path in Path(pin["directory"]).glob("*.json")
        if path.name != "manifest.json"
    }
    aliases = members["experiment.json"]["source_catalogue"][0]["identity_keys"]
    if corruption == "source_duplicate":
        context["experiment"]["sites"][0]["identity_keys"].append("site:BOKE")
    elif corruption == "missing":
        aliases.pop()
    elif corruption == "foreign":
        aliases[0] = "collection:foreign"
    elif corruption == "duplicate":
        aliases.append(aliases[0])
    else:
        aliases.reverse()
    replacement = write_product(
        tmp_path / "artifacts/alias-tamper", science, members, phase="predictions"
    )
    replacement["method_dispositions"] = pin["method_dispositions"]
    with pytest.raises(ValueError):
        check_prediction(tmp_path, replacement, context, TOLERANCE)


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_prediction",
        "pollen",
        "training_identity",
        "regional_predictor",
        "heldout_ancestor",
        "missing_ancestor",
        "bad_refusal",
    ],
)
def test_closed_product_missing_identity_role_lineage_or_numerical_tamper_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    pin, context, native, science = prediction_fixture(
        tmp_path, refused=corruption == "bad_refusal"
    )
    monkeypatch.setattr(observer, "check_batches", lambda *args: native)
    if corruption == "missing_prediction":
        science["predictions"].pop()
    elif corruption == "pollen":
        science["predictions"][0]["pollen_fraction"]["Betula"] = 0.5
    elif corruption == "training_identity":
        science["training"][0]["training_products"][0]["request_sha256"] = "0" * 64
    elif corruption == "regional_predictor":
        science["training"][0]["predictor_group_ids"].append(
            "site-group:" + digest(["KRAGMJNY"])
        )
    elif corruption in {"heldout_ancestor", "missing_ancestor"}:
        row = science["predictions"][0]
        published = row["prediction_manifest"]
        graph = published["input_lineage"]
        if corruption == "heldout_ancestor":
            node = published["forward_inputs"]["parameter_input_ids"][0]
            graph[node] = published["fold"]["test_record_ids"]
        else:
            del graph[published["fold"]["train_record_ids"][0]]
        row["prediction_manifest_sha256"] = digest(published)
    else:
        for values in native.values():
            for item in values.values():
                item["cover"] = (0.75, 0.25)
    old_members = {
        path.name: decode(path.read_bytes())
        for path in Path(pin["directory"]).glob("*.json")
        if path.name != "manifest.json"
    }
    for key in ("predictions", "training", "preparations", "failures"):
        old_members[key + ".json"] = science[key]
    replacement = write_product(
        tmp_path / "artifacts/changed", science, old_members, phase="predictions"
    )
    replacement["method_dispositions"] = pin["method_dispositions"]
    with pytest.raises(ValueError):
        check_prediction(tmp_path, replacement, context, TOLERANCE)
