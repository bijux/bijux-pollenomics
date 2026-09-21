/** Receipt-bound bytes for managed generated-report browser candidates. */
import { createHash } from 'node:crypto';
import { constants } from 'node:fs';
import { lstat, open, readdir } from 'node:fs/promises';
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';

const DIGEST = /^[0-9a-f]{64}$/;
const BUILD_ID = /^atlas-[0-9a-f]{64}$/;
const COUNTRIES = ['Sweden', 'Norway', 'Finland', 'Denmark'];
const RAA_KEY = 'raa-archaeology';
const hash = (value) => createHash('sha256').update(value).digest('hex');
const compare = (left, right) => left < right ? -1 : left > right ? 1 : 0;

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
      || value.split('/').some((part) => ['', '.', '..'].includes(part))) throw new Error('unsafe generated-report path');
  return value;
}

async function regularBytes(path) {
  let ancestor = resolve(path);
  while (true) {
    if ((await lstat(ancestor)).isSymbolicLink()) throw new Error('generated report contains a symbolic link');
    const parent = dirname(ancestor);
    if (parent === ancestor) break;
    ancestor = parent;
  }
  const file = await open(path, constants.O_RDONLY | constants.O_NONBLOCK | (constants.O_NOFOLLOW || 0));
  try {
    if (!(await file.stat()).isFile()) throw new Error('generated report contains a nonregular member');
    return await file.readFile();
  } finally { await file.close(); }
}

async function bound(root, member, expected) {
  if (!DIGEST.test(expected)) throw new Error('invalid generated-report SHA256');
  const payload = await regularBytes(join(root, safe(member)));
  if (hash(payload) !== expected) throw new Error(`generated report digest changed: ${member}`);
  return payload;
}

async function inventory(root, prefix = '') {
  if ((await lstat(root)).isSymbolicLink()) throw new Error('symbolic generated-report root');
  const rows = [];
  for (const name of (await readdir(root)).sort(compare)) {
    const member = safe(prefix + name);
    const path = join(root, name);
    const state = await lstat(path);
    if (state.isSymbolicLink()) throw new Error('symbolic generated-report member');
    if (state.isDirectory()) rows.push(...await inventory(path, `${member}/`));
    else {
      const payload = await regularBytes(path);
      rows.push({ path: member, sha256: hash(payload), byte_count: payload.length });
    }
  }
  return rows.sort((left, right) => compare(left.path, right.path));
}

function commandOption(command, name) {
  const indexes = command.flatMap((value, index) => value === name ? [index] : []);
  if (indexes.length !== 1 || indexes[0] + 1 >= command.length) throw new Error(`publisher requires one ${name}`);
  return command[indexes[0] + 1];
}

function exactRaaContract(status, contract, manifest, candidate) {
  const reasons = ['missing_raw_inventory', 'missing_raw_summary', 'missing_scientific_review'];
  const raaLayers = Array.isArray(contract.layer_rows)
    ? contract.layer_rows.filter((row) => row?.key === RAA_KEY) : [];
  const layer = raaLayers[0];
  if (raaLayers.length !== 1 || layer.default_enabled !== true || layer.applies_time_filter !== false
      || layer.contribution_role !== 'display_only' || layer.candidate_ranking_eligible !== false
      || layer.scientific_classification_eligible !== false || layer.propagation_status !== 'refused'
      || layer.propagation_reason_code !== 'archaeology_context_only' || layer.edge_count !== 0
      || layer.authority_status !== 'degraded' || canonical(layer.authority_reason_codes) !== canonical(reasons)) {
    throw new Error('RAÄ publication contract differs');
  }
  const geometry = status.geometry_publication;
  const accounting = status.density_count_accounting;
  if (status.schema_version !== 'raa-atlas-input-status.v1' || status.atlas_input_status !== 'degraded'
      || canonical(status.reason_codes) !== canonical(reasons) || status.evidence_role !== 'archaeology_context_only'
      || status.propagation_eligible !== false || geometry?.default_map_state !== 'enabled_degraded_context'
      || geometry?.default_enabled !== true || geometry?.retained_density_is_authoritative !== false
      || accounting?.density_feature_count !== 106 || accounting?.density_cell_count_sum !== 339412
      || accounting?.metadata_fornlamning_count !== 318265 || accounting?.difference !== 21147
      || accounting?.reconciled !== false) throw new Error('RAÄ retained-input status differs');
  const fields = manifest.assets?.fields;
  const records = manifest.assets?.records;
  if (!Array.isArray(fields) || !Array.isArray(records)) throw new Error('static asset table is absent');
  const rows = records.filter((row) => Array.isArray(row) && row.length === fields.length)
    .map((row) => Object.fromEntries(fields.map((field, index) => [field, row[index]])));
  const assets = rows.filter((row) => row.layer_key === RAA_KEY);
  const asset = assets[0];
  const edges = manifest.domains?.edges;
  if (manifest.build_id !== candidate.build_id || assets.length !== 1 || asset.domain !== 'nodes'
      || asset.sha256 !== 'f9c34eccd0ca76ef5fc1e4a1a6b46d6678a9389044cbf3a6ce2d925fd30c353b'
      || asset.payload_sha256 !== '9b37afcf73e93465fc255d8f6fd9e33b711b7c8d6dc6026db1af143f5ff577c1'
      || asset.record_count !== 106 || asset.untimed_record_count !== 106
      || asset.chronology_absent_record_count !== 106 || asset.time_min_bp !== null || asset.time_max_bp !== null
      || edges?.status !== 'unavailable' || edges?.reason_code !== 'governed_map_edge_model_not_available'
      || edges?.record_count !== 0) throw new Error('RAÄ static asset or edge posture differs');
}

