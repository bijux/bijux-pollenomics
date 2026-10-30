// Export published selection rows; transport authentication and selection stay with their owners.
function atlasSelectionExportJson(value) {
  return JSON.stringify(value, (_key, item) => {
    if (typeof item === 'number' && !Number.isFinite(item)
      || ['undefined', 'function', 'symbol', 'bigint'].includes(typeof item)) {
      throw Error('Current selection export contains a value that JSON cannot preserve.');
    }
    return item;
  });
}

async function prepareAtlasSelectionExport(owner) {
  // snapshot includes current capture, shared selection, display and generation.
  // readAsset exposes only authenticated node chunks; layerForAsset returns the
  // original provenance layer, without hydrated feature arrays. Existing host
  // predicates own asset/feature selection and uncapped endpoint eligibility.
  const refuse = reason => { throw Error(`Current selection export unavailable: ${reason}`); };
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const integer = (value, label) => {
    if (!Number.isSafeInteger(value) || value < 0) refuse(`${label} is invalid.`);
    return value;
  };
  const callbacks = ['snapshot', 'assetNeeded', 'isLoaded', 'loadAsset', 'readAsset',
    'layerForAsset', 'featureSelected', 'relations', 'endpointEligible'];
  if (!object(owner) || callbacks.some(key => typeof owner[key] !== 'function')) refuse('selection owners are missing.');
  const bootstrap = owner.bootstrap;
  if (!object(bootstrap) || !['atlas-static-bootstrap.v2', 'atlas-static-bootstrap.v3'].includes(bootstrap.schema_version)
    || !['build_id', 'scope_slug', 'version'].every(key => typeof bootstrap[key] === 'string' && bootstrap[key])
    || !Array.isArray(bootstrap.assets) || bootstrap.assets.some(row => !object(row))
    || !object(bootstrap.budgets)) refuse('published static identity is missing.');
  const snapshotText = atlasSelectionExportJson(owner.snapshot());
  const snapshot = JSON.parse(snapshotText);
  const current = () => {
    if (!object(snapshot) || snapshot.ready !== true
      || !['build_id', 'scope_slug', 'version'].every(key => snapshot[key] === bootstrap[key])
      || atlasSelectionExportJson(owner.snapshot()) !== snapshotText) refuse('the build, filters or display changed; request the selection again.');
  };
  current();
  const requestLimit = integer(bootstrap.budgets.interaction_max_requests, 'interaction request budget');
  const byteLimit = integer(bootstrap.budgets.interaction_max_bytes, 'interaction byte budget');
  const chunkLimit = integer(bootstrap.budgets.chunk_max_bytes, 'decoded chunk budget');
  const overhead = owner.transportOverhead === undefined ? {request_count: 0, byte_count: 0} : owner.transportOverhead;
  if (!object(overhead) || Object.keys(overhead).sort().join('|') !== 'byte_count|request_count') refuse('transport overhead is invalid.');
  const overheadRequests = integer(overhead.request_count, 'transport overhead request count');
  const overheadBytes = integer(overhead.byte_count, 'transport overhead byte count');
  const assets = bootstrap.assets.filter(row => row.domain === 'nodes' && owner.assetNeeded(row));
  if (new Set(assets.map(row => row.asset_key)).size !== assets.length) refuse('selected asset identities are repeated.');
  let decodedBytes = 0;
  for (const row of assets) {
    if (!object(row) || typeof row.asset_key !== 'string' || !row.asset_key
      || !['point', 'polygon'].includes(row.layer_kind)) refuse('selected node metadata is invalid.');
    const size = row.decoded_byte_count === undefined ? chunkLimit : integer(row.decoded_byte_count, 'decoded asset size');
    if (size > chunkLimit) refuse('a selected asset exceeds its decoded chunk budget.');
    decodedBytes += size;
    if (!Number.isSafeInteger(decodedBytes) || decodedBytes > byteLimit) refuse('complete selected assets exceed the interaction byte budget. Narrow the filters.');
  }
  const missing = assets.filter(row => !owner.isLoaded(row));
  const requestBytes = overheadBytes + missing.reduce((total, row) => total + integer(row.byte_count, 'asset byte count'), 0);
  const requests = overheadRequests + missing.length;
  if (!Number.isSafeInteger(requests) || requests > requestLimit || !Number.isSafeInteger(requestBytes) || requestBytes > byteLimit) {
    refuse('complete selected assets exceed the interaction request or byte budget. Narrow the filters.');
  }
  const outcomes = await Promise.allSettled(missing.map(row => Promise.resolve().then(() => owner.loadAsset(row))));
  current();
  if (outcomes.some(result => result.status === 'rejected')) refuse('a selected asset failed loading or authentication; no partial download was produced.');
  const layers = [], entries = [], literalIds = new Set();
  let inspected = 0, selected = 0, pointCount = 0, polygonCount = 0, identifiedRows = 0;
  const groups = new Map();
  for (const row of assets) {
    if (owner.isLoaded(row) !== true) refuse('a selected asset was not authenticated.');
    const payload = owner.readAsset(row), metadata = owner.layerForAsset(row);
    if (!object(payload) || !object(metadata) || metadata.key !== row.layer_key
      || Object.hasOwn(metadata, 'features') || Object.hasOwn(metadata.geojson || {}, 'features')
      || payload.asset_key !== row.asset_key || payload.build_id !== bootstrap.build_id
      || payload.scope_slug !== bootstrap.scope_slug || payload.version !== bootstrap.version
      || payload.layer_key !== row.layer_key || payload.layer_index !== row.layer_index || payload.layer_kind !== row.layer_kind
      || !Array.isArray(payload.features) || !Array.isArray(payload.feature_indexes)
      || payload.features.length !== integer(row.record_count, 'asset row count')
      || payload.feature_indexes.length !== payload.features.length) refuse('a selected decoded asset or layer is missing or inconsistent.');
    const key = `${row.layer_kind}:${row.layer_index}`;
    let group = groups.get(key);
    if (!group) {
      group = {layer_index: row.layer_index, layer_key: row.layer_key, layer_kind: row.layer_kind, metadata, records: []};
      groups.set(key, group); layers.push(group);
    } else if (group.layer_key !== row.layer_key || atlasSelectionExportJson(group.metadata) !== atlasSelectionExportJson(metadata)) {
      refuse('selected layer identities disagree.');
    }
    payload.features.forEach((feature, index) => {
      if (!object(feature)) refuse('a decoded public row is invalid.');
      const featureIndex = integer(payload.feature_indexes[index], 'published feature index');
      inspected++;
      if (!owner.featureSelected(metadata, feature, row.layer_kind)) return;
      group.records.push({asset_key: row.asset_key, feature_index: featureIndex, feature});
      selected++;
      if (row.layer_kind === 'point') pointCount++;
      else polygonCount++;
      const id = row.layer_kind === 'point' ? feature.record_id : feature.properties?.record_id;
      if (typeof id === 'string' && id) { identifiedRows++; literalIds.add(id); }
    });
  }
  layers.sort((left, right) => left.layer_index - right.layer_index);
  for (const layer of layers) {
    layer.records.sort((left, right) => left.feature_index - right.feature_index);
    if (layer.layer_kind === 'point') layer.records.forEach(row => entries.push({layer: layer.metadata, feature: row.feature}));
  }
  const relations = owner.relations();
  if (!object(relations) || !Array.isArray(relations.records)
    || integer(relations.retained_count, 'retained relation count') < relations.records.length
    || relations.records.some(row => !object(row))) refuse('retained relation selection is unavailable.');
  const eligibility = relations.records.map((edge, index) => {
    const eligible = owner.endpointEligible(edge, entries);
    if (typeof eligible !== 'boolean') refuse('relation endpoint eligibility is unavailable.');
    return {relation_index: index, endpoint_eligible: eligible};
  });
  const counts = {
    selected_node_assets: assets.length, authenticated_cached_node_assets: assets.length - missing.length,
    newly_loaded_node_assets: missing.length, inspected_public_rows: inspected, selected_public_rows: selected,
    point_rows: pointCount, polygon_rows: polygonCount, rows_with_literal_record_id: identifiedRows,
    unique_literal_record_ids: literalIds.size, retained_relation_rows: relations.retained_count,
    selected_relation_rows: relations.records.length,
    unique_literal_edge_ids: new Set(relations.records.map(row => row.edge_id).filter(id => typeof id === 'string' && id)).size,
    endpoint_eligible_relation_rows: eligibility.filter(row => row.endpoint_eligible).length,
  };
  current();
  const payload = {
    schema_version: 'atlas-selection-export.v1', snapshot, counts,
    scope: {
      nodes: 'complete_public_rows_matching_existing_selection_without_viewport_pruning',
      relations: 'complete_retained_rows_matching_relation_country_signal_filters_before_endpoint_time_layer_viewport_display_eligibility',
      endpoint_eligibility: 'existing_endpoint_selector_on_complete_selected_point_rows_without_viewport_or_primitive_cap',
      drawing_mode_filters_rows: false, source_series_included: false,
      unit_policy: 'literal_public_fields_without_conversion_or_cross_unit_aggregation',
      scientific_admission: 'not_asserted', rights_approval: 'not_asserted',
    },
    layers, relations: {records: relations.records, endpoint_eligibility: eligibility},
  };
  const text = atlasSelectionExportJson(payload) + '\n';
  const byteCount = new TextEncoder().encode(text).byteLength;
  if (byteCount > byteLimit) refuse('the complete JSON exceeds the interaction byte budget. Narrow the filters.');
  current();
  return Object.freeze({text, byte_count: byteCount, counts: Object.freeze(counts)});
}
