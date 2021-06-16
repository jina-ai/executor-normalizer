import pathlib
import sys

__version__ = '0.1.0'

__resources_path__ = (
    pathlib.Path(sys.modules['normalizer'].__file__).parent / 'resources'
)
