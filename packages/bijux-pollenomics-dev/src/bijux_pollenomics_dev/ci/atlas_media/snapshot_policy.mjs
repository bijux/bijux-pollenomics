export function validateSnapshot(snapshot, frame, story, atlasIdentity) {
  if (
    snapshot?.capture_api_version !== 'atlas-capture.v1'
    || snapshot.ready !== true
    || snapshot.build_id !== atlasIdentity.build_id
    || snapshot.scope_slug !== atlasIdentity.scope_slug
    || snapshot.version !== atlasIdentity.version
    || snapshot.basemap !== 'none'
  ) throw new Error('captured atlas identity differs');
  if (JSON.stringify(snapshot.countries) !== JSON.stringify(frame.countries)) throw new Error('captured countries differ');
  for (const field of ['visible_point_count', 'visible_polygon_layer_count', 'visible_polygon_feature_count']) {
    if (!Number.isInteger(snapshot[field]) || snapshot[field] < 0) throw new Error(`captured ${field} is invalid`);
  }
  validateCaptureLayers(snapshot.capture_layers, frame);
  validateCapturePresentation(snapshot.capture_presentation, frame, story, snapshot);
  validateCaptureLayout(snapshot.capture_layout);
  if (frame.story_kind === 'source_chronology') {
    if (snapshot.time_window_bp?.younger_bp !== frame.time_start_bp || snapshot.time_window_bp?.older_bp !== frame.time_end_bp) {
      throw new Error('captured BP interval differs');
    }
    if (snapshot.source_chronology?.level !== frame.source_level) throw new Error('captured source level differs');
    const expectedCode = frame.source_level === 'source_ecological_code' ? frame.source_code : null;
    const expectedTaxon = frame.source_level === 'source_taxon' ? frame.source_taxon : null;
    if (snapshot.source_chronology.source_code !== expectedCode) throw new Error('captured source code differs');
    if (snapshot.source_chronology.source_taxon !== expectedTaxon) throw new Error('captured source taxon differs');
    if (snapshot.modeled_context !== null) throw new Error('source frame exposed modeled context');
    if (snapshot.source_chronology?.facet_node_count !== story.node_count) throw new Error('captured source node denominator differs');
    if (snapshot.source_chronology?.facet_observation_denominator !== story.observation_denominator) {
      throw new Error('captured source observation denominator differs');
    }
    if (
      !Number.isInteger(snapshot.visible_source_chronology_point_count)
      || snapshot.visible_source_chronology_point_count < 0
      || snapshot.visible_source_chronology_point_count > story.node_count
    ) throw new Error('captured source selected-layer visibility differs');
    if (snapshot.source_chronology?.visible_node_count !== snapshot.visible_source_chronology_point_count) {
      throw new Error('captured source visible-node accounting differs');
    }
    const visibleObservations = snapshot.source_chronology?.visible_observation_denominator;
    if (
      visibleObservations !== null
      && (!Number.isInteger(visibleObservations) || visibleObservations < 0 || visibleObservations > story.observation_denominator)
    ) throw new Error('captured source visible-observation accounting differs');
    if (
      (snapshot.visible_source_chronology_point_count === 0 && visibleObservations !== 0)
      || (snapshot.visible_source_chronology_point_count > 0 && (!Number.isInteger(visibleObservations) || visibleObservations <= 0))
    ) throw new Error('captured source visible-observation accounting differs');
    if (snapshot.visible_modeled_no_pollen_data_count !== null) throw new Error('source frame exposed modeled quality counts');
    if (frame.no_pollen_data_count != null) throw new Error('source frame carries modeled quality denominator');
    if (snapshot.visible_modeled_context_feature_count !== 0) {
      throw new Error('source frame exposed modeled selected-layer visibility');
    }
    if (snapshot.visible_point_count !== snapshot.visible_source_chronology_point_count) {
      throw new Error('source frame exposed non-source points');
    }
  }
  if (frame.story_kind === 'modeled_context') {
    if (snapshot.source_chronology !== null) throw new Error('modeled frame exposed source chronology');
    if (snapshot.modeled_context?.window_label !== frame.source_window_label) throw new Error('captured modeled window differs');
    if (snapshot.modeled_context?.metric_family_key !== frame.metric_family_key) throw new Error('captured modeled family differs');
    if (snapshot.modeled_context?.metric_key !== frame.metric_key) throw new Error('captured modeled metric differs');
    if (snapshot.modeled_context?.feature_count !== frame.feature_count) throw new Error('captured modeled feature denominator differs');
    if (snapshot.modeled_context?.no_pollen_data_count !== frame.no_pollen_data_count) {
      throw new Error('captured modeled no-pollen-data denominator differs');
    }
    if (snapshot.visible_modeled_context_feature_count !== frame.feature_count) {
      throw new Error(
        `captured modeled selected-layer visibility differs: expected ${frame.feature_count}, observed ${snapshot.visible_modeled_context_feature_count}`,
      );
    }
    if (snapshot.visible_source_chronology_point_count !== 0) {
      throw new Error(
        `modeled frame exposed source selected-layer visibility: observed ${snapshot.visible_source_chronology_point_count}`,
      );
    }
    if (
      !Number.isSafeInteger(frame.no_pollen_data_count)
      || frame.no_pollen_data_count < 0
      || frame.no_pollen_data_count > frame.feature_count
      || snapshot.visible_modeled_no_pollen_data_count !== frame.no_pollen_data_count
    ) throw new Error('captured modeled no-pollen-data count differs');
    if (snapshot.visible_point_count !== 0) {
      throw new Error(`modeled frame exposed point features: observed ${snapshot.visible_point_count}`);
    }
    if (snapshot.visible_polygon_feature_count < snapshot.visible_modeled_context_feature_count) {
      throw new Error('modeled selected-layer visibility exceeds rendered visibility');
    }
    if (snapshot.modeled_context?.interpolation_allowed !== false || snapshot.modeled_context?.propagation_use_allowed !== false) {
      throw new Error('captured modeled context lost refusal posture');
    }
  }
  if (
    snapshot.scientific_posture?.classifications_status !== 'unavailable'
    || snapshot.scientific_posture?.classifications_reason_code !== 'accepted_scientific_classifications_not_available'
    || snapshot.scientific_posture?.observation_chronology_is_propagation !== false
  ) throw new Error('capture lost exact scientific refusal posture');
  if (snapshot.visible_governed_candidate_count !== 0) throw new Error('capture exposed candidate succession');
}

