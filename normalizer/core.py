import ast
import pathlib
from typing import Dict, List

from jina.helper import colored, get_readable_size
import jinja2

from .docker import ExecutorDockerfile
from .excepts import (
    DependencyError,
    ExecutorExistsError,
    ExecutorNotFoundError,
    IllegalExecutorError,
)
from .helper import (
    get_config_template,
    get_imports,
    resolve_import,
    topological_sort,
)
from normalizer import excepts


def order_py_modules(py_modules: List['pathlib.Path'], work_path: 'pathlib.Path'):

    dependencies = {x: [] for x in py_modules}

    for py_module in py_modules:
        py_imports = [m[:-1] for m in get_imports(py_module) if m[-1] is None]

        py_import_moduels = [resolve_import(*m, work_path) for m in py_imports]
        for imp_m in py_import_moduels:
            if imp_m is None:
                continue
            if imp_m not in dependencies:
                dependencies[imp_m] = []
            dependencies[py_module].append(imp_m)

    orders = list(topological_sort([(k, v) for k, v in dependencies.items()]))
    return orders


def inspect_executors(py_modules: List['pathlib.Path']):
    def _inspect_class_defs(tree):
        return [o for o in ast.walk(tree) if isinstance(o, ast.ClassDef)]

    executors = []
    for filepath in py_modules:
        with filepath.open() as fin:
            tree = ast.parse(fin.read(), filename=str(filepath))

            for class_def in _inspect_class_defs(tree):
                base_name = None
                for base_class in class_def.bases:
                    # if the class looks like class MyExecutor(Executor)
                    if isinstance(base_class, ast.Name):
                        base_name = base_class.id
                    # if the class looks like class MyExecutor(jina.Executor):
                    if isinstance(base_class, ast.Attribute):
                        base_name = base_class.attr
                if base_name != 'Executor':
                    continue

                has_init_func = False
                for body_item in class_def.body:
                    # check __init__ function arguments
                    if (
                        isinstance(body_item, ast.FunctionDef)
                        and body_item.name == '__init__'
                    ):
                        has_init_func = True

                        func_args = body_item.args.args
                        func_args_defaults = body_item.args.defaults

                        executors.append(
                            (class_def.name, func_args, func_args_defaults, filepath)
                        )
                if not has_init_func:
                    executors.append((class_def.name, ['self'], [], filepath))

    return executors


def filter_executors(executors):
    result = []
    for i, (executor, func_args, func_args_defaults, _) in enumerate(executors):
        if len(func_args) - len(func_args_defaults) == 1:
            result.append(executors[i])
    return result


def normalize(
    work_path: 'pathlib.Path',
    meta: Dict = {'jina': 'master'},
    env: Dict = {},
    verbose: bool = False,
    **kwargs,
) -> None:
    """Normalize the executor package.

    :param work_path: the executor folder where it located
    :param meta: the version info of the Jina to work with
    :param env: the environment variables the Jina works with
    :param verbose : set verbose level
    """
    if verbose:
        print(f'=> The executor repository is located at: {work_path}')

        print(f'=> The Jina version info: ')
        for k, v in meta.items():
            print('%20s: -> %20s' % (k, v))

        print(f'=> The environment variables: ')
        for k, v in env.items():
            print('%20s: -> %20s' % (k, v))

    if not work_path.exists():
        raise FileNotFoundError(
            f'The folder "{work_path}" does not exist, can not normalize'
        )

    dockerfile_path = work_path / 'Dockerfile'
    manifest_path = work_path / 'manifest.yml'
    config_path = work_path / 'config.yml'
    readme_path = work_path / 'README.md'
    requirements_path = work_path / 'requirements.txt'

    py_glob = list(work_path.glob('*.py'))
    test_glob = list(work_path.glob('tests/test_*.py'))

    completeness = {
        'Dockerfile': dockerfile_path,
        'manifest.yml': manifest_path,
        'config.yml': config_path,
        'README.md': readme_path,
        'requirements.txt': requirements_path,
        '*.py': py_glob,
        'tests': test_glob,
    }

    if verbose:
        print(
            f'=> checking executor repository ...\n'
            + '\n'.join(
                f'\t{colored("✓", "green") if (v if isinstance(v, list) else v.exists()) else colored("✗", "red"):>4} {k:<20} {v}'
                for k, v in completeness.items()
            )
            + '\n'
        )

    if not requirements_path.exists():
        requirements_path.touch()

    # manifest = load_manifest(manifest_path)

    executor = None

    if not config_path.exists():
        # inspect executor
        executors = inspect_executors(py_glob)
        if len(executors) == 0:
            raise ExecutorNotFoundError
        if len(executors) > 1:
            raise ExecutorExistsError

        executors = filter_executors(executors)
        if len(executors) == 0:
            raise IllegalExecutorError

        executor, *_ = executors[0]
        try:
            py_moduels = order_py_modules(py_glob, work_path)
        except Exception as ex:
            raise DependencyError
        py_modules = [f'{p.relative_to(work_path)}' for p in py_moduels]

        # render config.yml content
        template = get_config_template()
        config_content = template.render(executor=executor, py_modules=py_modules)

        # dump config.yml
        with open(config_path, 'w') as f:
            f.write(config_content)

    if not dockerfile_path.exists():
        dockerfile = ExecutorDockerfile(build_args={'JINA_VERSION': meta['jina']})

        # if len(test_glob) > 0:
        #     dockerfile.add_unitest()

        dockerfile.entrypoint = [
            'jina',
            'executor',
            '--uses',
            f'{config_path.relative_to(work_path)}',
        ]

        dockerfile.dump(dockerfile_path)
