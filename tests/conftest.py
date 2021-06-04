import os
import random
import string

import pytest

from normalizer.docker import ExecutorDockerfile


@pytest.fixture(scope='function', autouse=False)
def exe_dockerfile():
    return ExecutorDockerfile()
