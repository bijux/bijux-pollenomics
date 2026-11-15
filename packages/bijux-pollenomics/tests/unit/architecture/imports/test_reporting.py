"""Public reporting access must not depend on which analysis module loaded first."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

from tests.support.repository import REPOSITORY_ROOT


def run(script: str) -> None:
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(REPOSITORY_ROOT / "packages/bijux-pollenomics/src"),
    }
    result = subprocess.run(
        [sys.executable, "-B", "-c", textwrap.dedent(script)],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "first",
    [
        "bijux_pollenomics.analysis.propagation",
        "bijux_pollenomics.publication_policy",
        "bijux_pollenomics.reporting.models",
    ],
)
def test_analysis_and_policy_can_load_before_reporting_service(first: str) -> None:
    run(
        f"""
        import importlib
        importlib.import_module({first!r})
        reporting = importlib.import_module('bijux_pollenomics.reporting')
        service = importlib.import_module('bijux_pollenomics.reporting.service')
        assert reporting.generate_multi_country_map is service.generate_multi_country_map
        """
    )


def test_reporting_discovery_does_not_initialize_the_publication_graph() -> None:
    run(
        """
        import importlib
        import sys
        reporting = importlib.import_module('bijux_pollenomics.reporting')
        before = set(sys.modules)
        assert 'generate_multi_country_map' in dir(reporting)
        assert 'service' in dir(reporting)
        assert not any(name.startswith('bijux_pollenomics.analysis') for name in before)
        assert 'bijux_pollenomics.reporting.service' not in before
        try:
            reporting.unknown_reporting_attribute
        except AttributeError:
            pass
        else:
            raise AssertionError('Unknown reporting attribute must refuse')
        assert set(sys.modules) == before
        assert reporting.service is importlib.import_module('bijux_pollenomics.reporting.service')
        """
    )


def test_public_reporting_objects_keep_their_original_api_owners() -> None:
    run(
        """
        import importlib
        import inspect
        import pickle
        reporting = importlib.import_module('bijux_pollenomics.reporting')
        expected = ['AdnaLocalitySummary', 'AdnaSampleRecord', 'AnimalFoundationRefreshReport',
            'CountryReport', 'MultiCountryMapReport', 'PublishedReportsReport', 'SchemaError',
            'generate_country_report', 'generate_multi_country_map', 'generate_published_reports',
            'load_country_samples', 'refresh_animal_adna_foundation', 'slugify', 'summarize_localities']
        assert reporting.__all__ == expected
        namespace = {}
        exec('from bijux_pollenomics.reporting import *', namespace)
        assert set(namespace) - {'__builtins__'} == set(expected)
        api = importlib.import_module('bijux_pollenomics.reporting.api')
        for name in expected:
            actual = getattr(reporting, name)
            assert actual is getattr(api, name) is namespace[name], name
            if inspect.isclass(actual):
                assert pickle.loads(pickle.dumps(actual)) is actual
        replacement = object()
        reporting.generate_country_report = replacement
        assert reporting.__getattr__('generate_country_report') is replacement
        """
    )
