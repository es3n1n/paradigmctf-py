from cheb3 import Connection

from . import Instance, compile_src_for


def test_challenge_hello() -> None:
    instance = Instance(port=31337)
    data = instance.launch()
    assert instance.get_pwn_flag() is None

    contracts = compile_src_for('hello', 'Hello.sol', solc_version='0.8.20')
    conn = Connection(data['http_endpoint'])
    acc = conn.account(data['private_key'])

    hello_abi, hello_bytecode = contracts['Hello']
    hello = conn.contract(signer=acc, address=data['contracts']['Hello'], abi=hello_abi, bytecode=hello_bytecode)
    hello.functions.solve().send_transaction()

    assert instance.get_pwn_flag() == 'cr3{paradigm_ctf_hello_world}'
