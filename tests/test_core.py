import os
from pathlib import Path

import pytest

from normalizer import core

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_inspect_dummy_execs():
    executors = core.inspect_executors([Path(cur_dir) / 'cases' / 'dummy_exec.py'])
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

def test_choose_jina_version(mocker):
    mocker.patch('normalizer.helper.get_jina_latest_version', return_value='2.0.0rc10')

    assert helper.choose_jina_version('2.0.0rc11') == '2.0.0rc10'
    assert helper.choose_jina_version('2.0.0rc9') == '2.0.0rc9'
    assert helper.choose_jina_version('master') == 'master'