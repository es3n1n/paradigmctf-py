import time
from json import dumps, loads
from typing import Any, Dict, List, Optional, Union

import redis

from ctf_server.types import UserData

from .database import Database


class RedisDatabase(Database):
    def __init__(self, url: str, redis_kwargs: Dict[str, Any] = {}) -> None:
        super().__init__()

        # note(es3n1n, 27.03.24): For some reason their typehint is set to None, but in their code they're literally
        # returning the connection object, like what?
        self.__client: redis.Redis = redis.Redis.from_url(  # type: ignore
            url,
            decode_responses=True,
            **redis_kwargs,
        )

    def register_instance(self, instance_id: str, instance: UserData):
        pipeline = self.__client.pipeline()

        try:
            pipeline.json().set(f'instance/{instance["instance_id"]}', '$', instance)
            pipeline.hset(
                'external_ids', instance['external_id'], instance['instance_id']
            )
            pipeline.zadd(
                'expiries',
                {
                    instance['instance_id']: int(instance['expires_at']),
                },
            )
        finally:
            pipeline.execute()

    def update_instance(self, instance_id: str, instance: UserData):
        raise Exception('not supported')

    def unregister_instance(self, instance_id: str) -> Optional[UserData]:
        instance = self.__client.json().get(f'instance/{instance_id}')
        if instance is None:
            return None

        pipeline = self.__client.pipeline()
        try:
            pipeline.json().delete(f'instance/{instance_id}')
            pipeline.hdel('external_ids', instance['external_id'])
            pipeline.zrem('expiries', instance_id)
            pipeline.delete(f'metadata/{instance_id}')
            return instance
        finally:
            pipeline.execute()

    def get_instance(self, instance_id: str) -> Optional[UserData]:
        instance: Optional[UserData] = self.__client.json().get(f'instance/{instance_id}')
        if instance is None:
            return None

        instance['metadata'] = {}
        metadata = self.__client.hgetall(f'metadata/{instance_id}')
        if metadata is not None:
            metadata = {k: loads(v) for k, v in metadata.items()}  # type: ignore
            instance['metadata'] = metadata

        return instance

    def get_instance_by_external_id(self, rpc_id: str) -> Optional[UserData]:
        instance_id = self.__client.hget('external_ids', rpc_id)
        if instance_id is None:
            return None

        return self.get_instance(instance_id)  # type: ignore

    def get_all_instances(self) -> List[UserData]:
        keys = self.__client.keys('instance/*')

        result = []
        for key in keys:  # type: ignore
            if instance := self.get_instance(key.split('/')[1]):
                result.append(instance)

        return result

    def get_expired_instances(self) -> List[UserData]:
        instance_ids = self.__client.zrange(
            'expiries', 0, int(time.time()), byscore=True
        )

        instances = []
        for instance_id in instance_ids:  # type: ignore
            if instance := self.get_instance(instance_id):
                instances.append(instance)

        return instances

    def update_metadata(self, instance_id: str, metadata: Dict[str, Union[str, List[Dict[str, str]]]]):
        pipeline = self.__client.pipeline()
        try:
            for k, v in metadata.items():
                pipeline.hset(f'metadata/{instance_id}', k, dumps(v))
        finally:
            pipeline.execute()
