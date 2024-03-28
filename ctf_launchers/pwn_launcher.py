import os
from typing import List

import requests
from eth_abi import abi
from web3 import Web3

from ctf_launchers.launcher import ORCHESTRATOR_HOST, Action, Launcher
from ctf_launchers.team_provider import TeamProvider, get_team_provider
from ctf_launchers.types import ChallengeContract
from ctf_server.types import get_privileged_web3


FLAG = os.getenv('FLAG', 'cr3{flag}')


class PwnChallengeLauncher(Launcher):
    def __init__(
        self,
        project_location: str = 'challenge/project',
        provider: TeamProvider = get_team_provider(),
    ):
        super().__init__(
            project_location,
            provider,
            [
                Action(name='get flag', handler=self.get_flag),
            ],
        )

    def get_flag(self) -> int:
        instance_body = requests.get(f'{ORCHESTRATOR_HOST}/instances/{self.get_instance_id()}').json()
        if not instance_body['ok']:
            print(instance_body['message'])
            return 1

        user_data = instance_body['data']

        web3 = get_privileged_web3(user_data, 'main')
        if not self.is_solved(
            web3, user_data['metadata']['challenge_contracts']
        ):
            print('are you sure you solved it?')
            return 0

        print(FLAG)
        return 0

    def is_contract_solved(self, web3: Web3, contract: ChallengeContract) -> bool:
        (result,) = abi.decode(
            ['bool'],
            web3.eth.call(
                {
                    'to': contract['address'],
                    'data': web3.keccak(text='isSolved()')[:4],
                }
            ),
        )

        return result

    def is_solved(self, web3: Web3, contracts: List[ChallengeContract]) -> bool:
        return not any(
            not self.is_contract_solved(web3, contract) for contract in contracts
        )
