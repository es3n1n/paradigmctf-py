import abc
import os
import traceback
from dataclasses import dataclass
from time import time
from typing import Callable, Dict, List, Optional, Union

import requests
from eth_account.hdaccount import generate_mnemonic

from ctf_launchers.deployer import deploy
from ctf_launchers.team_provider import TeamProvider
from ctf_launchers.types import ChallengeContract
from ctf_launchers.utils import http_url_to_ws
from ctf_server.types import (
    DEFAULT_MNEMONIC,
    CreateInstanceRequest,
    DaemonInstanceArgs,
    LaunchAnvilInstanceArgs,
    UserData,
    get_player_account,
    get_privileged_web3,
)


CHALLENGE = os.getenv('CHALLENGE', 'challenge')
ORCHESTRATOR_HOST = os.getenv('ORCHESTRATOR_HOST', 'http://orchestrator:7283')
PUBLIC_HOST = os.getenv('PUBLIC_HOST', 'http://127.0.0.1:8545')
PUBLIC_WEBSOCKET_HOST = http_url_to_ws(PUBLIC_HOST)

ETH_RPC_URL = os.getenv('ETH_RPC_URL')
TIMEOUT = int(os.getenv('TIMEOUT', '1440'))


@dataclass
class Action:
    name: str
    handler: Callable[[], int]


class NonSensitiveError(Exception):
    pass


class Launcher(abc.ABC):
    def __init__(
            self, project_location: str, provider: TeamProvider, actions: List[Action] = []
    ):
        self.mnemonic: str = DEFAULT_MNEMONIC
        self.team: Optional[str] = None
        self.project_location = project_location
        self.__team_provider = provider

        self._actions = []
        self._actions.append(Action(name='launch new instance', handler=self.launch_instance))
        self._actions.append(Action(name='instance info', handler=self.instance_info))
        self._actions.append(Action(name='kill instance', handler=self.kill_instance))
        self._actions = [*self._actions, *actions]

    def run(self):
        self.team = self.__team_provider.get_team()
        if not self.team:
            exit(1)

        self.mnemonic = generate_mnemonic(12, lang='english')

        for i, action in enumerate(self._actions):
            print(f'{i + 1} - {action.name}')

        try:
            handler = self._actions[int(input('action? ')) - 1]
        except:  # noqa
            print('can you not')
            exit(1)

        try:
            exit(handler.handler())
        except NonSensitiveError as e:
            print('error:', e)
            exit(1)
        except Exception:  # noqa
            traceback.print_exc()
            print('an internal error occurred, contact admins')
            exit(1)
        finally:
            exit(0)  # should never happen, but just in case

    def get_anvil_instances(self) -> Dict[str, LaunchAnvilInstanceArgs]:
        return {
            'main': self.get_anvil_instance(),
        }

    def get_daemon_instances(self) -> Dict[str, DaemonInstanceArgs]:
        return {}

    def get_anvil_instance(self, **kwargs) -> LaunchAnvilInstanceArgs:
        if 'balance' not in kwargs:
            kwargs['balance'] = 1000
        if 'accounts' not in kwargs:
            kwargs['accounts'] = 2
        if 'fork_url' not in kwargs:
            kwargs['fork_url'] = ETH_RPC_URL
        if 'mnemonic' not in kwargs:
            kwargs['mnemonic'] = self.mnemonic
        return LaunchAnvilInstanceArgs(**kwargs)  # type: ignore

    def get_instance_id(self) -> str:
        return f'blockchain-{CHALLENGE}-{self.team}'.lower()

    # todo(es3n1n, 28.03.24): create a type alias for metadata and replace it everywhere
    def update_metadata(self, new_metadata: Dict[str, Union[str, List[ChallengeContract]]]):
        resp = requests.post(
            f'{ORCHESTRATOR_HOST}/instances/{self.get_instance_id()}/metadata',
            json=new_metadata,
        )
        body = resp.json()
        if not body['ok']:
            print(body['message'])
            return 1

    def launch_instance(self) -> int:
        print('creating private blockchain...')
        body = requests.post(
            f'{ORCHESTRATOR_HOST}/instances',
            json=CreateInstanceRequest(
                instance_id=self.get_instance_id(),
                timeout=TIMEOUT,
                anvil_instances=self.get_anvil_instances(),
                daemon_instances=self.get_daemon_instances(),
            ),
        ).json()
        if not body['ok']:
            raise NonSensitiveError(body['message'])

        user_data = body['data']

        print('deploying challenge...')
        challenge_contracts = self.deploy(user_data, self.mnemonic)

        if x := self.update_metadata(
            {'mnemonic': self.mnemonic, 'challenge_contracts': challenge_contracts}
        ):
            print('unable to update metadata')
            return x

        print('your private blockchain has been set up!')
        self._print_instance_info(user_data, self.mnemonic, challenge_contracts)
        return 0

    def instance_info(self) -> int:
        body = requests.get(
            f'{ORCHESTRATOR_HOST}/instances/{self.get_instance_id()}'
        ).json()
        if not body['ok']:
            raise NonSensitiveError(body['message'])

        self._print_instance_info(body['data'])
        return 0

    def kill_instance(self) -> int:
        resp = requests.delete(f'{ORCHESTRATOR_HOST}/instances/{self.get_instance_id()}')
        body = resp.json()

        print(body['message'])
        return 0

    def deploy(self, user_data: UserData, mnemonic: str) -> List[ChallengeContract]:
        web3 = get_privileged_web3(user_data, 'main')

        return deploy(
            web3, self.project_location, mnemonic, env=self.get_deployment_args(user_data)
        )

    def get_deployment_args(self, user_data: UserData) -> Dict[str, str]:
        return {}

    def _print_instance_info(
            self,
            user_data: dict,
            mnemonic: Optional[str] = None,
            challenge_contracts: Optional[List[ChallengeContract]] = None
    ) -> None:
        print('---- instance info ----')
        print(f'- will be terminated in: {(user_data.get("expires_at", 0) - time()) / 60:.2f} minutes')
        print('- rpc endpoints:')
        for anvil_id in user_data['anvil_instances']:
            print(f'    - {PUBLIC_HOST}/{user_data["external_id"]}/{anvil_id}')
            print(f'    - {PUBLIC_WEBSOCKET_HOST}/{user_data["external_id"]}/{anvil_id}/ws')

        metadata = user_data.get('metadata', {})
        mnemonic = mnemonic or metadata.get('mnemonic', 'none')
        challenge_contracts = challenge_contracts or metadata.get('challenge_contracts', [])

        print(f'- your private key: {get_player_account(mnemonic).key.hex()}')

        for contract in challenge_contracts:
            print(f'- {contract["name"]} contract: {contract["address"]}')
