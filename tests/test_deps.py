import os
from pathlib import Path
import pytest

from normalizer import deps

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def test_imports():
    imports = [
        deps.Package(name='tensorflow', version='2.5.0'),
    ]


def test_get_imports():
    imports = deps.get_all_imports(cur_dir + '/cases/simple_case')

    assert set(imports) == set(['jina', 'tensorflow'])


def test_get_import_info():
    pkg = deps.get_import_info('requests')
    assert pkg.name == 'requests'


def test_get_dep_tools():
    pkg = deps.Package(name='git+https://www.github.com/', version=None)
    assert deps.get_dep_tools(pkg) == ['git']


@pytest.mark.parametrize(
    'package, expect_base_image',
    [
        (
            deps.Package(name='tensorflow', version='2.5.0'),
            'tensorflow/tensorflow:2.5.0',
        ),
        (
            deps.Package(name='tensorflow-cpu', version='2.1.0'),
            'tensorflow/tensorflow:2.1.0-py3',
        ),
        (
            deps.Package(name='tensorflow-gpu', version='2.1.0'),
            'tensorflow/tensorflow:2.1.0-gpu-py3',
        ),
        (
            deps.Package(name='tensorflow-gpu', version='1.12.0'),
            'tensorflow/tensorflow:1.12.0-gpu-py3',
        ),
        (deps.Package(name='pytorch', version='1.8.0+cpu'), 'bitnami/pytorch:1.8.0'),
        (
            deps.Package(name='pytorch', version='1.8.0'),
            'pytorch/pytorch:1.8.0-cuda10.2-cudnn7-runtime',
        ),
    ],
)
def test_get_base_images(package, expect_base_image):
    assert deps.get_baseimage(package) == expect_base_image
