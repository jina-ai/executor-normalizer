from posixpath import basename
from textwrap import dedent
from typing import Dict, List

from dockerfile_parse import DockerfileParser


class ExecutorDockerfile:
    def __init__(self, build_args: Dict = {'JINA_VERSION': 'master'}):
        self._parser = DockerfileParser(env_replace=True, build_args=build_args)

        dockerfile_template = dedent(
            """\
            ARG JINA_VERSION
            FROM jinaai/jina:$JINA_VERSION

            ARG JINA_VERSION

            # setup the workspace
            COPY . /workspace
            WORKDIR /workspace

            # install the third-party requirements
            RUN pip install -r requirements.txt

            # for testing the image
            RUN pip install pytest && pytest
            """
        )

        self._parser.content = dockerfile_template.format()

        self._entrypoint = None

    def __str__(self):
        return self.content

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

    def dumps(self, dockerfile: str):
        with open(dockerfile, 'wb') as fp:
            fp.write(self.content.encode('utf-8'))
