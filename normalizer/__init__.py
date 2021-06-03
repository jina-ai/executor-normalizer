import os
import pathlib
import platform as _platform
import signal as _signal
import sys
import types as _types

__version__ = '0.0.1'

__resources_path__ = (
    pathlib.Path(sys.modules['normalizer'].__file__).parent / 'resources'
)
