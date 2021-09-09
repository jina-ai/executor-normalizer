import traceback
import sys
import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from loguru import logger
from pydantic import BaseModel
from pydantic.utils import BUILTIN_COLLECTIONS
from starlette.requests import Request

from normalizer.core import normalize as _normalize
from normalizer import excepts
from .errors import ErrorCode

router = APIRouter()


class PackagePayload(BaseModel):
    package_path: Path
    meta: Optional[Dict] = {'jina': 'master'}
    env: Optional[Dict] = {}


class Arg(BaseModel):
    arg: str
    annotation: Optional[str]


class KWArg(Arg):
    default: str


class FuncArgs(BaseModel):
    args: List[Arg]
    kwargs: List[KWArg]
    docstring: Optional[str]


class EndpointArgs(BaseModel):
    name: str
    args: List[Arg]
    kwargs: List[KWArg]
    docstring: Optional[str]
    requests: str


class Executor(BaseModel):
    executor: str
    docstring: Optional[str]
    init: Optional[FuncArgs]
    endpoints: List[EndpointArgs]
    hubble_score_metrics: Dict
    filepath: str


class NormalizeResult(BaseModel):
    success: bool
    code: int
    data: Optional[Executor]
    message: str


@router.post('/', name='normalizer', response_model=NormalizeResult)
def normalize(
        request: Request,
        block_data: PackagePayload = None,
):
    now = datetime.datetime.now()

    result = {
        'success': True,
        'code': 200,
        'data': None,
        'message': 'The uploaded executor is normalized successfully!',
    }

    try:
        executor, docstring, init, endpoints, filepath, hubble_score_metrics = _normalize(
            block_data.package_path,
            meta=block_data.meta,
            env=block_data.env,
        )
        if init:
            init_args, init_kwargs, init_docstring = init
            init = {
                'args': [
                    {
                        'arg': arg,
                        'annotation': annotation
                    }
                    for arg, annotation in init_args
                ],
                'kwargs': [
                    {
                        'arg': arg,
                        'annotation': annotation,
                        'default': default
                    }
                    for arg, annotation, default in init_kwargs
                ],
                'docstring': init_docstring
            }
        result['data'] = {
            'executor': executor,
            'docstring': docstring,
            'init': init,
            'endpoints': [
                {
                    'name': endpoint_name,
                    'args': [
                        {
                            'arg': arg,
                            'annotation': annotation
                        }
                        for arg, annotation in endpoint_args
                    ],
                    'kwargs': [
                        {
                            'arg': arg,
                            'annotation': annotation,
                            'default': default
                        }
                        for arg, annotation, default in endpoint_kwargs
                    ],
                    'docstring': endpoint_docstring,
                    'requests': endpoint_requests
                }
                for endpoint_name, endpoint_args, endpoint_kwargs, endpoint_docstring, endpoint_requests in endpoints
            ],
            'hubble_score_metrics': hubble_score_metrics,
            'filepath': str(filepath)
        }
    except Exception as ex:
        result['success'] = False
        if isinstance(ex, excepts.ExecutorNotFoundError):
            result['code'] = ErrorCode.ExecutorNotFound.value
            result['message'] = 'None of executor can be found!'
        elif isinstance(ex, excepts.ExecutorExistsError):
            result['code'] = ErrorCode.ExecutorExists.value
            result[
                'message'
            ] = 'Multiple executors are placed at one package, which is not allowed by Jina Hub now!'
        elif isinstance(ex, excepts.IllegalExecutorError):
            result['code'] = ErrorCode.IllegalExecutor.value
            result[
                'message'
            ] = 'The uploaded executor is illegal, please double check it!'
        elif isinstance(ex, excepts.DependencyError):
            result['code'] = ErrorCode.BrokenDependency.value
            result[
                'message'
            ] = 'The uploaded executor contains cycing and missing dependencies'
        else:
            result['code'] = ErrorCode.Others.value

            result['message'] = str(ex)

    logger.info(
        {
            'payload': jsonable_encoder(block_data),
            'time_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'response': result,
        }
    )
    return NormalizeResult(
        success=result['success'],
        code=result['code'],
        data=Executor(**result['data']) if result['data'] else None,
        message=result['message'],
    )
