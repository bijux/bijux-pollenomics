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
