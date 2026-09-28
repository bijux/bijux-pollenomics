from __future__ import annotations

from .support import run_node_json, template_block


def test_manual_bp_step_preserves_keyboard_focus_at_each_boundary() -> None:
    handlers = template_block(
        "timeStepOlder.addEventListener('click',",
        "modeledContextFamily.addEventListener('change',",
    )
    result = run_node_json(
        """
const listeners = {};
const document = { body: {}, activeElement: null };
const button = name => ({
  disabled: false,
  addEventListener(type, handler) { listeners[name] = handler; },
  focus() { document.activeElement = this; },
});
const timeStepOlder = button('older'), timeStepNewer = button('newer');
let timeStartBp = 100, timeIntervalYears = 100;
const stopTimePlayback = () => {};
const deactivateModeledContext = () => {};
const previousPlaybackTimeStart = () => 200;
const nextPlaybackTimeStart = () => 0;
const renderMapState = async () => {
  timeStepOlder.disabled = timeStartBp >= 200;
  timeStepNewer.disabled = timeStartBp <= 0;
  if (document.activeElement.disabled) document.activeElement = document.body;
};
"""
        + handlers
        + """
(async () => {
  document.activeElement = timeStepOlder;
  await listeners.older();
  const olderBoundary = {start: timeStartBp, focus: document.activeElement === timeStepNewer};
  document.activeElement = timeStepNewer;
  timeStartBp = 100;
  await listeners.newer();
  const newerBoundary = {start: timeStartBp, focus: document.activeElement === timeStepOlder};
  console.log(JSON.stringify({olderBoundary, newerBoundary}));
})();
"""
    )
    assert result == {
        "olderBoundary": {"start": 200, "focus": True},
        "newerBoundary": {"start": 0, "focus": True},
    }
