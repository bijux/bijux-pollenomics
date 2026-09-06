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
  for (const field of ['visible_point_count', 'visible_polygon_layer_count']) {
    if (!Number.isInteger(snapshot[field]) || snapshot[field] < 0) throw new Error(`captured ${field} is invalid`);
  }
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
    if (snapshot.visible_modeled_context_feature_count !== 0) {
      throw new Error('source frame exposed modeled selected-layer visibility');
    }
    if (snapshot.visible_point_count + snapshot.visible_polygon_layer_count < snapshot.visible_source_chronology_point_count) {
      throw new Error('source selected-layer visibility exceeds rendered visibility');
    }
  }
  if (frame.story_kind === 'modeled_context') {
    if (snapshot.source_chronology !== null) throw new Error('modeled frame exposed source chronology');
    if (snapshot.modeled_context?.window_label !== frame.source_window_label) throw new Error('captured modeled window differs');
    if (snapshot.modeled_context?.metric_family_key !== frame.metric_family_key) throw new Error('captured modeled family differs');
    if (snapshot.modeled_context?.metric_key !== frame.metric_key) throw new Error('captured modeled metric differs');
    if (snapshot.modeled_context?.feature_count !== frame.feature_count) throw new Error('captured modeled feature denominator differs');
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
    if (snapshot.visible_point_count + snapshot.visible_polygon_layer_count < snapshot.visible_modeled_context_feature_count) {
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
