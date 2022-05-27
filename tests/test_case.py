import json
from pathlib import Path
import pytest

from normalizer import deps, core

cur_dir = Path(__file__).parent

def test_nested_cases():
    work_path = cur_dir / 'cases' / 'nested'
    core.normalize(work_path, dry_run=True)

    work_path = cur_dir / 'cases' / 'nested_2'
    core.normalize(work_path, dry_run=True)

    work_path = cur_dir / 'cases' / 'nested_3'
    core.normalize(work_path, dry_run=True)