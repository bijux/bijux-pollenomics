from __future__ import annotations

from bijux_pollenomics.data_downloader.svar import (
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
        <gml:Polygon gml:id="lakes.736633-154404.1" srsName="urn:ogc:def:crs:EPSG::3786">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2">579976.7462 7364709.7328 579953.595 7364730.9234 579976.7462 7364709.7328</gml:posList>
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
    assert feature["geometry"]["type"] == "Polygon"
    properties = feature["properties"]
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
        <gml:Polygon gml:id="lakes.708193-151564.1" srsName="urn:ogc:def:crs:EPSG::3786">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2">578986.0 7080000.0 578987.0 7080001.0 578986.0 7080000.0</gml:posList>
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
    assert properties["name"] == "Älgtjärnen"
    assert properties["water_name"] == "Älgtjärnen"
    assert properties["fallback_name"] == "38000_Älgtjärnen_(16.12,63.85)"
