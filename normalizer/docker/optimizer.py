import io
from posixpath import basename
from textwrap import dedent
from typing import Dict, List
from pathlib import Path
from dockerfile_parse import DockerfileParser
from .parser import ExecutorDockerfile

class DockerfileOptimizer:
    def __init__(self, docker_file: 'Path' = None, build_args: Dict = {'JINA_VERSION': 'master'}):
        self._parser = ExecutorDockerfile(docker_file=docker_file, build_args=build_args)

    def __str__(self):
        return self.content

    