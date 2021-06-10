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


def order_py_modules(py_modules: List['pathlib.Path'], work_path: 'pathlib.Path'):
    from importlab.import_finder import get_imports

    dependencies = {x: [] for x in py_modules}

    def _import_to_path(import_stmt):
        parts = list(import_stmt.split('.'))
        parts[-1] += '.py'
        return work_path / pathlib.Path('/'.join(parts))

    for py_module in py_modules:
        py_imports = [m[0] for m in get_imports(py_module) if m[-1] is None]
        py_import_moduels = [_import_to_path(m) for m in py_imports]
        dependencies[py_module].extend(py_import_moduels)

    orders = list(topological_sort([(k, v) for k, v in dependencies.items()]))
    return orders


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
