import io
from posixpath import basename
from textwrap import dedent
from typing import Dict, List

from dockerfile_parse import DockerfileParser


class ExecutorDockerfile:
    def __init__(self, build_args: Dict = {'JINA_VERSION': 'master'}):
        self._buffer = io.BytesIO()
        self._parser = DockerfileParser(
            fileobj=self._buffer, env_replace=True, build_args=build_args
        )

        dockerfile_template = dedent(
            """\
            FROM jinaai/jina:{0}

            ARG JINA_VERSION

            # setup the workspace
            COPY . /workspace
            WORKDIR /workspace

            # install the third-party requirements
            RUN pip install -r requirements.txt

            """
        )

        self._parser.content = dockerfile_template.format(build_args['JINA_VERSION'])

        self._has_unittests = False

        self._entrypoint = None

    def __str__(self):
        return self.content

    def add_unitest(self):
        self._parser.content += dedent(
            """\
            # for testing the image
            RUN pip install pytest && pytest

            """
        )

    @property
    def content(self):
        return self._parser.content

    @property
    def lines(self):
        return self._parser.lines

    @property
    def baseimage(self):
        return self._parser.baseimage

    @baseimage.setter
    def baseimage(self, value: str):
        self._parser.baseimage = value

    @property
    def entrypoint(self):
        return self._entrypoint

    @entrypoint.setter
    def entrypoint(self, commands: List[str]):
        self._entrypoint = commands
        command_line = ', '.join([f'"{c}"' for c in commands])

        entrypoint_line = f'ENTRYPOINT [{command_line}]'

        if self._parser.lines[-1].startswith('ENTRYPOINT'):
            self._parser.content = ''.join(self.lines[:-1] + [entrypoint_line])
        else:
            self._parser.content += entrypoint_line

    def dumps(self):
        return self._buffer.getvalue().decode()

    def dump(self, dockerfile: str):
        with open(dockerfile, 'wb') as fp:
            fp.write(self._buffer.getvalue())
