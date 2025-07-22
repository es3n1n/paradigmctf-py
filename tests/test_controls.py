from urllib.parse import urlparse

from cheb3 import Connection
from web3 import Web3

from . import HELLO_PWN


# flags will be tested in challenge tests


def test_launch() -> None:
    # Kill if it already exists
    instance = HELLO_PWN.launch(kill_if_exists=True)
    http_endpoint = urlparse(instance['http_endpoint'])
    assert http_endpoint.scheme in ('http', 'https')
    assert urlparse(instance['ws_endpoint']).scheme == {'http': 'ws', 'https': 'wss'}[http_endpoint.scheme]
    assert bytes.fromhex(instance['private_key'])
    assert instance['contracts']['Hello'].startswith('0x')

    # Make sure the chain is up
    connection = Connection(instance['http_endpoint'])
    account = connection.account(instance['private_key'])
    assert connection.get_balance(account.address)

    # Make sure ws endpoint is also up
    w3 = Web3(Web3.LegacyWebSocketProvider(instance['ws_endpoint']))
    w3.is_connected(show_traceback=True)
    assert w3.eth.get_balance(account.address)


def test_get_info() -> None:
    HELLO_PWN.launch(kill_if_exists=False)
    instance = HELLO_PWN.get()
    assert instance


def test_kill() -> None:
    instance = HELLO_PWN.launch(kill_if_exists=False)
    assert instance
    HELLO_PWN.kill()
    assert HELLO_PWN.get() is None
