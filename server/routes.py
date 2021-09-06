import traceback
import sys
import datetime
from typing import Dict, Any, Optional
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


class ExecutorData(BaseModel):
    executor: str
    func_args: Any
    func_args_defaults: Any
    filepath: str


class NormalizeResult(BaseModel):
    success: bool
    code: int
    data: Optional[ExecutorData]
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
        executor, func_args, func_args_defaults, filepath = _normalize(
            block_data.package_path,
            meta=block_data.meta,
            env=block_data.env,
        )
        result['data'] = {
            'executor': executor,
            'func_args': func_args,
            'func_args_defaults': func_args_defaults,
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
        data=ExecutorData(**result['data']) if result['data'] else None,
        message=result['message'],
    )
