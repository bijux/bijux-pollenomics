// Ancillary metadata has its own identities and counts, never dataset or sample mass.
function createSourceResourceAncillaryContract(domain, fail) {
  const counts = domain.schema_version === 'atlas-source-resources.v2' ? {
    ancillary_context: null, facet_slots: 'ancillary_slot_count', ancillary_observations: 'ancillary_observation_count',
    linked_occurrences: 'ancillary_linked_occurrence_count', supporting_archives: 'supporting_archive_count', supporting_entries: 'supporting_entry_count'
  } : {};
  const kinds = Object.keys(counts), support = {unit_metadata:'units', reference_tables:'tables', context_resources:'resources', taxon_ancestry:'targets'};
  const isSupport = kind => kind.startsWith('supporting_');
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const native = value => Number.isSafeInteger(value) && value > 0;
  const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
  const literal = value => typeof value === 'string' && value.length > 0 && value.length <= 4096;
  function metadata(value) {
    if (Array.isArray(value)) { value.forEach(metadata); return; }
    if (!object(value)) { if (value !== null && !['string','number','boolean'].includes(typeof value)) fail('non-JSON ancillary metadata'); if (typeof value === 'number' && !Number.isFinite(value)) fail('nonfinite ancillary metadata'); return; }
    for (const [key, item] of Object.entries(value)) {
      if (['native_body','native_payload','body_buffer','href','download_url'].includes(key)) fail('native body or route is outside ancillary metadata');
      if (['entity_body_hashes_verified','source_entity_bodies_verified','body_hashes_verified','native_profiles_verified','native_field_value_verified','source_assessments_replayed','related_resource_graph_complete','current_roles_revalidated','native_source_fields_revalidated','GET_authorized'].includes(key) && item !== false
        || key === 'scientific_admission' && item !== 'not_asserted') fail('ancillary metadata cannot elevate source verification or scientific admission');
      if (key === 'native_entity_bodies_opened' && item !== 0) fail('native bodies are outside metadata');
      metadata(item);
    }
  }
  function valid(kind, identity) {
    if (!kinds.includes(kind) || !literal(identity)) return false;
    if (kind === 'ancillary_context') return identity === 'ancillary';
    if (isSupport(kind)) {
      const [archive,pin,population,ordinal,...extra] = identity.split(':');
      if (!Object.hasOwn(support,archive) || !hash(pin)) return false;
      return kind === 'supporting_archives' ? population === undefined
        : support[archive] === population && /^(0|[1-9][0-9]*)$/.test(ordinal || '') && Number.isSafeInteger(Number(ordinal)) && !extra.length;
    }
    return true;
  }
  // Canonical IDs bound safe ordinals; explicit types prevent string/boolean coercion.
  function identity(kind, row) {
    metadata(row);
    let value;
    if (isSupport(kind)) {
      value = `${row.archive_kind}:${row.archive_manifest_sha256}`;
      if (kind === 'supporting_entries') value += `:${row.population}:${row.row_index}`;
      if (kind === 'supporting_entries' && (typeof row.row_index !== 'number' || !object(row.entry))) fail('supporting metadata row differs');
    } else value = row[{ancillary_context:'record_id',facet_slots:'slot_key',ancillary_observations:'observation_id',linked_occurrences:'occurrence_id'}[kind]];
    if (!valid(kind,value)) fail('ancillary record identity differs');
    if (isSupport(kind) && row.archive_kind === 'taxon_ancestry') {
      const entry = kind === 'supporting_entries', target = entry ? row.entry : row;
      if (target.integrity_scope !== (entry ? 'anchored_selected_metadata_parts_only' : 'SELECTED_RECORDED_TARGETS_ONLY')
        || target.current_roles_revalidated !== false || target.native_source_fields_revalidated !== false
        || target.GET_authorized !== false || target.native_entity_bodies_opened !== 0 || target.scientific_admission !== 'not_asserted') fail('selected ancestry posture differs');
      if (entry && (!['taxon','publication'].includes(target.kind) || !native(target.native_id)
        || target.target_key !== `${target.kind}-${target.native_id}` || !object(target.recorded_node)
        || target.recorded_node.target_kind !== target.kind || ['target_key','native_id'].some(key=>target.recorded_node[key] !== target[key]))) fail('selected ancestry native owner differs');
    }
    if (kind === 'ancillary_context' && (!object(row.source_manifest) || !object(row.summary) || !object(row.provenance))) fail('ancillary context differs');
    if (kind === 'facet_slots' && (!object(row.root_identity) || !['dataset_id','site_id','collection_unit_id'].every(key=>native(row.root_identity[key]))
      || value !== `dataset-${row.root_identity.dataset_id}-facet-${row.facet}-current`)) fail('facet native owner differs');
    if (kind === 'ancillary_observations' && (!['facet','linked'].includes(row.kind) || !object(row.capture_epoch)
      || row.selected_by_default !== false || !hash(row.source_capture_manifest_sha256) || !hash(row.capsule_manifest_sha256)
      || value !== `${row.source_capture_manifest_sha256}:${row.source_entry_pointer}`)) fail('captured observation identity differs');
    return value;
  }
  function index(row) {
    metadata(row);
    if (!valid(row.entity_type,row.record_id)) fail('ancillary index identity differs');
    if (row.entity_type === 'facet_slots' && (!native(row.root_dataset_id) || !native(row.site_id) || !native(row.collection_unit_id)
      || row.record_id !== `dataset-${row.root_dataset_id}-facet-${row.facet}-current`)) fail('facet index owner differs');
    if (row.entity_type === 'ancillary_observations' && (!['facet','linked'].includes(row.kind) || !hash(row.source_capture_manifest_sha256)
      || !object(row.capture_epoch))) fail('observation index kind or epoch differs');
    if (isSupport(row.entity_type)) {
      const expected = `${row.archive_kind}:${row.archive_manifest_sha256}` + (row.entity_type === 'supporting_entries' ? `:${row.population}:${row.row_index}` : '');
      if (row.record_id !== expected || row.entity_type === 'supporting_entries' && typeof row.row_index !== 'number') fail('supporting index identity differs');
    }
  }
  // Match the producer's ancillary_index_entry projection without loading other parts.
  function projection(kind,row,partId) {
    const result={entity_type:kind,record_id:identity(kind,row),part_id:partId};
    const take=(owner,fields)=>{
      if(!object(owner) || fields.some(key=>!Object.hasOwn(owner,key)))fail('indexed source fields are absent');
      return Object.fromEntries(fields.map(key=>[key,owner[key]]));
    };
    const owner=()=>{
      const nativeOwner=take(row.root_identity,['dataset_id','site_id','collection_unit_id','dataset_type']);
      return {root_dataset_id:nativeOwner.dataset_id,site_id:nativeOwner.site_id,
        collection_unit_id:nativeOwner.collection_unit_id,dataset_type:nativeOwner.dataset_type};
    };
    if(kind==='facet_slots')Object.assign(result,owner(),take(row,['facet','current_use_role','coverage_status','current_declared_role']));
    else if(kind==='ancillary_observations') {
      Object.assign(result,take(row,['kind','terminal_status','current_owner_join','current_use_role','source_capture_manifest_sha256','capture_epoch']));
      if(row.kind==='facet')Object.assign(result,owner(),take(row,['facet','facet_key']),{original_role:row.parent_scope_role ?? null});
      else Object.assign(result,{linked_kind:row.identity?.kind,native_id:row.identity?.native_id});
    } else if(kind==='linked_occurrences')Object.assign(result,take(row,['observation_id','current_owner_join','current_use_role']),
      {root_dataset_id:Object.hasOwn(row,'root_dataset_id')?row.root_dataset_id:row.source_proof?.root_dataset_id ?? null});
    else if(isSupport(kind)) {
      Object.assign(result,take(row,['archive_kind','archive_manifest_sha256']));
      if(kind==='supporting_entries')Object.assign(result,take(row,['row_index','population']),{
        source_selectors:Object.fromEntries(Object.entries(row.entry).filter(([key])=>['unit_key','resource_key','table_key','table','site_id','terminal_status'].includes(key) || row.archive_kind==='taxon_ancestry' && ['target_key','kind','native_id'].includes(key))),scope:row.entry.scope ?? null});
    }
    metadata(result);
    return result;
  }
  function same(left,right) {
    if(left===right)return true;
    if(left===null || right===null || typeof left!=='object' || typeof right!=='object' || Array.isArray(left)!==Array.isArray(right))return false;
    const keys=Object.keys(left);
    return keys.length===Object.keys(right).length && keys.every(key=>Object.hasOwn(right,key) && same(left[key],right[key]));
  }
  return Object.freeze({kinds, counts, metadata, valid, identity, index, projection, same});
}
