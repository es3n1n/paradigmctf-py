import json
import sqlite3
from threading import Lock

from loguru import logger

from ctf_server.databases import Database
from ctf_server.types import InstanceInfo, UserData


class SQLiteDatabase(Database):
    def __init__(self, db_path: str) -> None:
        super().__init__()

        self.__conn_lock = Lock()
        self.__conn = sqlite3.connect(database=db_path, check_same_thread=False)
        self.__conn.execute(
            """
CREATE TABLE IF NOT EXISTS anvil_instances
(
    instance_id VARCHAR PRIMARY KEY,
    rpc_id VARCHAR,
    instance_data JSON
);"""
        )

    def register_instance(self, instance_id: str, instance: UserData) -> None:
        self.__conn_lock.acquire()
        try:
            cursor = self.__conn.execute(
                'INSERT INTO anvil_instances(instance_id, instance_data) VALUES (?, ?)',
                (instance_id, json.dumps(instance)),
            )
        finally:
            cursor.close()
            self.__conn_lock.release()

    def update_instance(self, instance_id: str, instance: InstanceInfo) -> None:
        self.__conn_lock.acquire()
        try:
            cursor = self.__conn.execute(
                'UPDATE anvil_instances SET instance_data = ? WHERE instance_id = ?',
                (json.dumps(instance), instance_id),
            )
        finally:
            cursor.close()
            self.__conn_lock.release()

    def unregister_instance(self, instance_id: str) -> UserData | None:
        self.__conn_lock.acquire()
        try:
            cursor = self.__conn.execute(
                'DELETE FROM anvil_instances WHERE instance_id = ? RETURNING instance_data', (instance_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return None

            return json.loads(row[0])
        finally:
            cursor.close()
            self.__conn_lock.release()

    def get_all_instances(self) -> list[InstanceInfo]:
        self.__conn_lock.acquire()
        try:
            cursor = self.__conn.execute('SELECT instance_data FROM anvil_instances')
            result = []
            while True:
                row = cursor.fetchone()
                if row is None:
                    break

                result.append(json.loads(row[0]))
            return result
        finally:
            cursor.close()
            self.__conn_lock.release()

    def get_instance_by_external_id(self, rpc_id: str) -> UserData | None:
        self.__conn_lock.acquire()
        try:
            cursor = self.__conn.execute('SELECT instance_data FROM anvil_instances WHERE rpc_id = ?', (rpc_id,))
            row = cursor.fetchone()
            if row is None:
                return None

            return json.loads(row[0])
        finally:
            cursor.close()
            self.__conn_lock.release()

    def get_instance(self, instance_id: str) -> UserData | None:
        self.__conn_lock.acquire()
        try:
            cursor = self.__conn.execute(
                'SELECT instance_data FROM anvil_instances WHERE instance_id = ?', (instance_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return None

            return json.loads(row[0])
        finally:
            cursor.close()
            self.__conn_lock.release()

    def get_expired_instances(self) -> list[UserData]:
        return []

    def update_metadata(self, instance_id: str, metadata: dict[str, str | list[dict[str, str]]]) -> None:
        logger.warning(f'Update metadata not supported in SQLiteDatabase: {instance_id} {metadata}')
