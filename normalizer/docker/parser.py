from textwrap import dedent

from dockerfile_parse import DockerfileParser


class ExecutorDockerfile:
    def __init__(self, build_args={'JINA_VERSION': 'master'}):
        self._parser = DockerfileParser(env_replace=True, build_args=build_args)

        template = dedent(
            """\
            ARG JINA_VERSION
            ARG BUILD_DATE

            FROM jinaai/jina:$JINA_VERSION

            # setup the workspace
            COPY . /workspace
            WORKDIR /workspace

            # install the third-party requirements
            RUN pip install -r requirements.txt

            # for testing the image
            RUN pip install pytest && pytest
            """
        )

        self._parser.content = template.format()

    @property
    def content(self):
        return self._parser.content
