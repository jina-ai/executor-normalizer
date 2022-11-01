import ast
import re
import pathlib
import yaml
from typing import Dict, List, Tuple, Optional, Sequence

from loguru import logger
from jina.helper import colored

from . import __resources_path__
from .deps import (
    Package,
    get_dep_tools,
    get_baseimage,
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
    convert_from_to_path,
    topological_sort,
    choose_jina_version,
    get_jina_image_tag,
)
from .models import ExecutorModel

ArgType = List[Tuple[str, Optional[str]]]
KWArgType = List[Tuple[str, Optional[str], str]]

InitInspectionType = Tuple[ArgType, KWArgType, str]
EndpointInspectionType = Tuple[str, ArgType, KWArgType, str, str]


def order_py_modules(py_modules: List['pathlib.Path'], work_path: 'pathlib.Path'):
    """
    Order the py_modules in the right order to be imported

    :param py_modules: list of py_modules to be imported
    :param work_path: path to the working directory

    :return: ordered list of py_modules
    """

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


def _get_element_source(
    lines: List[str], element: ast.expr, remove_whitespace: bool = False
) -> str:
    if element.lineno == element.end_lineno:
        source = lines[element.lineno - 1][element.col_offset : element.end_col_offset]
    else:
        source = (
            lines[element.lineno - 1][element.col_offset :]
            + ''.join(lines[element.lineno : element.end_lineno - 1])
            + lines[element.end_lineno - 1][: element.end_col_offset]
        )
    if remove_whitespace:
        source = re.sub(r'\s+', '', source)
        source = source.replace(',', ', ')
    return source


def _get_args_kwargs(
    func_args: List[str],
    func_args_defaults: List[str],
    annotations: List[Optional[str]],
) -> Tuple[ArgType, KWArgType]:
    if len(func_args_defaults) == 0:
        kwargs_idx = len(func_args)
    else:
        kwargs_idx = -len(func_args_defaults)
    kwarg_arguments, kwargs_annotations, kwargs_defaults = (
        func_args[kwargs_idx:],
        annotations[kwargs_idx:],
        func_args_defaults,
    )

    kwargs = [
        (arg, annotation, default)
        for arg, annotation, default in zip(
            kwarg_arguments, kwargs_annotations, kwargs_defaults
        )
    ]

    arg_arguments, args_annotations = func_args[:kwargs_idx], annotations[:kwargs_idx]
    args = [
        (arg, annotation) for arg, annotation in zip(arg_arguments, args_annotations)
    ]
    return args, kwargs


def _inspect_requests(element: ast.FunctionDef, lines: List[str]) -> Optional[str]:
    """
    Returns requests inspection details about a method

    :param element: Function definition
    :param lines: Lines of the file which the function live in

    :return: the endpoints that defines which incoming request will be handled by this function

    This can return:
        * None : the method is not an endpoint (not decorated with @requests)
        * "'ALL'": this is an endpoint method that will be triggered on every endpoint (decorated with @requests)
        * "['/<endpoint>']": this is an endpoint method that will be triggered on '/<endpoint>' (decorated with
        @requests(on='/<endpoint>') or @requests(on=['/<endpoint>'])
        * "['/<endpoint1>', '/<endpoint2>', ...]": this is an endpoint method that will be triggered on any of the
        endpoints in the list
    """
    for decorator in element.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and (
                decorator.func.id == 'requests' or decorator.func.id == 'jina.requests'
            )
        ):
            for keyword in decorator.keywords:
                if (
                    isinstance(keyword, ast.keyword)
                    and keyword.arg == 'on'
                    and isinstance(keyword.value, ast.expr)
                ):
                    return _get_element_source(
                        lines, keyword.value, remove_whitespace=True
                    )
        elif (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and (
                decorator.func.attr == 'requests'
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == 'jina'
            )
        ):
            for keyword in decorator.keywords:
                if (
                    isinstance(keyword, ast.keyword)
                    and keyword.arg == 'on'
                    and isinstance(keyword.value, ast.expr)
                ):
                    return _get_element_source(
                        lines, keyword.value, remove_whitespace=True
                    )
        elif (
            isinstance(decorator, ast.Attribute)
            and decorator.attr == 'requests'
            and isinstance(decorator.value, ast.Name)
            and decorator.value.id == 'jina'
        ):
            return 'ALL'
        elif isinstance(decorator, ast.Name) and (
            decorator.id == 'requests' or decorator.id == 'jina.requests'
        ):
            return 'ALL'


