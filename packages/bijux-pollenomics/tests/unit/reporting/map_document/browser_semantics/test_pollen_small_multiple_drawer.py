"""Compatible taxon panels mount in the actual drawer with a local selected anchor."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from .chronology import test_age_depth_diagram as age
from .chronology.test_pollen_age_drawer import mounted_choices
from .test_pollen_diagram import decoded
from .test_pollen_small_multiples import add_variable


def test_actual_drawer_compares_taxa_and_highlights_the_explicit_anchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(
        cast(dict[str, Any], age.decoded(age.projected_tabs(tmp_path, monkeypatch)))
    )
    add_variable(tabs)
    output = mounted_choices(tabs)
    captured = output["captured"]
    for name in ("initial", "chosen", "returned", "nativeChanged", "newRecord"):
        html = captured[name]
        assert html.count('data-native-panel="') == 2
        prefix = (
            "native-value-source-age"
            if name in ("chosen", "returned")
            else "native-value-depth"
        )
        assert html.count(f'id="{prefix}-title-0"') == 1
        assert f'id="{prefix}-title-1"' in html
        assert 'id="native-value-depth-title"' not in html
        assert "Showing 1–2 of 2" in html
    assert "Selected anchor: Triticum" in captured["initial"]
    assert "Selected anchor: Native taxon 51" in captured["nativeChanged"]
    assert "Selected anchor: Triticum" in captured["newRecord"]
    assert captured["chosen"].count(">Source age (year)</text>") == 2
    assert (
        captured["nativeChanged"].count(">Source depth (unit not supplied)</text>") == 2
    )
    for option in output["options"]:
        html = captured[option["key"]]
        assert html.count('data-native-panel="') == 2
        assert "2 of 2 aligned observations drawn" in html
        assert "neotoma:observation:40:50:1" in html and "observation-51" in html
    assert "compatible native variable panels" not in captured["overview"].lower()
    assert output["unchanged"] is True
