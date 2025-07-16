from web3 import Web3
from web3.types import RPCResponse


class AnvilError(Exception):
    """Custom exception for Anvil RPC errors."""


def check_error(resp: RPCResponse) -> None:
    if 'error' in resp:
        msg = f'rpc exception: {resp["error"]}'
        raise AnvilError(msg)


def anvil_auto_impersonate_account(web3: Web3, *, enabled: bool) -> None:
    check_error(
        web3.provider.make_request(
            'anvil_autoImpersonateAccount',  # type: ignore[arg-type]
            [enabled],
        )
    )


def anvil_set_code(web3: Web3, addr: str, bytecode: str) -> None:
    check_error(
        web3.provider.make_request(
            'anvil_setCode',  # type: ignore[arg-type]
            [addr, bytecode],
        )
    )


def anvil_set_storage_at(
    web3: Web3,
    addr: str,
    slot: str,
    value: str,
) -> None:
    check_error(
        web3.provider.make_request(
            'anvil_setStorageAt',  # type: ignore[arg-type]
            [addr, slot, value],
        )
    )


def anvil_set_balance(
    web3: Web3,
    addr: str,
    balance: str,
) -> None:
    check_error(
        web3.provider.make_request(
            'anvil_setBalance',  # type: ignore[arg-type]
            [addr, balance],
        )
    )
