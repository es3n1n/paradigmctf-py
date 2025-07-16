import contextlib

from filelock import FileLock, Timeout


class Worker:
    def __init__(self) -> None:
        self.lock: FileLock | None = None

    def setup(self, service_name: str) -> None:
        self.lock = FileLock(f'worker-{service_name}.lock')
        with contextlib.suppress(Timeout):
            self.lock.acquire(blocking=False)

    @property
    def is_first(self) -> bool:
        if self.lock is None:
            return False
        return self.lock.is_locked


worker = Worker()
