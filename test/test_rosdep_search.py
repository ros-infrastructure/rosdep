# Copyright (c) 2026, Dori
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from rosdep2 import main
from rosdep2.sources_list import CachedDataSource


def search_packages(rule):
    source = CachedDataSource('yaml', 'https://example.org/python.yaml', [], {
        'python3-pyqt6.qtwebengine': {'ubuntu': rule},
        'other-platform': {'debian': ['PyQt6-WebEngine']},
    })
    query = main.re.compile(main.re.escape('PyQt6-WebEngine'), main.re.IGNORECASE)
    return main.search_cached_data_source(source, [query], 'ubuntu')


@pytest.mark.parametrize('rule', [
    'PyQt6-WebEngine',
    ['PyQt6-WebEngine'],
    {'pip': {'packages': ['PyQt6-WebEngine']}},
    {'jammy': ['PyQt6-WebEngine']},
    {'jammy': {'pip': {'packages': ['PyQt6-WebEngine']}}},
    {'*': {'pip': {'packages': ['PyQt6-WebEngine']}}},
    {
        'bionic': None,
        'focal': {'pip': {'packages': ['PyQt6-WebEngine']}},
        'jammy': {'pip': {'packages': ['PyQt6-WebEngine']}},
    },
])
def test_search_packages_in_supported_rule_formats(rule):
    assert search_packages(rule) == ([], [{
        'key': 'python3-pyqt6.qtwebengine',
        'pkg': 'PyQt6-WebEngine',
        'os': 'ubuntu',
        'error': 0,
    }])


@pytest.mark.parametrize('rule', [
    {'jammy': {'source': {'uri': 'https://example.org/PyQt6-WebEngine'}}},
    {'jammy': {'pip': {'packages': ['unrelated'], 'depends': ['PyQt6-WebEngine']}}},
])
def test_search_does_not_match_installer_metadata(rule):
    assert search_packages(rule) == ([], [])
