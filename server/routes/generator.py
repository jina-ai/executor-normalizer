import datetime
from fastapi import APIRouter, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from starlette.requests import Request
from loguru import logger

from generator.models import PackagePayload
from generator.core import generate as generate_yaml, clean as clean_yaml

router = APIRouter()

@router.post('/generate')
async def generate(
    request: Request,
    block_data: PackagePayload,
    background_tasks: BackgroundTasks,
):
    now = datetime.datetime.now()

    (path, file_type) = generate_yaml(
        block_data.executor,
        block_data.type,
        block_data.protocol
    )
    # Remove the file after the request is done
    background_tasks.add_task(clean_yaml, path)

    logger.info(
        {
            'payload': jsonable_encoder(block_data),
            'time_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        }
    )

    return FileResponse(path, media_type='application/octet-stream', filename=f'{block_data.type}.{file_type}')