def inspect_executors(
    py_modules: Sequence['pathlib.Path'],
    class_name: Optional[str] = None,
) -> List[Tuple[str, str, Optional[str], Tuple, List[Tuple]]]:
    """
    Inspect the executors in the given modules
    :param py_modules: list of py_modules to be inspected
    :param class_name: name of the class to be inspected

    :return: list of tuples (module_name, class_name, class_docstring, class_args, class_kwargs)
    """

    def _inspect_class_defs(tree):
        return [o for o in ast.walk(tree) if isinstance(o, ast.ClassDef)]

    executors = []
    for filepath in py_modules:
        with filepath.open() as fin:
            tree = ast.parse(fin.read(), filename=str(filepath))
            fin.seek(0)
            lines = fin.readlines()

            for class_def in _inspect_class_defs(tree):
                if class_name:
                    if class_name != class_def.name:
                        continue
                else:
                    base_names = []
                    for base_class in class_def.bases:
                        # if the class looks like class MyExecutor(Executor)
                        if isinstance(base_class, ast.Name):
                            base_names.append(base_class.id)
                        # if the class looks like class MyExecutor(jina.Executor):
                        if isinstance(base_class, ast.Attribute):
                            base_names.append(base_class.attr)
                    if 'Executor' not in base_names:
                        continue

                init = None
                endpoints = []
                for body_item in class_def.body:
                    if not isinstance(body_item, ast.FunctionDef):
                        continue
                    docstring = ast.get_docstring(body_item)
                    func_args = [
                        element.arg
                        for element in body_item.args.args + body_item.args.kwonlyargs
                    ]
                    annotations = [
                        _get_element_source(
                            lines, element.annotation, remove_whitespace=True
                        )
                        if element.annotation
                        else None
                        for element in body_item.args.args + body_item.args.kwonlyargs
                    ]
                    func_args_defaults = [
                        _get_element_source(lines, element, remove_whitespace=False)
                        if element
                        else None
                        for element in body_item.args.defaults
                        + body_item.args.kw_defaults
                    ]

                    # check __init__ function arguments
                    if body_item.name == '__init__':
                        init = (func_args, func_args_defaults, annotations, docstring)
                    else:
                        requests_decorator = _inspect_requests(body_item, lines)

                        # add only methods that are decorated with requests
                        if requests_decorator:
                            if re.match('\'.*\'', requests_decorator, flags=re.DOTALL):
                                requests_decorator = f'[{requests_decorator}]'
                            endpoints.append(
                                (
                                    body_item.name,
                                    func_args,
                                    func_args_defaults,
                                    annotations,
                                    docstring,
                                    requests_decorator,
                                )
                            )
                executors.append(
                    (
                        class_def.name,
                        filepath,
                        ast.get_docstring(class_def),
                        init,
                        endpoints,
                    )
                )
    return executors


def filter_executors(executors: List[Tuple[str, str, Tuple, List[Tuple]]]):
    """
    Filter the executors based on the given criteria
    :param executors: list of tuples (class_name, filepath, class_docstring, class_args, class_kwargs)
    :return: list of tuples (class_name, filepath, class_docstring, class_args, class_kwargs)
    """
    result = []
    for i, (executor, _, _, init, _) in enumerate(executors):
        # An Executor without __init__ should be valid
        if not init:
            result.append(executors[i])
        else:
            func_args, func_args_defaults, _, _ = init
            if len(func_args) - len(func_args_defaults) >= 1:
                result.append(executors[i])
    return result


