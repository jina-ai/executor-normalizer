from typing import List, Dict, Optional
from pathlib import Path
from packaging.version import parse

from pipreqs import pipreqs
from pypi_simple import PyPISimple
from loguru._logger import Logger


def get_sys_deps(requiremnt: 'Path'):
    pass


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
                return pkg
    except Exception as ex:
        # print(f'Package {import_name} does not exist or network problems')
        return None


def get_imports_info(imports):
    result = []

    for item in imports:
        pkg = get_import_info(item)
        if pkg:
            result.append({'name': pkg.project, 'version': pkg.version})
    return result


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
            if 'version' in m:
                f.write(f'{m["name"]}=={m["version"]}\n')
            else:
                f.write(f'{m["name"]}\n')


def parse_requirements(path: 'Path'):
    """Parse a requirements formatted file.
    Traverse a string until a delimiter is detected, then split at said
    delimiter, get module name by element index, create a dict consisting of
    module:version, and add dict to list of parsed modules.

    :param path: the file to parse
    :return: list of requiemented modules, excluding comments.

    """
    return pipreqs.parse_requirements(str(path))
