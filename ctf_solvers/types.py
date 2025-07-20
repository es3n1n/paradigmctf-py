from typing import TypedDict


class ChallengeInstanceInfo(TypedDict):
    # TODO(es3n1n, 20.07.25): rename _compose to _in_network
    http_endpoint: str
    http_endpoint_compose: str
    ws_endpoint: str
    ws_endpoint_compose: str
    private_key: str
    contracts: dict[str, str]  # name: address
