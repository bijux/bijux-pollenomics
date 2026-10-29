"""Historical display implementations remain witnesses to their own browser epoch.

Current rendering is checked as maintained software. These paths do not confer
fresh browser observations, current-source reproduction or scientific admission.
"""

from __future__ import annotations

import ast
import copy

HISTORICAL_RENDERING_SOURCES = frozenset(
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/" + name
    for name in (
        "assets/document.html",
        "template.py",
        "static_assets/index_bundles.py",
        "static_assets/indexes.py",
        "static_assets/validation.py",
        "static_assets/writer.py",
    )
)


WORKFLOW = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/lra_products/workflow.py"
PAYLOAD = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/payload.py"
)
VERDICT = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/verdict.py"
ASSET_IMPORT = "from importlib.resources import files\n"
ASSET_WRITE = """    asset_directory = copy_map_assets(stage)
    (asset_directory / "native-lra.js").write_bytes(
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/native-lra.js")
        .read_bytes()
    )
"""
SCRIPT_BINDING = """        "__NATIVE_LRA_SCRIPT_TAG__": (
            f'<script src="{escape_html_fn(asset_base_path)}/native-lra.js"></script>'
            if native_lra is not None and static_assets is not None
            else ""
        ),
"""
PAYLOAD_DOC = '"""Prepare map document bindings and the declared native-controller asset route."""\n\n'
MODE_GUARD = """    if document.get("verification_mode", "complete-profile") != "complete-profile":
        raise AtlasBrowserContractError(
            "scoped provider matrix is not a complete browser profile"
        )
"""


def _replace_once(body: str, old: str, new: str) -> str | None:
    if body.count(old) != 1:
        return None
    return body.replace(old, new, 1)


def _signature(node: ast.FunctionDef) -> str:
    skeleton = copy.deepcopy(node)
    skeleton.body = [ast.Pass()]
    return ast.dump(skeleton, include_attributes=False)


def _dump(node: ast.AST) -> str:
    return ast.dump(node, include_attributes=False)


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    selected = [
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name
    ]
    return selected[0] if len(selected) == 1 else None


def _workflow_nodes(tree: ast.Module) -> bool:
    target = _function(tree, "_map")
    if target is None:
        return False
    expected = ast.parse("def owned():\n" + ASSET_WRITE).body[0]
    assert isinstance(expected, ast.FunctionDef)
    sequences = sum(
        [_dump(n) for n in target.body[i : i + 2]] == [_dump(n) for n in expected.body]
        for i in range(len(target.body) - 1)
    )
    imported = ast.parse(ASSET_IMPORT).body[0]
    return sequences == 1 and sum(_dump(n) == _dump(imported) for n in tree.body) == 1


def _payload_nodes(tree: ast.Module) -> bool:
    target = _function(tree, "build_map_document_payload")
    if target is None:
        return False
    matches = [
        n
        for n in ast.walk(target)
        if isinstance(n, ast.Dict)
        and any(
            isinstance(k, ast.Constant) and k.value == "__NATIVE_LRA_CONTROLLER__"
            for k in n.keys
        )
    ]
    if len(matches) != 1:
        return False
    bindings = matches[0]
    keys = [k.value if isinstance(k, ast.Constant) else None for k in bindings.keys]
    if keys.count("__NATIVE_LRA_SCRIPT_TAG__") != 1:
        return False
    script = keys.index("__NATIVE_LRA_SCRIPT_TAG__")
    controller = keys.index("__NATIVE_LRA_CONTROLLER__")
    expected_dict = ast.parse("{\n" + SCRIPT_BINDING + "}", mode="eval").body
    assert isinstance(expected_dict, ast.Dict)
    expected_controller = ast.parse(
        "NATIVE_LRA_CONTROLLER if native_lra is not None and static_assets is None else ''",
        mode="eval",
    ).body
    return (
        script + 1 == controller
        and _dump(bindings.values[script]) == _dump(expected_dict.values[0])
        and _dump(bindings.values[controller]) == _dump(expected_controller)
    )


def _verdict_guard(tree: ast.Module) -> bool:
    target = _function(tree, "evaluate_browser_report")
    if target is None or len(target.body) < 3:
        return False
    expected = ast.parse(
        "def owned():\n    document = _mapping(report, label='browser report')\n"
        + MODE_GUARD
    ).body[0]
    assert isinstance(expected, ast.FunctionDef)
    return [_dump(n) for n in target.body[1:3]] == [_dump(n) for n in expected.body]


def atlas_extension_matches(name: str, captured: bytes, current: bytes) -> bool:
    """Preserve all old bytes except the exact named addition or isolated new entrypoint.

    The caller authenticates captured member identity, path, detached custody and
    current regular/single-link ownership. This predicate grants no current
    renderer, browser, native-model or provider-matrix qualification.
    """
    try:
        old = captured.decode("utf-8")
        body: str | None = current.decode("utf-8")
        ast.parse(old)
        tree = ast.parse(body)
        if name == WORKFLOW:
            if not _workflow_nodes(tree):
                return False
            body = _replace_once(body, ASSET_IMPORT, "")
            if body is None:
                return False
            body = _replace_once(body, ASSET_WRITE, "    copy_map_assets(stage)\n")
        elif name == PAYLOAD:
            if not _payload_nodes(tree):
                return False
            if body.startswith(PAYLOAD_DOC):
                body = body[len(PAYLOAD_DOC) :]
            body = _replace_once(body, SCRIPT_BINDING, "")
            if body is None:
                return False
            body = _replace_once(
                body,
                "        if native_lra is not None and static_assets is None\n",
                "        if native_lra is not None\n",
            )
        elif name == VERDICT:
            if not _verdict_guard(tree):
                return False
            functions = [
                n
                for n in tree.body
                if isinstance(n, ast.FunctionDef)
                and n.name == "evaluate_provider_failure_matrix"
            ]
            if len(functions) != 1:
                return False
            function = functions[0]
            expected = ast.parse(
                "def evaluate_provider_failure_matrix(report: object, *, "
                "candidate: BrowserCandidate, scopes: frozenset[str]) -> JsonObject:\n"
                "    pass\n"
            ).body[0]
            if not isinstance(expected, ast.FunctionDef) or _signature(
                function
            ) != _signature(expected):
                return False
            # Only one new deferred, undecorated entrypoint may be absent from
            # the historical module. Its body is outside this historical claim.
            # Current provider assertions require separate ordinary unit tests.
            if function is not tree.body[-1]:
                return False
            prior = ast.parse(old)
            if any(
                isinstance(n, ast.Name)
                and n.id
                in {
                    "evaluate_provider_failure_matrix",
                    "eval",
                    "exec",
                    "globals",
                    "locals",
                    "vars",
                    "dir",
                }
                for n in ast.walk(prior)
            ):
                return False
            futures = [
                n
                for n in prior.body
                if isinstance(n, ast.ImportFrom) and n.module == "__future__"
            ]
            if not any(any(a.name == "annotations" for a in n.names) for n in futures):
                return False
            marker = "\n\n\ndef evaluate_provider_failure_matrix("
            if body.count(marker) != 1:
                return False
            start = body.index(marker)
            # No expressions after the new definition or altered old source
            # whitespace are hidden by removing it.
            lines = body.splitlines(keepends=True)
            if "".join(lines[function.end_lineno :]):
                return False
            body = body[:start] + "\n"
            body = _replace_once(body, MODE_GUARD, "")
        else:
            return False
        return body is not None and body.encode("utf-8") == captured
    except (SyntaxError, UnicodeDecodeError, ValueError, TypeError):
        return False
