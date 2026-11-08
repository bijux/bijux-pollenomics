"""Bind current compiled decks without reviving historical source inventories."""
from pathlib import Path
import json
import re

HELPER = 'configs/docs/publication/deck_build.py'
HELPER_SHA256 = '06872a6ac4a9fe1d716dcf53c09a4516a4ff4d382537b8f53d10e391138675c4'
DECKS = ('big-picture', 'developer', 'scientific-evidence')
INPUTS = tuple(f'presentation/{name}.tex' for name in DECKS) + (
    'presentation/shared.tex', 'presentation/build.py',
)
FLAGS = ('-pdf', '-g', '-recorder', '-interaction=nonstopmode',
         '-halt-on-error', '-file-line-error')


def capture(hook, root, regular, require, digest, _blobs, _git):
    """Independently verify Git inputs before the reviewed hook executes its helper."""
    root = Path(root)
    helper = regular(root, root / HELPER)
    require(digest(helper) == HELPER_SHA256,
            'Compiled decks: source helper differs from reviewed recipe')
    head = _git(root, 'rev-parse', '--verify', 'HEAD').decode().strip()
    values, modes = _blobs(root, head, [HELPER], require)
    mode = b'100755' if (root / HELPER).stat().st_mode & 0o100 else b'100644'
    require(values[HELPER] == helper and modes[HELPER] == mode,
            'Compiled decks: helper differs from committed source')
    raw = regular(root, root / hook.MANIFEST)
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Compiled decks: duplicate manifest key')
            result[key] = value
        return result
    manifest = json.loads(raw, object_pairs_hook=pairs)
    build = manifest.get('deck_build')
    require(isinstance(build, dict)
            and set(build) == {'schema_version', 'source_revision', 'source_date_epoch', 'inputs', 'compilers'}
            and build['schema_version'] == 'git-compiled-deck-inputs.v1'
            and isinstance(build['source_revision'], str)
            and re.fullmatch('[0-9a-f]{40}', build['source_revision']) is not None
            and type(build['source_date_epoch']) is int and build['source_date_epoch'] >= 0
            and build['inputs'] == list(INPUTS)
            and isinstance(build['compilers'], list) and len(build['compilers']) == 3,
            'Compiled decks: exact current build identity required')
    for name, row in zip(DECKS, build['compilers']):
        require(isinstance(row, dict) and set(row) == {'deck', 'argv', 'actual_exit'}
                and row['deck'] == name and type(row['actual_exit']) is int and row['actual_exit'] == 0
                and row['argv'] == ['latexmk', *FLAGS, f'-outdir=artifacts/jobs/presentation/{name}', f'presentation/{name}.tex'],
                'Compiled decks: compiler completion or command differs')
    stale = {'presentation/source-lock.json', 'presentation/retained-source-context.json',
             'presentation/retained-build-source-context.json', 'presentation/current-build-export-context.json',
             'configs/docs/publication/deck_exports.py'}
    require(isinstance(manifest.get('inputs'), dict) and not stale.intersection(manifest['inputs']),
            'Compiled decks: historical inventory cannot identify current compilation')
    require(isinstance(manifest.get('files'), list), 'Compiled decks: export rows required')
    rows = [row for row in manifest['files'] if isinstance(row, dict)
            and isinstance(row.get('path'), str) and row['path'].startswith('presentation/')]
    require(len(rows) == 3 and {row['path'] for row in rows} == {f'presentation/{name}.pdf' for name in DECKS}
            and all('source_sha256' not in row for row in rows),
            'Compiled decks: current exports cannot claim historical source hashes')
    revision = build['source_revision']
    _git(root, 'merge-base', '--is-ancestor', revision, 'HEAD')
    require(int(_git(root, 'show', '-s', '--format=%ct', revision)) == build['source_date_epoch'],
            'Compiled decks: source date epoch differs')
    original, _ = _blobs(root, revision, list(INPUTS), require)
    current, modes = _blobs(root, head, list(INPUTS), require)
    for name in INPUTS:
        mode = b'100755' if (root / name).stat().st_mode & 0o100 else b'100644'
        require(original[name] == current[name] == regular(root, root / name) and mode == modes[name],
                'Compiled decks: compiled input bytes or mode changed')
    expected = {'context': build, 'current_inputs': [{'path': name, 'source_revision': revision} for name in INPUTS]}
    require(hook.retained_deck_sources(root) == expected,
            'Compiled decks: callback differs from independent Git capture')
    require(_git(root, 'rev-parse', '--verify', 'HEAD').decode().strip() == head
            and regular(root, root / hook.MANIFEST) == raw and regular(root, root / HELPER) == helper
            and all(regular(root, root / name) == original[name] for name in INPUTS),
            'Compiled decks: consumed sources changed during capture')
    return expected
