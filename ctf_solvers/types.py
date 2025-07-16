from typing import TypedDict


class ChallengeInstanceInfo(TypedDict):
    http_endpoint: str
    http_endpoint_compose: str
    ws_endpoint: str
    ws_endpoint_compose: str
    private_key: str
    contracts: dict[str, str]  # name: address
