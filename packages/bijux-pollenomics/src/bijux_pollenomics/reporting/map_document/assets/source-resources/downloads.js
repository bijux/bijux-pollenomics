// Verify shared source metadata and only the explicitly selected entity buffer.
function createSourceResourceDownloads({domain, context, resource, fetcher = globalThis.fetch,
  cryptoProvider = globalThis.crypto, location = globalThis.location}) {
  const metadataCap = 16 * 1024 * 1024, bodyCap = 32 * 1024 * 1024;
  const development = new Set(['development_resource_discovery', 'exposed_development']);
  let archiveRequest = null;
  function refuse(code, message) {
    const error = Error(message);
    error.code = code;
    throw error;
  }
  const digest = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
  const nativeId = value => typeof value === 'string' && /^[1-9][0-9]*$/.test(value);
  const ordinary = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const stable = value => JSON.stringify(value && typeof value === 'object'
    ? Array.isArray(value) ? value.map(item => JSON.parse(stable(item)))
      : Object.fromEntries(Object.keys(value).sort().map(key => [key, JSON.parse(stable(value[key]))])) : value);
  function memberPath(value) {
    if (typeof value !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._/-]*$/.test(value)
      || value.split('/').some(part => !part || part === '.' || part === '..')
      || value.split('/').length > 32) refuse('member_path', 'Source download member path is unavailable.');
    return value;
  }
  function baseURL(reference) {
    if (!['http:', 'https:'].includes(location?.protocol)) {
      refuse('file_protocol', 'Verified source downloads require HTTPS or a local HTTP server. File-mode downloads are unavailable.');
    }
    if (typeof cryptoProvider?.subtle?.digest !== 'function' || typeof fetcher !== 'function') {
      refuse('verification_unavailable', 'Source download verification is unavailable. Use HTTPS or localhost HTTP.');
    }
    const path = reference?.published_base_url;
    if (typeof path !== 'string' || !/^\/(?:[A-Za-z0-9][A-Za-z0-9._-]*\/)*$/.test(path)
      || path.split('/').some(part => part.toLowerCase() === 'artifacts')) refuse('public_route', 'The shared source publication route is invalid.');
    const base = new URL(path, location.href);
    if (base.origin !== location.origin) refuse('public_route', 'Source downloads require the declared same-origin publication.');
    return base;
  }
  async function buffer(base, path, expectedDigest, expectedSize, cap, signal) {
    memberPath(path);
    if (!digest(expectedDigest) || expectedSize !== undefined
      && (!Number.isSafeInteger(expectedSize) || expectedSize < 0 || expectedSize > cap)) {
      refuse('declared_size', 'The selected source file exceeds its declared download bound.');
    }
    const url = new URL(path, base);
    if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname)) refuse('member_path', 'Source download escaped its declared publication.');
    const response = await fetcher(url.href, {redirect: 'error', credentials: 'same-origin', signal});
    async function cancel(code, message) {
      await response.body?.cancel().catch(() => {});
      refuse(code, message);
    }
    if (!response.ok || response.url && response.url !== url.href) {
      return cancel('http_response', 'The selected source file could not be loaded from its declared location.');
    }
    // Fetch decodes content encodings; wire length is not the original file length.
    const encoded = Boolean(response.headers.get('Content-Encoding')
      && response.headers.get('Content-Encoding').trim().toLowerCase() !== 'identity');
    const declared = response.headers.get('Content-Length');
    if (declared !== null && (!/^[0-9]+$/.test(declared) || !Number.isSafeInteger(Number(declared))
      || Number(declared) > cap || !encoded && expectedSize !== undefined && Number(declared) !== expectedSize)) {
      return cancel('response_size', 'The source response size differs from the declared file.');
    }
    if (!response.body || typeof response.body.getReader !== 'function') {
      return cancel('stream_unavailable', 'Bounded source download streaming is unavailable in this browser.');
    }
    const reader = response.body.getReader(), chunks = [];
    let total = 0;
    try {
      while (true) {
        const next = await reader.read();
        if (next.done) break;
        if (!(next.value instanceof Uint8Array) || next.value.byteLength > cap - total
          || expectedSize !== undefined && next.value.byteLength > expectedSize - total) {
          await reader.cancel();
          refuse('response_size', 'The source response exceeded its declared file size.');
        }
        total += next.value.byteLength;
        chunks.push(next.value);
      }
    } finally { reader.releaseLock(); }
    if (expectedSize !== undefined && total !== expectedSize) refuse('response_size', 'The source response ended before its declared file size.');
    const bytes = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    const actual = [...new Uint8Array(await cryptoProvider.subtle.digest('SHA-256', bytes))]
      .map(value => value.toString(16).padStart(2, '0')).join('');
    if (actual !== expectedDigest) refuse('file_digest', 'Source file verification failed. The original bytes were not downloaded.');
    return bytes;
  }
  function object(bytes) {
    try {
      const value = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
      if (!ordinary(value)) throw Error('Not an object');
      return value;
    } catch { refuse('metadata_json', 'The shared source metadata is not a valid JSON object.'); }
  }
  function fileMember(manifest, path, cap) {
    memberPath(path);
    const member = manifest.files[path];
    if (!ordinary(member) || Object.keys(member).sort().join('|') !== 'bytes|sha256'
      || !Number.isSafeInteger(member.bytes) || member.bytes < 0 || member.bytes > cap || !digest(member.sha256)) {
      refuse('declared_size', 'The selected source file has no valid bounded manifest member.');
    }
    return member;
  }
  async function loadArchive(signal) {
    const metadata = await context(), reference = metadata?.provenance?.source_archive;
    if (reference?.schema_version !== 'atlas-source-resource-archive-reference.v1'
      || reference.catalogue_manifest_sha256 !== domain.catalogue_manifest_sha256
      || !digest(reference.manifest_sha256) || reference.index?.path !== 'downloads/index.json'
      || reference.validation_scope !== 'manifest_and_download_index_only'
      || reference.scientific_admission !== 'not_asserted') refuse('archive_reference', 'This catalogue has no independently pinned source download publication.');
    const base = baseURL(reference);
    const manifest = object(await buffer(base, 'manifest.json', reference.manifest_sha256, undefined, metadataCap, signal));
    if (manifest.schema_version !== 'neotoma-source-resource-archive.v1'
      || manifest.catalogue_manifest_sha256 !== domain.catalogue_manifest_sha256
      || manifest.scientific_admission !== 'not_asserted' || manifest.historical_snapshot_replaced !== false
      || !ordinary(manifest.files) || Object.keys(manifest.files).length > 20000) refuse('archive_manifest', 'The source publication manifest does not match this catalogue.');
    let total = 0;
    for (const path of Object.keys(manifest.files)) total += fileMember(manifest, path, 512 * 1024 * 1024).bytes;
    if (!Number.isSafeInteger(total) || total > 512 * 1024 * 1024 || manifest.source_bytes !== total) refuse('archive_manifest', 'The source publication byte population differs.');
    const declaration = fileMember(manifest, 'downloads/index.json', metadataCap);
    if (declaration.bytes !== reference.index.bytes || declaration.sha256 !== reference.index.sha256) refuse('index_identity', 'The source download index differs from its catalogue reference.');
    const index = object(await buffer(base, 'downloads/index.json', declaration.sha256, declaration.bytes, metadataCap, signal));
    if (index.schema_version !== 'neotoma-source-download-index.v1'
      || index.catalogue_manifest_sha256 !== domain.catalogue_manifest_sha256
      || index.scientific_admission !== 'not_asserted' || !Array.isArray(index.resources)
      || index.resources.length !== 2 * domain.record_count) refuse('index_identity', 'The source download index population differs.');
    const seen = new Set(), partitions = {};
    for (const row of index.resources) {
      const key = `${row.dataset_id}:${row.version}`;
      if (![row.dataset_id,row.site_id,row.collection_unit_id].every(nativeId)
        || !['current','doi_frozen'].includes(row.version) || seen.has(key)
        || row.scientific_admission !== 'not_asserted' || row.use_scope !== 'source_entity_download_only'
        || !['available_source_entity','unavailable_source_entity','blocked_exposure_role'].includes(row.state)) refuse('index_identity', 'The source download index contains an ambiguous resource.');
      seen.add(key);
      partitions[row.state] = (partitions[row.state] || 0) + 1;
      if (!development.has(row.exposure_role) && (row.state !== 'blocked_exposure_role'
        || 'download_path' in row || 'source' in row)) refuse('blocked_role', 'A protected resource has an unowned source download link.');
    }
    if (stable(partitions) !== stable(index.partitions)) refuse('index_identity', 'The source download state counts differ.');
    return {base, manifest, index};
  }
  // Shared metadata survives cancellation of an individual selected download.
  function archive() {
    return archiveRequest ||= loadArchive().catch(error => { archiveRequest = null; throw error; });
  }
  function active(signal) {
    if (signal?.aborted) throw new DOMException('The selected source download was cancelled.', 'AbortError');
  }
  async function download(dataset, version, kind = 'body', {signal} = {}) {
    active(signal);
    if (!nativeId(dataset) || !['current','doi_frozen'].includes(version)) refuse('resource_identity', 'Select one exact native dataset and version.');
    const record = await resource(dataset);
    if (!record || record.dataset_id !== dataset || !ordinary(record.versions?.[version])) refuse('resource_identity', 'The selected native resource is unavailable.');
    if (!development.has(record.exposure_role)) refuse('blocked_role', 'This resource is metadata-only under its declared exposure role.');
    active(signal);
    const publication = await archive(), selected = record.versions[version];
    active(signal);
    const row = publication.index.resources.find(value => value.dataset_id === dataset && value.version === version);
    const statuses = Object.fromEntries(Object.entries(selected).filter(([key]) => key.endsWith('_status')));
    if (!row || ['dataset_id','site_id','collection_unit_id','exposure_role'].some(key => row[key] !== record[key])
      || stable(row.statuses) !== stable(statuses) || stable(row.source ?? null) !== stable(selected.source ?? null)) {
      refuse('resource_identity', 'The selected source version does not match its catalogue identity, role or status.');
    }
    let path, cap;
    if (kind === 'receipt') {
      if (row.source?.source_kind !== 'source_http_attempt' || !digest(row.source.capture_manifest_sha256)
        || !digest(row.source.receipt_sha256)) refuse('source_unavailable', 'No captured HTTP receipt is available for this source version.');
      path = `captures/${row.source.capture_manifest_sha256}/${memberPath(row.source.receipt_file)}`;
      cap = metadataCap;
    } else {
      if (row.state !== 'available_source_entity') refuse('source_unavailable', 'No complete public source entity is available for this version.');
      const source = row.source;
      if (source?.source_kind === 'retained_public_response') {
        path = `captures/retained/dataset-${dataset}-${version}/native.body`;
      } else if (source?.source_kind === 'source_http_attempt' && source.http_status === 200
        && source.body_complete === true && digest(source.capture_manifest_sha256)) {
        path = `captures/${source.capture_manifest_sha256}/${memberPath(source.body_file)}`;
      } else refuse('source_unavailable', 'No complete public source entity is available for this version.');
      if (path !== row.download_path) refuse('resource_identity', 'The source entity path differs from its captured identity.');
      cap = bodyCap;
    }
    const member = fileMember(publication.manifest, path, cap);
    const expectedDigest = kind === 'receipt' ? row.source.receipt_sha256 : row.source.body_sha256;
    if (member.sha256 !== expectedDigest || kind !== 'receipt' && 'body_bytes' in row.source
      && row.source.body_bytes !== member.bytes) refuse('resource_identity', 'The selected source file identity differs from its receipt.');
    active(signal);
    const bytes = await buffer(publication.base, path, member.sha256, member.bytes, cap, signal);
    active(signal);
    return {bytes, filename: path.split('/').at(-1), sha256: member.sha256, dataset_id: dataset, version,
      scientific_admission: 'not_asserted', source: row.source};
  }
  return Object.freeze({body: (dataset, version, options) => download(dataset, version, 'body', options),
    receipt: (dataset, version, options) => download(dataset, version, 'receipt', options)});
}
