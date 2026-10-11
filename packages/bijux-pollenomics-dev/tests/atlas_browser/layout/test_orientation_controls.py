"""Orientation must not cover visible control labels or their hit targets."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

import pytest

from bijux_pollenomics_dev.ci import atlas_browser


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("separate", True),
        ("descendant-hit", True),
        ("edge-touch", True),
        ("visual-overlap-pointer-through", False),
        ("fractional-overlap", False),
        ("center-obscured", False),
        ("edge-obscured", False),
        ("missing-north", False),
        ("hidden-north", False),
        ("offscreen-north", False),
        ("missing-panel-control", False),
        ("hidden-panel-control", False),
        ("wrong-north-label", False),
        ("offscreen-control", False),
    ],
)
def test_dom_orientation_contract_distinguishes_labels_from_pointer_targets(
    scenario: str, expected: bool
) -> None:
    source = Path(atlas_browser.__file__).with_name("probe.mjs").read_text()
    match = re.search(
        r"function northOrientationFacts\(\).*?\n}\n\nfunction northOrientationPasses\(facts\).*?\n}",
        source,
        re.DOTALL,
    )
    assert match is not None
    script = (
        match.group(0)
        + "\nconst scenario = "
        + json.dumps(scenario)
        + ";\n"
        + r"""
const rect=(left,top,width,height)=>({left,top,right:left+width,bottom:top+height,width,height});
const node=(id,bounds)=>({id, bounds, disabled:false, style:{display:'block',visibility:'visible',opacity:'1'},
  getBoundingClientRect(){return this.bounds},
  getAttribute(name){return name==='role'?'img':name==='aria-label'?this.label??'North is up':null},
  contains(hit){return hit?.parent===this},
});
const controls=[node('fit-active',rect(450,20,80,34)),node('search-toggle',rect(540,20,64,34)),node('panel-toggle',rect(614,20,120,34))];
let north=node('north-orientation',rect(750,16,54,44));
globalThis.innerWidth=900;globalThis.innerHeight=1000;
if(scenario==='edge-touch')north.bounds=rect(734,16,54,44);
if(scenario==='visual-overlap-pointer-through')north.bounds=rect(690,16,54,44);
if(scenario==='fractional-overlap')north.bounds=rect(733.999,16,54,44);
if(scenario==='missing-north')north=null;
if(scenario==='hidden-north')north.style.display='none';
if(scenario==='offscreen-north')north.bounds=rect(880,16,54,44);
if(scenario==='missing-panel-control')controls.pop();
if(scenario==='hidden-panel-control')controls[2].style.visibility='hidden';
if(scenario==='wrong-north-label')north.label='Unknown orientation';
if(scenario==='offscreen-control')controls[2].bounds=rect(-1,20,120,34);
globalThis.getComputedStyle=(element)=>element.style;
globalThis.document={
  getElementById(){return north},querySelectorAll(){return controls},
  elementFromPoint(x,y){
    if(scenario==='center-obscured'&&x===674&&y===37)return {};
    if(scenario==='edge-obscured'&&x===618&&y===37)return {};
    const found=controls.find(c=>x>=c.bounds.left&&x<=c.bounds.right&&y>=c.bounds.top&&y<=c.bounds.bottom);
    return scenario==='descendant-hit'?{parent:found}:found??{};
  },
};
const facts=northOrientationFacts();
process.stdout.write(JSON.stringify({passed:northOrientationPasses(facts),facts}));
"""
    )
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    facts = json.loads(result.stdout)
    assert facts["passed"] is expected
    if scenario == "visual-overlap-pointer-through":
        panel = next(
            row for row in facts["facts"]["controls"] if row["id"] == "panel-toggle"
        )
        assert panel["hit_points_uncovered"] is True
        assert panel["overlaps_north"] is True


def test_responsive_layouts_require_the_observed_orientation_geometry() -> None:
    source = Path(atlas_browser.__file__).with_name("probe.mjs").read_text()
    assert "const northOrientation = (${northOrientationFacts.toString()})();" in source
    assert "north_orientation: northOrientation," in source
    assert source.count("&& northOrientationPasses(layout.north_orientation)") == 2
