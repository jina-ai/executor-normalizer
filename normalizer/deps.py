from pathlib import Path
from pipreqs import pipreqs
from pypi_simple import PyPISimple


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
            pkg = result.packages[0]

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
