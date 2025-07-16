from typing import TypedDict


class ChallengeInstanceInfo(TypedDict):
    http_endpoint: str
    ws_endpoint: str
    private_key: str
    contracts: dict[str, str]  # name: address
