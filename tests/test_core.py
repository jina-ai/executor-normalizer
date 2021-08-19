from pathlib import Path
import pytest

from normalizer import deps, core


def test_inspect_dummy_execs():
    executors = core.inspect_executors(
        [Path(__file__).parent / 'cases' / 'simple_case' / 'dummy_exec.py']
    )
    assert len(executors) == 4
    assert executors[0][0] == 'DummyExecutor'
    assert executors[1][0] == 'Dummy2Executor'
    assert executors[2][0] == 'Dummy3Executor'
    assert executors[3][0] == 'FailedExecutor'

    # success case
    assert len(executors[0][1]) == 1
    assert len(executors[0][2]) == 0

    # success case with argument with default values
    assert len(executors[2][1]) == 2
    assert len(executors[2][2]) == 1

    # failed case
    assert len(executors[3][1]) == 2
    assert len(executors[3][2]) == 0


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
