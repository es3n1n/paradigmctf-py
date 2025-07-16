import sys
from pprint import pprint

from web3 import Web3

from ctf_solvers.solver import get_pwn_flag, kill_instance, launch_instance
from ctf_solvers.types import ChallengeInstanceInfo
from ctf_solvers.utils import solve


class PwnChallengeSolver:
    def start(self) -> None:
        kill_instance()
        data = launch_instance()

        print('[+] instance:', flush=True)
        pprint(data)
        print(end='', flush=True)

        self._solve(data)
        flag = get_pwn_flag()
        print('[+] flag:', flag, flush=True)
        sys.exit(0 if flag else 1)

    def _solve(self, data: ChallengeInstanceInfo) -> None:
        # Can be overriden, if needed
        web3 = Web3(Web3.HTTPProvider(data['http_endpoint']))
        contract = data['contracts'][next(iter(data['contracts'].keys()))]
        solve(web3, 'project', data['private_key'], contract, 'script/Solve.s.sol:Solve')
