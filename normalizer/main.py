import pathlib

import click
from jina import __version__ as __jina_version__

from server import __version__
from .core import normalize


@click.command()
@click.argument('path', default='.')
@click.option('--jina-version', default='2', help='Specify the jina version.')
@click.option('--verbose', '-v', is_flag=True, help='Enables verbose mode.')
@click.version_option(
    f'{__version__} (Jina=v{__jina_version__})',
    prog_name='executor-normarlizer',
)
def cli(path, jina_version, verbose):
    """Jina Executor Normalizer."""
    normalize(pathlib.Path(path), meta={'jina': jina_version}, verbose=verbose)


if __name__ == '__main__':
    cli()
