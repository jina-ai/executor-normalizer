import pathlib

import click
from jina import __version__ as __iina_version__

from . import __version__ as __normalizer_version__
from .core import normalize


@click.command()
@click.argument('path', default='.')
@click.option('--jina-version', default='2.0.0', help='Specify the jina version.')
@click.option('--verbose', '-v', is_flag=True, help='Enables verbose mode.')
@click.version_option(
    f'{__normalizer_version__} (Jina=v{__iina_version__})',
    prog_name='executor-normarlizer',
)
def cli(path, jina_version, verbose):
    """Jina Executor Normalizer."""
    normalize(pathlib.Path(path), meta={'jina': jina_version}, verbose=verbose)


if __name__ == '__main__':
    cli()
