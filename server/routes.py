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

    _normalize(
        block_data.package_path,
        meta=block_data.meta,
        env=block_data.env,
    )

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
