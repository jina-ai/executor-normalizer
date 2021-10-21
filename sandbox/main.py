import click
from jina import __version__ as __jina_version__
from server import __version__
from .core import deploy

@click.group()
def cli():
    pass

@cli.command()
@click.option('--executor', type=str, required=True)
@click.option('--endpoints', type=str, multiple=True)
@click.option('--replicas', type=int, default=1)
@click.version_option(
    f'{__version__} (Jina=v{__jina_version__})',
    prog_name='executor-sandbox',
)
def deploy(executor, endpoints, replicas):
    """Deploy Jina Executor Sandbox"""
    deploy(executor, endpoints, replicas)


if __name__ == "__main__":
    cli()