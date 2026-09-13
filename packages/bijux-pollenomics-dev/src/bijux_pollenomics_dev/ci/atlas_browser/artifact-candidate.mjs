/** Exact local artifact/source bytes for the existing browser verifier. */
import { createHash } from 'node:crypto';
import { constants } from 'node:fs';
import { lstat, open, readdir } from 'node:fs/promises';
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { boundedGit } from '../atlas_media/candidate_git.mjs';

const SOURCE_ROOTS = ['packages/bijux-pollenomics/src', 'packages/bijux-pollenomics/pyproject.toml', 'pyproject.toml', 'uv.lock', 'configs/scientific-contracts'];
const DIGEST = /^[0-9a-f]{64}$/;
const hash = (value, algorithm = 'sha256') => createHash(algorithm).update(value).digest('hex');
const compare = (left, right) => {
  const a = Array.from(left, (v) => v.codePointAt(0));
  const b = Array.from(right, (v) => v.codePointAt(0));
  for (let index = 0; index < Math.min(a.length, b.length); index += 1) {
    if (a[index] !== b[index]) return a[index] - b[index];
  }
  return a.length - b.length;
};
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    return `{${Object.keys(value).sort(compare).map((key) => `${canonical(key)}:${canonical(value[key])}`).join(',')}}`;
  }
  if (typeof value === 'number' && !Number.isFinite(value)) throw new Error('nonfinite candidate JSON');
  return JSON.stringify(value).replace(/[\u007f-\uffff]/g, (character) => `\\u${character.charCodeAt(0).toString(16).padStart(4, '0')}`);
}
function safe(value) {
  if (typeof value !== 'string' || !value || value.includes('\\') || value.includes('\0') || isAbsolute(value)
      || value.split('/').some((part) => ['', '.', '..'].includes(part))) throw new Error('unsafe candidate path');
  return value;
}
function assertDigest(value) {
  if (typeof value !== 'string' || !DIGEST.test(value)) throw new Error('invalid candidate SHA256');
}
async function regularBytes(path) {
  let ancestor = resolve(path);
  while (true) {
    if ((await lstat(ancestor)).isSymbolicLink()) throw new Error('candidate contains a symbolic link');
    const parent = dirname(ancestor);
    if (parent === ancestor) break;
    ancestor = parent;
  }
  const file = await open(path, constants.O_RDONLY | constants.O_NONBLOCK | (constants.O_NOFOLLOW || 0));
  try {
    if (!(await file.stat()).isFile()) throw new Error('candidate contains a nonregular member');
    return await file.readFile();
  } finally { await file.close(); }
}
async function bound(root, member, expected) {
  assertDigest(expected);
  const value = await regularBytes(join(root, safe(member)));
  if (hash(value) !== expected) throw new Error(`candidate digest changed: ${member}`);
  return value;
}
async function inventory(root, prefix = '') {
  if ((await lstat(root)).isSymbolicLink()) throw new Error('symbolic candidate root');
  const rows = [];
  for (const name of (await readdir(root)).sort(compare)) {
    const member = safe(prefix + name);
    const path = join(root, name);
    const state = await lstat(path);
    if (state.isSymbolicLink()) throw new Error('symbolic candidate member');
    if (state.isDirectory()) rows.push(...await inventory(path, `${member}/`));
    else {
      const payload = await regularBytes(path);
      rows.push({ path: member, sha256: hash(payload), byte_count: payload.length });
    }
  }
  return rows.sort((a, b) => compare(a.path, b.path));
}
async function sourceClosure(repositoryRoot, candidate, receipt, signed) {
  if (receipt.schema_version !== (signed ? 'atlas-artifact-generation.v2' : 'atlas-artifact-generation.v1')
      || (signed ? receipt.temporal_profile !== 'calendar-bp1950-signed.v1' || receipt.temporal_axis !== 'BP1950' : 'temporal_profile' in receipt || 'temporal_axis' in receipt)
      || receipt.source_relation !== 'committed_tree'
      || receipt.generator_repository_head !== candidate.generator_repository_head
      || receipt.generator_repository_tree !== candidate.generator_repository_tree
      || receipt.entry_point !== 'bijux_pollenomics.reporting.lra_products.api:render_lra_report') throw new Error('generator receipt identity differs');
  const head = candidate.generator_repository_head;
  if (!/^(?:[0-9a-f]{40}|[0-9a-f]{64})$/.test(head)
      || boundedGit(repositoryRoot, ['rev-parse', `${head}^{tree}`]) !== candidate.generator_repository_tree) throw new Error('generator HEAD/tree relationship differs');
  const objects = new Map();
  const listing = boundedGit(repositoryRoot, ['ls-tree', '-r', '-z', '--full-tree', head, '--', ...SOURCE_ROOTS]);
  for (const row of listing.split('\0').filter(Boolean)) {
    const split = row.indexOf('\t');
    const [mode, kind, id] = row.slice(0, split).split(' ');
    const member = safe(row.slice(split + 1));
    if (!['100644', '100755'].includes(mode) || kind !== 'blob' || objects.has(member)) throw new Error('unsupported generator tree entry');
    objects.set(member, id);
  }
  const source = join(repositoryRoot, safe(receipt.source_root));
  const observed = {};
  const physical = new Set();
  for (const selected of SOURCE_ROOTS) {
    if (![...objects.keys()].some((name) => name === selected || name.startsWith(`${selected}/`))) throw new Error('incomplete generator tree');
    const path = join(source, selected);
    const state = await lstat(path);
    if (state.isSymbolicLink()) throw new Error('symbolic generator source');
    if (state.isDirectory()) {
      for (const row of await inventory(path)) {
        if (!row.path.split('/').includes('__pycache__')) physical.add(`${selected}/${row.path}`);
      }
    } else physical.add(selected);
  }
  if (canonical([...physical].sort(compare)) !== canonical([...objects.keys()].sort(compare))) throw new Error('generator source closure differs');
  for (const [member, id] of objects) {
    const payload = await regularBytes(join(source, member));
    const blob = Buffer.concat([Buffer.from(`blob ${payload.length}\0`), payload]);
    if (hash(blob, id.length === 40 ? 'sha1' : 'sha256') !== id) throw new Error(`generator byte mismatch: ${member}`);
    observed[member] = hash(payload);
  }
  if (canonical(observed) !== canonical(receipt.source_files)) throw new Error('generator receipt source inventory differs');
  await bound(repositoryRoot, safe(receipt.inputs.geometry_path), candidate.display_geometry_sha256);
  const original = join(repositoryRoot, safe(receipt.inputs.product_directory));
  const originalManifest = JSON.parse((await bound(original, 'manifest.json', candidate.product_manifest_sha256)).toString('utf8'));
  const originalFiles = Object.fromEntries((await inventory(original)).filter((row) => row.path !== 'manifest.json').map((row) => [row.path, row.sha256]));
  if (canonical(originalFiles) !== canonical(originalManifest.files)) throw new Error('original product inventory differs');
}

