import abc
import os
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass

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

        self.mnemonic = generate_mnemonic(12, lang='english')

        for _i, _action in enumerate(self._actions):
            pass

        try:
            handler = self._actions[int(input('action? ')) - 1]
        except (KeyError, ValueError, IndexError, EOFError):
            sys.exit(1)

        try:
            sys.exit(handler.handler())
        except NonSensitiveError:
            sys.exit(1)
        except Exception:
            traceback.print_exc()
            sys.exit(1)

    def get_anvil_instances(self) -> dict[str, LaunchAnvilInstanceArgs]:
        return {
            'main': self.get_anvil_instance(),
        }

    def get_daemon_instances(self) -> dict[str, DaemonInstanceArgs]:
        return {}

    def get_anvil_instance(self, **kwargs: int | str | None) -> LaunchAnvilInstanceArgs:
        if 'balance' not in kwargs:
            kwargs['balance'] = 1000
        if 'accounts' not in kwargs:
            kwargs['accounts'] = 2
        if 'fork_url' not in kwargs:
            kwargs['fork_url'] = ETH_RPC_URL
        if 'mnemonic' not in kwargs:
            kwargs['mnemonic'] = self.mnemonic
        return LaunchAnvilInstanceArgs(**kwargs)  # type: ignore[typeddict-item]

    def get_instance_id(self) -> str:
        return f'blockchain-{CHALLENGE}-{self.team}'.lower()

    # TODO(es3n1n, 28.03.24): create a type alias for metadata and replace it everywhere
    def update_metadata(self, new_metadata: dict[str, str | list[ChallengeContract]]) -> int | None:
        resp = requests.post(
            f'{ORCHESTRATOR_HOST}/instances/{self.get_instance_id()}/metadata',
            json=new_metadata,
            timeout=5,
        )
        body = resp.json()
        if not body['ok']:
            return 1
        return None

    def launch_instance(self) -> int:
        body = requests.post(
            f'{ORCHESTRATOR_HOST}/instances',
            json=CreateInstanceRequest(
                instance_id=self.get_instance_id(),
                timeout=TIMEOUT,
                anvil_instances=self.get_anvil_instances(),
                daemon_instances=self.get_daemon_instances(),
            ),
            timeout=5,
        ).json()
        if not body['ok']:
            raise NonSensitiveError(body['message'])

        user_data = body['data']

        challenge_contracts = self.deploy(user_data, self.mnemonic)

        if x := self.update_metadata({'mnemonic': self.mnemonic, 'challenge_contracts': challenge_contracts}):
            return x

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
        resp.json()
        return 0

    def deploy(self, user_data: UserData, mnemonic: str) -> list[ChallengeContract]:
        web3 = get_privileged_web3(user_data, 'main')

        return deploy(web3, self.project_location, mnemonic, env=self.get_deployment_args(user_data))

    @abc.abstractmethod
    def get_deployment_args(self, user_data: UserData) -> dict[str, str]:
        return {}

    @abc.abstractmethod
    def _print_instance_info(
        self,
        user_data: dict,
        mnemonic: str | None = None,
        challenge_contracts: list[ChallengeContract] | None = None,
    ) -> None:
        for _anvil_id in user_data['anvil_instances']:
            pass

        metadata = user_data.get('metadata', {})
        mnemonic = mnemonic or metadata.get('mnemonic', 'none')
        challenge_contracts = challenge_contracts or metadata.get('challenge_contracts', [])

        for _contract in challenge_contracts:
            pass