def prelude(imports: List['Package']):
    """
    Generate the prelude of the generated python file
    :param imports: list of packages to be imported
    :return: prelude of the generated python file
    """
    dep_tools = set([])
    base_images = set([])
    for pkg in imports:
        for tool in get_dep_tools(pkg):
            dep_tools.add(tool)
        _base_image = get_baseimage(pkg)
        if _base_image:
            base_images.add(_base_image)
    return base_images, dep_tools


def to_dto(
    executor: str,
    docstring: Optional[str],
    init: InitInspectionType,
    endpoints: List[EndpointInspectionType],
    filepath: str,
    hubble_score_metrics: Dict,
) -> ExecutorModel:
    """
    Convert the given executor to a DTO
    :param executor: name of the executor
    :param docstring: docstring of the executor
    :param init: init function of the executor
    :param endpoints: endpoints of the executor
    :param filepath: filepath of the executor
    :param hubble_score_metrics: hubble score metrics of the executor
    :return: DTO of the executor
    """
    if init:
        init_args, init_kwargs, init_docstring = init
        init = {
            'args': [
                {'arg': arg, 'annotation': annotation} for arg, annotation in init_args
            ],
            'kwargs': [
                {'arg': arg, 'annotation': annotation, 'default': default}
                for arg, annotation, default in init_kwargs
            ],
            'docstring': init_docstring,
        }
    result = {
        'executor': executor,
        'docstring': docstring,
        'init': init,
        'endpoints': [
            {
                'name': endpoint_name,
                'args': [
                    {'arg': arg, 'annotation': annotation}
                    for arg, annotation in endpoint_args
                ],
                'kwargs': [
                    {'arg': arg, 'annotation': annotation, 'default': default}
                    for arg, annotation, default in endpoint_kwargs
                ],
                'docstring': endpoint_docstring,
                'requests': endpoint_requests,
            }
            for endpoint_name, endpoint_args, endpoint_kwargs, endpoint_docstring, endpoint_requests in endpoints
        ],
        'hubble_score_metrics': hubble_score_metrics,
        'filepath': str(filepath),
    }
    return ExecutorModel(**result)


