from contextlib import asynccontextmanager
from typing import Annotated

import sentry_sdk
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import ORJSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from starlette import status
from starlette.middleware.cors import CORSMiddleware

from app.db.neptune_database import NeptuneDatabase
from app.config import settings
from app.routes import create_routes

# Sentry
if settings.sentry_sdk_key is not None:
    sentry_sdk.init(
        settings.sentry_sdk_key,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        release=settings.release_version,
        integrations=[
            StarletteIntegration(transaction_style='url'),
            FastApiIntegration(transaction_style='url'),
        ],
    )

# Neptune
neptune_database = NeptuneDatabase(
    cluster_id=settings.neptune_cluster_id,
    region=settings.neptune_region,
    pool_size=settings.neptune_pool_size,
    read_from_writer=settings.neptune_read_from_writer,
    recycle_connections_period=settings.neptune_recycle_conn_period,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    yield
    # Shutdown
    await neptune_database.close()

app = FastAPI(
    lifespan=lifespan,
    version=settings.release_version,
    default_response_class=ORJSONResponse,
)


@app.exception_handler(Exception)
def mapped_exception_handler(req: Request, _: Exception):
    request_origin = req.headers.get('origin', '')
    response = ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={'message': 'Internal Server Error'},
    )
    response.headers['Access-Control-Allow-Origin'] = request_origin
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health', include_in_schema=False)
async def health():
    return True


async def verify_api_key(api_key: Annotated[str, Header()] = None):
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized',
            headers={"WWW-Authenticate": "Bearer"},
        )


app.include_router(
    create_routes(neptune_database),
    dependencies=[Depends(verify_api_key)],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', loop='asyncio')
