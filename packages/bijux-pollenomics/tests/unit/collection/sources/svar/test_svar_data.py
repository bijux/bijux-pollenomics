from __future__ import annotations

import pytest

from bijux_pollenomics.collection.sources.svar.collection import (
    _parse_pos_list,
    _parse_svar_lake_features,
)


def test_parse_pos_list_transforms_sweref99_tm_to_wgs84() -> None:
    coordinates = _parse_pos_list(
        "579976.7462 7364709.7328 579953.595 7364730.9234 579976.7462 7364709.7328"
    )

    assert len(coordinates) == 3
    longitude, latitude = coordinates[0]
    assert round(longitude, 2) == 16.79
    assert round(latitude, 2) == 66.39


def test_parse_svar_lake_features_keeps_stable_lake_identity_fields() -> None:
    payload = """<?xml version='1.0' encoding="UTF-8" ?>
<wfs:FeatureCollection xmlns:ms="http://mapserver.gis.umn.edu/mapserver" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:wfs="http://www.opengis.net/wfs/2.0">
  <wfs:member>
    <ms:lakes gml:id="lakes.736633-154404">
      <ms:msGeometry>
        <gml:Polygon gml:id="lakes.736633-154404.1" srsName="urn:ogc:def:crs:EPSG::3006">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2">7364709.7328 579976.7462 7364730.9234 579953.595 7364709.7328 579976.7462</gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </ms:msGeometry>
      <ms:VYNAMN></ms:VYNAMN>
      <ms:SJOID>736633-154404</ms:SJOID>
      <ms:VYHOJD>786.1</ms:VYHOJD>
      <ms:SJVattenID>WA81820449</ms:SJVattenID>
      <ms:SJ_UUID>648487F4-D6EA-4A94-B887-DB65C076AEBF</ms:SJ_UUID>
      <ms:LW_PopNamn>20000_Namnlos_(16.79,66.39)</ms:LW_PopNamn>
      <ms:DISTRICT>SE1</ms:DISTRICT>
      <ms:COUNTRY>SE</ms:COUNTRY>
      <ms:AREA>0.043182</ms:AREA>
      <ms:Register>
        <ms:SNAMN></ms:SNAMN>
      </ms:Register>
    </ms:lakes>
  </wfs:member>
</wfs:FeatureCollection>
"""

    features = _parse_svar_lake_features(payload)

    assert len(features) == 1
    feature = features[0]
    geometry = feature["geometry"]
    assert isinstance(geometry, dict)
    assert geometry["type"] == "Polygon"
    properties = feature["properties"]
    assert isinstance(properties, dict)
    assert properties["record_id"] == "736633-154404"
    assert properties["sjoid"] == "736633-154404"
    assert properties["sj_uuid"] == "648487F4-D6EA-4A94-B887-DB65C076AEBF"
    assert properties["sj_vatten_id"] == "WA81820449"
    assert properties["district"] == "SE1"
    assert properties["lake_name_status"] == "fallback_waterwebb_label"
    assert properties["name"] == "20000_Namnlos_(16.79,66.39)"


def test_parse_svar_lake_features_repairs_mojibake_names() -> None:
    payload = """<?xml version='1.0' encoding="UTF-8" ?>
<wfs:FeatureCollection xmlns:ms="http://mapserver.gis.umn.edu/mapserver" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:wfs="http://www.opengis.net/wfs/2.0">
  <wfs:member>
    <ms:lakes gml:id="lakes.708193-151564">
      <ms:msGeometry>
        <gml:Polygon gml:id="lakes.708193-151564.1" srsName="urn:ogc:def:crs:EPSG::3006">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2">7080000.0 578986.0 7080001.0 578987.0 7080000.0 578986.0</gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </ms:msGeometry>
      <ms:VYNAMN>Ã„lgtjÃ¤rnen</ms:VYNAMN>
      <ms:SJOID>708193-151564</ms:SJOID>
      <ms:VYHOJD>251.9</ms:VYHOJD>
      <ms:SJVattenID>WA21354911</ms:SJVattenID>
      <ms:SJ_UUID>19BA25D6-23A1-4423-87E5-F07BB8C2A536</ms:SJ_UUID>
      <ms:LW_PopNamn>38000_Ã„lgtjÃ¤rnen_(16.12,63.85)</ms:LW_PopNamn>
      <ms:DISTRICT>SE2</ms:DISTRICT>
      <ms:COUNTRY>SE</ms:COUNTRY>
      <ms:AREA>0.165111</ms:AREA>
      <ms:Register>
        <ms:SNAMN></ms:SNAMN>
      </ms:Register>
    </ms:lakes>
  </wfs:member>
</wfs:FeatureCollection>
"""

    features = _parse_svar_lake_features(payload)

    assert len(features) == 1
    properties = features[0]["properties"]
    assert isinstance(properties, dict)
    assert properties["name"] == "Älgtjärnen"
    assert properties["water_name"] == "Älgtjärnen"
    assert properties["fallback_name"] == "38000_Älgtjärnen_(16.12,63.85)"
    native = properties["source_native_properties"]
    assert isinstance(native, dict)
    assert native["VYNAMN"] == [{"text": "Ã„lgtjÃ¤rnen", "attributes": {}}]


def test_native_fields_preserve_missing_empty_nil_duplicates_and_numeric_text() -> None:
    from .test_capture import page

    source = page(("x",)).replace(
        b"<ms:AREA>0</ms:AREA>",
        b"""<ms:AREA> 0.000 </ms:AREA><ms:VYNAMN/>
<ms:VYNAMN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>
<ms:Register><ms:SNAMN> A &amp; B </ms:SNAMN></ms:Register>
<ms:SJ_UUID>first</ms:SJ_UUID><ms:SJ_UUID>second</ms:SJ_UUID>""",
    )
    props = _parse_svar_lake_features(source)[0]["properties"]
    assert isinstance(props, dict)
    native = props["source_native_properties"]
    assert isinstance(native, dict)
    assert set(native) == {
        "Register/SNAMN",
        "VYNAMN",
        "LW_PopNamn",
        "COUNTRY",
        "SJOID",
        "SJ_UUID",
        "SJVattenID",
        "DISTRICT",
        "VYHOJD",
        "AREA",
    }
    assert native["COUNTRY"] == []
    assert native["VYNAMN"] == [
        {"text": None, "attributes": {}},
        {
            "text": None,
            "attributes": {"{http://www.w3.org/2001/XMLSchema-instance}nil": "true"},
        },
    ]
    assert native["AREA"] == [{"text": " 0.000 ", "attributes": {}}]
    assert native["Register/SNAMN"] == [{"text": " A & B ", "attributes": {}}]
    assert native["SJ_UUID"] == [
        {"text": "first", "attributes": {}},
        {"text": "second", "attributes": {}},
    ]
    assert props["country"] == "SE"
    assert props["name"] == "A & B"
    assert props["area_km2"] == 0
    policy = props["derived_properties_policy"]
    assert isinstance(policy, dict)
    assert policy["country"] == "legacy_absent_element_default_SE_not_source_assertion"


def test_nested_scalar_property_refuses_instead_of_losing_child_text() -> None:
    from .test_capture import page

    source = page(("x",)).replace(
        b"<ms:AREA>0</ms:AREA>",
        b"<ms:AREA>0</ms:AREA><ms:VYNAMN>A<ms:x>B</ms:x>C</ms:VYNAMN>",
    )
    with pytest.raises(ValueError, match="non_scalar_property"):
        _parse_svar_lake_features(source)