function validateCaptureLayers(value, frame) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('captured layer inventory is invalid');
  }
  const { active_keys: activeKeys, evidence_layer_key: evidenceLayerKey, orientation_keys: orientationKeys } = value;
  if (
    typeof evidenceLayerKey !== 'string'
    || !evidenceLayerKey
    || !Array.isArray(activeKeys)
    || !Array.isArray(orientationKeys)
    || [...activeKeys, ...orientationKeys].some((key) => typeof key !== 'string' || !key)
  ) throw new Error('captured layer inventory is invalid');
  const sourceLayerKeys = {
    source_sample_presence: 'neotoma-source-sample-pollen-context',
    source_ecological_code: 'neotoma-source-ecological-code',
    source_taxon: 'neotoma-source-exact-taxon',
  };
  const expectedEvidenceLayerKey = frame.story_kind === 'modeled_context'
    ? 'landclim-reveals-temporal-grid'
    : sourceLayerKeys[frame.source_level];
  const expectedOrientationKeys = ['country-boundaries'];
  const expected = [...expectedOrientationKeys, expectedEvidenceLayerKey].sort();
  if (
    new Set(activeKeys).size !== activeKeys.length
    || new Set(orientationKeys).size !== orientationKeys.length
    || orientationKeys.includes(evidenceLayerKey)
    || evidenceLayerKey !== expectedEvidenceLayerKey
    || JSON.stringify(orientationKeys) !== JSON.stringify(expectedOrientationKeys)
    || JSON.stringify(activeKeys) !== JSON.stringify([...activeKeys].sort())
    || JSON.stringify(orientationKeys) !== JSON.stringify([...orientationKeys].sort())
    || JSON.stringify(activeKeys) !== JSON.stringify(expected)
  ) throw new Error('captured layer inventory differs');
}

