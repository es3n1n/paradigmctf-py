import os

from .backends import Backend, DockerBackend, KubernetesBackend
from .databases import Database, RedisDatabase, SQLiteDatabase


class BackendLoaderError(Exception):
    """Custom exception for errors in backend loading."""


def load_database() -> Database:
    dbtype = os.getenv('DATABASE', 'redis')
    if dbtype == 'sqlite':
        dbpath = os.getenv('SQLITE_PATH', ':memory:')
        return SQLiteDatabase(dbpath)
    if dbtype == 'redis':
        url = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
        return RedisDatabase(url)

    msg = f'Invalid database type: {dbtype}'
    raise BackendLoaderError(msg) from None


def load_backend(database: Database) -> Backend:
    backend_type = os.getenv('BACKEND', 'docker')
    if backend_type == 'docker':
        return DockerBackend(database=database)
    if backend_type == 'kubernetes':
        config_file = os.getenv('KUBECONFIG', 'incluster')
        return KubernetesBackend(database, config_file)

    msg = f'Invalid backend type: {backend_type}'
    raise BackendLoaderError(msg) from None
