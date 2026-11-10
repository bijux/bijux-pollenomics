#!/usr/bin/env python3
"""Build and qualify one documentation artifact under its actual renderer."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import sys
import subprocess
import tempfile

sys.dont_write_bytecode=True


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def build_artifact(root: Path, config_name: str, site_name: str, *, site_url='', source_identity=None, strict=True, source_recipe=None, reader_owner=None, interactive_report_owner=None, preflight=False, admission_policy=None):
    shared=Path(__file__).resolve().parents[1]
    identity=load('bijux_renderer_identity',shared/'security/build_identity.py')
    publication=load('bijux_renderer_publication',shared/'security/publication.py')
    producer=publication.producer_module(shared)
    policy=load('bijux_renderer_csp',shared/'security/csp.py')
    redirects=load('bijux_renderer_redirects',shared/'security/redirects.py')
    site=publication.site_directory(root,site_name)
    checkpoint=None
    if source_identity:
        if not strict:
            raise ValueError("Publication build: source-qualified publication requires strict rendering")
        checkpoint=json.loads(identity.artifact(root,source_identity).read_text())
        identity.verify_source(root,checkpoint)
        record=checkpoint.get('derivation')
        if record is not None and not isinstance(record,dict):
            raise ValueError('Publication build: typed derivation record required')
        expected_recipe=record.get('recipe') if record else None
        if source_recipe is not None and source_recipe!=expected_recipe:
            raise ValueError('Publication build: recipe differs from owner checkpoint')
        source_recipe=expected_recipe
        selected_config=record['configuration']['path'] if record else checkpoint.get('config',{}).get('path')
        if selected_config!=config_name:
            raise ValueError('Publication build: owner checkpoint must select the actual config')
    if admission_policy is not None and (checkpoint is None or preflight):
        raise ValueError('Publication admission requires a qualified source and an actual build')
    from mkdocs.config import load_config
    from mkdocs.commands.build import build
    import material
    catalogue=None
    if source_recipe:
        producer.dependencies(shared,root,publication=checkpoint is not None)
        if reader_owner is not None or interactive_report_owner is not None:
            raise ValueError("Publication build: report readers require a tracked MkDocs config; catalogue recipe composition remains separate")
        catalogue=identity.catalogue_derivation(root,source_recipe,checkpoint.get('derivation') if checkpoint else None)
        if config_name!=catalogue.record['configuration']['path']:
            raise ValueError('Publication build: exact reconstructed configuration required')
        configuration=catalogue.configuration(site)
    else:
        configuration=load_config(config_file=str(identity.regular(root,config_name)),site_dir=str(site))
    actual_url=site_url or configuration.site_url
    publication.validate_url(actual_url)
    if actual_url!=configuration.site_url:
        raise ValueError('Publication build: actual configuration selects another production URL')
    # A source refusal must not erase retained public bytes or their receipts.
    # This check is repeated inside actual independent reconstruction.
    producer.report_source(root,config_name,shared,configuration,source_recipe=source_recipe,
                           reader_owner=reader_owner,interactive_report_owner=interactive_report_owner)
    if preflight:
        return {'state':'report-source-validated','rendered':False,'verification_only':True,
                'site_url':actual_url,'site_dir':site_name}
    evidence=root/'artifacts/website-security';evidence.mkdir(parents=True,exist_ok=True)
    # Clear prior success receipts before a build can fail. Reports belong outside site.
    for name in ('build-identity','csp','producer-reconstruction','site-verification'):
        destination=identity.artifact(root,'artifacts/website-security/'+name+'.json')
        if destination.is_relative_to(site):raise ValueError('Publication build: evidence cannot be published')
        destination.write_text(json.dumps({'schema':1,'passed':False,'verification_only':True,'error':'Producer qualification incomplete'})+'\n')
    templates=Path(material.__file__).parent/'templates'
    with tempfile.TemporaryDirectory(prefix='renderer-reference-',dir=evidence) as scratch:
        prepared=producer.prepare(root,config_name,shared,templates,Path(scratch)/'site',site,
                                  publication_scope=checkpoint is not None,source_recipe=source_recipe,reader_owner=reader_owner,
                                  interactive_report_owner=interactive_report_owner,
                                  source_sha=checkpoint['repository_source']['sha'] if checkpoint else None)
        receipt=identity.begin(root,config_name,site_name,actual_url,source_identity,source_recipe)
        previous_strict=configuration.strict
        configuration.strict=strict
        try:
            producer.render(configuration,catalogue=catalogue is not None,source_root=root if checkpoint is not None else None,
                            source_sha=checkpoint['repository_source']['sha'] if checkpoint else None)
        finally:
            configuration.strict=previous_strict
        configuration=(catalogue.configuration(site) if catalogue else
                       load_config(config_file=str(identity.regular(root,config_name)),site_dir=str(site)))
        plan=redirects.normalize_redirects(configuration,site,actual_url,write=False,source_root=root if catalogue else None)
        report=(policy.apply(site,shared,templates,plan) if prepared.reader_source is None else
                prepared.reader_source.compose(site,receipt,policy,shared,templates,plan))
        inputs=report['policy_inputs'];inputs['redirects']=plan['policy_inputs']
        report.update(site_url=actual_url,site_dir=site_name,bundle_sha256=publication.public_bundle_identity(site)[1],
                      policy_inputs=inputs,processor_sha256=hashlib.sha256((shared/'security/csp.py').read_bytes()).hexdigest())
        receipt=identity.finish(root,receipt)
        reconstruction=producer.verify(site,prepared,receipt['renderer'],report,actual_url,completed_build=receipt,checkpoint=checkpoint)
        if checkpoint:
            identity.verify_source(root,checkpoint)
        for name,value in [('build-identity',receipt),('csp',report),('producer-reconstruction',reconstruction)]:
            output=identity.artifact(root,'artifacts/website-security/'+name+'.json')
            if output.is_relative_to(site):raise ValueError('Publication build: evidence cannot be published')
            output.write_text(json.dumps(value,indent=2)+'\n')
        environment={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
        if source_identity:environment['DOCS_SOURCE_IDENTITY']=source_identity
        else:environment.pop('DOCS_SOURCE_IDENTITY',None)
        arguments=[sys.executable,str(shared/'tooling/quality/validate_site_routes.py'),
                   '--repo-root',str(root),'--site-dir',site_name,'--site-url',actual_url,
                   '--output','artifacts/website-security/site-verification.json']
        if reader_owner is not None or interactive_report_owner is not None:
            arguments.extend(['--embedded-csp-report', 'artifacts/website-security/csp.json',
                              '--completed-build-receipt', 'artifacts/website-security/build-identity.json',
                              '--source-sha', prepared.reader_source.source_sha])
            arguments.extend(['--reader-owner', reader_owner] if reader_owner is not None else
                             ['--interactive-report-owner', interactive_report_owner])
            if source_identity: arguments.extend(['--source-identity', source_identity])
        exception=os.environ.get('BIJUX_DOCS_DEVELOPMENT_LINK_POLICY')
        if exception:arguments.extend(['--development-link-policy',exception])
        subprocess.run(arguments,cwd=root,env=environment,check=True)
        if checkpoint:identity.verify_source(root,checkpoint)
        if admission_policy is not None:
            # Keep the actual module/class and independent scratch reference alive.
            # A retained JSON receipt cannot enter this path.
            selected_policy=admission_policy() if callable(admission_policy) else admission_policy
            environment.update(PYTHONNOUSERSITE='1',DOCS_PYTHON=sys.executable,DOCS_SITE_DIR=site_name,
                               DOCS_BUILD_SITE_URL=actual_url,BIJUX_DOCS_SITE_REPORT='artifacts/website-security/site-verification.json')
            for key in ('BIJUX_DOCS_READER_OWNER','BIJUX_DOCS_INTERACTIVE_REPORT_OWNER','BIJUX_DOCS_READER_SOURCE_SHA'):
                environment.pop(key,None)
            if interactive_report_owner:
                environment.update(BIJUX_DOCS_INTERACTIVE_REPORT_OWNER=interactive_report_owner,
                                   BIJUX_DOCS_READER_SOURCE_SHA=checkpoint['repository_source']['sha'])
            elif reader_owner:
                environment.update(BIJUX_DOCS_READER_OWNER=reader_owner,
                                   BIJUX_DOCS_READER_SOURCE_SHA=checkpoint['repository_source']['sha'])
            subprocess.run(['bash',str(shared/'tooling/scripts/verify_bijux_docs_site.sh')],cwd=root,env=environment,check=True)
            manifest=publication.qualified_manifest(root,site_name,actual_url,checkpoint['repository_source']['sha'],
                publication.load_policy(Path(selected_policy)),source_identity,'artifacts/website-security/build-identity.json',
                'artifacts/website-security/site-verification.json','artifacts/website-security/csp.json',
                prepared_producer=prepared)
            destination=identity.artifact(root,'artifacts/website-security/publication.json')
            if destination.is_relative_to(site):raise ValueError('Publication manifest cannot be published')
            destination.write_text(json.dumps(manifest,indent=2)+'\n')
    return {'site_url':actual_url,'site_dir':site_name,'bundle_sha256':report['bundle_sha256'],
            'verification_only':checkpoint is None,'producer':reconstruction}


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(name)s: %(message)s')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True)
    parser.add_argument('--site-dir',required=True)
    parser.add_argument('--site-url',default='')
    parser.add_argument('--source-recipe',choices=['masterclass-catalogue'])
    parser.add_argument('--source-identity',default=os.environ.get('DOCS_SOURCE_IDENTITY'))
    parser.add_argument('--reader-owner', default=os.environ.get('BIJUX_DOCS_READER_OWNER'), help='Explicit committed finite static-reader ownership descriptor')
    parser.add_argument('--interactive-report-owner', help='Explicit committed config-selected interactive report ownership descriptor')
    parser.add_argument('--no-strict',action='store_true')
    parser.add_argument('--preflight',action='store_true',help='Validate report source selection without rendering or changing retained artifacts')
    parser.add_argument('--admit',action='store_true',help='Admit this actual build using its live independent producer')
    parser.add_argument('--policy',type=Path,help='Explicit admission policy; requires --admit')
    args=parser.parse_args()
    if args.policy is not None and not args.admit:parser.error('--policy requires --admit')
    from mkdocs.exceptions import MkDocsException
    try:
        result=build_artifact(Path.cwd().resolve(),args.config,args.site_dir,site_url=args.site_url,
                              source_identity=args.source_identity,strict=not args.no_strict,source_recipe=args.source_recipe,reader_owner=args.reader_owner,
                              interactive_report_owner=args.interactive_report_owner,preflight=args.preflight,
                              admission_policy=(args.policy or Path(__file__).with_name('policy.json')) if args.admit else None)
        print(json.dumps({key:value for key,value in result.items() if key!='producer'}))
        return 0
    except (MkDocsException,OSError,ValueError,KeyError,subprocess.CalledProcessError) as error:
        print('Documentation artifact rejected: '+str(error),file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