def normalize(
    work_path: 'pathlib.Path',
    meta: Dict = {'jina': '2'},
    env: Dict = {},
    build_env: Dict = {},
    dry_run: bool = False,
    dockerfile: str = None,
    **kwargs,
) -> ExecutorModel:
    """Normalize the executor package.

    :param work_path: the executor folder where it located
    :param meta: the version info of the Jina to work with
    :param env: the environment variables the Jina works with
    :param build_env: the environment variables in use set in build steps
    :param dry_run: if True, dry_run the file dumps

    :return: normalized Executor model

    :raises DependencyError: Error during resolve the dependencies of Executor
    :raises Exception: Other error
    :raises ExecutorExistsError: Detect there are more than one Executors
    :raises ExecutorNotFoundError: Can't detect any Executor
    :raises FileNotFoundError: Can't find the path of the folder
    :raises IllegalExecutorError: The count of legal Executor is 0
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

    dockerfile_path = (work_path / dockerfile) if dockerfile else (work_path / 'Dockerfile')
    manifest_cfg = None
    manifest_location = None
    manifest_path = work_path / 'manifest.yml'
    manifest_keys = ['name', 'description', 'url', 'keywords']
    config_path = work_path / 'config.yml'
    readme_path = work_path / 'README.md'
    requirements_path = work_path / 'requirements.txt'
    gpu_dockerfile_path = work_path / 'Dockerfile.gpu'
    test_glob = list(work_path.glob('tests/test_*.py'))

    # load manifest configuration
    if manifest_path.exists():
        manifest_location = manifest_path
        raw_manifest_cfg = yaml.safe_load(open(manifest_path, 'r'))
        parsed_manifest_cfg = {k: v for k, v in raw_manifest_cfg.items() if k in manifest_keys}
        if len(parsed_manifest_cfg) > 0:
            manifest_cfg = parsed_manifest_cfg

    class_name = None
    py_glob = []
    if config_path.exists():
        config = yaml.safe_load(open(config_path, 'r'))
        try:
            class_name: str = config['jtype']
        except Exception as ex:
            raise ex

        if class_name is None:
            raise Exception('Not found jtype in config.yml')
        
        metas_py_modules = config.get('metas', {}).get('py_modules', None)
        root_py_modules = config.get('py_modules', None)

        if metas_py_modules and root_py_modules:
            raise Exception('The parameter py_modules can only be appear in one of metas and root in config.yml')

        py_modules = metas_py_modules if metas_py_modules else root_py_modules
        if isinstance(py_modules, str):
            py_glob = [work_path.joinpath(py_modules)]
        elif isinstance(py_modules, list):
            py_glob += [work_path.joinpath(p) for p in py_modules]

        # extend the path from import statement
        extended_path = None
        for filepath in py_glob:
            with filepath.open() as fin:
                tree = ast.parse(fin.read(), filename=str(filepath))
                fin.seek(0)
                lines = fin.readlines()
                for o in ast.walk(tree):
                    if isinstance(o, ast.ImportFrom):
                        for alias in o.names:
                            if alias.name == class_name:
                                from_state = list(lines[o.lineno - 1].split(' '))[1]
                                extended_path = convert_from_to_path(
                                    from_state, base_dir=filepath.parent
                                )
                                if extended_path:
                                    py_glob.append(extended_path)
                                    break

        # appending manifest.yml into config.yml
        # this is done due to deprectation of manifest.yml
        if manifest_cfg is not None:
            metas_cfg = {**config.get('metas', {}), **manifest_cfg}
            config['metas'] = metas_cfg
            if not dry_run:
                with open(config_path, 'w') as f:
                    yaml.dump(config, f, sort_keys=False)
        else:
            metas_cfg = config.get('metas', {})
            if 'name' in metas_cfg:
                manifest_path = config_path
    else:
        py_glob = list(work_path.glob('*.py')) + list(work_path.glob('executor/*.py'))

    py_glob = list(set(py_glob))

    completeness = {
        'Dockerfile': dockerfile_path,
        'manifest': manifest_path,
        'config.yml': config_path,
        'README.md': readme_path,
        'requirements.txt': requirements_path,
        '*.py': py_glob,
        'tests': test_glob,
    }

    logger.info(
        f'=> checking executor repository ...\n'
        + '\n'.join(
            f'\t{colored("✓", "green") if (None if v is None else v if isinstance(v, list) else v.exists()) else colored("✗", "red"):>4} {k:<20} {v}'
            for k, v in completeness.items()
        )
        + '\n'
    )

    hubble_score_metrics = {
        'dockerfile_exists': dockerfile_path.exists(),
        'manifest_exists':  manifest_path is not None,
        'config_exists': config_path.exists(),
        'readme_exists': readme_path.exists(),
        'requirements_exists': requirements_path.exists(),
        'tests_exists': bool(test_glob),
        'gpu_dockerfile_exists': gpu_dockerfile_path.exists(),
    }

    # if not requirements_path.exists():
    #     requirements_path.touch()

    # inspect executor
    executors = inspect_executors(py_glob, class_name)
    if len(executors) == 0:
        raise ExecutorNotFoundError
    if len(executors) > 1:
        raise ExecutorExistsError

    executors = filter_executors(executors)
    if len(executors) == 0:
        raise IllegalExecutorError

    executor, filepath, docstring, init, endpoints = executors[0]
    if init:
        init_args, init_args_defaults, init_annotations, init_docstring = init
        init_args, init_kwargs = _get_args_kwargs(
            init_args, init_args_defaults, init_annotations
        )
        init = (init_args, init_kwargs, init_docstring)

    for i, endpoint in enumerate(endpoints):
        if endpoint is not None:
            (
                endpoint_name,
                endpoint_args,
                endpoint_args_defaults,
                endpoint_annotations,
                endpoint_docstring,
                endpoint_requests,
            ) = endpoint
            endpoint_args, endpoint_kwargs = _get_args_kwargs(
                endpoint_args, endpoint_args_defaults, endpoint_annotations
            )
            endpoints[i] = (
                endpoint_name,
                endpoint_args,
                endpoint_kwargs,
                endpoint_docstring,
                endpoint_requests,
            )

    if not config_path.exists():
        try:
            py_modules = order_py_modules(py_glob, work_path)
        except Exception as ex:
            raise DependencyError
        py_modules = [f'{p.relative_to(work_path)}' for p in py_modules]

        # render config.yml content
        template = get_config_template()
        config_content = template.render(executor=executor, py_modules=py_modules)

        if not dry_run:
            # dump config.yml
            with open(config_path, 'w') as f:
                f.write(config_content)

            if manifest_cfg is not None:
                config = yaml.safe_load(open(config_path, 'r'))
                metas_cfg = {**config.get('metas', {}), **manifest_cfg}
                config['metas'] = metas_cfg
                with open(config_path, 'w') as f:
                    yaml.dump(config, f, sort_keys=False)

    if requirements_path.exists():
        imports = [
            Package(name=p['name'], version=p['version'])
            for p in parse_requirements(requirements_path)
        ]
        logger.debug(f'=> existed imports: {imports}')
    else:
        imports = []
        # WIP: TODO....
        # candidates = get_all_imports(work_path)
        # candidates = get_pkg_names(candidates)

        # logger.debug(f'=> inspect imports: {candidates}')

        # imports = [get_import_info(m) for m in candidates]
        # logger.debug(f'=> import pypi package : {imports}')
        # logger.debug(f'=> writing {len(imports)} requirements.txt')

        # if len(imports) > 0:
        #     dump_requirements(requirements_path, imports)

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

    dockerfile = None
    if dockerfile_path.exists():
        dockerfile = ExecutorDockerfile(
            docker_file=dockerfile_path,
            build_args={'JINA_VERSION': f'{jina_version}'},
        )
        if build_env and isinstance(build_env, dict) and len(build_env.keys()):
            dockerfile.insert_build_env(build_env)
        # if dockerfile.is_multistage():
        #     # Don't support multi-stage Dockerfie Optimization
        #     return

        # if dockerfile.baseimage.startswith('jinaai/jina') and len(base_images) > 0:
        #     dockerfile.baseimage = base_images.pop()
        #     dockerfile._parser.add_lines(
        #         f'RUN pip install jina=={jina_version}', at_start=True
        #     )
        #     dockerfile.dump(work_path / 'Dockerfile.normed')
        if not dry_run:
            dockerfile.dump(dockerfile_path)
    else:
        logger.debug('=> generating Dockerfile ...')
        dockerfile = ExecutorDockerfile(build_args={'JINA_VERSION': jina_image_tag})

        # if len(base_images) > 0:
        #     logger.debug(f'=> use base image: {base_images}')
        #     dockerfile.baseimage = base_images.pop()

        dockerfile.add_work_dir()
        # dockerfile._parser.add_lines(f'RUN pip install jina=={jina_version}')

        if len(dep_tools) > 0:
            dockerfile.add_apt_installs(dep_tools)

        if requirements_path.exists():
            dockerfile.add_pip_install()

        if build_env and isinstance(build_env, dict) and len(build_env.keys()):
            dockerfile.insert_build_env(build_env)

        # if len(test_glob) > 0:
        #     dockerfile.add_unitest()

        dockerfile.entrypoint = [
            'jina',
            'executor',
            '--uses',
            f'{config_path.relative_to(work_path)}',
        ]
        if not dry_run:
            dockerfile.dump(dockerfile_path)

    entrypoint_value = dockerfile.entrypoint

    new_dockerfile = ExecutorDockerfile(
        docker_file=__resources_path__ / 'templates' / 'dockerfile.base'
    )
    new_dockerfile.set_entrypoint(entrypoint_value)

    new_dockerfile_path = work_path / '__jina__.Dockerfile'
    if not dry_run:
        new_dockerfile.dump(new_dockerfile_path)

    return to_dto(executor, docstring, init, endpoints, filepath, hubble_score_metrics)
