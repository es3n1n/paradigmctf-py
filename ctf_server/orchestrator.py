from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI
from loguru import logger

from .backends import Backend
from .backends.backend import InstanceExistsError
from .databases import Database
from .loaders import load_backend, load_database
from .types import CreateInstanceRequest, UserData
from .utils import worker


@dataclass
class Context:
    # note(es3n1n, 27.03.24): HACK: mypy won't know that we will initialize these within the lifespan
    database: Database = None  # type: ignore[assignment]
    backend: Backend = None  # type: ignore[assignment]

    def setup(self) -> None:
        self.database = load_database()
        self.backend = load_backend(self.database)


context = Context()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    worker.setup('orchestrator')
    context.setup()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.post('/instances')
def create_instance(args: CreateInstanceRequest) -> dict[str, bool | str | UserData]:
    logger.info(f'launching new instance: {args["instance_id"]}')

    try:
        user_data = context.backend.launch_instance(args)
    except InstanceExistsError:
        logger.warning(f'instance already exists: {args["instance_id"]}')
        return {
            'ok': False,
            'message': 'instance already exists',
        }
    except Exception as e:
        logger.opt(exception=e).error(f'failed to launch instance: {args["instance_id"]}')
        return {
            'ok': False,
            'message': 'an internal error occurred',
        }

    logger.info(f'launched new instance: {args["instance_id"]}')
    return {
        'ok': True,
        'message': 'instance launched',
        'data': user_data,
    }


@app.get('/instances/{instance_id}')
def get_instance(instance_id: str) -> dict[str, bool | str | UserData]:
    user_data = context.database.get_instance(instance_id)
    if user_data is None:
        return {
            'ok': False,
            'message': 'instance does not exist',
        }

    return {'ok': True, 'message': 'fetched metadata', 'data': user_data}


@app.post('/instances/{instance_id}/metadata')
def update_metadata(instance_id: str, metadata: dict[str, str | list[dict[str, str]]]) -> dict[str, bool | str]:
    try:
        context.database.update_metadata(instance_id, metadata)
    except Exception:
        # FIXME(es3n1n, 16.07.25): do not catch all exceptions, but only the ones we expect
        return {'ok': False, 'message': 'instance does not exist'}

    return {
        'ok': True,
        'message': 'metadata updated',
    }


@app.delete('/instances/{instance_id}')
def delete_instance(instance_id: str) -> dict[str, bool | str]:
    logger.info(f'killing instance: {instance_id}')
    instance = context.backend.kill_instance(instance_id)
    if instance is None:
        return {
            'ok': False,
            'message': 'no instance found',
        }

    return {
        'ok': True,
        'message': 'instance deleted',
    }
