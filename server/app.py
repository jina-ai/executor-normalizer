from fastapi import APIRouter, FastAPI
from loguru import logger
from starlette.config import Config

import normalizer

from .routes import router

APP_VERSION = normalizer.__version__
APP_NAME = 'Jina Executor Package Normalizer'
API_PREFIX = '/normalizer'

config = Config()

IS_DEBUG: bool = config('IS_DEBUG', cast=bool, default=False)


def create_app() -> FastAPI:
    fast_app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=IS_DEBUG)

    api_router = APIRouter()

    api_router.include_router(router, tags=['normalizer'], prefix='')

    fast_app.include_router(api_router, prefix=API_PREFIX)

    from fastapi.openapi.docs import (
        get_redoc_html,
        get_swagger_ui_html,
        get_swagger_ui_oauth2_redirect_html,
    )

    @fast_app.get(f'{API_PREFIX}/docs', include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=fast_app.openapi_url,
            title=fast_app.title + ' - Swagger UI',
            oauth2_redirect_url=fast_app.swagger_ui_oauth2_redirect_url,
            # swagger_js_url='/static/swagger-ui-bundle.js',
            # swagger_css_url='/static/swagger-ui.css',
        )

    @fast_app.get(
        f'{API_PREFIX}/{fast_app.swagger_ui_oauth2_redirect_url}',
        include_in_schema=False,
    )
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @fast_app.get(f'{API_PREFIX}/redoc', include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=fast_app.openapi_url,
            title=fast_app.title + ' - ReDoc',
            # redoc_js_url='/static/redoc.standalone.js',
        )

    return fast_app


app = create_app()
