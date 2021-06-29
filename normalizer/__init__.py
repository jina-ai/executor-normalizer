import pathlib
import sys

__version__ = '0.0.4'

__resources_path__ = (
    pathlib.Path(sys.modules['normalizer'].__file__).parent / 'resources'
)
