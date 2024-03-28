import json

from web3 import Web3

from foundry.anvil import anvil_setCode


def anvil_setCodeFromFile(
        web3: Web3,
        addr: str,
        target: str,  # 'ContractFile.sol:ContractName',
):
    file, contract = target.split(':')

    with open(f'/artifacts/out/{file}/{contract}.json', 'r') as f:
        cache = json.load(f)

        bytecode = cache['deployedBytecode']['object']

    anvil_setCode(web3, addr, bytecode)


def http_url_to_ws(url: str) -> str:
    if url.startswith('http://'):
        return 'ws://' + url[len('http://'):]
    elif url.startswith('https://'):
        return 'wss://' + url[len('https://'):]

    return url
