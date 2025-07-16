import os
from types import TracebackType
from urllib.parse import urlparse

from pwn import context, remote

from ctf_solvers.types import ChallengeInstanceInfo


class TicketedRemote:
    def __enter__(self) -> remote:
        # note(es3n1n, 30.03.24): designed only to be used within the healthchecker
        with context.quiet:
            self.__r = remote('challenge', 1337)

        data = self.__r.recvuntil(b'?')
        data_str = data.decode()
        if 'ticket' not in data_str and 'token' not in data_str:
            self.__r.unrecv(data)
            return self.__r

        self.__r.sendline(os.getenv('TICKET', '').encode('utf8'))
        return self.__r

    def __exit__(
        self, type_: type[BaseException] | None, value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        with context.quiet:
            self.__r.close()


def kill_instance() -> None:
    with TicketedRemote() as r:
        r.sendlineafter(b'?', b'3')
        with context.quiet:
            r.recvall()


def get_pwn_flag() -> str | None:
    with TicketedRemote() as r:
        r.sendlineafter(b'?', b'4')
        flag = r.recvline().decode().strip()

    return None if 'are you sure you solved it?' in flag else flag


def _sanitize_rpc_url(url: str) -> str:
    url_info = urlparse(url)
    return f'http://ctf-server-anvil-proxy:8545/{url_info.path.lstrip("/")}'


def launch_instance() -> ChallengeInstanceInfo:
    with TicketedRemote() as r:
        r.sendlineafter(b'?', b'1')
        r.recvuntil(b'- rpc endpoints:\n')

    http_endpoint = r.recvline().decode().split('- ')[1].strip()
    ws_endpoint = r.recvline().decode().split('- ')[1].strip()
    r.recvuntil(b'private key: ')
    private_key = r.recvline().decode().strip()

    contracts: dict[str, str] = {}
    while True:
        try:
            line = r.recvline().decode()[2:]
        except EOFError:
            break
        contracts[line.split(' contract')[0]] = line.split(':')[1].strip()

    return {
        'http_endpoint': _sanitize_rpc_url(http_endpoint),
        'ws_endpoint': _sanitize_rpc_url(ws_endpoint),
        'private_key': private_key,
        'contracts': contracts,
    }
