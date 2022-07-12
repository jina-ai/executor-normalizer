from fastapi import APIRouter, FastAPI
from loguru import logger
from starlette.config import Config

import server

from server.routes.normalizer import router as normalizer_router
from server.routes.generator import router as generator_router

APP_VERSION = server.__version__
APP_NAME = 'Jina Hubble Python Services'

config = Config()

IS_DEBUG: bool = config('IS_DEBUG', cast=bool, default=False)


def create_app() -> FastAPI:
    fast_app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=IS_DEBUG)

    api_router = APIRouter()

    api_router.include_router(normalizer_router, tags=['normalizer'], prefix='/normalizer/api/v1')
    api_router.include_router(generator_router, tags=['generator'], prefix='/generator/api/v1')

    fast_app.include_router(api_router)

    from fastapi.openapi.docs import (
        get_redoc_html,
        get_swagger_ui_html,
        get_swagger_ui_oauth2_redirect_html,
    )

    @fast_app.get(f'/docs', include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=fast_app.openapi_url,
            title=fast_app.title + ' - Swagger UI',
            oauth2_redirect_url=fast_app.swagger_ui_oauth2_redirect_url,
            # swagger_js_url='/static/swagger-ui-bundle.js',
            # swagger_css_url='/static/swagger-ui.css',
        )

    @fast_app.get(
        f'/{fast_app.swagger_ui_oauth2_redirect_url}',
        include_in_schema=False,
    )
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @fast_app.get(f'/redoc', include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=fast_app.openapi_url,
            title=fast_app.title + ' - ReDoc',
            # redoc_js_url='/static/redoc.standalone.js',
        )
    
    @fast_app.get(f'/ping', include_in_schema=False)
    async def ping():
        return 'pong'

    return fast_app


app = create_app()
