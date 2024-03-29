import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Union

from fastapi import FastAPI

from .backends import Backend
from .backends.backend import InstanceExists
from .databases import Database
from .loaders import load_backend, load_database
from .types import CreateInstanceRequest
from .utils import worker


# note(es3n1n, 27.03.24): HACK: mypy won't know that we will initialize these within the lifespan
database: Database = None  # type: ignore
backend: Backend = None  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    global database, backend

    worker.setup('orchestrator')

    database = load_database()
    backend = load_backend(database)

    logging.root.setLevel(logging.INFO)

    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.post('/instances')
def create_instance(args: CreateInstanceRequest):
    logging.info('launching new instance: %s', args['instance_id'])

    try:
        user_data = backend.launch_instance(args)
    except InstanceExists:
        logging.warning('instance already exists: %s', args['instance_id'])

        return {
            'ok': False,
            'message': 'instance already exists',
        }
    except Exception as e:
        logging.error(
            'failed to launch instance: %s', args['instance_id'], exc_info=e
        )
        return {
            'ok': False,
            'message': 'an internal error occurred',
        }

    logging.info('launched new instance: %s', args['instance_id'])
    return {
        'ok': True,
        'message': 'instance launched',
        'data': user_data,
    }


@app.get('/instances/{instance_id}')
def get_instance(instance_id: str):
    user_data = database.get_instance(instance_id)
    if user_data is None:
        return {
            'ok': False,
            'message': 'instance does not exist',
        }

    return {
        'ok': True,
        'message': 'fetched metadata',
        'data': user_data
    }


@app.post('/instances/{instance_id}/metadata')
def update_metadata(instance_id: str, metadata: Dict[str, Union[str, List[Dict[str, str]]]]):
    try:
        database.update_metadata(instance_id, metadata)
    except:  # noqa: E722
        return {
            'ok': False,
            'message': 'instance does not exist'
        }

    return {
        'ok': True,
        'message': 'metadata updated',
    }


@app.delete('/instances/{instance_id}')
def delete_instance(instance_id: str):
    logging.info('killing instance: %s', instance_id)

    instance = backend.kill_instance(instance_id)
    if instance is None:
        return {
            'ok': False,
            'message': 'no instance found',
        }

    return {
        'ok': True,
        'message': 'instance deleted',
    }
