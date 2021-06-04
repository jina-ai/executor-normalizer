import os

import numpy as np
import pytest

from normalizer.docker import ExecutorDockerfile

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_exe_dockerfile(exe_dockerfile):
    print(exe_dockerfile.content)
