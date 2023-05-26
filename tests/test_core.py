import json
from pathlib import Path
import pytest
import os

from normalizer import deps, core
from normalizer.models import ExecutorModel


def test_inspect_dummy_execs():
    executors = core.inspect_executors(
        [Path(__file__).parent / 'cases' / 'simple_case' / 'dummy_exec.py']
    )
    assert len(executors) == 4
    assert executors[0][0] == 'DummyExecutor'
    assert executors[1][0] == 'Dummy2Executor'
    assert executors[2][0] == 'Dummy3Executor'
    assert executors[3][0] == 'FailedExecutor'

    for executor in executors:
        assert len(executor) == 5

    # success case
    assert len(executors[0][3][0]) == 1
    assert len(executors[0][3][1]) == 0
    assert len(executors[0][3][2]) == 1

    # success case with argument with default values
    assert len(executors[2][3][0]) == 2
    assert len(executors[2][3][1]) == 1
    assert len(executors[2][3][2]) == 2

    # failed case
    assert len(executors[3][3][0]) == 2
    assert len(executors[3][3][1]) == 0
    assert len(executors[3][3][2]) == 2


@pytest.mark.parametrize(
    'package_path, expected_path',
    [
        (
            Path(__file__).parent / 'cases' / 'executor_1',
            Path(__file__).parent / 'cases' / 'executor_1.json'
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_2',
            Path(__file__).parent / 'cases' / 'executor_2.json'
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_3',
            Path(__file__).parent / 'cases' / 'executor_3.json'
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_4',
            Path(__file__).parent / 'cases' / 'executor_4.json'
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_5',
            None
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_6',
            None
        ),
        (
            Path(__file__).parent / 'cases' / 'nested',
            Path(__file__).parent / 'cases' / 'nested.json'
        ),
        (
            Path(__file__).parent / 'cases' / 'nested_2',
            None
        ),
        (
            Path(__file__).parent / 'cases' / 'nested_3',
            None
        ),
        (
            Path(__file__).parent / 'cases' / 'nested_4',
            None
        ),
        (
            Path(__file__).parent / 'cases' / 'nested_5',
            None
        ),
    ],
)
def test_get_executor_args(package_path, expected_path):
    if expected_path:
        with open(expected_path, 'r') as fp:
            expected_executor = ExecutorModel(**json.loads(fp.read()))
            executor = core.normalize(package_path, dry_run=True)
            executor.hubble_score_metrics = expected_executor.hubble_score_metrics
            executor.filepath = expected_executor.filepath
            assert executor == expected_executor
    else:
        core.normalize(package_path, dry_run=True)


@pytest.mark.parametrize(
    'package_path, dockerfile_syntax, meta_dict, dockerfile_name',
    [
        (
            Path(__file__).parent / 'cases' / 'executor_1',
            None,
            {'jina': '2'},
            'Dockerfile'
        ),
         (
            Path(__file__).parent / 'cases' / 'executor_2',
            None,
            {'jina': '2'},
            'Dockerfile'
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_6',
            'jinahub/dockerfile:1.4.3-magic-shell',
            {'jina': '2'},
            'Dockerfile'
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_7',
            'jinahub/dockerfile:1.4.3-magic-shell',
            {'jina': '2'},
            'Dockerfile'
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_8',
            None,
            {'jina': '3.16.0', 'docarray': '0.30.0'},
            'Dockerfile'
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_9',
            None,
            {'jina': '3.16.0', 'docarray': '0.30.0'},
            '__jina__.Dockerfile'
        ),
    ],
)
def test_compare_dockerfile_syntax(package_path, dockerfile_syntax, meta_dict, dockerfile_name):

    dockerfile_path = Path(package_path / dockerfile_name)
    dockerfile_expected_path = Path(package_path / 'Dockerfile.expect')

    originDockerfileStr = None;
    if dockerfile_path.exists():
        with open(dockerfile_path, 'r') as fp:
            originDockerfileStr = str(fp.read())

    core.normalize(package_path, dockerfile_syntax=dockerfile_syntax, dry_run=False, meta=meta_dict, dockerfile=dockerfile_name)
    assert dockerfile_path.exists() == True;

    dockerfileStr = None
    with open(dockerfile_path, 'r') as fp:
        dockerfileStr = str(fp.read())

    dockerfileExpectedStr = ''
    with open(dockerfile_expected_path, 'r') as fp:
        dockerfileExpectedStr = str(fp.read())

    if originDockerfileStr:
        with open(dockerfile_path, 'w') as fp:
            fp.write(originDockerfileStr)
    else:
        os.remove(dockerfile_path)

    assert dockerfileExpectedStr == dockerfileStr


def test_prelude():
    imports = [
        deps.Package(name='tensorflow', version='2.5.0'),
        deps.Package(name='pytorch', version='1.6.0'),
        deps.Package(name='git+http://www.github.com', version=None),
    ]

    base_images, tools = core.prelude(imports)
    # assert base_images == set(
    #     ['tensorflow/tensorflow:2.5.0', 'pytorch/pytorch:1.6.0-cuda10.2-cudnn7-runtime']
    # )
    assert tools == set(['git'])


@pytest.mark.parametrize(
    'package_path, dockerfile_syntax, dockerfile',
    [
        (
            Path(__file__).parent / 'cases' / 'executor_7',
            'jinahub/dockerfile:1.4.3-magic-shell',
            'Dockerfile.custom'
        ),
    ],
)
def test_normalized_custom_dockerfile(package_path, dockerfile_syntax, dockerfile):
    dockerfile_path = Path(package_path / dockerfile)
    dockerfile_expected_path = Path(package_path / 'Dockerfile.expect')

    originDockerfileStr = None;
    if dockerfile_path.exists():
        with open(dockerfile_path, 'r') as fp:
            originDockerfileStr = str(fp.read())

    core.normalize(package_path, dockerfile_syntax=dockerfile_syntax, dockerfile=dockerfile , dry_run=False)

    dockerfileStr = None
    with open(dockerfile_path, 'r') as fp:
        dockerfileStr = str(fp.read())

    dockerfileExpectedStr = ''
    with open(dockerfile_expected_path, 'r') as fp:
        dockerfileExpectedStr = str(fp.read())

    assert dockerfileStr == dockerfileExpectedStr

    if originDockerfileStr:
        with open(dockerfile_path, 'w') as fp:
            fp.write(originDockerfileStr)
