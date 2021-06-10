import pathlib
from typing import Dict, List

from jina.jaml import JAML

from . import __resources_path__


def inspect_executors(py_modules: List['pathlib.Path']):
    def _inspect_class_defs(tree):
        return [o for o in ast.walk(tree) if isinstance(o, ast.ClassDef)]

    import ast

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

                for body_item in class_def.body:
                    # check __init__ function arguments
                    if (
                        isinstance(body_item, ast.FunctionDef)
                        and body_item.name == '__init__'
                    ):

                        func_args = body_item.args.args
                        func_args_defaults = body_item.args.defaults

                        executors.append(
                            (class_def.name, func_args, func_args_defaults, filepath)
                        )

    return executors


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