export async function assertGeneratedReportCandidate(plan) {
  const candidate = plan.candidate;
  if (plan.schema_version !== 'atlas-browser-verification-plan.v4'
      || plan.verification_profile !== 'raa-retained-context-v1'
      || candidate.kind !== 'generated_report_publication' || !BUILD_ID.test(candidate.build_id)) {
    throw new Error('unsupported generated-report candidate/profile');
  }
  const repositoryRoot = resolve(plan.repository_root);
  const presentationRoot = join(repositoryRoot, safe(candidate.presentation_root));
  if (!candidate.presentation_root.startsWith('artifacts/')) throw new Error('presentation is outside artifacts');
  const receiptPayload = await bound(repositoryRoot, candidate.generator_receipt, candidate.generator_receipt_sha256);
  const receipt = JSON.parse(receiptPayload.toString('utf8'));
  const required = ['job_id', 'input_commit', 'input_tree', 'exit_code', 'termination', 'read_set_unchanged', 'command', 'cwd', 'outputs', 'output_hashes'];
  if (!required.every((field) => field in receipt) || receipt.job_id !== dirname(candidate.generator_receipt).split('/').at(-1)
      || receipt.input_commit !== candidate.generator_repository_head || receipt.input_tree !== candidate.generator_repository_tree
      || receipt.exit_code !== 0 || receipt.termination !== 'exited' || receipt.read_set_unchanged !== true) {
    throw new Error('managed publication receipt differs');
  }
  const command = receipt.command;
  if (!Array.isArray(command) || command.some((value) => typeof value !== 'string' || !value)
      || !command.some((value, index) => value === '-m' && command[index + 1] === 'bijux_pollenomics' && command[index + 2] === 'publish-reports')) {
    throw new Error('managed publisher command differs');
  }
  const countries = command.indexOf('--countries');
  if (countries < 0 || canonical(command.slice(countries + 1, countries + 5)) !== canonical(COUNTRIES)
      || commandOption(command, '--output-root') !== presentationRoot
      || commandOption(command, '--published-output-root') !== 'docs/report') throw new Error('publisher output/country closure differs');
  if (typeof receipt.cwd !== 'string' || !isAbsolute(receipt.cwd)
      || !resolve(receipt.cwd).startsWith(join(repositoryRoot, 'artifacts') + sep)
      || resolve(receipt.cwd).startsWith(presentationRoot + sep)
      || !Array.isArray(receipt.outputs) || !receipt.outputs.includes(presentationRoot)
      || receipt.output_hashes === null || typeof receipt.output_hashes !== 'object' || Array.isArray(receipt.output_hashes)) {
    throw new Error('managed publisher paths differ');
  }
  const files = await inventory(presentationRoot);
  const physicalHashes = Object.fromEntries(files.map((row) => [row.path, row.sha256]));
  const prefix = `${presentationRoot}/`;
  const receiptHashes = Object.fromEntries(Object.entries(receipt.output_hashes)
    .filter(([path]) => path.startsWith(prefix)).map(([path, digest]) => [path.slice(prefix.length), digest]));
  if (canonical(receiptHashes) !== canonical(physicalHashes)
      || hash(Buffer.from(canonical(physicalHashes))) !== candidate.presentation_inventory_sha256) {
    throw new Error('managed publication inventory differs');
  }
  const scopeDirectory = dirname(join(repositoryRoot, plan.scopes[0].document));
  const inputStatusPayload = await regularBytes(join(scopeDirectory, 'raa_atlas_input_status.json'));
  const contractPayload = await regularBytes(join(scopeDirectory, 'nordic_map_publication_contract.json'));
  const manifestPayload = await regularBytes(join(scopeDirectory, 'nordic_map_assets.json'));
  exactRaaContract(
    JSON.parse(inputStatusPayload.toString('utf8')),
    JSON.parse(contractPayload.toString('utf8')),
    JSON.parse(manifestPayload.toString('utf8')),
    candidate,
  );
  return {
    schema_version: 'atlas-generated-report-integrity.v1', candidate,
    files: files.map((row) => ({ ...row, path: `${candidate.presentation_root}/${row.path}` })),
    generator_receipt_sha256: candidate.generator_receipt_sha256,
    raa_contract: {
      input_status_sha256: hash(inputStatusPayload), publication_contract_sha256: hash(contractPayload),
      retained_density_sha256: 'acac7a952dc31be8b988ecb35386c877628e2580fae427f32281310635489d20',
      retained_metadata_sha256: 'baa5f7ec34e290d5b52ad93afb8a05e77830bd2b2672a15a579e571f5f6d91d8',
    },
  };
}

export async function readGeneratedReportMember(plan, audit, requestedAbsolutePath) {
  const root = resolve(plan.repository_root);
  const member = relative(root, resolve(requestedAbsolutePath)).split(sep).join('/');
  const expected = audit.files.find((row) => row.path === member);
  if (!expected) return null;
  safe(member);
  const payload = await regularBytes(join(root, member));
  const receipt = { path: member, sha256: hash(payload), byte_count: payload.length };
  if (canonical(receipt) !== canonical(expected)) throw new Error(`served report bytes changed: ${member}`);
  return { payload, receipt };
}
