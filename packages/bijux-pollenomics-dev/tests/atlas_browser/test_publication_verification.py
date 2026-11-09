"""Exercise the wrapper's exact owner invocation with source-free processes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from bijux_pollenomics_dev.ci import atlas_browser

MODULE = Path(atlas_browser.__file__).with_name("wrapper-runtime.mjs")


def _node(program: str) -> dict[str, object]:
    result = subprocess.run(
        [
            "node",
            "--input-type=module",
            "--eval",
            f"import * as wrapper from {json.dumps(MODULE.as_uri())};\n" + program,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    value = json.loads(result.stdout)
    assert isinstance(value, dict)
    return value


def _repository(tmp_path: Path, program: str) -> Path:
    repository = tmp_path / "repository"
    adapter = repository / "configs/docs/publication/admission.py"
    adapter.parent.mkdir(parents=True)
    adapter.write_text(program)
    python = repository / "artifacts/docs/publication/python/bin/python"
    python.parent.mkdir(parents=True)
    python.symlink_to(sys.executable)
    return repository


def _call(repository: Path, options: str = "{}") -> dict[str, object]:
    return _node(f"""
      try {{const done=await wrapper.verifyPublication({json.dumps(str(repository))},{options});
        console.log(JSON.stringify({{...done,stdout:done.stdout.toString(),stderr:done.stderr.toString()}}));}}
      catch(error) {{const done=error.verification;
        console.log(JSON.stringify({{error:String(error),...(done?{{...done,stdout:done.stdout.toString(),stderr:done.stderr.toString()}}:{{}})}}));}}
    """)


def test_verifier_invokes_the_existing_policy_owner_and_production_bounds(
    tmp_path: Path,
) -> None:
    repository = _repository(
        tmp_path,
        "import json,os,sys;print(json.dumps({'argv':sys.argv,'cwd':os.getcwd(),'pythonpath':os.environ.get('PYTHONPATH'),'nousersite':os.environ.get('PYTHONNOUSERSITE')}))\n",
    )
    result = _call(repository)
    assert result["returncode"] == 0 and result["process_group_closed"] is True
    assert result["timeout_seconds"] == 900
    assert result["max_output_bytes"] == 16 * 1024 * 1024
    assert result["command"] == [
        str(repository / "artifacts/docs/publication/python/bin/python"),
        "-B",
        str(repository / "configs/docs/publication/admission.py"),
        "verify",
    ]
    actual = json.loads(str(result["stdout"]))
    assert actual == {
        "argv": [str(repository / "configs/docs/publication/admission.py"), "verify"],
        "cwd": str(repository),
        "pythonpath": os.pathsep.join(
            str(repository / "packages" / name / "src")
            for name in (
                "bijux-pollenomics",
                "bijux-pollenomics-dev",
                "bijux-pollenomics-lra",
                "pollenomics",
            )
        ),
        "nousersite": "1",
    }


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_verifier_refuses_excess_output_without_unbounded_capture(
    tmp_path: Path, stream: str
) -> None:
    repository = _repository(
        tmp_path, f"import sys;sys.{stream}.write('x'*256);sys.{stream}.flush()\n"
    )
    result = _call(repository, "{timeoutMs:1000,maxOutputBytes:32}")
    assert result["reason"] == "output byte limit exceeded"
    assert result["captured_output_bytes"] == 32
    assert (
        len(str(result["stdout"]).encode()) + len(str(result["stderr"]).encode()) == 32
    )
    assert result["process_group_closed"] is True


def test_verifier_preserves_policy_refusal_and_spawn_failure(tmp_path: Path) -> None:
    repository = _repository(
        tmp_path,
        "import sys;print('effective policy refused',file=sys.stderr);sys.exit(2)\n",
    )
    result = _call(repository, "{timeoutMs:1000}")
    assert result["returncode"] == 2 and "effective policy refused" in str(
        result["stderr"]
    )
    assert "refused" in str(result["error"]) and result["process_group_closed"] is True
    (repository / "artifacts/docs/publication/python/bin/python").unlink()
    missing = _call(repository, "{timeoutMs:1000}")
    assert "ENOENT" in str(missing["error"]) and missing["process_group_closed"] is True


def test_verifier_escalates_a_term_resistant_parent(tmp_path: Path) -> None:
    repository = _repository(
        tmp_path,
        "import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)\n",
    )
    result = _call(repository, "{timeoutMs:500}")
    assert result["reason"] == "deadline exceeded"
    assert result["signal"] == "SIGKILL" and result["process_group_closed"] is True
    assert float(str(result["duration_seconds"])) < 3


@pytest.mark.parametrize("cancel", [False, True])
def test_deadline_and_cancellation_reap_the_verifier_descendant(
    tmp_path: Path, cancel: bool
) -> None:
    repository = _repository(
        tmp_path,
        """import signal,subprocess,sys,time
