"""Bind historical paper epochs to the reviewed source-storage resolver."""
from __future__ import annotations

import functools
import gc
import hashlib
import inspect
import json
from pathlib import Path
import re
import sys
import types

PACKAGE = 'bijux_pollenomics_dev.ci.report_rebuild'
SOURCE_ROOT = 'packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/'
SOURCES = {
    'contracts': ('contracts.py', 'fda58e268123ad12e851f358271217f7c7c56ec1eafa3c36505451202e2a5ac6'),
    'retained_source': ('retained_source/__init__.py', '10d1944cef9893a40f61d5ab611f48fba12c13c14f00ec7b24816121d0fb70a6'),
    'retained_source.index': ('retained_source/index.py', 'cc8af8223df2491554ea2354fdd15444a8b254dbfa7c363fbd91f62d020c1044'),
    'retained_source.objects': ('retained_source/objects.py', '34bd7a90ea41551f3d0330f786cb4d99655f28734d2aa6b7efeabf1479e8647a'),
    'retained_source.descriptor': ('retained_source/descriptor.py', '044cd6e22e7a38f9812a200f246aa91b171fa7317efd8b00fc4467b803beea47'),
}
INDEX = 'configs/ci/source-retention/index.json'
INDEX_BYTES = 9775
INDEX_SHA256 = 'fd031bb89abcdfda0d2a4c1dec1afd6d6fa5c6c3ba42604ddf6a33f750ad71d3'
PAPER_STORAGE = {
    '133447b8ae71754d9799355b9c6af48f2fa74711': '066a02d7b59c75ec28adb7960856c3a047d95a59',
    '7b2008c740c0f66db669d37e6f24ede58ba81817': '7277d6e290701ab282b3a93015257a849789afa9',
    '84a0f2bec7906a247573a2b73c111b752ec17491': 'edae2bd150452af61fcc482d0da4a3578af83e2e',
    'f02670c3e123effe1a277b3de422247e575d0ded': '03b2d7b39100bc34fbab68ae9e722a54e51becb1',
}
FUNCTIONS = {
    'contracts': ('require_string', 'require_relative_path'),
    'retained_source.index': ('_seal', '_index_buffer', 'configured_index', 'source_revision'),
    'retained_source.objects': ('require', 'hexadecimal', 'physical'),
    'retained_source.descriptor': ('object_fields', 'json_object', 'pinned_bytes'),
}


