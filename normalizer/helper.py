import pathlib
from typing import Dict, List
import toml
import re
from pprint import pformat
from loguru import logger
from jinja2 import Environment, FileSystemLoader
from jina.jaml import JAML
from importlab.import_finder import get_imports
from importlab.resolve import convert_to_path
from . import __resources_path__


def convert_from_to_path(from_state, base_dir: 'pathlib.Path' = pathlib.Path('.')):
    """
    Convert a state name to a path.

    :param from_state: the state name
    :param base_dir: the base directory to search
    :return: the path to the state
    """
    for i, c in enumerate(from_state):
        if c != '.':
            break

    if i > 0:
        path_name = from_state[:i] + '/' + from_state[i:].replace('.', '/')
    else:
        path_name = from_state.replace('.', '/')

    if base_dir.joinpath(path_name + '.py').exists():
        return base_dir.joinpath(path_name + '.py')
    elif base_dir.joinpath(path_name + '/__init__.py').exists():
        return base_dir.joinpath(path_name + '/__init__.py')
    return None


def load_manifest(yaml_path: 'pathlib.Path') -> Dict:
    """Load manifest of executor from YAML file."""
    with open(__resources_path__ / 'manifest.yml') as fp:
        tmp = JAML.load(
            fp
        )  # do not expand variables at here, i.e. DO NOT USE expand_dict(yaml.load(fp))

    if yaml_path.exists():
        with open(yaml_path) as fp:
            tmp.update(JAML.load(fp))

    return tmp


def convert_version(version: str) -> str:
    """Convert version specifier to requirements.txt format."""
    version = re.sub(r'~=|==|!=|>=|<=', '', version)
    if version.startswith('^'):
        version = '==' + version[1:]
    elif version.startswith('~'):
        version = (
            '>='
            + version[1:]
            + ','
            + '<'
            + re.sub(r'[^\d\.]', '', version[1:])
            + '.999'
        )
    elif version.startswith('*') or version == '':
        version = ''
    else:
        version = '==' + version
    return version


def get_dependencies_from_pyproject(pyproject_path: 'pathlib.Path') -> List[str]:
    """Extract dependencies from pyproject.toml file."""
    try:
        with open(pyproject_path, 'r') as f:
            pyproject = toml.load(f)

        # Try to extract dependencies from different sections of pyproject.toml
        dependencies = pyproject.get('project', {}).get('dependencies')
        if dependencies is None:
            dependencies = (
                pyproject.get('tool', {}).get('poetry', {}).get('dependencies')
            )
        else:
            return dependencies

        if dependencies is None:
            raise KeyError

        # Convert dependencies to requirements.txt format
        requirements = []
        for package, version in dependencies.items():
            # Ignore "python" package since it's already specified in the runtime environment
            if package != 'python':
                version = convert_version(version)
                requirements.append(f'{package}{version}')

        return requirements

    except KeyError:
        logger.error(f'Could not find dependencies in {pyproject_path}')
        logger.error(f'pyproject.toml content:\n {pformat(pyproject)}')
        return []
    except Exception as e:
        logger.error(f'Error while processing {pyproject_path}: {e}')
        return []


def get_config_template():
    """Load a Jinja2 template for config.yml"""
    env = Environment(loader=FileSystemLoader(__resources_path__ / 'templates'))
    return env.get_template('config.yml.jinja2')


def resolve_import(name, alias, is_from, is_star, work_path):
    """Use python to resolve an import.

    :argument name: The fully qualified module name.
    :returns: the path to the module source file or None.
    """

    py_path = work_path / pathlib.Path(convert_to_path(name)[0])

    while True:
        if py_path.is_dir():
            if (py_path / '__init__.py').exists():
                return py_path / '__init__.py'
            return None

        if py_path.with_suffix('.py').exists():
            return py_path.with_suffix('.py')
        else:
            py_path = py_path.parent


# copy from: https://stackoverflow.com/a/11564323
def topological_sort(source):
    """perform topo sort on elements.

    :argument source: list of ``(name, [list of dependancies])`` pairs
    :returns: list of names, with dependancies listed first
    """
    pending = [
        (name, set(deps)) for name, deps in source
    ]  # copy deps so we can modify set in-place
    emitted = []
    while pending:
        next_pending = []
        next_emitted = []
        for entry in pending:
            name, deps = entry
            deps.difference_update(emitted)  # remove deps we emitted last pass
            if deps:  # still has deps? recheck during next pass
                next_pending.append(entry)
            else:  # no more deps? time to emit
                yield name
                emitted.append(
                    name
                )  # <-- not required, but helps preserve original ordering
                next_emitted.append(
                    name
                )  # remember what we emitted for difference_update() in next pass
        if (
            not next_emitted
        ):  # all entries have unmet deps, one of two things is wrong...
            raise ValueError(
                'cyclic or missing dependancy detected: %r' % (next_pending,)
            )
        pending = next_pending
        emitted = next_emitted


def choose_jina_version(client_version: str) -> str:
    if client_version == 'master':
        return 'master'

    from distutils.version import LooseVersion

    latest_version = get_jina_latest_version()

    return (
        latest_version
        if latest_version
        and LooseVersion(client_version) > LooseVersion(latest_version)
        else client_version
    )


def get_jina_latest_version() -> str:
    try:
        from urllib.request import Request, urlopen
        import json

        req = Request(
            'https://pypi.org/pypi/jina/json', headers={'User-Agent': 'Mozilla/5.0'}
        )

        with urlopen(req, timeout=1) as resource:
            latest_ver = json.load(resource)['info']['version']

            return latest_ver
    except:
        return None


def get_jina_image_tag(jina_version, py_version):
    py_tag = 'py37'
    if py_version.startswith('3.8'):
        py_tag = 'py38'
    elif py_version.startswith('3.9'):
        py_tag = 'py39'

    return f'{jina_version}-{py_tag}'
