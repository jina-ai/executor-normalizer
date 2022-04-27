import pathlib
import click

from jina import __version__ as __jina_version__
from server import __version__
from normalizer.core import normalize as normalizer_normalize
from generator.core import generate as generate_yaml

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

@cli.command()
@click.argument('executor')
@click.option('--type', type=click.Choice(['k8s', 'docker_compose', 'jcloud']), default='k8s', help='Specify the deployment type.')
def generate(executor, type):
    """
    Generate corresponding deployment files for EXECUTOR.

    EXECUTOR format should be in the form of:
    <executor_name>[/<executor_tag>]
    For example: `Hello/latest` or just `Hello`
    """

    return generate_yaml(executor, type)


if __name__ == "__main__":
    cli()