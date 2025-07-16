import abc
import os
import time

import requests

from ctf_server.types import UserData


ORCHESTRATOR = os.getenv('ORCHESTRATOR_HOST', 'http://orchestrator:7283')
INSTANCE_ID = os.getenv('INSTANCE_ID')


class DaemonError(Exception):
    """Custom exception for Daemon errors."""


class Daemon(abc.ABC):
    def __init__(self, required_properties: list[str] | None = None) -> None:
        if required_properties is None:
            required_properties = []
        self.__required_properties = required_properties

    def start(self) -> None:
        while True:
            instance_body = requests.get(f'{ORCHESTRATOR}/instances/{INSTANCE_ID}', timeout=5).json()
            if not instance_body['ok']:
                msg = f'oops: {instance_body}'
                raise DaemonError(msg)

            user_data = instance_body['data']
            if any(v not in user_data['metadata'] for v in self.__required_properties):
                time.sleep(1)
                continue

            break

        self._run(user_data)

    @staticmethod
    def update_metadata(new_metadata: dict[str, str]) -> None:
        resp = requests.post(
            f'{ORCHESTRATOR}/instances/{INSTANCE_ID}/metadata',
            json=new_metadata,
            timeout=5,
        )
        body = resp.json()
        if not body['ok']:
            msg = f'failed to update metadata: {body["message"]}'
            raise DaemonError(msg)

    @abc.abstractmethod
    def _run(self, user_data: UserData) -> None:
        pass
