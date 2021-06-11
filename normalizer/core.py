import pathlib

from jina.helper import colored, get_readable_size

from .docker import ExecutorDockerfile
from .excepts import (
    DependencyError,
    ExecutorExistsError,
    ExecutorNotFoundError,
    IllegalExecutorError,
)
from .helper import inspect_executors, load_manifest, order_py_modules


def filter_executors(executors):
    result = []
    for i, (executor, func_args, func_args_defaults, _) in enumerate(executors):
        if len(func_args) - len(func_args_defaults) == 1:
            result.append(executors[i])
    return result


def normalize(
    work_path: 'pathlib.Path',
    jina_version: str = 'master',
    verbose: bool = False,
) -> None:
    """Normalize the executor package.

    :param work_path: the executor folder where it located
    :param jina_version: the version of Jina to work with
    :param verbose : set verbose level
    """
    if verbose:
        print(f'=> The executor repository is located at: {work_path}')

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

    if not dockerfile_path.exists():
        dockerfile = ExecutorDockerfile(build_args={'JINA_VERSION': jina_version})

        if len(test_glob) > 0:
            dockerfile.add_unitest()

        if config_path.exists():
            dockerfile.entrypoint = [
                'jina',
                'pod',
                '--uses',
                f'{config_path.relative_to(work_path)}',
            ]
        else:
            executors = inspect_executors(py_glob)
            if len(executors) == 0:
                raise ExecutorNotFoundError
            if len(executors) > 1:
                raise ExecutorExistsError

            executors = filter_executors(executors)
            if len(executors) == 0:
                raise IllegalExecutorError

            executor, *_ = executors[0]

            try:
                py_moduels = order_py_modules(py_glob, work_path)
            except Exception as ex:
                raise DependencyError

            entrypoint_args = ['jina', 'pod', '--uses', f'{executor}']
            for p in py_moduels:
                entrypoint_args.append('--py-modules')
                entrypoint_args.append(f'{p.relative_to(work_path)}')

            dockerfile.entrypoint = entrypoint_args

        dockerfile.dump(dockerfile_path)
