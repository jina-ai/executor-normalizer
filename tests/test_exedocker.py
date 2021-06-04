import os

import numpy as np
import pytest

from normalizer.docker import ExecutorDockerfile

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_dockerfile(exe_dockerfile):
    assert exe_dockerfile.entrypoint is None


def test_entrypoint(exe_dockerfile):
    exe_dockerfile.entrypoint = ['jina', 'pod']
    assert exe_dockerfile.lines[-1] == 'ENTRYPOINT ["jina", "pod"]'

    exe_dockerfile.entrypoint = ['jina', 'pod', '--uses']
    assert exe_dockerfile.lines[-1] == 'ENTRYPOINT ["jina", "pod", "--uses"]'


def test_baseimage(exe_dockerfile):
    assert exe_dockerfile.baseimage == 'jinaai/jina:master'

    exe_dockerfile.baseimage = 'jinaai/jina:latest'
    assert exe_dockerfile.baseimage == 'jinaai/jina:latest'
    assert exe_dockerfile.lines[1] == 'FROM jinaai/jina:latest\n'
