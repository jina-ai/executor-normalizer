import datetime
from typing import Dict

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from loguru import logger
from pydantic import BaseModel
from starlette.requests import Request

from normalizer.main import normalize as _normalize

router = APIRouter()


class PackagePayload(BaseModel):
    jina_version: str = 'master'
    package_path: str


class NormalizeResult(BaseModel):
    result: Dict


@router.post('/', name='normalizer')
def normalize(
    request: Request,
    block_data: PackagePayload = None,
):
    now = datetime.datetime.now()

    _normalize(block_data.package_path, jina_version=block_data.jina_version)

    result = {
        'success': True,
        'code': 200,
        'reason': None,
    }

    logger.info(
        {
            'payload': jsonable_encoder(block_data),
            'time_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'response': result,
        }
    )
    return NormalizeResult(result=result)
