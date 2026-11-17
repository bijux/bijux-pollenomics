// Read only independently pinned catalogue metadata through the common asset loader.
function createSourceResourceBrowser({manifest, loadAsset, payloadForAsset, downloadTransport = {}, readerContext = {}}) {
  const domain = manifest?.domains?.resources;
  const fail = message => { throw Error(`Source resource metadata: ${message}`); };
  if (!domain || !['atlas-source-resources.v1','atlas-source-resources.v2'].includes(domain.schema_version)
    || !/^[a-f0-9]{64}$/.test(domain.catalogue_manifest_sha256 || '')
    || domain.source_family !== 'neotoma' || domain.scientific_admission !== 'not_asserted'
    || domain.numerical_atlas_denominator_changed !== false || domain.initial_load !== false
    || domain.payload_encoding !== 'gzip_base64' || domain.metadata_only !== true
    || !Array.isArray(manifest.assets)
    || typeof loadAsset !== 'function' || typeof payloadForAsset !== 'function') fail('catalogue or loader unavailable');
  const ancillary = createSourceResourceAncillaryContract(domain, fail);
  const populations = {resources:'record_count',sites:'site_count',descriptors:'source_descriptor_count',...ancillary.counts};
  const mapping = domain.part_asset_keys;
  if (!mapping || Array.isArray(mapping) || typeof mapping !== 'object'
    || !Array.isArray(domain.index_part_ids)
    || !Number.isSafeInteger(domain.part_count) || Object.keys(mapping).length !== domain.part_count
    || new Set(Object.values(mapping)).size !== domain.part_count
    || new Set(domain.index_part_ids).size !== domain.index_part_ids.length) fail('part inventory differs');
  const allowedKinds=['context','index',...Object.keys(populations)], ordinals=new Map();
  for (const [partId,key] of Object.entries(mapping)) {
    const [kind,number,...extra]=partId.split(':');
    if (!allowedKinds.includes(kind) || !/^(0|[1-9][0-9]*)$/.test(number || '') || extra.length
      || typeof key !== 'string' || !key || !manifest.assets.some(row=>row.asset_key===key && row.domain==='resources')) fail('part kind or binding differs');
    if(!ordinals.has(kind))ordinals.set(kind,[]);ordinals.get(kind).push(Number(number));
  }
  for(const values of ordinals.values())if(values.sort((a,b)=>a-b).some((value,number)=>value!==number))fail('part sequence differs');
  if (domain.index_part_ids.some((id,number)=>id!==`index:${number}` || !Object.hasOwn(mapping,id))
    || (ordinals.get('index')?.length || 0)!==domain.index_part_ids.length
    || ordinals.get('context')?.length!==1 || !Object.hasOwn(mapping,'context:0')
    || ancillary.kinds.length && domain.ancillary_context_part_id !== 'ancillary_context:0') fail('index or ancillary context part differs');
  const payloads = new Map(), index = new Map(), partCounts = new Map();
  let indexRequest = null;
  const clone = value => JSON.parse(JSON.stringify(value));
  const nativeId = value => typeof value === 'string' && /^[1-9][0-9]*$/.test(value);
  const rowId = (kind, row) => ancillary.kinds.includes(kind) ? ancillary.identity(kind,row)
    : kind === 'resources' ? row.dataset_id : kind === 'sites' ? row.site_id : row.record_id;
  const count = name => {
    if (!Number.isSafeInteger(domain[name]) || domain[name] < 0) fail(`invalid ${name}`);
    return domain[name];
  };
  function consume(row, payload) {
    if (row?.domain !== 'resources' || payload?.schema_version !== 'atlas-source-resource-chunk.v1'
      || payload.source_family !== 'neotoma' || payload.catalogue_manifest_sha256 !== domain.catalogue_manifest_sha256
      || payload.scientific_admission !== 'not_asserted'
      || !['context','sites','resources','descriptors','index',...ancillary.kinds].includes(payload.kind)
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
    if(indexRequest)return indexRequest;
    indexRequest = (async () => {
      const next = new Map();
      const parts = await Promise.all(domain.index_part_ids.map(part));
      for (const payload of parts) {
        if (payload.kind !== 'index') fail('index part has another kind');
        for (const record of payload.records) {
          const kind = record.entity_type, identity = record.record_id, key = `${kind}:${identity}`;
          if (!Object.hasOwn(populations,kind)
            || (ancillary.kinds.includes(kind) ? !ancillary.valid(kind,identity) : kind === 'descriptors' ? !/^[a-f0-9]{64}$/.test(identity || '') : !nativeId(identity))
            || typeof record.part_id !== 'string' || !record.part_id.startsWith(`${kind}:`)
            || !mapping[record.part_id] || next.has(key)) fail('index identity repeats or dangles');
          if (ancillary.kinds.includes(kind)) ancillary.index(record);
          next.set(key, record);
        }
      }
      const referenced=new Set([...next.values()].map(row=>row.part_id));
      if(Object.keys(mapping).some(id=>!id.startsWith('index:') && id!=='context:0' && !referenced.has(id)))fail('metadata part has no index membership');
      for (const [kind, field] of Object.entries(populations)) {
        if ([...next.values()].filter(row => row.entity_type === kind).length !== (field === null ? 1 : count(field))) fail('index population differs');
      }
      if (ancillary.kinds.length && (count('ancillary_facet_observation_count') + count('ancillary_linked_observation_count') !== count('ancillary_observation_count')
        || [...next.values()].filter(row=>row.entity_type==='ancillary_observations' && row.kind==='facet').length !== count('ancillary_facet_observation_count')
        || [...next.values()].filter(row=>row.entity_type==='ancillary_observations' && row.kind==='linked').length !== count('ancillary_linked_observation_count'))) fail('ancillary observation population differs');
      if (count('version_status_count') !== 2 * count('record_count')) fail('version population differs');
      next.forEach((value,key)=>{index.set(key,value);partCounts.set(value.part_id,(partCounts.get(value.part_id)||0)+1);});
    })();
    indexRequest = indexRequest.catch(error=>{indexRequest=null;throw error;});
    return indexRequest;
  }
  async function record(kind, identity) {
    if (!Object.hasOwn(populations,kind) || (ancillary.kinds.includes(kind) ? !ancillary.valid(kind,identity) : !nativeId(identity) && kind !== 'descriptors')) fail('native identity is invalid');
    await loadIndex();
    const reference = index.get(`${kind}:${identity}`);
    if (!reference) return null;
    const payload = await part(reference.part_id);
    if (payload.kind !== kind) fail('record reference has another kind');
    if (ancillary.kinds.includes(kind)) {
      if(partCounts.get(payload.part_id)!==payload.records.length)fail('selected ancillary part membership differs');
      const seen=new Set();
      for(const member of payload.records) {
        const projected=ancillary.projection(kind,member,payload.part_id);
        if(seen.has(projected.record_id) || !ancillary.same(projected,index.get(`${kind}:${projected.record_id}`)))fail('selected ancillary index owner or source posture differs');
        seen.add(projected.record_id);
      }
    }
    const found = payload.records.find(row => rowId(kind, row) === identity);
    if (!found) fail('referenced record is absent');
    return clone(found);
  }
  async function search(query = '', filters = {}) {
    const population=filters.population || 'resources';
    if (!Object.hasOwn(populations,population) || ['sites','descriptors'].includes(population)) fail('unsupported search population');
    if (population !== 'resources' && Object.keys(filters).some(key=>key!=='population')) fail('native filters do not apply to the catalogue-wide ancillary population');
    await loadIndex();
    const text = String(query).trim().toLocaleLowerCase();
    return [...index.values()].filter(row => {
      if (row.entity_type !== population) return false;
      if (population !== 'resources') return !text || JSON.stringify(row).toLocaleLowerCase().includes(text);
      const site = index.get(`sites:${row.site_id}`), names = site?.native_site_names || [];
      return (!filters.country || (row.country_code ?? 'UNASSIGNED') === filters.country)
        && (!filters.type || row.dataset_type === filters.type)
        && (!filters.role || row.exposure_role === filters.role)
        && (!filters.statusField || Object.hasOwn(row.version_statuses?.[filters.version] || {}, filters.statusField)
          && row.version_statuses[filters.version][filters.statusField] === filters.status)
        && (!text || [row.record_id, row.site_id, row.collection_unit_id, row.dataset_type, row.country_code, ...names].join(' ').toLocaleLowerCase().includes(text));
    }).map(clone);
  }
  async function inventory() {
    await loadIndex();
    return Object.fromEntries(Object.keys(populations).map(kind => [kind,
      [...index.values()].filter(row => row.entity_type === kind).map(clone)]));
  }
  async function context() {
    if (domain.context_part_id !== undefined && domain.context_part_id !== 'context:0') fail('context part identity differs');
    const payload = await part(domain.context_part_id ?? 'context:0');
    if (payload.kind !== 'context' || payload.records.length !== 1 || payload.records[0].record_id !== 'catalogue') fail('catalogue context differs');
    return clone(payload.records[0]);
  }
  let reader = null;
  const api = {consume, loadIndex, search, inventory, context, site: identity => record('sites', identity), resource: identity => record('resources', identity), ancillary:(kind,identity)=>{if(!ancillary.kinds.includes(kind))fail('unknown ancillary kind');return record(kind,identity);}};
  let downloads = null;
  function downloadManager() {
    return downloads ||= createSourceResourceDownloads({domain, context, resource: identity => record('resources', identity),
      fetcher: downloadTransport.fetcher, cryptoProvider: downloadTransport.cryptoProvider, location: downloadTransport.location});
  }
  return Object.freeze(Object.assign(api, {open: selection => (reader ||= createSourceResourceReader({...readerContext,browser:api,domain})).open(selection),
    countriesChanged: () => reader?.countriesChanged(),
    downloadResource: (identity, version, options) => downloadManager().body(identity, version, options),
    downloadReceipt: (identity, version, options) => downloadManager().receipt(identity, version, options)}));
}
