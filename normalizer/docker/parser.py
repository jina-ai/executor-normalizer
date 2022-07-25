import io
from re import template
from normalizer import docker
from pathlib import Path
from posixpath import basename
from textwrap import dedent
from typing import Dict, List
import re
FROM_VAR_RE = re.compile(r"(?P<var>(?P<name>FROM .*))")

from dockerfile_parse import DockerfileParser


class ExecutorDockerfile:
    def __init__(
        self, docker_file: 'Path' = None, build_args: Dict = {'JINA_VERSION': 'master'}
    ):
        self._buffer = io.BytesIO()
        if docker_file and docker_file.exists():
            self._buffer.write(docker_file.open('rb').read())
            self._parser = DockerfileParser(
                fileobj=self._buffer, env_replace=True, build_args=build_args
            )
        else:

            self._parser = DockerfileParser(
                fileobj=self._buffer, env_replace=True, build_args=build_args
            )

            dockerfile_template = dedent(
                """\
                # This file is automatically generated by Jina executor normalizer plugin.
                # It is not intended for manual editing.

                FROM jinaai/jina:{0}-perf

                """
            )

            self._parser.content = dockerfile_template.format(
                build_args['JINA_VERSION']
            )

    def __str__(self):
        return self.content
    
    def get_build_args_envs(self, build_args_envs): 
        build_args = '';
        build_args_line_num = 0;
        for index, item in enumerate(build_args_envs):
            build_args_line_num += 1
            build_args += dedent(
            f"""\
            ARG {item}
            """
        )
        build_envs = '';
        build_envs_line_num = 0
        for index, item in enumerate(build_args_envs):
            build_envs_line_num += 1
            build_envs += dedent(
            f"""\
            ENV {item}=${item}
            """
        )
        return (build_args, build_envs, build_args_line_num, build_envs_line_num)
    
    def insert_build_args_envs(self, build_args_envs):
        build_args, build_envs, build_args_line_num, build_envs_line_num = self.get_build_args_envs(build_args_envs)
        build_args_envs_line_num = 0;
        build_args_envs_str = '';
        if len(build_args): 
            build_args_envs_str += build_args
            build_args_envs_line_num += build_args_line_num
        
        if len(build_envs): 
            build_args_envs_str += build_envs
            build_args_envs_line_num += build_envs_line_num

        if len(build_args_envs_str):
            insert_num = 0
            for index, line in enumerate(self._parser.lines):
                if (FROM_VAR_RE.match(line) is not None):
                    insert_line_num = index + insert_num * build_args_envs_line_num + 1
                    self._parser.add_lines_at(insert_line_num, build_args_envs_str)
                    insert_num += 1

    def add_apt_installs(self, tools):
        instruction_template = dedent(
            """\
            # install the third-party requirements
            RUN apt-get update && apt-get install --no-install-recommends -y {0} \\
                && rm -rf /var/lib/apt/lists/*

            """
        )
        content = instruction_template.format(' '.join(tools))
        self._parser.content += content

    def add_work_dir(self):
        content = dedent(
            """\
            # setup the workspace
            COPY . /workspace
            WORKDIR /workspace

            """
        )
        self._parser.content += content

    def add_unitest(self):
        self._parser.content += dedent(
            """\

            """
        )

    def add_pip_install(self):
        self._parser.content += dedent(
            """\
            # install the third-party requirements
            RUN pip install --default-timeout=1000 --compile --no-cache-dir \\
                 -r requirements.txt

            """
        )

    @property
    def is_multistage(self):
        return self._parser.is_multistage()

    @property
    def parent_images(self):
        return self._parser.parent_images

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
        """
        Determine the final ENTRYPOINT instruction, if any, in the final build stage.
        ENTRYPOINTs from earlier stages are ignored.
        :return: value of final stage ENTRYPOINT
        """
        value = None
        for insndesc in self._parser.structure:
            if insndesc['instruction'] == 'FROM':  # new stage, reset
                value = None
            elif insndesc['instruction'].upper() == 'ENTRYPOINT':
                value = insndesc['value'].strip()
        return value

    @entrypoint.setter
    def entrypoint(self, values: List[str]):
        """
        setter for final 'entrypoint' instruction in final build stage
        """
        cmd = None
        for insndesc in self._parser.structure:
            if insndesc['instruction'] == 'FROM':  # new stage, reset
                cmd = None
            elif insndesc['instruction'].upper() == 'ENTRYPOINT':
                cmd = insndesc

        new_cmd = 'ENTRYPOINT ' + '[' + ', '.join([f'"{_}"' for _ in values]) + ']'
        if cmd:
            self._parser.add_lines_at(cmd, new_cmd, replace=True)
        else:
            self._parser.add_lines(new_cmd)

    def set_entrypoint(self, value: str):
        """
        setter for final 'entrypoint' instruction in final build stage
        """
        cmd = None
        for insndesc in self._parser.structure:
            if insndesc['instruction'] == 'FROM':  # new stage, reset
                cmd = None
            elif insndesc['instruction'].upper() == 'ENTRYPOINT':
                cmd = insndesc

        new_cmd = 'ENTRYPOINT ' + value
        if cmd:
            self._parser.add_lines_at(cmd, new_cmd, replace=True)
        else:
            self._parser.add_lines(new_cmd)

    # @property
    # def entrypoint(self):
    #     return self._entrypoint

    # @entrypoint.setter
    # def entrypoint(self, commands: List[str]):
    #     self._entrypoint = commands
    #     command_line = ', '.join([f'"{c}"' for c in commands])

    #     entrypoint_line = f'ENTRYPOINT [{command_line}]'

    #     if self._parser.lines[-1].startswith('ENTRYPOINT'):
    #         self._parser.content = ''.join(self.lines[:-1] + [entrypoint_line])
    #     else:
    #         self._parser.content += entrypoint_line

    def dumps(self):
        return self._buffer.getvalue().decode()

    def dump(self, dockerfile: str):
        with open(dockerfile, 'wb') as fp:
            fp.write(self._buffer.getvalue())
