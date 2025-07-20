import os
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from time import time

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
EXTRA_ALLOWED_METHODS = os.getenv('EXTRA_ALLOWED_METHODS', '').split(',')


@dataclass
class Action:
    name: str
    handler: Callable[[], int]


class NonSensitiveError(Exception):
    pass


class Launcher:
    def __init__(self, project_location: str, provider: TeamProvider, actions: list[Action] | None = None) -> None:
        if actions is None:
            actions = []
        self.mnemonic: str = DEFAULT_MNEMONIC
        self.team: str | None = None
        self.project_location = project_location
        self.__team_provider = provider

        self._actions = []
        self._actions.append(Action(name='launch new instance', handler=self.launch_instance))
        self._actions.append(Action(name='instance info', handler=self.instance_info))
        self._actions.append(Action(name='kill instance', handler=self.kill_instance))
        self._actions = [*self._actions, *actions]

    def run(self) -> None:
        self.team = self.__team_provider.get_team()
        if not self.team:
            sys.exit(1)

        for i, action in enumerate(self._actions):
            print(f'{i + 1} - {action.name}')

        # TODO(es3n1n, 20.07.25): generate only when needed
        self.mnemonic = generate_mnemonic(12, lang='english')

        try:
            handler = self._actions[int(input('action? ')) - 1]
        except (KeyError, ValueError, IndexError, EOFError):
            sys.exit(1)

        try:
            sys.exit(handler.handler())
        except NonSensitiveError as e:
            print('error:', e)
            sys.exit(1)
        except Exception:
            print('an unexpected error occurred, please report it to the organizers (not the team)')
            traceback.print_exc()
            sys.exit(1)

    def get_anvil_instances(self) -> dict[str, LaunchAnvilInstanceArgs]:
        return {
            'main': self.get_anvil_instance(),
        }

    def get_daemon_instances(self) -> dict[str, DaemonInstanceArgs]:
        return {}

    def get_anvil_instance(self, **kwargs: int | str | list[str] | None) -> LaunchAnvilInstanceArgs:
        if 'balance' not in kwargs:
            kwargs['balance'] = 1000
        if 'accounts' not in kwargs:
            kwargs['accounts'] = 2
        if 'fork_url' not in kwargs:
            kwargs['fork_url'] = ETH_RPC_URL
        if 'mnemonic' not in kwargs:
            kwargs['mnemonic'] = self.mnemonic
        if 'extra_allowed_methods' not in kwargs:
            kwargs['extra_allowed_methods'] = EXTRA_ALLOWED_METHODS
        return LaunchAnvilInstanceArgs(**kwargs)  # type: ignore[typeddict-item]

    def get_instance_id(self) -> str:
        return f'blockchain-{CHALLENGE}-{self.team}'.lower()

    # TODO(es3n1n, 28.03.24): create a type alias for metadata and replace it everywhere
    def update_metadata(self, new_metadata: dict[str, str | list[ChallengeContract]]) -> int | None:
        resp = requests.post(
            f'{ORCHESTRATOR_HOST}/instances/{self.get_instance_id()}/metadata',
            json=new_metadata,
            timeout=60,
        )
        body = resp.json()
        if not body['ok']:
            return 1
        return None

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
            timeout=60,
        ).json()
        if not body['ok']:
            raise NonSensitiveError(body['message'])

        user_data = body['data']

        print('deploying challenge...')
        challenge_contracts = self.deploy(user_data, self.mnemonic)

        if x := self.update_metadata({'mnemonic': self.mnemonic, 'challenge_contracts': challenge_contracts}):
            print('unable to update metadata')
            return x

        print('your private blockchain has been set up!')
        self._print_instance_info(user_data, self.mnemonic, challenge_contracts)
        return 0

    def instance_info(self) -> int:
        body = requests.get(f'{ORCHESTRATOR_HOST}/instances/{self.get_instance_id()}', timeout=5).json()
        if not body['ok']:
            raise NonSensitiveError(body['message'])

        self._print_instance_info(body['data'])
        return 0

    def kill_instance(self) -> int:
        resp = requests.delete(f'{ORCHESTRATOR_HOST}/instances/{self.get_instance_id()}', timeout=5)
        body = resp.json()

        print(body.get('message', 'no message'))
        return 0

    def deploy(self, user_data: UserData, mnemonic: str) -> list[ChallengeContract]:
        web3 = get_privileged_web3(user_data, 'main')

        return deploy(web3, self.project_location, mnemonic, env=self.get_deployment_args(user_data))

    def get_deployment_args(self, _: UserData) -> dict[str, str]:
        # This method can be overridden to provide additional deployment arguments
        return {}

    @staticmethod
    def _print_instance_info(
        user_data: dict, mnemonic: str | None = None, challenge_contracts: list[ChallengeContract] | None = None
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
