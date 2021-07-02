import os
from pathlib import Path
import pytest

from normalizer import deps

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_get_imports():
    imports = deps.get_all_imports(cur_dir + '/cases')

    assert imports == ['jina']


def test_get_import_info():
    pkg = deps.get_import_info('requests')
    assert pkg.project == 'requests'
