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
  const transformations = renderSourceTransformationContext(tabs);
  const table = family === 'neotoma' ? tabs.samples?.datasets
    : family === 'sead' ? tabs.pollen_composition?.dataset_semantics : null;
  try {
    if (!['neotoma','sead'].includes(family)) throw Error('unsupported source');
    const datasets = sourceRecordRows(table,family === 'neotoma' ? ['dataset_id','source_payload'] : ['dataset_id']);
    const providerLink = row => {
      const id = row.source_dataset_id;
      if (!Number.isSafeInteger(id) || id <= 0 || row.source_payload?.datasetid !== id
        || row.dataset_id !== `neotoma:dataset:${id}`
        || datasets.filter(candidate => candidate.source_dataset_id === id).length !== 1
        || datasets.filter(candidate => candidate.dataset_id === row.dataset_id).length !== 1) return '<p>Current provider dataset JSON link is unavailable: native dataset identities are missing, unsafe, inconsistent or ambiguous.</p>';
      const url = `https://api.neotomadb.org/v2.0/data/downloads/${id}`;
      return `<p><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Current provider dataset JSON</a> for ${escapeHtml(row.dataset_id)}.</p>`;
    };
    const citations = family === 'neotoma' ? datasets.map(row => {
      const payload = row.source_payload;
      const native = key => payload && typeof payload === 'object' && !Array.isArray(payload) && Object.hasOwn(payload,key) ? payload[key] : undefined;
      return `<article><h4>Native dataset ${escapeHtml(detailTableText(row.dataset_id))}</h4>${sourceRecordFields([
        ['Dataset DOI values as reported',native('doi')],['Dataset investigators as reported',native('datasetpi')],
        ['Constituent database',native('database')],['Dataset notes',native('datasetnotes')],
      ])}${providerLink(row)}</article>`;
    }).join('') : '<p>SEAD dataset semantics are available below; primary publication citations are not exposed by this dataset table.</p>';
    const navigation = family === 'neotoma' ? '<p>Current provider data may differ from the retained source snapshot. These links do not retrieve the retained serialized archive; that archive is not the original HTTP response bytes.</p>' : '';
    return `<section aria-label="Source dataset metadata">${heading}${citations}${navigation}<p>Native metadata and the original dataset table are retained without selecting, merging or normalizing citation alternatives. A dataset DOI alone is not a full primary publication citation or a rights decision. Missing, source-null and empty citation values remain distinct; captured publication records require a separate qualified join and capture identity.</p>${renderDetailTable(table,'provenance.datasets')}${family === 'neotoma' ? renderCapturedSourcePublications(tabs) : ''}${transformations}<p>Source identities, digests, schema tags and record locators are retained in this tab where supplied. Record and part locators identify the preserved evidence named there; they do not establish a complete original-acquisition or transformation chain. No transformation history is invented here. Supplied transformation fields remain unchanged in Chronology.</p></section>`;
  } catch (error) {
    return `<section aria-label="Source dataset metadata">${heading}<p>Dataset citation context is unavailable for source family ${escapeHtml(detailTableText(family))}. Existing provenance remains available; missing citation metadata is not a claim that the original source is externally unavailable.</p>${transformations}</section>`;
  }
}
function renderSourceTransformationContext(tabs) {
  const family = tabs?.overview?.source_family, heading = '<h3>Supplied source transformations</h3>';
  const unavailable = reason => `<section aria-label="Supplied source transformations">${heading}<p>${escapeHtml(reason)}</p></section>`;
  if (family !== 'sead') return unavailable(`A per-record transformation table is not supplied for source family ${detailTableText(family)}. Source identities and locators do not imply an unavailable processing history.`);
  try {
    const table = tabs.chronology, rows = sourceRecordRows(table,['chronology_claim_id','source_age_value','source_age_unit','younger_bp','older_bp','original_interval_orientation','selection_rule_version','source_relation_path','reason_codes']);
    if (rows.some(row => row.source_family !== 'sead' || !Object.hasOwn(row,'provenance_record_id'))) throw Error('source claim context unavailable');
    if (rows.some(row => row.transformation_id != null && typeof row.transformation_id !== 'string')) throw Error('invalid transformation identity');
    const supplied = rows.filter(row => typeof row.transformation_id === 'string' && row.transformation_id.trim());
    const absent = rows.filter(row => row.transformation_id === undefined).length;
    const nullable = rows.filter(row => row.transformation_id === null).length;
    const empty = rows.length - supplied.length - absent - nullable;
    const ids = [...new Set(supplied.map(row => row.transformation_id))];
    return `<section aria-label="Supplied source transformations">${heading}<p>${rows.length} chronology claims; ${supplied.length} with an explicit transformation ID, ${absent} with no supplied field, ${nullable} with source-null ID and ${empty} with an empty ID. Missing IDs do not establish that no processing occurred.</p><p>Provided IDs: ${escapeHtml(ids.length ? ids.join('; ') : 'None supplied')}. IDs and selection-rule versions are shown as supplied, without inferring an operation from an unknown identifier. Source age values retain their reported units and endpoint orientation; younger BP and older BP columns retain the supplied normalized bounds. No conversion is performed in this view. Relation paths, provenance locators, qualification and refusal reasons remain attached to every claim; this is not a complete transformation ledger or an analysis-chronology selection.</p>${renderDetailTable(table,'provenance.transformations')}</section>`;
  } catch (error) {
    return unavailable('SEAD transformation context is unavailable or cannot be decoded consistently. Original chronology and provenance remain available.');
  }
}
function renderCapturedSourcePublications(tabs) {
  const heading = '<h4>Separately captured provider publications</h4>', capture = tabs.provenance?.publication_capture;
  if (!capture) return `${heading}<p>Provider publication records are unavailable: no separate publication capture is configured.</p>`;
  try {
    if (capture.epoch_posture !== 'separate_provider_capture_not_original_pollen_snapshot') throw Error('capture epoch unavailable');
    sourceRecordRows(capture.datasets,['dataset_id','status','publication_count','source_primary_count','request_url','retrieved_at_utc','response_sha256','response_byte_count']);
    const publications = sourceRecordRows(capture.publications,['dataset_id','publication_id','source_primary_flag','source_payload']);
    const citations = publications.map(row => `<article><h5>${escapeHtml(detailTableText(row.dataset_id))}, publication ${escapeHtml(detailTableText(row.publication_id))}</h5>${sourceRecordFields([['Citation as reported',row.source_payload?.citation],['Title as reported',row.source_payload?.articletitle],['Authors as reported',row.source_payload?.author],['Year as reported',row.source_payload?.year],['Provider primary flag',row.source_primary_flag]])}</article>`).join('');
    return `${heading}<p>These native bibliography records were captured separately from the original pollen snapshot. Per-dataset retrieval dates, request URLs and response identities are retained below. A provider primary flag is a source designation only; null, false, multiple primaries and no linked publication remain distinct. Uncaptured datasets are not failed publication searches. No reviewed citation choice, full-paper access, rights decision or scientific admission follows.</p>${sourceRecordFields([['Publication capture source',capture.source_id],['Publication capture manifest SHA-256',capture.manifest_sha256]])}${citations}${renderDetailTable(capture.datasets,'provenance.publication_datasets')}${renderDetailTable(capture.publications,'provenance.publications')}`;
  } catch (error) {
    return `${heading}<p>Separate provider publication metadata is unavailable or cannot be decoded consistently. Original source dataset metadata remains available.</p>`;
  }
}