function validateCapturePresentation(value, frame, story, snapshot) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('captured presentation identity is invalid');
  }
  const expectedFields = [
    'caveat', 'counts_label', 'evidence_role', 'interpolation_allowed', 'key_items',
    'key_labels', 'null_handling', 'propagation_use_allowed', 'role_label', 'schema_version', 'time_label', 'title',
  ];
  if (JSON.stringify(Object.keys(value).sort()) !== JSON.stringify(expectedFields)) {
    throw new Error('captured presentation identity is invalid');
  }
  const expectedRole = frame.story_kind === 'source_chronology' ? 'observation_chronology' : 'modeled_context';
  const expectedTime = `[${frame.time_start_bp}, ${frame.time_end_bp}] BP · oldest → present`;
  const sourceFrame = frame.story_kind === 'source_chronology';
  const expectedRoleLabel = sourceFrame ? 'Observed source chronology' : 'Modeled context · published source window';
  const expectedCaveat = sourceFrame
    ? 'Observed source records only · display clusters are not abundance · no interpolation, flow, or propagation inference.'
    : 'Published modeled cells are context only · no atlas interpolation, flow, or propagation inference.';
  const expectedKeyLabels = sourceFrame
    ? ['source record', 'records grouped at current zoom', 'country boundary']
    : ['0–20%', '>20–40%', '>40–60%', '>60–80%', '>80–100%', 'no pollen data · N/A, not 0', 'country boundary'];
  const expectedCues = sourceFrame
    ? ['point', 'cluster-count', 'line']
    : ['area', 'area', 'area', 'area', 'area', 'area', 'line'];
  const sourceColors = {
    source_sample_presence: ['rgb(180, 83, 9)', 'rgb(120, 53, 15)'],
    source_ecological_code: ['rgb(15, 118, 110)', 'rgb(19, 78, 74)'],
    source_taxon: ['rgb(124, 58, 237)', 'rgb(76, 29, 149)'],
  };
  const expectedSourceColors = sourceColors[frame.source_level];
  const visibleObservations = snapshot.source_chronology?.visible_observation_denominator;
  const expectedCounts = sourceFrame
    ? `${snapshot.visible_source_chronology_point_count}/${story.node_count} governed source nodes in this interval · ${visibleObservations}/${story.observation_denominator} contributing observations`
    : `${frame.feature_count}/${frame.feature_count} published cells visible · ${frame.no_pollen_data_count} explicitly have no pollen data · ${frame.source_window_label}`;
  if (
    value.schema_version !== 'atlas-capture-presentation.v1'
    || value.null_handling !== 'null_not_zero'
    || value.interpolation_allowed !== false
    || value.propagation_use_allowed !== false
    || value.evidence_role !== expectedRole
    || value.role_label !== expectedRoleLabel
    || value.title !== story.title
    || value.time_label !== expectedTime
    || value.counts_label !== expectedCounts
    || JSON.stringify(value.key_labels) !== JSON.stringify(expectedKeyLabels)
    || !Array.isArray(value.key_labels)
    || !Array.isArray(value.key_items)
    || value.key_items.length !== expectedKeyLabels.length
    || value.key_items.some((item, index) => (
      !item || typeof item !== 'object' || Array.isArray(item)
      || JSON.stringify(Object.keys(item).sort()) !== JSON.stringify(['cue', 'fill', 'label', 'stroke'])
      || item.label !== expectedKeyLabels[index]
      || item.cue !== expectedCues[index]
      || [item.fill, item.stroke].some((style) => typeof style !== 'string' || !style.trim())
    ))
    || (sourceFrame && (
      !expectedSourceColors
      || value.key_items[0].fill !== expectedSourceColors[0]
      || value.key_items[0].stroke !== expectedSourceColors[1]
      || value.key_items[1].fill !== expectedSourceColors[0]
      || value.key_items[1].stroke !== expectedSourceColors[1]
    ))
    || value.caveat !== expectedCaveat
  ) throw new Error('captured presentation identity differs');
}

function validateCaptureLayout(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('captured layout evidence is invalid');
  }
  if (
    JSON.stringify(Object.keys(value).sort()) !== JSON.stringify([
      'map_bounded', 'map_height_px', 'map_width_px', 'overlay_bounded',
      'overlay_content_bounded', 'overlay_content_overflow', 'overlay_overlaps_map',
      'overlay_visible', 'scroll_x_px', 'scroll_y_px', 'viewport_height_px',
      'viewport_width_px',
    ])
    || value.overlay_visible !== true
    || value.overlay_bounded !== true
    || value.overlay_content_bounded !== true
    || value.overlay_content_overflow !== false
    || value.overlay_overlaps_map !== false
    || value.map_bounded !== true
    || value.scroll_x_px !== 0
    || value.scroll_y_px !== 0
    || value.viewport_width_px !== 1440
    || value.viewport_height_px !== 900
    || !Number.isInteger(value.map_width_px)
    || !Number.isInteger(value.map_height_px)
    || value.map_width_px < Math.ceil(value.viewport_width_px * 0.65)
    || value.map_width_px > value.viewport_width_px
    || value.map_height_px <= 0
    || value.map_height_px > value.viewport_height_px
  ) throw new Error('captured layout evidence differs');
}
