import json
from pathlib import Path

from web3 import Web3

from foundry.anvil import anvil_set_code


def anvil_set_code_from_file(
    web3: Web3,
    addr: str,
    target: str,  # 'ContractFile.sol:ContractName',
) -> None:
    file, contract = target.split(':')

    with Path(f'/artifacts/out/{file}/{contract}.json').open('r') as f:
        cache = json.load(f)
        bytecode = cache['deployedBytecode']['object']

    anvil_set_code(web3, addr, bytecode)


def http_url_to_ws(url: str) -> str:
    if url.startswith('http://'):
        return 'ws://' + url[len('http://') :]
    if url.startswith('https://'):
        return 'wss://' + url[len('https://') :]

    return url
