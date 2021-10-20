import click
from .core import deploy

@click.command()
@click.option('--executor', type=str, required=True)
@click.option('--endpoints', type=str, multiple=True, required=True)
@click.option('--replicas', type=int, default=1)
def main(executor, endpoints, replicas):
    deploy(executor, endpoints, replicas)


if __name__ == "__main__":
    main()