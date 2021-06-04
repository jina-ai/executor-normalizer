import os
import pathlib

import click
from jina import __version__ as __iina_version__
from jina.helper import colored, get_readable_size

from . import __version__
from .helper import load_manifest


@click.command()
@click.argument('path', default='.')
@click.option('--verbose', '-v', is_flag=True, help='Enables verbose mode.')
@click.version_option(
    f'{__version__} (Jina=v{__iina_version__})', prog_name='executor-normarlizer'
)
def cli(path, verbose):
    """Jina Executor Normalizer."""

    work_path = pathlib.Path(path)

    dockerfile_path = work_path / 'Dockerfile'
    manifest_path = work_path / 'manifest.yml'
    config_path = work_path / 'config.yml'
    readme_path = work_path / 'README.md'
    requirements_path = work_path / 'requirements.txt'

    py_glob = [_.as_posix() for _ in work_path.glob('*.py')]

    test_glob = [_.as_posix() for _ in work_path.glob('tests/test_*.py')]

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

    manifest = load_manifest(manifest_path)

    print(f'=> manifest: {manifest}')


if __name__ == '__main__':
    cli()
