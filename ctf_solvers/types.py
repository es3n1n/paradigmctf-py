from typing import Dict, TypedDict


class ChallengeInstanceInfo(TypedDict):
    http_endpoint: str
    ws_endpoint: str
    private_key: str
    contracts: Dict[str, str]  # name: address
