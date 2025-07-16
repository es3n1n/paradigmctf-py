import abc

from ctf_server.types import UserData


class Database(abc.ABC):
    def __init__(self) -> None:
        super().__init__()

    @abc.abstractmethod
    def register_instance(self, instance_id: str, instance: UserData) -> None:
        pass

    @abc.abstractmethod
    def unregister_instance(self, instance_id: str) -> UserData | None:
        pass

    @abc.abstractmethod
    def get_instance(self, instance_id: str) -> UserData | None:
        pass

    @abc.abstractmethod
    def get_instance_by_external_id(self, external_id: str) -> UserData | None:
        pass

    @abc.abstractmethod
    def get_expired_instances(self) -> list[UserData]:
        pass

    @abc.abstractmethod
    def update_metadata(self, instance_id: str, metadata: dict[str, str | list[dict[str, str]]]) -> None:
        pass
