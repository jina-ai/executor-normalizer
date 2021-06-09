import os
import pathlib
from typing import List

import click
from jina import __version__ as __iina_version__
from jina.helper import colored, get_readable_size

from . import __version__
from .docker import ExecutorDockerfile
from .helper import load_manifest


def inspect_executors(py_modules: List[str]):
    def _inspect_class_defs(tree):
        return [o for o in ast.walk(tree) if isinstance(o, ast.ClassDef)]

    import ast

    classes = []
    for filepath in py_modules:
        # with open(filename, mode='rt') as fin:
        with filepath.open() as fin:
            tree = ast.parse(fin.read(), filename=str(filepath))
            # print(tree)
            # print(filepath)
            # for o in tree.body:
            #     print(o)
            classes.extend(_inspect_class_defs(tree))
            # print(_inspect_class_defs(tree))
    class_names = [obj.name for obj in classes]

    executors = []
    for base_class in classes[0].bases:
        # if the test class looks like class Test(TestCase)
        if isinstance(base_class, ast.Name):
            base_name = base_class.id
        # if the test class looks like class Test(unittest.TestCase):
        if isinstance(base_class, ast.Attribute):
            base_name = base_class.attr
        if base_name == 'Executor':
            executors.append(classes[0].name)

    return executors


def normalize(
    path,
    executor_class: str = None,
    executor_py_path: str = None,
    config_yaml_path: str = None,
    jina_version: str = 'master',
    verbose: bool = False,
):
    work_path = pathlib.Path(path)

    if verbose:
        print(f'=> The executor repository is located at: {work_path}')

    dockerfile_path = work_path / 'Dockerfile'
    manifest_path = work_path / 'manifest.yml'
    config_path = (
        pathlib.Path(config_yaml_path) if config_yaml_path else work_path / 'config.yml'
    )
    readme_path = work_path / 'README.md'
    requirements_path = work_path / 'requirements.txt'

    # py_glob = [_.as_posix() for _ in work_path.glob('*.py')]

    # test_glob = [_.as_posix() for _ in work_path.glob('tests/test_*.py')]

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

    manifest = load_manifest(manifest_path)

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
        elif executor_class:
            entrypoint_args = ['jina', 'pod', '--uses', f'{executor_class}']
            for p in py_glob:
                entrypoint_args.append('--py-modules')
                entrypoint_args.append(f'{p.relative_to(work_path)}')

            dockerfile.entrypoint = entrypoint_args
        else:
            executors = inspect_executors(py_glob)

            entrypoint_args = ['jina', 'pod', '--uses', f'{executors[0]}']
            for p in py_glob:
                entrypoint_args.append('--py-modules')
                entrypoint_args.append(f'{p.relative_to(work_path)}')

            dockerfile.entrypoint = entrypoint_args

        dockerfile.dump(dockerfile_path)


@click.command()
@click.argument('path', default='.')
@click.option('--jina-version', default='master', help='Specify the jina version.')
@click.option('--verbose', '-v', is_flag=True, help='Enables verbose mode.')
@click.version_option(
    f'{__version__} (Jina=v{__iina_version__})', prog_name='executor-normarlizer'
)
def cli(path, jina_version, verbose):
    """Jina Executor Normalizer."""
    normalize(path, jina_version=jina_version, verbose=verbose)


if __name__ == '__main__':
    cli()
