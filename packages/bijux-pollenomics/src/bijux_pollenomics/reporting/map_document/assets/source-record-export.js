function sourcePollenTableAvailable(table) {
  return Boolean(table && typeof table === 'object' && table.status !== 'unavailable'
    && Array.isArray(table.fields) && Array.isArray(table.records)
    && Number.isInteger(table.record_count) && table.record_count === table.records.length);
}

function sourcePollenExportAvailable(focus) {
  const tabs = focus?.detailTabs;
  return Boolean(focus?.kind === 'point' && focus.recordId
    && sourcePollenTableAvailable(tabs?.pollen_composition)
    && ['sample_id', 'source_value', 'source_unit'].every(field => tabs.pollen_composition.fields.includes(field))
    && sourcePollenTableAvailable(tabs?.chronology)
    && (tabs.chronology.fields.includes('comparability_status') || Object.prototype.hasOwnProperty.call(tabs.chronology.common_fields || {}, 'comparability_status'))
    && sourcePollenTableAvailable(tabs?.samples?.samples)
    && tabs.samples.samples.fields.includes('sample_id')
    && tabs?.provenance && tabs.provenance.status !== 'unavailable');
}

function sourcePollenDecodedTable(table, decodeRow) {
  if (!sourcePollenTableAvailable(table)) throw Error('source_pollen_table_unavailable');
  if (table.fields.some(field => typeof field !== 'string') || new Set(table.fields).size !== table.fields.length) throw Error('source_pollen_table_fields_invalid');
  return {
    record_count: table.record_count,
    records: table.records.map(row => decodeRow(table, row)),
  };
}

function buildSourcePollenRecordExport(focus, selection, decodeRow) {
  if (!sourcePollenExportAvailable(focus)) throw Error('source_pollen_record_export_unavailable');
  const tabs = focus.detailTabs;
  return {
    schema_version: 'source-pollen-record-export.v1',
    record_id: focus.recordId,
    feature_identity: { layer_key: focus.layerKey, feature_key: focus.featureKey },
    title: focus.title,
    selection,
    source_provenance: { ...tabs.provenance },
    record_scope: 'complete_source_record_not_filtered_to_map_time_window',
    temporal_support: {
      chronology_scope: 'all_source_claims_including_contextual_and_refused',
      interval_semantics: tabs.chronology.interval_semantics || null,
      interpolation_allowed: false,
      site_range_is_continuous_support: false,
    },
    source_semantics: {
      unit_policy: 'literal_source_unit_per_observation',
      denominator_policy: 'literal_source_denominator_and_status; null_remains_null',
      aggregation_policy: tabs.pollen_composition.aggregation_posture || 'source_observations_without_reaggregation',
      classification_status: tabs.pollen_composition.classification_status || 'not_asserted',
    },
    samples: sourcePollenDecodedTable(tabs.samples.samples, decodeRow),
    chronology_claims: sourcePollenDecodedTable(tabs.chronology, decodeRow),
    pollen_observations: sourcePollenDecodedTable(tabs.pollen_composition, decodeRow),
    source_variables: sourcePollenTableAvailable(tabs.pollen_composition.variables)
      ? sourcePollenDecodedTable(tabs.pollen_composition.variables, decodeRow) : null,
    collection_units: sourcePollenTableAvailable(tabs.samples.collection_units)
      ? sourcePollenDecodedTable(tabs.samples.collection_units, decodeRow) : null,
    datasets: sourcePollenTableAvailable(tabs.samples.datasets)
      ? sourcePollenDecodedTable(tabs.samples.datasets, decodeRow) : null,
  };
}

function sourcePollenRecordFilename(recordId) {
  return `${String(recordId).replace(/[^A-Za-z0-9._-]+/g, '-')}.pollen-series.json`;
}

function sourceRecordFocusFromHash(params, allowedTabs) {
  const layerKey = params.get('focus_layer');
  const featureKey = params.get('focus_feature');
  const recordId = params.get('focus_record');
  if (!layerKey || !featureKey || !recordId) return null;
  const tab = params.get('focus_tab');
  return { kind: 'point', layerKey, featureKey, recordId, tab: allowedTabs.includes(tab) ? tab : 'overview' };
}

function writeSourceRecordFocusHash(params, focus, tab) {
  if (focus?.kind !== 'point' || !focus.layerKey || !focus.featureKey || !focus.recordId) return;
  params.set('focus_layer', focus.layerKey);
  params.set('focus_feature', focus.featureKey);
  params.set('focus_record', focus.recordId);
  if (tab !== 'overview') params.set('focus_tab', tab);
}