def capture(hook, root, regular, require, digest, _blobs, _git):
    """Authenticate the finite resolver closure before any download callback runs.

    The mappings locate retained source bytes. Original manifest revisions remain
    the execution epochs; reachable storage commits never replace those labels.
    """
    root = Path(root)
    head = _git(root, 'rev-parse', '--verify', 'HEAD').decode().strip()
    paths = [SOURCE_ROOT + name for name, _ in SOURCES.values()] + [INDEX]
    committed, modes = _blobs(root, head, paths, require)
    inputs, modules, bodies = [], {}, {}
    for suffix, (relative, checksum) in SOURCES.items():
        name = SOURCE_ROOT + relative
        path = root / name
        body = regular(root, path)
        mode = b'100755' if path.stat().st_mode & 0o100 else b'100644'
        require(path.stat().st_nlink == 1 and digest(body) == checksum
                and committed[name] == body and modes[name] == mode,
                'Scientific revisions: reviewed committed resolver source required')
        module = sys.modules.get(PACKAGE + '.' + suffix)
        require(isinstance(module, types.ModuleType) and getattr(module, '__file__', None) == str(path),
                'Scientific revisions: resolver module must belong to current owner')
        modules[suffix], bodies[suffix] = module, body
        inputs.append({'path': name, 'sha256': checksum})
    for suffix, names in FUNCTIONS.items():
        module = modules[suffix]
        path = root / (SOURCE_ROOT + SOURCES[suffix][0])
        compiled = compile(bodies[suffix], str(path), 'exec', dont_inherit=True)
        codes = {item.co_name: item for item in compiled.co_consts if isinstance(item, types.CodeType)}
        for name in names:
            actual = getattr(module, name, None)
            if name == '_index_buffer':
                wrapper_type = type(functools.lru_cache(maxsize=8)(lambda: None))
                require(type(actual) is wrapper_type
                        and actual.cache_parameters() == {'maxsize': 8, 'typed': False},
                        'Scientific revisions: native index cache binding differs')
                wrapped = getattr(actual, '__wrapped__', None)
                require([item for item in gc.get_referents(actual) if inspect.isfunction(item)] == [wrapped],
                        'Scientific revisions: index cache wraps another callable')
                actual = wrapped
            require(inspect.isfunction(actual) and actual.__code__ == codes.get(name)
                    and actual.__globals__ is vars(module) and actual.__closure__ is None
                    and actual.__defaults__ is None and actual.__kwdefaults__ is None,
                    'Scientific revisions: loaded resolver callable differs from reviewed source')
    owner, index = modules['retained_source'], modules['retained_source.index']
    objects, descriptor, contracts = (modules[name] for name in
                                    ('retained_source.objects', 'retained_source.descriptor', 'contracts'))
    require(hook.source_revision is owner.source_revision is index.source_revision,
            'Scientific revisions: imported source resolver differs from reviewed owner')
    bindings = (
        (index, {'Path': Path, 'require_relative_path': contracts.require_relative_path,
                 'object_fields': descriptor.object_fields, 'json_object': descriptor.json_object,
                 'pinned_bytes': descriptor.pinned_bytes, 'physical': objects.physical,
                 'require': objects.require, 'hexadecimal': objects.hexadecimal}),
        (objects, {'Path': Path, 'ReportRebuildError': contracts.ReportRebuildError}),
        (descriptor, {'Path': Path, 'hashlib': hashlib, 'json': json, 'objects': objects,
                      'require_relative_path': contracts.require_relative_path,
                      'require': objects.require, 'physical': objects.physical,
                      'hexadecimal': objects.hexadecimal}),
    )
    require(all(getattr(module, name, None) is value for module, values in bindings
                for name, value in values.items()),
            'Scientific revisions: resolver dependency binding differs')
    require(index.INDEX_PATH == INDEX and index.INDEX_SHA256 == INDEX_SHA256
            and type(index.INDEX_BYTES) is int and index.INDEX_BYTES == INDEX_BYTES
            and type(index.MAX_DESCRIPTOR_BYTES) is int and index.MAX_DESCRIPTOR_BYTES == 8 * 1024**2,
            'Scientific revisions: fixed registry identity differs')
    raw = regular(root, root / INDEX)
    mode = b'100755' if (root / INDEX).stat().st_mode & 0o100 else b'100644'
    require(len(raw) == INDEX_BYTES and digest(raw) == INDEX_SHA256
            and (root / INDEX).stat().st_nlink == 1 and committed[INDEX] == raw and modes[INDEX] == mode,
            'Scientific revisions: fixed source registry differs')
    registry = json.loads(raw)
    require(all(registry['source_revisions'].get(old) == new for old, new in PAPER_STORAGE.items()),
            'Scientific revisions: historical paper storage differs')
    manifest = json.loads(regular(root, root / 'reports/exports/papers/manifest.json'))
    revisions = {manifest['repository_revision'], manifest['producer_revision']}
    for paper in manifest['papers']:
        revisions.update((paper.get('source_revision', manifest['repository_revision']),
                          paper.get('producer_revision', manifest['producer_revision'])))
    require(len(revisions) <= 20 and all(isinstance(value, str)
            and re.fullmatch('[0-9a-f]{40}', value) is not None for value in revisions),
            'Scientific revisions: finite literal paper epochs required')
    require(json.dumps(index.configured_index(root), sort_keys=True, allow_nan=False)
            == json.dumps(registry, sort_keys=True, allow_nan=False),
            'Scientific revisions: loaded registry differs from independently read bytes')
    mappings = []
    for historical in sorted(revisions):
        storage = registry['source_revisions'].get(historical, historical)
        require(storage == PAPER_STORAGE.get(historical, historical)
                and hook.source_revision(root, historical) == storage,
                'Scientific revisions: loaded paper resolution differs from fixed storage')
        mappings.append({'historical_revision': historical, 'storage_revision': storage})
    inputs.append({'path': INDEX, 'sha256': INDEX_SHA256})
    require(_git(root, 'rev-parse', '--verify', 'HEAD').decode().strip() == head
            and all(regular(root, root / row['path']) == committed[row['path']] for row in inputs),
            'Scientific revisions: source authority changed during capture')
    return {'inputs': sorted(inputs, key=lambda row: row['path']), 'paper_source_revisions': mappings}