export async function assertArtifactCandidate(plan) {
  const candidate = plan.candidate;
  const signed = plan.verification_profile === 'native-lra-signed-calendar-v1';
  if (plan.schema_version !== 'atlas-browser-verification-plan.v3' || candidate.kind !== 'local_lra_presentation'
      || !['native-lra-exploratory-v1', 'native-lra-signed-calendar-v1'].includes(plan.verification_profile)) throw new Error('unsupported artifact candidate/profile');
  const repositoryRoot = resolve(plan.repository_root);
  const root = join(repositoryRoot, safe(candidate.presentation_root));
  if (!candidate.presentation_root.startsWith('artifacts/')) throw new Error('presentation is outside artifacts');
  const encodedReceipt = await bound(repositoryRoot, candidate.generator_receipt, candidate.generator_receipt_sha256);
  const receipt = JSON.parse(encodedReceipt.toString('utf8'));
  await sourceClosure(repositoryRoot, candidate, receipt, signed);
  const encoded = await bound(root, 'manifest.json', candidate.presentation_manifest_sha256);
  const manifest = JSON.parse(encoded.toString('utf8'));
  const files = await inventory(root);
  if (hash(Buffer.from(canonical(files))) !== candidate.presentation_inventory_sha256) throw new Error('presentation inventory differs');
  const hashes = Object.fromEntries(files.filter((row) => row.path !== 'manifest.json').map((row) => [row.path, row.sha256]));
  if (canonical(hashes) !== canonical(manifest.files) || manifest.schema_version !== (signed ? 'lra-presentation.v2' : 'lra-presentation.v1')
      || (signed ? manifest.temporal_profile !== 'calendar-bp1950-signed.v1' || manifest.temporal_axis !== 'BP1950' : 'temporal_profile' in manifest || 'temporal_axis' in manifest)
      || manifest.status !== 'generated_exploratory' || manifest.scientific_acceptance !== 'not_evaluated'
      || manifest.publication_authorized !== false || manifest.data_kind !== 'synthetic' || manifest.operation !== 'lra' || manifest.map_build_id !== candidate.build_id
      || manifest.product_manifest_sha256 !== candidate.product_manifest_sha256
      || manifest.display_geometry_sha256 !== candidate.display_geometry_sha256) throw new Error('presentation identity/posture differs');
  await bound(root, 'display-geometry.json', candidate.display_geometry_sha256);
  await bound(root, 'product/manifest.json', candidate.product_manifest_sha256);
  return { schema_version: 'atlas-artifact-integrity.v1', candidate, files: files.map((row) => ({ ...row, path: `${candidate.presentation_root}/${row.path}` })), generator_receipt_sha256: candidate.generator_receipt_sha256 };
}

export async function readArtifactMember(plan, audit, requestedAbsolutePath) {
  const root = resolve(plan.repository_root);
  const member = relative(root, resolve(requestedAbsolutePath)).split(sep).join('/');
  const expected = audit.files.find((row) => row.path === member);
  if (!expected) return null;
  safe(member);
  const payload = await regularBytes(join(root, member));
  const receipt = { path: member, sha256: hash(payload), byte_count: payload.length };
  if (canonical(receipt) !== canonical(expected)) throw new Error(`served candidate bytes changed: ${member}`);
  return { payload, receipt };
}
