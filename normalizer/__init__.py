import pathlib
import sys

__resources_path__ = (
    pathlib.Path(sys.modules['normalizer'].__file__).parent / 'resources'
)
