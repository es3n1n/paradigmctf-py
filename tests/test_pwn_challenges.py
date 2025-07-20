from cheb3 import Connection
from requests import post

from . import Instance, compile_src_for


HELLO = Instance(port=31337)
EXTRA_METHODS = Instance(port=31338)


def test_challenge_hello() -> None:
    data = HELLO.launch()
    assert HELLO.get_pwn_flag() is None

    contracts = compile_src_for('hello', 'Hello.sol', solc_version='0.8.20')
    conn = Connection(data['http_endpoint'])
    acc = conn.account(data['private_key'])

    hello_abi, hello_bytecode = contracts['Hello']
    hello = conn.contract(signer=acc, address=data['contracts']['Hello'], abi=hello_abi, bytecode=hello_bytecode)
    hello.functions.solve().send_transaction()

    assert HELLO.get_pwn_flag() == 'cr3{paradigm_ctf_hello_world}'


def test_extra_methods() -> None:
    extra_methods = EXTRA_METHODS.launch(kill_if_exists=False)
    hello = HELLO.launch(kill_if_exists=False)

    payload = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'eth_sign',
        'params': ['2'],
    }
    resp_ok = {'jsonrpc': '2.0', 'id': 1, 'error': {'code': -32602, 'message': 'odd number of digits'}}
    resp_denied = {'jsonrpc': '2.0', 'id': 1, 'error': {'code': -32600, 'message': 'forbidden jsonrpc method'}}

    assert post(extra_methods['http_endpoint'], json=payload, timeout=60).json() == resp_ok
    assert post(hello['http_endpoint'], json=payload, timeout=60).json() == resp_denied
