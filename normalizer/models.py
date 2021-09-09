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


class EndpointArgsModel(BaseModel):
    name: str
    args: List[ArgModel]
    kwargs: List[KWArgModel]
    docstring: Optional[str]
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


class NormalizeResult(BaseModel):
    success: bool
    code: int
    data: Optional[ExecutorModel]
    message: str
