from __future__ import annotations

from ..support import run_node_json, template_block


def test_diameter_hash_value_is_finite_bounded_and_step_normalized() -> None:
    helper = template_block(
        "function finiteControlNumber", "function clampTimeInterval"
    )
    helper = helper.replace("__INITIAL_DIAMETER__", "40")
    observed = run_node_json(
        helper
        + """
console.log(JSON.stringify({
  invalid:clampDiameter('abc'),
  blank:clampDiameter(''),
  low:clampDiameter(-20),
  high:clampDiameter(140),
  stepped:clampDiameter(42),
  zero:clampDiameter(0),
  array:clampDiameter([]),
  singletonArray:clampDiameter([0]),
  object:clampDiameter({}),
}));
"""
    )

    assert observed == {
        "invalid": 40,
        "blank": 40,
        "low": 0,
        "high": 100,
        "stepped": 40,
        "zero": 0,
        "array": 40,
        "singletonArray": 40,
        "object": 40,
    }
