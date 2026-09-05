from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from .support import run_node_json, template_block


def test_browser_coordinates_and_counts_preserve_missing_values() -> None:
    helpers = template_block("function finiteTimeValue", "function featureTimeWindow")
    observed = run_node_json(
        helpers
        + """
console.log(JSON.stringify({
  missingPair: featureCoordinatePair({latitude:null, longitude:18}),
  zeroPair: featureCoordinatePair({latitude:0, longitude:'0'}),
  booleanPair: featureCoordinatePair({latitude:false, longitude:18}),
  impossiblePair: featureCoordinatePair({latitude:91, longitude:18}),
  missingLabel: coordinateLabel({latitude:null, longitude:null}, 6),
  zeroLabel: coordinateLabel({latitude:0, longitude:0}, 6),
  missingCount: countDisplayValue(null, null),
  zeroCount: countDisplayValue(0, null),
  invalidCount: countDisplayValue('nan', ''),
  missingMapped: mappedPointCountLabel(undefined),
  zeroMapped: mappedPointCountLabel(0),
  popupValues: availablePopupRows([
    {label:'zero',value:0}, {label:'missing',value:null},
    {label:'blank',value:'  '}, {label:'false',value:false},
  ]).map((row) => row.value),
}));
"""
    )

    assert observed == {
        "missingPair": None,
        "zeroPair": {"latitude": 0, "longitude": 0},
        "booleanPair": None,
        "impossiblePair": None,
        "missingLabel": "Unavailable",
        "zeroLabel": "0.000000, 0.000000",
        "missingCount": "Unavailable",
        "zeroCount": "0",
        "invalidCount": "Unavailable",
        "missingMapped": "mapped count unavailable",
        "zeroMapped": "0 mapped points",
        "popupValues": [0, False],
    }


def test_invalid_point_coordinates_are_refused_before_leaflet_rendering() -> None:
    assert "&& featureCoordinatePair(feature) !== null" in MAP_DOCUMENT_TEMPLATE
    assert "const latLng = [coordinates.latitude, coordinates.longitude]" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "Number(feature.latitude)" not in MAP_DOCUMENT_TEMPLATE
    assert "Number(entry.feature.latitude)" not in MAP_DOCUMENT_TEMPLATE
    assert "Number(feature.longitude)" not in MAP_DOCUMENT_TEMPLATE
    assert "Number(entry.feature.longitude)" not in MAP_DOCUMENT_TEMPLATE


def test_generic_and_animal_popup_html_render_numeric_zero_rows() -> None:
    value_helpers = template_block(
        "function finiteTimeValue", "function featureTimeWindow"
    )
    popup_helpers = template_block("function popupHtml", "function polygonPopupHtml")
    observed = run_node_json(
        """
function escapeHtml(value){return String(value)}
function scientificSignalsForFeature(){return []}
function normalizedMediaLinks(){return []}
function mediaLinksHtml(){return ''}
function formatAnimalScope(value){return value}
function formatCoordinateConfidence(value){return value}
function formatCoordinateBasis(value){return value}
"""
        + value_helpers
        + popup_helpers
        + """
const generic=popupHtml({latitude:0,longitude:0,popup_rows:[{label:'Count',value:0}]});
const animal=popupHtml({
  species_latin_name:'Bos taurus',latitude:0,longitude:0,
  temporal_semantics:{
    evidence_class:'archaeological_context_date',
    precision_posture:'sample_approximate_or_modeled',
    comparability_posture:'contextual_label_only',
    comparison_note:'Numeric publication is withheld.',
  },
  popup_rows:[{label:'Interpretation',value:0},{label:'Warning',value:0}],
});
console.log(JSON.stringify({
  genericZero:generic.includes('<strong>Count</strong> 0'),
  animalInterpretationZero:animal.includes('popup-row-value">0</span>'),
  animalWarningZero:animal.includes('popup-warning">0</div>'),
  animalEvidenceClass:animal.includes('archaeological_context_date'),
  animalPrecisionPosture:animal.includes('sample_approximate_or_modeled'),
  animalComparisonPosture:animal.includes('contextual_label_only'),
  animalComparisonNote:animal.includes('Numeric publication is withheld.'),
}));
"""
    )

    assert observed == {
        "genericZero": True,
        "animalInterpretationZero": True,
        "animalWarningZero": True,
        "animalEvidenceClass": True,
        "animalPrecisionPosture": True,
        "animalComparisonPosture": True,
        "animalComparisonNote": True,
    }


def test_missing_density_count_has_explicit_unavailable_presentation() -> None:
    assert "countDisplayValue(feature.properties.count" in MAP_DOCUMENT_TEMPLATE
    assert "if (count === null || maxCount === null) return '#cbd5e1'" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "feature.properties.count || '0'" not in MAP_DOCUMENT_TEMPLATE


def test_polygon_geometry_admission_rejects_bad_coordinates_and_shape() -> None:
    coordinate_helpers = template_block(
        "function finiteTimeValue", "function featureTimeWindow"
    )
    geometry_helpers = template_block(
        "function geoJsonPositionIsAdmitted", "function removeRenderedLayers"
    )
    observed = run_node_json(
        coordinate_helpers
        + geometry_helpers
        + """
const polygon = (coordinates) => ({geometry:{type:'Polygon',coordinates}});
console.log(JSON.stringify({
  valid: polygonGeometryIsAdmitted(polygon([[[0,0],[10,0],[10,10],[0,0]]])),
  zero: polygonGeometryIsAdmitted(polygon([[[0,0],[1,0],[1,1],[0,0]]])),
  nullCoordinate: polygonGeometryIsAdmitted(polygon([[[null,0],[1,0],[1,1],[null,0]]])),
  nonfinite: polygonGeometryIsAdmitted(polygon([[[0,0],[1,0],[1,'nan'],[0,0]]])),
  outOfRange: polygonGeometryIsAdmitted(polygon([[[181,0],[1,0],[1,1],[181,0]]])),
  openRing: polygonGeometryIsAdmitted(polygon([[[0,0],[1,0],[1,1],[0,1]]])),
  wrongType: polygonGeometryIsAdmitted({geometry:{type:'LineString',coordinates:[[0,0],[1,1]]}}),
}));
"""
    )

    assert observed == {
        "valid": True,
        "zero": True,
        "nullCoordinate": False,
        "nonfinite": False,
        "outOfRange": False,
        "openRing": False,
        "wrongType": False,
    }
    assert (
        "polygonGeometryIsAdmitted(feature) && polygonFeatureVisible"
        in MAP_DOCUMENT_TEMPLATE
    )
