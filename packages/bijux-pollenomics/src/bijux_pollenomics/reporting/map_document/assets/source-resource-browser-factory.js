// Read only independently pinned catalogue metadata through the common asset loader.
function createSourceResourceBrowser({manifest, loadAsset, payloadForAsset}) {
  const domain = manifest?.domains?.resources;
  const fail = message => { throw Error(`Source resource metadata: ${message}`); };
  if (!domain || domain.schema_version !== 'atlas-source-resources.v1'
    || !/^[a-f0-9]{64}$/.test(domain.catalogue_manifest_sha256 || '')
    || domain.scientific_admission !== 'not_asserted'
    || typeof loadAsset !== 'function' || typeof payloadForAsset !== 'function') fail('catalogue or loader unavailable');
  const mapping = domain.part_asset_keys;
  if (!mapping || Array.isArray(mapping) || typeof mapping !== 'object'
    || !Array.isArray(domain.index_part_ids)
    || Object.keys(mapping).length !== domain.part_count) fail('part inventory differs');
  const payloads = new Map(), index = new Map();
  let indexRequest = null;
  const clone = value => JSON.parse(JSON.stringify(value));
  const nativeId = value => typeof value === 'string' && /^[1-9][0-9]*$/.test(value);
  const rowId = (kind, row) => kind === 'resources' ? row.dataset_id : kind === 'sites' ? row.site_id : row.record_id;
  const count = name => {
    if (!Number.isSafeInteger(domain[name]) || domain[name] < 0) fail(`invalid ${name}`);
    return domain[name];
  };
  function consume(row, payload) {
    if (row?.domain !== 'resources' || payload?.schema_version !== 'atlas-source-resource-chunk.v1'
      || payload.source_family !== 'neotoma' || payload.catalogue_manifest_sha256 !== domain.catalogue_manifest_sha256
      || payload.scientific_admission !== 'not_asserted'
      || !['context','sites','resources','descriptors','index'].includes(payload.kind)
      || mapping[payload.part_id] !== row.asset_key || payload.asset_key !== row.asset_key
      || !Array.isArray(payload.records) || !payload.records.length || row.record_count !== payload.records.length) fail('part identity differs');
    const seen = new Set();
    for (const record of payload.records) {
      if (!record || typeof record !== 'object' || Array.isArray(record)) fail('record is malformed');
      if (payload.kind === 'index') continue;
      const identity = rowId(payload.kind, record);
      if ((['resources','sites'].includes(payload.kind) && !nativeId(identity))
        || (payload.kind === 'descriptors' && !/^[a-f0-9]{64}$/.test(identity || ''))
        || (payload.kind === 'context' && identity !== 'catalogue') || seen.has(identity)) fail('record identity repeats or differs');
      seen.add(identity);
      if (payload.kind === 'resources' && ('native_body' in record || 'native_payload' in record)) fail('native body is outside metadata transport');
    }
    const old = payloads.get(payload.part_id);
    if (old && JSON.stringify(old) !== JSON.stringify(payload)) fail('part was replaced');
    payloads.set(payload.part_id, payload);
  }
  async function part(identity) {
    const key = mapping[identity];
    const row = manifest.assets.find(candidate => candidate.asset_key === key && candidate.domain === 'resources');
    if (!row) fail('part is absent from the asset inventory');
    if (!payloads.has(identity)) {
      await loadAsset(row);
      const payload = payloadForAsset(key);
      if (!payload) fail('loaded metadata part unavailable');
      consume(row, payload);
    }
    return payloads.get(identity);
  }
  function loadIndex() {
    return indexRequest ||= (async () => {
      const parts = await Promise.all(domain.index_part_ids.map(part));
      for (const payload of parts) {
        if (payload.kind !== 'index') fail('index part has another kind');
        for (const record of payload.records) {
          const kind = record.entity_type, identity = record.record_id, key = `${kind}:${identity}`;
          if (!['sites','resources','descriptors'].includes(kind)
            || (kind === 'descriptors' ? !/^[a-f0-9]{64}$/.test(identity || '') : !nativeId(identity))
            || typeof record.part_id !== 'string' || !record.part_id.startsWith(`${kind}:`)
            || !mapping[record.part_id] || index.has(key)) fail('index identity repeats or dangles');
          index.set(key, record);
        }
      }
      for (const [kind, field] of [['resources','record_count'],['sites','site_count'],['descriptors','source_descriptor_count']]) {
        if ([...index.values()].filter(row => row.entity_type === kind).length !== count(field)) fail('index population differs');
      }
      if (count('version_status_count') !== 2 * count('record_count')) fail('version population differs');
    })();
  }
  async function record(kind, identity) {
    if (!nativeId(identity) && kind !== 'descriptors') fail('native identity is invalid');
    await loadIndex();
    const reference = index.get(`${kind}:${identity}`);
    if (!reference) return null;
    const payload = await part(reference.part_id);
    if (payload.kind !== kind) fail('record reference has another kind');
    const found = payload.records.find(row => rowId(kind, row) === identity);
    if (!found) fail('referenced record is absent');
    return clone(found);
  }
  async function search(query = '', filters = {}) {
    await loadIndex();
    const text = String(query).trim().toLocaleLowerCase();
    return [...index.values()].filter(row => {
      if (row.entity_type !== 'resources') return false;
      const site = index.get(`sites:${row.site_id}`), names = site?.native_site_names || [];
      return (!filters.country || row.country_code === filters.country)
        && (!filters.type || row.dataset_type === filters.type)
        && (!filters.role || row.exposure_role === filters.role)
        && (!text || [row.record_id, row.site_id, row.collection_unit_id, row.dataset_type, row.country_code, ...names].join(' ').toLocaleLowerCase().includes(text));
    }).map(clone);
  }
  return Object.freeze({consume, loadIndex, search, site: identity => record('sites', identity), resource: identity => record('resources', identity)});
}