from pathlib import Path
child=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(30)'])
Path('descendant.pid').write_text(str(child.pid))
def finish(*args):
    child.wait(timeout=2)
    raise SystemExit(0)
signal.signal(signal.SIGTERM,finish)
time.sleep(30)
""",
    )
    if cancel:
        result = _node(f"""
          const controller=new AbortController();
          const pending=wrapper.verifyPublication({json.dumps(str(repository))},{{timeoutMs:3000,signal:controller.signal}});
          const {{access}}=await import('node:fs/promises');
          for(let n=0;n<100;n++){{try{{await access({json.dumps(str(repository / "descendant.pid"))});break;}}catch{{await new Promise(r=>setTimeout(r,10));}}}}
          controller.abort();
          try{{await pending;console.log(JSON.stringify({{accepted:true}}));}}
          catch(error){{console.log(JSON.stringify({{...error.verification,error:String(error)}}));}}
        """)
    else:
        result = _call(repository, "{timeoutMs:500}")
    assert result["reason"] == ("cancelled" if cancel else "deadline exceeded")
    assert result["process_group_closed"] is True
    pid = int((repository / "descendant.pid").read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


@pytest.mark.parametrize(
    "options",
    [
        "{timeoutMs:0}",
        "{timeoutMs:900001}",
        "{maxOutputBytes:0}",
        "{maxOutputBytes:16777217}",
    ],
)
def test_verifier_does_not_expand_its_production_bounds(
    tmp_path: Path, options: str
) -> None:
    repository = _repository(
        tmp_path, "from pathlib import Path;Path('executed').touch()\n"
    )
    assert "bounds are invalid" in str(_call(repository, options)["error"])
    assert not (repository / "executed").exists()


@pytest.mark.parametrize(
    "options,reason",
    [
        ("{signal:{}}", "cancellation signal is invalid"),
        ("{signal:AbortSignal.abort()}", "cancelled before launch"),
    ],
)
def test_invalid_or_preaborted_cancellation_never_launches_a_verifier(
    tmp_path: Path,
    options: str,
    reason: str,
) -> None:
    repository = _repository(
        tmp_path, "from pathlib import Path;Path('executed').touch()\n"
    )
    assert reason in str(_call(repository, options)["error"])
    assert not (repository / "executed").exists()


def test_wrapper_stops_before_browser_after_owning_verifier_refusal(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path, "import sys;sys.exit(2)\n")
    (repository / "configs/docs/publication/downloads.json").write_text("{}\n")
    module = repository / "packages/atlas_browser/wrapper-runtime.mjs"
    module.parent.mkdir(parents=True)
    for name in (
        "wrapper-runtime.mjs",
        "browser-transport.mjs",
        "provider-failures.mjs",
    ):
        shutil.copyfile(MODULE.with_name(name), module.with_name(name))
    browser = repository / "browser"
    browser.write_text("#!/bin/sh\ntouch browser-started\n")
    browser.chmod(0o755)
    for args in [
        ["init", "--quiet"],
        ["add", "configs", "packages", "browser"],
        [
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "test(ci): own verifier fixture",
        ],
    ]:
        subprocess.run(["git", *args], cwd=repository, check=True, capture_output=True)
    result = _node(f"""
      const actual=await import({json.dumps(module.as_uri())});
      try{{await actual.runWrapper({{repository:{json.dumps(str(repository))},site:{json.dumps(str(repository / "artifacts/docs/site"))},output:{json.dumps(str(repository / "artifacts/probe"))},browserBinary:{json.dumps(str(browser))}}});console.log(JSON.stringify({{accepted:true}}));}}
      catch(error){{console.log(JSON.stringify({{error:String(error)}}));}}
    """)
    assert "owning publication verification refused" in str(result["error"])
    assert not (repository / "browser-started").exists()
    assert (
        json.loads(
            (repository / "artifacts/probe/publication-verification.json").read_text()
        )["returncode"]
        == 2
    )
