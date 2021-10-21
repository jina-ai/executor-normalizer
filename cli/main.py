import pathlib
import click

from jina import __version__ as __jina_version__
from server import __version__
from normalizer.core import normalize as normalizer_normalize
from sandbox.core import deploy as sandbox_deploy

@click.group()
@click.version_option(
    f'{__version__} (Jina=v{__jina_version__})',
    prog_name='executor-manager',
)
def cli():
    pass

@cli.command()
@click.argument('path', default='.')
@click.option('--jina-version', default='2', help='Specify the jina version.')
@click.option('--verbose', '-v', is_flag=True, help='Enables verbose mode.')
def normalize(path, jina_version, verbose):
    normalizer_normalize(pathlib.Path(path), meta={'jina': jina_version}, verbose=verbose)

@cli.group()
def sandbox():
    pass

@sandbox.command()
@click.option('--executor', type=str, required=True)
@click.option('--endpoints', type=str, multiple=True)
@click.option('--replicas', type=int, default=1)
def deploy(executor, endpoints, replicas):
    """Deploy Jina Executor Sandbox"""
    sandbox_deploy(executor, endpoints, replicas)


if __name__ == "__main__":
    cli()