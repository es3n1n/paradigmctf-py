from web3 import Web3
from web3.types import RPCResponse


def check_error(resp: RPCResponse):
    if 'error' in resp:
        raise Exception('rpc exception', resp['error'])


def anvil_autoImpersonateAccount(web3: Web3, enabled: bool):
    check_error(web3.provider.make_request(
        'anvil_autoImpersonateAccount',  # type: ignore
        [enabled]
    ))


def anvil_setCode(web3: Web3, addr: str, bytecode: str):
    check_error(web3.provider.make_request(
        'anvil_setCode',  # type: ignore
        [addr, bytecode]
    ))


def anvil_setStorageAt(
    web3: Web3,
    addr: str,
    slot: str,
    value: str,
):
    check_error(web3.provider.make_request(
        'anvil_setStorageAt',  # type: ignore
        [addr, slot, value]
    ))


def anvil_setBalance(
    web3: Web3,
    addr: str,
    balance: str,
):
    check_error(web3.provider.make_request(
        'anvil_setBalance',  # type: ignore
        [addr, balance]
    ))
