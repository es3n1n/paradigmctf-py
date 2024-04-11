import abc
from pprint import pprint

from web3 import Web3

from ctf_solvers.solver import get_pwn_flag, kill_instance, launch_instance
from ctf_solvers.types import ChallengeInstanceInfo
from ctf_solvers.utils import solve


class PwnChallengeSolver(abc.ABC):
    def start(self):
        kill_instance()

        data = launch_instance()

        print('[+] instance:', flush=True)
        pprint(data)
        print('', end='', flush=True)

        self._solve(data)

        flag = get_pwn_flag()
        print('[+] flag:', flag, flush=True)

        exit(0 if flag else 1)

    def _solve(self, data: ChallengeInstanceInfo):
        web3 = Web3(Web3.HTTPProvider(data['http_endpoint']))
        contract = data['contracts'][list(data['contracts'].keys())[0]]
        solve(web3, 'project', data['private_key'], contract, 'script/Solve.s.sol:Solve')
