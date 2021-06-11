import traceback
import sys
import datetime
from typing import Dict, Optional
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


class NormalizeResult(BaseModel):
    result: Dict


@router.post('/', name='normalizer')
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
        _normalize(
            block_data.package_path,
            meta=block_data.meta,
            env=block_data.env,
        )
    except Exception as ex:
        result['success'] = False
        if isinstance(ex, excepts.ExecutorNotFoundError):
            result['code'] = ErrorCode.ExecutorNotFound
            result['message'] = 'None of executor can be found!'
        elif isinstance(ex, excepts.ExecutorExistsError):
            result['code'] = ErrorCode.ExecutorExists
            result[
                'message'
            ] = 'Multiple executors are placed at one package, which is not allowed by Jina Hub now!'
        elif isinstance(ex, excepts.IllegalExecutorError):
            result['code'] = ErrorCode.IllegalExecutor
            result[
                'message'
            ] = 'The uploaded executor is illegal, please double check it!'
        elif isinstance(ex, excepts.DependencyError):
            result['code'] = ErrorCode.BrokenDependency
            result[
                'message'
            ] = 'The uploaded executor contains cycing and missing dependencies'
        else:
            result['code'] = ErrorCode.Others
            exc_type, exc_value, exc_tb = sys.exc_info()
            result['message'] = traceback.format_exception(exc_type, exc_value, exc_tb)

    logger.info(
        {
            'payload': jsonable_encoder(block_data),
            'time_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'response': result,
        }
    )
    return NormalizeResult(result=result)
