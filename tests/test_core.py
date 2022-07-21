import json
from pathlib import Path
from pickle import TRUE
import pytest
import re

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
    'package_path, expected_path, build_args_envs, dry_run',
    [
        (
            Path(__file__).parent / 'cases' / 'executor_1',
            Path(__file__).parent / 'cases' / 'executor_1.json',
            { 
                'AUTH_TOKEN': "AUTH_TOKEN",
                'TOKEN': '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'
            } ,
            False
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_2',
            Path(__file__).parent / 'cases' / 'executor_2.json',
            {},
            True
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_3',
            Path(__file__).parent / 'cases' / 'executor_3.json',
            {},
            True
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_4',
            Path(__file__).parent / 'cases' / 'executor_4.json',
            {},
            True
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_5',
            None,
            {},
            True
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_6',
            None,
            {},
            True
        ),
        (
            Path(__file__).parent / 'cases' / 'executor_7',
            None,
            { 
                'AUTH_TOKEN': "AUTH_TOKEN",
                'TOKEN': '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'
            },
            True
        ),
        (
            Path(__file__).parent / 'cases' / 'nested',
            Path(__file__).parent / 'cases' / 'nested.json',
            {},
            True
        ),
        (
            Path(__file__).parent / 'cases' / 'nested_2',
            None,
            { 
                'AUTH_TOKEN': "AUTH_TOKEN",
                'TOKEN': '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'
            },
            False
        ),
        (
            Path(__file__).parent / 'cases' / 'nested_3',
            None,
            {},
            True
        ),
        (
            Path(__file__).parent / 'cases' / 'nested_4',
            None,
            {},
            True
        ),
        (
            Path(__file__).parent / 'cases' / 'nested_5',
            None,
            {},
            True
        ),
    ],
)
def test_get_executor_args(package_path, expected_path, build_args_envs, dry_run):
    if expected_path:
        with open(expected_path, 'r') as fp:
            expected_executor = ExecutorModel(**json.loads(fp.read()))
            executor = core.normalize(package_path, build_args_envs=build_args_envs, dry_run=dry_run)
            executor.hubble_score_metrics = expected_executor.hubble_score_metrics
            executor.filepath = expected_executor.filepath
            assert executor == expected_executor
    else:
        core.normalize(package_path, build_args_envs=build_args_envs, dry_run=dry_run)
    
    dockerfilePath = Path(package_path / 'Dockerfile') 
    if dry_run is False and dockerfilePath.exists():
        with open(dockerfilePath, 'r') as fp:
            dockerfileStr = str(fp.read())
            for index, item in enumerate(build_args_envs):
                print('search', dockerfileStr, item, re.search(item, dockerfileStr))
                assert re.search(item, dockerfileStr) is not None


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
