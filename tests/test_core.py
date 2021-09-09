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

    for executor in executors:
        assert len(executor) == 5

    # success case
    assert len(executors[0][1]) == 1
    assert len(executors[0][2]) == 0

    # success case with argument with default values
    assert len(executors[2][1]) == 2
    assert len(executors[2][2]) == 1

    # failed case
    assert len(executors[3][1]) == 2
    assert len(executors[3][2]) == 0


@pytest.mark.parametrize('package_path, expected', [
    (
        Path(__file__).parent / 'cases' / 'executor_1',
        ('Executor1', 'My executor docstring', (
            [('self', None), ('arg1', 'str'), ('arg2', 'Optional[List[str]]'), ('arg3', 'Tuple[int, str]')],
            [('arg4', 'Optional[int]', 'None'), ('arg5', 'Optional[Tuple[int, str]]', '(123, \'123\')')],
            'init docstring'
        ), [('foo', [('self', None)], [], 'foo docstring', 'ALL')])
    ),
    (
        Path(__file__).parent / 'cases' / 'executor_2',
        ('Executor2', 'My executor docstring\n:param: arg1\n:param: arg2', (
            [('self', None), ('arg1', 'Optional[Tuple[int, str, List[int]]]')],
            [('arg2', 'Optional[Tuple[int, str, List[int]]]', "(123, 'test', [123])")],
            'init docstring'
        ), [
            (
                'foo', [('self', None), ('arg1', 'Tuple[int, str]')],
                [('arg2', 'Optional[int]', 'None')], 'foo docstring', '[\'/index\', \'/foo\']'
            ),
            (
                'bar', [('self', None), ('docs', 'Optional[DocumentArray]')], [('parameters', 'Dict', '{}')],
                'bar docstring\n:param docs:\n:param parameters:', '[\'/bar\']'
            ),
        ])
    ),
    (
        Path(__file__).parent / 'cases' / 'executor_3',
        ('Executor3', 'Executor 3', (
            [('self', None)],
            [('arg1', 'int', '1'), ('arg2', 'Tuple[str, str]', '(\'123  123\', \'test\\ntest\')')],
            None
        ), [
            ('foo', [('self', None), ('docs', 'DocumentArray')], [('parameters', 'Dict', '{}')], 'foo docstring',
             '[\'/foo\']'),
            ('bar', [('self', None), ('docs', 'DocumentArray')], [('parameters', 'Dict', '{}')], 'bar docstring',
             'ALL'),
        ])
    ),
])
def test_get_executor_args(package_path, expected):
    executor, docstring, init, endpoints, filepath = core.normalize(package_path, meta={'jina': 'master'}, env={})
    expected_executor, expected_docstring, expected_init, expected_endpoints = expected
    assert executor == expected_executor
    assert docstring == expected_docstring
    assert init == expected_init
    assert endpoints == expected_endpoints

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
