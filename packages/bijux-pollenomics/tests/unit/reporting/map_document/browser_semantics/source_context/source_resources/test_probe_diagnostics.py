"""Native source probe refusals retain the JavaScript error that caused them."""

from __future__ import annotations

from collections.abc import Callable
import subprocess
from typing import Any

import pytest


def test_native_probe_reports_javascript_stderr_with_original_cause(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    marker = "bijux-native-source-probe-diagnostic"
    with pytest.raises(AssertionError, match=marker) as reported:
        browser_probe("", driver=f"throw new Error('{marker}');")
    cause = reported.value.__cause__
    assert isinstance(cause, subprocess.CalledProcessError)
    assert cause.returncode != 0
    assert marker in cause.stderr


def test_native_probe_retains_successful_json_result(
    browser_probe: Callable[..., dict[str, Any]],
) -> None:
    observed = browser_probe("({diagnostic:'native-probe-ok',values:[1,null,false]})")
    assert observed["result"] == {
        "diagnostic": "native-probe-ok",
        "values": [1, None, False],
    }
    assert observed["failures"] == []
    assert not any(path.endswith(".body") for path in observed["calls"])
