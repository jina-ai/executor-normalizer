import pathlib
from typing import Dict

from jina.helper import colored, get_readable_size
import jinja2

from .docker import ExecutorDockerfile
from .excepts import (
    DependencyError,
    ExecutorExistsError,
    ExecutorNotFoundError,
    IllegalExecutorError,
)
from .helper import (
    inspect_executors,
    get_config_template,
    load_manifest,
    order_py_modules,
)
from normalizer import excepts


def filter_executors(executors):
    result = []
    for i, (executor, func_args, func_args_defaults, _) in enumerate(executors):
        if len(func_args) - len(func_args_defaults) == 1:
            result.append(executors[i])
    return result


def normalize(
    work_path: 'pathlib.Path',
    meta: Dict = {'jina': 'master'},
    env: Dict = {},
    verbose: bool = False,
    **kwargs,
) -> None:
    """Normalize the executor package.

    :param work_path: the executor folder where it located
    :param meta: the version info of the Jina to work with
    :param env: the environment variables the Jina works with
    :param verbose : set verbose level
    """
    if verbose:
        print(f'=> The executor repository is located at: {work_path}')

        print(f'=> The Jina version info: ')
        for k, v in meta.items():
            print('%20s: -> %20s' % (k, v))

        print(f'=> The environment variables: ')
        for k, v in env.items():
            print('%20s: -> %20s' % (k, v))

    if not work_path.exists():
        raise FileNotFoundError(
            f'The folder "{work_path}" does not exist, can not normalize'
        )

    dockerfile_path = work_path / 'Dockerfile'
    manifest_path = work_path / 'manifest.yml'
    config_path = work_path / 'config.yml'
    readme_path = work_path / 'README.md'
    requirements_path = work_path / 'requirements.txt'

    py_glob = list(work_path.glob('*.py'))
    test_glob = list(work_path.glob('tests/test_*.py'))

    completeness = {
        'Dockerfile': dockerfile_path,
        'manifest.yml': manifest_path,
        'config.yml': config_path,
        'README.md': readme_path,
        'requirements.txt': requirements_path,
        '*.py': py_glob,
        'tests': test_glob,
    }

    if verbose:
        print(
            f'=> checking executor repository ...\n'
            + '\n'.join(
                f'\t{colored("✓", "green") if v else colored("✗", "red"):>4} {k:<20} {v}'
                for k, v in completeness.items()
            )
            + '\n'
        )

    if not requirements_path.exists():
        requirements_path.touch()

    # manifest = load_manifest(manifest_path)

    executor = None

    if not config_path.exists():
        # inspect executor
        executors = inspect_executors(py_glob)
        if len(executors) == 0:
            raise ExecutorNotFoundError
        if len(executors) > 1:
            raise ExecutorExistsError

        executors = filter_executors(executors)
        if len(executors) == 0:
            raise IllegalExecutorError

        executor, *_ = executors[0]
        # try:
        #     py_moduels = order_py_modules(py_glob, work_path)
        # except Exception as ex:
        #     raise DependencyError
        py_modules = [f'{p.relative_to(work_path)}' for p in py_glob]

        # render config.yml content
        template = get_config_template()
        config_content = template.render(executor=executor, py_modules=py_modules)

        # dump config.yml
        with open(config_path, 'w') as f:
            f.write(config_content)

    if not dockerfile_path.exists():
        dockerfile = ExecutorDockerfile(build_args={'JINA_VERSION': meta['jina']})

        if len(test_glob) > 0:
            dockerfile.add_unitest()

        dockerfile.entrypoint = [
            'jina',
            'pod',
            '--uses',
            f'{config_path.relative_to(work_path)}',
        ]

        dockerfile.dump(dockerfile_path)
