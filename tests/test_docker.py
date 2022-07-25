import os
from pathlib import Path
import pytest

from normalizer.docker import ExecutorDockerfile

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_dockerfile(exe_dockerfile):
    assert exe_dockerfile.baseimage == 'jinaai/jina:master-perf'
    assert exe_dockerfile.entrypoint is None


def test_entrypoint(exe_dockerfile):
    exe_dockerfile.entrypoint = ['jina', 'pod']
    assert exe_dockerfile.lines[-1].strip() == 'ENTRYPOINT ["jina", "pod"]'
    assert exe_dockerfile.entrypoint == '["jina", "pod"]'

    exe_dockerfile.set_entrypoint('["jina", "pod", "--uses", "config.yml"]')
    assert exe_dockerfile.entrypoint == '["jina", "pod", "--uses", "config.yml"]'
    assert (
        exe_dockerfile.lines[-1].strip()
        == 'ENTRYPOINT ["jina", "pod", "--uses", "config.yml"]'
    )


def test_baseimage(exe_dockerfile):
    assert exe_dockerfile.baseimage == 'jinaai/jina:master-perf'
    assert exe_dockerfile.lines[3] == 'FROM jinaai/jina:master-perf\n'

    exe_dockerfile.baseimage = 'jinaai/jina:latest-perf'
    assert exe_dockerfile.baseimage == 'jinaai/jina:latest-perf'
    assert exe_dockerfile.lines[3] == 'FROM jinaai/jina:latest-perf\n'


@pytest.mark.parametrize(
    'build_args_envs',
    [   
        (
             { 
                'AUTH_TOKEN': "AUTH_TOKEN",
                'TOKEN': 'ghp_Nwh9o70GDSzs'
            }
        ),
    ],
)
def test_load_dockerfile(build_args_envs):
    docker_file = Path(__file__).parent / 'docker_cases' / 'Dockerfile.case1'
    docker_expect_file = Path(__file__).parent / 'docker_cases' / 'Dockerfile.case1.expect'

    parser = ExecutorDockerfile(docker_file=docker_file)
    parser.insert_build_args_envs(build_args_envs)

    expect_parser = ExecutorDockerfile(docker_file=docker_expect_file)
    
    assert str(parser) == str(expect_parser)
    assert len(parser.parent_images) == 1
    assert parser.baseimage == 'jinaai/jina:2.0-perf'
    assert parser.entrypoint == '["jina", "executor", "--uses", "config.yml"]'
    assert (
        parser.lines[-1].strip()
        == 'ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]'
    )

    parser.entrypoint = ['jina', 'pod', '--uses']
    assert parser.entrypoint == '["jina", "pod", "--uses"]'
    assert parser.lines[-1].strip() == 'ENTRYPOINT ["jina", "pod", "--uses"]'


def test_dump(exe_dockerfile):
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(delete=False)

    exe_dockerfile.dump(temp_file.name)

    with open(temp_file.name, 'r') as fp:
        lines = fp.readlines()

        assert lines == exe_dockerfile.lines

    os.unlink(temp_file.name)
