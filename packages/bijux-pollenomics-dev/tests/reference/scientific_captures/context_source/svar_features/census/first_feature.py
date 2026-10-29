"""Inspect only one bounded, source-authenticated SVAR feature; never census the file."""
from __future__ import annotations

import codecs
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[3]
SOURCE=Path(__file__).resolve().parent
RAW=Path('/Users/bijan/bijux/-bijux-pollenomics-data/svar/normalized-export-2026-09-08/sweden_lake_registry.geojson')
EXPECTED_SHA='d9a1943d1a35e7ab6d48e06156fef625e7c62c8bc410cecf9d8f592ccb07dfd8'
EXPECTED_BYTES=261041034
MAX_SCHEMA_BYTES=2*1024**2


def require(value: object,message: str) -> None:
    if not value:raise ValueError(message)


def pin(path: Path) -> dict[str,Any]:
    with path.open('rb') as stream:s=hashlib.file_digest(stream,'sha256').hexdigest()
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':s}


def pairs(items: list[tuple[str,Any]]) -> dict[str,Any]:
    require(len(items)==len({k for k,_ in items}),'Duplicate JSON key')
    return dict(items)


def invalid(value: str) -> None:
    raise ValueError('Invalid JSON numeric constant: '+value)


def first_feature(path: Path,maximum: int=MAX_SCHEMA_BYTES) -> tuple[dict[str,Any],dict[str,Any]]:
    decoder=json.JSONDecoder(object_pairs_hook=pairs,parse_float=Decimal,parse_constant=invalid)
    utf8=codecs.getincrementaldecoder('utf-8')('strict');buffer='';position=0;read_bytes=0;metadata={};seen=set()
    with path.open('rb') as stream:
        def fill() -> bool:
            nonlocal buffer,read_bytes
            require(read_bytes<maximum,'First-feature bounded schema budget exhausted')
            block=stream.read(min(65536,maximum-read_bytes));read_bytes+=len(block);buffer+=utf8.decode(block,final=not block);return bool(block)
        def space() -> None:
            nonlocal position
            while True:
                while position<len(buffer) and buffer[position] in ' \t\r\n':position+=1
                if position<len(buffer):return
                require(fill(),'Unexpected end of first-feature prefix')
        def take(value: str) -> None:
            nonlocal position
            space();require(buffer[position]==value,'Unexpected JSON wrapper token');position+=1
        def value() -> tuple[Any,str]:
            nonlocal position
            space();start=position
            while True:
                try:
                    decoded,end=decoder.raw_decode(buffer,position);position=end;return decoded,buffer[start:end]
                except json.JSONDecodeError:
                    require(fill(),'Incomplete first-feature prefix')
        take('{')
        while True:
            key,_=value();require(isinstance(key,str) and key not in seen,'Invalid/duplicate wrapper key');seen.add(key);take(':')
            if key=='features':
                take('[');feature,raw=value();require(isinstance(feature,dict) and feature.get('type')=='Feature','First collection item is not a Feature')
                require(metadata.get('type')=='FeatureCollection','Collection type must precede bounded feature inspection')
                return feature,{'read_prefix_bytes':read_bytes,'maximum_prefix_bytes':maximum,'first_feature_raw_sha256':hashlib.sha256(raw.encode()).hexdigest(),'first_feature_raw_bytes':len(raw.encode()),'wrapper_metadata_before_features':metadata,'first_feature_only':True,'full_document_parsed':False,'feature_population_censused':False}
            metadata[key]=value()[0];take(',')


def shape(value: Any) -> Any:
    if value is None:return 'null'
    if type(value) is bool:return 'boolean'
    if type(value) is int:return 'integer'
    if isinstance(value,Decimal):return {'type':'decimal_JSON_number','native_decimal_text':str(value)}
    if isinstance(value,str):return 'string'
    if isinstance(value,list):return {'type':'array','length':len(value),'first_item':shape(value[0]) if value else None}
    if isinstance(value,dict):return {k:shape(v) for k,v in value.items()}
    raise ValueError('Unexpected decoded shape')


def main() -> None:
    before=pin(RAW);require(before['sha256']==EXPECTED_SHA and before['bytes']==EXPECTED_BYTES,'Actual source identity differs')
    feature,scope=first_feature(RAW)
    properties=feature.get('properties');require(isinstance(properties,dict),'Missing first feature properties')
    scalars={k:(str(v) if isinstance(v,Decimal) else v) for k,v in properties.items() if v is None or type(v) in (str,int,bool) or isinstance(v,Decimal)}
    geometry=feature.get('geometry')
    result={'schema_version':'bounded-SVAR-first-feature-source-forensics.v1','source':before,'source_before_after_equal':pin(RAW)==before,'source_scope':'Only the first feature and wrapper prefix within2MiB are JSON-decoded; whole261MB bytes are hashed for source identity, never parsed/censused by this source check.','schema_scope':scope,'feature_top_level_keys':list(feature),'property_keys':list(properties),'first_feature_property_types':shape(properties),'first_feature_scalar_properties':scalars,'first_feature_geometry_type':geometry.get('type') if isinstance(geometry,dict) else None,'geometry_shape_only':shape(geometry),'raw_full_geometry_redistributed':False,'normalization_units_dates_coverage_or_WFS_authority_verified':False,'source_WFS_rights_human_ranking_admission':False}
    require(result['source_before_after_equal'] is True,'Source bytes changed during bounded metadata inspection')
    target=SOURCE/'first-feature-forensics.json';require(not target.exists(),'No evidence overwrite');target.write_text(json.dumps(result,indent=2,default=str,allow_nan=False)+'\n')
    print(json.dumps({'first_feature_keys':list(feature),'property_keys':list(properties),'geometry_type':result['first_feature_geometry_type'],'schema_scope':scope},default=str))


if __name__=='__main__':main()
