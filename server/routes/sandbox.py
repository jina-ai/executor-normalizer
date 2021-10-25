import datetime
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from starlette.requests import Request
from loguru import logger

from server.errors import ErrorCode
from sandbox.models import PackagePayload, DeployResult
from sandbox.core import deploy as sandbox_deploy

router = APIRouter()


@router.post('/')
def deploy(
    request: Request,
    block_data: PackagePayload = None,
):
    now = datetime.datetime.now()

    result = {
        'success': True,
        'code': 200,
        'data': None,
        'message': 'Deployed successfully!'
    }

    try:
        data = sandbox_deploy(block_data.executor, block_data.endpoints, block_data.replicas)
        result['data'] = data
    except Exception as ex:
        result['success'] = False
        result['code'] = ErrorCode.Others.value
        result['message'] = str(ex)

    logger.info(
        {
            'payload': jsonable_encoder(block_data),
            'time_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'response': result,
        }
    )

    return DeployResult(
        success = result['success'],
        code = result['code'],
        message = result['message'],
        data = result['data']
    )