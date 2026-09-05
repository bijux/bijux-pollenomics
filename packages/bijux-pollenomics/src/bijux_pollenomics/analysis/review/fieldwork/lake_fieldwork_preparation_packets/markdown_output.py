"""Human-review presentation for lake preparation packets."""

from __future__ import annotations

from typing import Any


def render_markdown(payload: dict[str, Any]) -> str:
    rows = (
        "\n".join(
            (
                f"| {row['fieldwork_rank']} | {row['aggregate_rank']} | {row['lake_label']} | "
                f"[{row['latitude']:.6f}, {row['longitude']:.6f}]({row['google_maps_url']}) | "
                f"{row['lake_registry_id'] or 'not_available'} | "
                f"{row['lake_name_status'] or 'not_available'} | "
                f"{row['fieldwork_shortlist_score']:.4f} | "
                f"{row['preparation_posture']} | {row['identity_posture']} | "
                f"{row['sampling_posture']} | {row['human_context_posture']} | "
                f"{row['sampling_fit']:.4f} | "
                f"{row['sampling_readiness_posture']} | "
                f"{row['scenario_consistency_posture']} | "
                f"{row['sead_context_posture']} | {row['palaeopen_alignment_posture']} | "
                f"{row['evidence_families_20km']} | {row['scenario_top20_presence_count']} | "
                f"{row['scenario_ranks']['20km']} | "
                f"{', '.join(row['required_actions']) or 'none'} |"
            )
            for row in payload["rows"]
        )
        or "| - | - | No reviewed lakes | - | not_available | not_available | - | - | - | - | - | - | - | - | - | - | 0 | 0 | - | none |"
    )
    return f"""# Sweden lake fieldwork preparation

This packet turns the Sweden lake richness ranking into a stricter
fieldwork-preparation screen. It keeps identity ambiguity, archaeology-context
depth, and interoperability fit visible before any stronger sampling language is
used.

## Methodology

- Scope: {payload["methodology"]["scope"]}
- Identity rule: {payload["methodology"]["identity_rule"]}
- Sampling rule: {payload["methodology"]["sampling_rule"]}
- Human context rule: {payload["methodology"]["human_context_rule"]}
- Scenario consistency rule: {payload["methodology"]["scenario_consistency_rule"]}
- Fieldwork ordering rule: {payload["methodology"]["fieldwork_ordering_rule"]}
- SEAD context rule: {payload["methodology"]["sead_context_rule"]}
- PalaeOpen alignment rule: {payload["methodology"]["palaeopen_alignment_rule"]}
- Warning: {payload["methodology"]["warning"]}

## Top Lake Preparation Rows

| Fieldwork rank | Aggregate rank | Lake | Coordinates | Lake registry id | Name status | Fieldwork shortlist score | Preparation posture | Identity posture | Sampling posture | Human context | Sampling fit | Sampling readiness | Scenario consistency | SEAD context | PalaeOpen alignment | Evidence families within 20 km | Top-20 scenario presence | 20 km rank | Required actions |
| ---: | ---: | --- | --- | --- | --- | ---: | --- | --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- |
{rows}
"""


def render_section(*, json_name: str, csv_name: str, markdown_name: str) -> str:
    return f"""

## Lake Fieldwork Preparation

- Sweden lake fieldwork preparation JSON: [`{json_name}`](./{json_name})
- Sweden lake fieldwork preparation CSV: [`{csv_name}`](./{csv_name})
- Sweden lake fieldwork preparation markdown: [`{markdown_name}`](./{markdown_name})
"""
