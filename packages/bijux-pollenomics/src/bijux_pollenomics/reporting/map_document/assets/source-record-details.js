// Source relationships and assertions are display context, not analysis admission.
function sourceRecordRows(table, required) {
  if (!detailTableShape(table) || table.record_count !== table.records.length
    || new Set(table.fields).size !== table.fields.length
    || required.some(field => !table.fields.includes(field))) throw Error('source table unavailable');
  return table.records.map(row => decodeDetailTableRow(table,row));
}
function sourceRecordFields(rows) {
  return rows.map(([label,value]) => `<div class="focus-detail-row"><span class="focus-detail-key">${escapeHtml(label)}</span><span>${escapeHtml(detailTableText(value))}</span></div>`).join('');
}
function renderSelectedSourceOverview(tabs, feature) {
  const unavailable = reason => `<section aria-label="Selected source record" data-source-record-details="unavailable"><h3>Selected source record</h3><p>${escapeHtml(reason)} Original source tables remain available.</p></section>`;
  const identifier = value => typeof value === 'string' && value.trim() && value === value.trim();
  if (tabs?.overview?.source_family !== 'neotoma' || feature?.source_family !== 'neotoma') return unavailable('Selected sample metadata is supported for Neotoma source features only.');
  if (![feature.record_id,feature.source_record_id,feature.source_snapshot_id,feature.build_id,
    tabs.overview.site_id,tabs.provenance?.source_snapshot_id,tabs.provenance?.build_id].every(identifier)
    || feature.record_id !== tabs.overview.site_id
    || feature.source_snapshot_id !== tabs.provenance.source_snapshot_id
    || feature.build_id !== tabs.provenance.build_id) return unavailable('Selected feature and detail site or source epoch do not agree.');
  if (!Number.isFinite(feature.latitude) || !Number.isFinite(feature.longitude)
    || Math.abs(feature.latitude) > 90 || Math.abs(feature.longitude) > 180) return unavailable('Selected feature representative coordinates are unavailable or outside geographic bounds.');
  try {
    const samples = sourceRecordRows(tabs.samples?.samples,['sample_id','dataset_id','collection_unit_id']);
    const datasets = sourceRecordRows(tabs.samples?.datasets,['dataset_id','collection_unit_id']);
    const units = sourceRecordRows(tabs.samples?.collection_units,['collection_unit_id']);
    const matching = samples.filter(row => row.sample_id === feature.source_record_id);
    if (matching.length !== 1) return unavailable('Selected native sample identity is missing or ambiguous.');
    const sample = matching[0];
    if (![sample.dataset_id,sample.collection_unit_id].every(identifier)) return unavailable('Selected sample dataset or collection identity is unavailable.');
    const dataset = datasets.filter(row => row.dataset_id === sample.dataset_id);
    if (dataset.length !== 1 || dataset[0].collection_unit_id !== sample.collection_unit_id
      || units.filter(row => row.collection_unit_id === sample.collection_unit_id).length !== 1) return unavailable('Selected sample dataset and collection relationships do not reconcile uniquely.');
    let claim = null, reason = 'The selected map age claim has no exact unique sample, dataset, collection and chronology join.';
    try {
      const claims = sourceRecordRows(tabs.chronology,['chronology_claim_id','subject_type','subject_id','source_record_id','dataset_id','collection_unit_id','chronology_id']);
      const matchingClaims = identifier(feature.chronology_claim_id) ? claims.filter(row => row.chronology_claim_id === feature.chronology_claim_id) : [];
      if (matchingClaims.length === 1) {
        const candidate = matchingClaims[0];
        if (candidate.subject_type === 'sample' && candidate.subject_id === sample.sample_id
          && candidate.source_record_id === sample.sample_id && candidate.dataset_id === sample.dataset_id
          && candidate.collection_unit_id === sample.collection_unit_id
          && candidate.chronology_id === feature.chronology_id) claim = candidate;
      }
    } catch (error) {
      reason = 'Source age claims are unavailable or cannot be decoded consistently.';
    }
    const refused = claim && (claim.comparability_status === 'refused' || Boolean(claim.refusal_reason));
    const status = !claim ? 'unmatched' : refused ? 'refused' : 'matched';
    const fields = [
      ['Source site ID',feature.record_id],['Native sample ID',sample.sample_id],
      ['Native dataset ID',sample.dataset_id],['Native collection-unit ID',sample.collection_unit_id],
      ['Source snapshot',feature.source_snapshot_id],['Source build',feature.build_id],
      ['Latitude',feature.latitude],['Longitude',feature.longitude],['Coordinate quality',feature.coordinate_quality],
      ['Source measurement unit',feature.source_unit],['Map age claim ID',feature.chronology_claim_id],
      ['Map chronology ID',feature.chronology_id],['Map chronology name',feature.chronology_name],
      ['Map source-default assertion',feature.is_default_chronology],
      ['Source chronology selection posture',feature.chronology_selection_posture],
      ['Candidate-generation status',feature.candidate_generation_status],
      ['Candidate refusal reason',feature.candidate_refusal_reason],['Propagation eligible',feature.propagation_eligible],
    ];
    if (claim) fields.push(
      ['Age-claim default flag',claim.is_default_chronology],['Source age type',claim.source_age_type],
      ['Source age unit',claim.source_age_unit],['Source age value',claim.source_age_value],
      ['Source younger endpoint',claim.source_age_younger],['Source older endpoint',claim.source_age_older],
      ['Age comparability status',claim.comparability_status],['Age refusal reason',claim.refusal_reason],
    );
    return `<section aria-label="Selected source record" data-source-record-details="${status}"><h3>Selected source record</h3><p>${!claim ? escapeHtml(reason) : refused ? 'The uniquely joined source age claim is refused; its values remain source context.' : 'One exact source sample and age claim are joined.'}</p>${sourceRecordFields(fields)}<p>Coordinates are source representative positions with the stated quality; that quality is not a numerical uncertainty estimate. Age values retain their reported units. Source-default flags and source selection posture do not select an analysis chronology. No age conversion, fitted age model, physical-core equivalence, ecological mapping or propagation admission is introduced. All source claims remain in the Chronology tab.</p></section>`;
  } catch (error) {
    return unavailable('Selected sample source tables are unavailable or cannot be decoded consistently.');
  }
}
function renderSourceSampleObservations(tabs) {
  const unavailable = reason => `<section aria-label="Sample source observations"><h3>Sample source observations</h3><p>${escapeHtml(reason)}</p></section>`;
  if (tabs?.overview?.source_family !== 'neotoma') return unavailable(`Sample observation values are not available through this view for source family ${detailTableText(tabs?.overview?.source_family)}.`);
  const table = tabs.pollen_composition;
  if (!detailTableShape(table) || ['observation_id','sample_id','source_value','source_unit','source_denominator','denominator_status','detection_status'].some(field => !table.fields.includes(field))) return unavailable('Neotoma sample observation values or measurement metadata are unavailable.');
  return `<section aria-label="Sample source observations"><h3>Sample source observations</h3><p>Original site-wide source observations, linked by native sample and observation IDs. Values, units, denominators and missingness are retained as reported; source null is not zero. No cross-unit sum, inferred percentage or vegetation reconstruction is made. This is the same observation table available in Pollen/composition.</p>${renderDetailTable(table,'samples.observations')}</section>`;
}
function renderNativeClassificationContext(tabs) {
  const family = tabs?.overview?.source_family;
  const table = family === 'neotoma' ? tabs.pollen_composition?.variables
    : family === 'sead' ? tabs.pollen_composition?.taxa : null;
  const required = family === 'neotoma' ? ['variable_id','source_taxon_id','source_reported_name','source_semantics']
    : ['taxon_relation_id','taxon_id','source_ecocodes','derived_classification_status'];
  const heading = '<h3>Native classification context</h3>';
  try {
    if (!['neotoma','sead'].includes(family)) throw Error('unsupported source');
    sourceRecordRows(table,required);
    return `<section aria-label="Native classification context">${heading}<p>Literal source names, taxon identities, group codes and element semantics only. Multiple reported codes or semantics are retained together; they do not establish accepted normalized names, memberships, crosswalk versions, review evidence or a ranking of alternatives. Per-observation codes and missingness remain in Samples and Pollen/composition. Accepted classification status is shown separately.</p>${renderDetailTable(table,'classification.native_context')}</section>`;
  } catch (error) {
    return `<section aria-label="Native classification context">${heading}<p>Native classification context is unavailable for source family ${escapeHtml(detailTableText(family))}: the supported native taxon table is not available. This does not establish an accepted classification.</p></section>`;
  }
}
function renderSourceProvenanceContext(tabs) {
  const family = tabs?.overview?.source_family, heading = '<h3>Source dataset metadata</h3>';
  const table = family === 'neotoma' ? tabs.samples?.datasets
    : family === 'sead' ? tabs.pollen_composition?.dataset_semantics : null;
  try {
    if (!['neotoma','sead'].includes(family)) throw Error('unsupported source');
    const datasets = sourceRecordRows(table,family === 'neotoma' ? ['dataset_id','source_payload'] : ['dataset_id']);
    const citations = family === 'neotoma' ? datasets.map(row => {
      const payload = row.source_payload;
      const native = key => payload && typeof payload === 'object' && !Array.isArray(payload) && Object.hasOwn(payload,key) ? payload[key] : undefined;
      return `<article><h4>Native dataset ${escapeHtml(detailTableText(row.dataset_id))}</h4>${sourceRecordFields([
        ['Dataset DOI values as reported',native('doi')],['Dataset investigators as reported',native('datasetpi')],
        ['Constituent database',native('database')],['Dataset notes',native('datasetnotes')],
      ])}</article>`;
    }).join('') : '<p>SEAD dataset semantics are available below; primary publication citations are not exposed by this dataset table.</p>';
    return `<section aria-label="Source dataset metadata">${heading}${citations}<p>Native metadata and the original dataset table are retained without selecting, merging or normalizing citation alternatives. A dataset DOI alone is not a full primary publication citation or a rights decision. Missing, source-null and empty citation values remain distinct; captured publication records require a separate qualified join before display.</p>${renderDetailTable(table,'provenance.datasets')}<p>Source identities, digests, schema tags and record locators are retained in this tab where supplied. Record and part locators identify the preserved evidence named there; they do not establish a complete original-acquisition or transformation chain. No transformation history is invented here. Source-specific transformation fields remain in Chronology where supplied.</p></section>`;
  } catch (error) {
    return `<section aria-label="Source dataset metadata">${heading}<p>Dataset citation context is unavailable for source family ${escapeHtml(detailTableText(family))}. Existing provenance remains available; missing citation metadata is not a claim that the original source is externally unavailable.</p></section>`;
  }
}
