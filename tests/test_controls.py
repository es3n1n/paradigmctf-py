from urllib.parse import urlparse

from cheb3 import Connection

from . import Instance


HELLO_PWN_INSTANCE = Instance(port=31337)
# flags will be tested in challenge tests


def test_launch() -> None:
    # Kill if it already exists
    HELLO_PWN_INSTANCE.kill()

    instance = HELLO_PWN_INSTANCE.launch()
    http_endpoint = urlparse(instance['http_endpoint'])
    assert http_endpoint.scheme in ('http', 'https')
    assert urlparse(instance['ws_endpoint']).scheme == {'http': 'ws', 'https': 'wss'}[http_endpoint.scheme]
    assert bytes.fromhex(instance['private_key'])
    assert instance['contracts']['Hello'].startswith('0x')

    # Make sure the chain is up
    connection = Connection(instance['http_endpoint'])
    account = connection.account(instance['private_key'])
    assert connection.get_balance(account.address)


def test_get_info() -> None:
    HELLO_PWN_INSTANCE.launch(kill_if_exists=False)

    instance = HELLO_PWN_INSTANCE.get()
    assert instance


def test_kill() -> None:
    instance = HELLO_PWN_INSTANCE.launch(kill_if_exists=False)
    assert instance
    HELLO_PWN_INSTANCE.kill()
    assert HELLO_PWN_INSTANCE.get() is None
