from typing import Dict
from typing import TypedDict


class ChallengeInstanceInfo(TypedDict):
    http_endpoint: str
    ws_endpoint: str
    private_key: str
    contracts: Dict[str, str]  # name: address
