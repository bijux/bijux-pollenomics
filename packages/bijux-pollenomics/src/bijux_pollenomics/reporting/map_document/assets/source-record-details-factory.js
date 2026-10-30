// Bind the existing source renderers to their owning table and escaping functions.
function createSourceRecordDetails(bindings) {
  const {detailTableShape, decodeDetailTableRow, detailTableText, renderDetailTable, escapeHtml} = bindings;
  if (![detailTableShape, decodeDetailTableRow, detailTableText, renderDetailTable, escapeHtml].every(value => typeof value === 'function')) {
    throw Error('Source detail renderer bindings are unavailable.');
  }
  __SOURCE_RECORD_DETAILS_CONTROLLER__
  return Object.freeze({overview: renderSelectedSourceOverview, samples: renderSourceSampleObservations,
    classification: renderNativeClassificationContext, provenance: renderSourceProvenanceContext});
}
