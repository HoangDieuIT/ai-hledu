from fastapi import FastAPI, APIRouter, Request
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_redoc_html
from typing import cast
from app.config import environment


router = APIRouter()


@router.get("/openapi.json", responses={
    200: {
        "content": {"application/json": {}},
        "description": "OpenAPI format JSON.",
    },
}, include_in_schema=False)
async def openapi(request: Request):
    env = environment()
    return get_openapi(
        title=env.settings.name,
        version=env.settings.version,
        routes=cast(FastAPI, request.app).routes,
    )


@router.get("/redoc", responses={
    200: {
        "content": {"text/html": {}},
        "description": "Redoc format API documentation.",
    },
}, include_in_schema=False)
async def redoc():
    env = environment()
    openapi_url=f"{env.settings.docs.url_prefix}/docs/openapi.json"
    return get_redoc_html(openapi_url=openapi_url, title="docs")
