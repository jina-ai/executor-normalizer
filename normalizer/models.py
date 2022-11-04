from pathlib import Path
from typing import Optional, List, Dict

from pydantic import BaseModel
from pydantic.utils import BUILTIN_COLLECTIONS


class ArgModel(BaseModel):
    arg: str
    annotation: Optional[str]


class KWArgModel(ArgModel):
    default: str


class FuncArgsModel(BaseModel):
    args: List[ArgModel]
    kwargs: List[KWArgModel]
    docstring: Optional[str]


class EndpointArgsModel(FuncArgsModel):
    name: str
    requests: str


class ExecutorModel(BaseModel):
    executor: str
    docstring: Optional[str]
    init: Optional[FuncArgsModel]
    endpoints: List[EndpointArgsModel]
    hubble_score_metrics: Dict
    filepath: str


class PackagePayload(BaseModel):
    package_path: Path
    meta: Optional[Dict] = {'jina': 'master'}
    env: Optional[Dict] = {}
    build_env: Optional[Dict] = {}
    dockerfile: Optional[str] = None
    build_env_file: Optional[str] = None


class NormalizeResult(BaseModel):
    success: bool
    code: int
    data: Optional[ExecutorModel]
    message: str
