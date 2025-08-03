import asyncio
import logging
import logging.config
import os
from typing import Optional, Awaitable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from PIL import JpegImagePlugin
from pillow_heif import register_heif_opener
from .config import root_package, app_env, environment
from .resources import configure
import yaml


async def create_app(
    env_key: Optional[str] = None,
) -> FastAPI:

    JpegImagePlugin._getmp = lambda x: None

    register_heif_opener()

    # Environment
    if env_key:
        os.environ[app_env()] = env_key

    env = environment()

    if env.settings.launch_screen:
        print(env.settings.dump())

    # Logging
    with open('./config/logging.yml', 'r') as f:
        logging.config.dictConfig(yaml.safe_load(f))

    logger = logging.getLogger(root_package().lower())

    try:
        docs_config = {}
        if env.settings.docs.enabled:
            if env.settings.docs.username:
                docs_config.update({
                    "openapi_url": None,
                    "docs_url": None,
                    "redoc_url": None,
                })
            else:
                docs_config.update({
                    "openapi_url": "/openapi.json",
                    "docs_url": "/docs",
                    "redoc_url": "/redoc",
                })
        else:
            docs_config.update({
                "openapi_url": None,
                "docs_url": None,
                "redoc_url": None,
            })
        
        app = FastAPI(
            title=env.settings.name,
            version=env.settings.version,
            **docs_config
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=env.settings.cors.origins,
            allow_credentials=env.settings.cors.credentials,
            allow_methods=env.settings.cors.methods,
            allow_headers=env.settings.cors.headers,
        )

        resources, call_session = await configure(env.settings, logger)

        app.state.resources = resources

        @app.middleware('http')
        async def call(req: Request, call_next) -> Awaitable[Response]:
            async def next(session):
                return await call_next(req)
            return await call_session(next)

        # Routes
        from .api import routes
        routes.setup_api(app, env, logger)

    except Exception as e:
        logger.error("Failed to configure resources.", exc_info=e)
        raise

    return app


def app():
    loop = asyncio.get_running_loop()
    if loop:
        future = loop.create_future()
        async def setup():
            try:
                future.set_result(await create_app())
            except:
                future.cancel()
                raise
        loop.create_task(setup())
        async def app(scope, receive, send):
            value = await future
            return await value(scope, receive, send)
    else:
        app = asyncio.run(create_app())

    return app