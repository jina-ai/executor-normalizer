import datetime
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from loguru import logger
from pydantic.utils import BUILTIN_COLLECTIONS
from starlette.requests import Request

from normalizer.core import normalize as _normalize
from normalizer import excepts
from normalizer.models import PackagePayload, NormalizeResult
from server.errors import ErrorCode

router = APIRouter()


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
        result['data'] = _normalize(
            block_data.package_path,
            meta=block_data.meta,
            env=block_data.env,
            build_env=block_data.build_env,
            dockerfile=block_data.dockerfile
        )

    except Exception as ex:
        result['success'] = False
        if isinstance(ex, excepts.ExecutorNotFoundError):
            result['code'] = ErrorCode.ExecutorNotFound.value
            result['message'] = """We can not discover any Executor in your bundle. This is often due to one of the following errors:
    The bundle did not contain any valid executor.
    The config.yml's jtype is mismatched with the actual Executor class name."""
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
            logger.exception(ex)

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
        data=result['data'],
        message=result['message'],
    )
