import ast
from logging import log
import pathlib
from platform import version
from typing import Dict, List
from loguru import logger
from jina.helper import colored, get_readable_size
from .deps import (
    Package,
    get_all_imports,
    get_import_info,
    get_pkg_names,
    get_dep_tools,
    get_baseimage,
    dump_requirements,
    parse_requirements,
)
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
    choose_jina_version,
    get_jina_image_tag,
    is_empty
)
from normalizer import docker


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


def prelude(imports: List['Package']):
    dep_tools = set([])
    base_images = set([])
    for pkg in imports:
        for tool in get_dep_tools(pkg):
            dep_tools.add(tool)
        _base_image = get_baseimage(pkg)
        if _base_image:
            base_images.add(_base_image)
    return base_images, dep_tools


def normalize(
    work_path: 'pathlib.Path',
    meta: Dict = {'jina': '2.0.0'},
    env: Dict = {},
    **kwargs,
) -> None:
    """Normalize the executor package.

    :param work_path: the executor folder where it located
    :param meta: the version info of the Jina to work with
    :param env: the environment variables the Jina works with
    """

    logger.debug(f'=> The executor repository is located at: {work_path}')

    logger.debug(f'=> The Jina version info: ')
    for k, v in meta.items():
        logger.debug('%20s: -> %20s' % (k, v))

    logger.debug(f'=> The environment variables: ')
    for k, v in env.items():
        logger.debug('%20s: -> %20s' % (k, v))

    if not work_path.exists():
        raise FileNotFoundError(
            f'The folder "{work_path}" does not exist, can not normalize'
        )

    dockerfile_path = work_path / 'Dockerfile'
    manifest_path = work_path / 'manifest.yml'
    config_path = work_path / 'config.yml'
    readme_path = work_path / 'README.md'
    requirements_path = work_path / 'requirements.txt'
    freeze_path = work_path / 'requirements.lock'

    py_glob = list(work_path.glob('*.py'))
    test_glob = list(work_path.glob('tests/test_*.py'))

    completeness = {
        'Dockerfile': dockerfile_path,
        'manifest.yml': manifest_path,
        'config.yml': config_path,
        'README.md': readme_path,
        'requirements.txt': requirements_path,
        'requirements.lock': freeze_path,
        '*.py': py_glob,
        'tests': test_glob,
    }

    logger.info(
        f'=> checking executor repository ...\n'
        + '\n'.join(
            f'\t{colored("✓", "green") if (v if isinstance(v, list) else v.exists()) else colored("✗", "red"):>4} {k:<20} {v}'
            for k, v in completeness.items()
        )
        + '\n'
    )

    # if not requirements_path.exists():
    #     requirements_path.touch()

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

    imports = []
    if requirements_path.exists():
        imports = [
            Package(name=p['name'], version=p['version'])
            for p in parse_requirements(requirements_path)
        ]
        logger.debug(f'=> include {len(imports)} deps in requirements')
    elif freeze_path.exists():
        local_packages = {
            p['name']: p['version'] for p in parse_requirements(freeze_path)
        }
        candidates = get_all_imports(work_path)
        candidates = get_pkg_names(candidates)

        logger.debug(f'=> inspected dependents: {candidates}')

        imports = [get_import_info(m) for m in candidates]
        logger.debug(f'=> get latest pypi packages : {imports}')

        for m in imports:
            local_version = local_packages.get(m.name, None)
            if local_version:
                m._replace(version=local_version)
        if len(imports) > 0:
            logger.debug(f'=> dump {len(imports)} deps into requirements.txt')
            dump_requirements(requirements_path, imports)

    base_images, dep_tools = prelude(imports)
    jina_version = choose_jina_version(meta['jina'])
    py_version = meta.get('python', '3.7.0')

    jina_image_tag = get_jina_image_tag(jina_version, py_version)

    logger.debug(
        f'=> collected env:\n'
        + f'\tapt installs: {dep_tools}\n'
        + f'\tbase_images: {base_images}\n'
        + f'\tjina_base_image: {jina_image_tag}'
    )

    if not is_empty(dockerfile_path):
        return

        # WIP: optimizing the Dockerfile from uploader
        # if dockerfile.is_multistage():
        #     # Don't support multi-stage Dockerfie Optimization
        #     return
        # dockerfile = ExecutorDockerfile(
        #     docker_file=dockerfile_path,
        #     build_args={'JINA_VERSION': f'{jina_version}-{py_tag}'},
        # )
        # if dockerfile.baseimage.startswith('jinaai/jina') and len(base_images) > 0:
        #     dockerfile.baseimage = base_images.pop()
        #     dockerfile._parser.add_lines(
        #         f'RUN pip install jina=={jina_version}', at_start=True
        #     )
        #     dockerfile.dump(work_path / 'Dockerfile.normed')
    else:
        logger.debug('=> generating Dockerfile ...')
        dockerfile = ExecutorDockerfile(build_args={'JINA_VERSION': jina_image_tag})

        dockerfile.add_work_dir()

        if len(dep_tools) > 0:
            dockerfile.add_apt_installs(dep_tools)

        if requirements_path.exists():
            dockerfile.add_pip_install()

        # if len(test_glob) > 0:
        #     dockerfile.add_unitest()

        dockerfile.entrypoint = [
            'jina',
            'executor',
            '--uses',
            f'{config_path.relative_to(work_path)}',
        ]

        dockerfile.dump(dockerfile_path)
