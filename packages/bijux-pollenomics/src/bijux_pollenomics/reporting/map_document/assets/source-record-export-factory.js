// Bind source export to the same table admission and decoder as its visible drawer.
function createSourceRecordExport(bindings) {
  const {tableAvailable:sourcePollenTableAvailable,exportAvailable:sourcePollenExportAvailable,decodeRow} = bindings;
  if (![sourcePollenTableAvailable,sourcePollenExportAvailable,decodeRow].every(value => typeof value === 'function')) throw Error('Source record export bindings are unavailable.');
  function sourcePollenDecodedTable(table, decodeRow) {
    if (!sourcePollenTableAvailable(table)) throw Error('source_pollen_table_unavailable');
    if (table.fields.some(field => typeof field !== 'string') || new Set(table.fields).size !== table.fields.length) throw Error('source_pollen_table_fields_invalid');
    return {
      record_count: table.record_count,
      records: table.records.map(row => decodeRow(table, row)),
    };
  }

  function sourcePollenChronologyMetadata(table, surface, decodeRow) {
    if (table === undefined) return {status:'unavailable', reason_code:`source_${surface}_surface_not_available`};
    if (table?.status === 'unavailable') return {...table};
    return {
      ...sourcePollenDecodedTable(table, decodeRow),
      ...(Object.hasOwn(table, 'source_locator_contract') ? {source_locator_contract:table.source_locator_contract} : {}),
    };
  }

  function sourcePollenChronologyIssues(issues) {
    if (issues == null) return {status:'unavailable', reason_code:'source_chronology_issues_not_available'};
    if (typeof issues !== 'object' || Array.isArray(issues)) throw Error('source_chronology_issues_invalid');
    if (issues.status === 'unavailable') return {...issues};
    const {conflicts, orphans, chronology_control_variants, ...metadata} = issues;
    return {
      ...metadata,
      conflicts: sourcePollenChronologyMetadata(conflicts, 'conflicts', decodeRow),
      orphans: sourcePollenChronologyMetadata(orphans, 'orphans', decodeRow),
      chronology_control_variants: sourcePollenChronologyMetadata(chronology_control_variants, 'chronology_control_variants', decodeRow),
    };
  }

  function buildSourcePollenRecordExport(focus, selection) {
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
        model_metadata_posture: tabs.chronology.model_metadata_posture || null,
        ...(Object.hasOwn(tabs.chronology, 'reference_verification_posture') ? {reference_verification_posture:tabs.chronology.reference_verification_posture} : {}),
      },
      source_semantics: {
        unit_policy: 'literal_source_unit_per_observation',
        denominator_policy: 'literal_source_denominator_and_status; null_remains_null',
        aggregation_policy: tabs.pollen_composition.aggregation_posture || 'source_observations_without_reaggregation',
        classification_status: tabs.pollen_composition.classification_status || 'not_asserted',
      },
      samples: sourcePollenDecodedTable(tabs.samples.samples, decodeRow),
      chronology_claims: sourcePollenDecodedTable(tabs.chronology, decodeRow),
      source_chronology_models: sourcePollenChronologyMetadata(tabs.chronology.models, 'chronologies', decodeRow),
      source_chronology_controls: sourcePollenChronologyMetadata(tabs.chronology.controls, 'chronology_controls', decodeRow),
      source_chronology_issues: sourcePollenChronologyIssues(tabs.chronology.source_issues),
      pollen_observations: sourcePollenDecodedTable(tabs.pollen_composition, decodeRow),
      source_variables: sourcePollenTableAvailable(tabs.pollen_composition.variables)
        ? sourcePollenDecodedTable(tabs.pollen_composition.variables, decodeRow) : null,
      collection_units: sourcePollenTableAvailable(tabs.samples.collection_units)
        ? sourcePollenDecodedTable(tabs.samples.collection_units, decodeRow) : null,
      datasets: sourcePollenTableAvailable(tabs.samples.datasets)
        ? sourcePollenDecodedTable(tabs.samples.datasets, decodeRow) : null,
    };
  }

  return buildSourcePollenRecordExport;
}
