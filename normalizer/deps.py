from platform import version
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from packaging.version import parse

from pipreqs import pipreqs
from pypi_simple import PyPISimple

from collections import namedtuple

Package = namedtuple('Package', ['name', 'version'])


def get_dep_tools(pkg: str):
    tool_deps = []
    if 'git+http' in pkg.name:
        tool_deps.append('git')
    return tool_deps


def get_baseimage(pkg: str) -> Tuple[str, str]:
    # base_image = None
    # version_tag = None
    # if pkg.name in ['tensorflow', 'tensorflow-cpu', 'tensorflow-gpu']:
    #     base_image = 'tensorflow/tensorflow'
    #     version_tag = pkg.version
    #     if pkg.name == 'tensorflow-gpu':
    #         version_tag += '-gpu'
    #     if pkg.version and pkg.version <= '2.1.0':
    #         version_tag += f'-py3'
    # elif pkg.name in ['pytorch', 'torch']:
    #     if pkg.version and pkg.version.endswith('+cpu'):
    #         base_image = 'bitnami/pytorch'
    #         version_tag = pkg.version.split('+')[0]
    #     else:
    #         base_image = 'pytorch/pytorch'
    #         version_tag = f'{pkg.version}-cuda10.2-cudnn7-runtime'
    # else:
    #     # return None, None
    #     return None

    # # return base_image, version_tag
    # return f'{base_image}:{version_tag}'
    return None


def get_all_imports(
    path: 'Path',
    encoding: str = 'utf-8',
    extra_ignore_dirs=[],
    follow_links=True,
):
    return pipreqs.get_all_imports(
        str(path),
        encoding=encoding,
        extra_ignore_dirs=extra_ignore_dirs + ['.jina'],
        follow_links=follow_links,
    )


def get_import_info(import_name):
    try:
        with PyPISimple() as client:
            result = client.get_project_page(import_name)
            if len(result.packages) == 0:
                return None

            pkg = sorted(result.packages, key=lambda p: parse(p.version), reverse=True)[
                0
            ]

            if pkg.project == import_name:
                return Package(pkg.project, pkg.version)
    except Exception as ex:
        # print(f'Package {import_name} does not exist or network problems')
        return None


def get_pkg_names(pkgs):
    """Get PyPI package names from a list of imports.
    Args:
        pkgs (List[str]): List of import names.
    Returns:
        List[str]: The corresponding PyPI package names.
    """
    return pipreqs.get_pkg_names(pkgs)


def dump_requirements(path: 'Path', imports: List[Dict] = []):
    with path.open('w') as f:

        for m in imports:
            if m.version:
                f.write(f'{m.name}=={m.version}\n')
            else:
                f.write(f'{m.name}\n')


def parse_requirements(path: 'Path'):
    """Parse a requirements formatted file.
    Traverse a string until a delimiter is detected, then split at said
    delimiter, get module name by element index, create a dict consisting of
    module:version, and add dict to list of parsed modules.

    :param path: the file to parse
    :return: list of requiemented modules, excluding comments.

    """
    return pipreqs.parse_requirements(str(path))
