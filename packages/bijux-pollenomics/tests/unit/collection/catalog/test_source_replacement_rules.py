"""Replacement metadata conserves historical rules and names runtime-owned candidates."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
import unittest

import pytest

from bijux_pollenomics.collection.catalog.replacement import (
    build_source_replacement_rules,
)


class SourceReplacementRulesUnitTests(unittest.TestCase):
    def test_build_source_replacement_rules_marks_destructive_refresh(self) -> None:
        rules = build_source_replacement_rules(
            selected_sources=("neotoma",),
            source_output_roots={"neotoma": "/tmp/data/neotoma"},
        )

        self.assertIn("neotoma", rules)
        self.assertTrue(rules["neotoma"].destructive_refresh)
        self.assertTrue(rules["neotoma"].preserves_previous_on_failure)
        self.assertEqual(rules["neotoma"].refresh_mode, "staging_swap")
        self.assertEqual(rules["neotoma"].final_output_root, "/tmp/data/neotoma")
        self.assertEqual(
            rules["neotoma"].staging_output_root,
            "/tmp/data/.neotoma.staging",
        )


if __name__ == "__main__":
    unittest.main()


@pytest.mark.parametrize(
    "source", ["aadr", "boundaries", "landclim", "raa", "sead", "svar"]
)
def test_callback_owned_catalog_has_no_fictional_fixed_candidate(source: str) -> None:
    rule = build_source_replacement_rules(
        selected_sources=(source,), source_output_roots={source: "generated/" + source}
    )[source]
    assert rule.refresh_mode == "owned_callback_replacement"
    assert rule.staging_output_root is None
    assert rule.preserves_previous_on_failure and rule.destructive_refresh


def test_catalog_follows_the_same_context_publication_routing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.workflow.planning.source_registry import (
        CONTEXT_SOURCE_SPECS,
    )

    monkeypatch.setitem(
        CONTEXT_SOURCE_SPECS,
        "neotoma",
        replace(CONTEXT_SOURCE_SPECS["neotoma"], owns_output_publication=False),
    )
    rule = build_source_replacement_rules(
        selected_sources=("neotoma",),
        source_output_roots={"neotoma": "generated/neotoma"},
    )["neotoma"]
    assert (
        rule.refresh_mode == "owned_callback_replacement"
        and rule.staging_output_root is None
    )


def test_historical_string_and_current_null_rules_roundtrip_without_reinterpretation() -> (
    None
):
    from bijux_pollenomics.collection import SourceReplacementRule

    for mode, path in (
        ("staging_swap", "generated/.source.staging"),
        ("owned_callback_replacement", None),
    ):
        values = {
            "source": "source",
            "refresh_mode": mode,
            "final_output_root": "generated/source",
            "staging_output_root": path,
            "destructive_refresh": True,
            "preserves_previous_on_failure": True,
        }
        rule = SourceReplacementRule(
            source="source",
            refresh_mode=mode,
            final_output_root="generated/source",
            staging_output_root=path,
            destructive_refresh=True,
            preserves_previous_on_failure=True,
        )
        assert asdict(rule) == values
        assert (
            asdict(SourceReplacementRule(**json.loads(json.dumps(asdict(rule)))))
            == values
        )
