import abc
import sys

from web3 import Web3

from ctf_solvers.solver import get_pwn_flag, kill_instance, launch_instance
from ctf_solvers.types import ChallengeInstanceInfo
from ctf_solvers.utils import solve


class PwnChallengeSolver(abc.ABC):
    def start(self) -> None:
        kill_instance()
        data = launch_instance()

        self._solve(data)
        flag = get_pwn_flag()
        sys.exit(0 if flag else 1)

    @abc.abstractmethod
    def _solve(self, data: ChallengeInstanceInfo) -> None:
        web3 = Web3(Web3.HTTPProvider(data['http_endpoint']))
        contract = data['contracts'][next(iter(data['contracts'].keys()))]
        solve(web3, 'project', data['private_key'], contract, 'script/Solve.s.sol:Solve')
