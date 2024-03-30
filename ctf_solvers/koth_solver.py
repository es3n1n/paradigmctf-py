import abc
from pprint import pprint

from ctf_solvers.solver import TicketedRemote, kill_instance, launch_instance
from ctf_solvers.types import ChallengeInstanceInfo


class KothChallengeSolver(abc.ABC):
    def start(self):
        kill_instance()

        data = self.launch_instance()

        print('[+] instance:', flush=True)
        pprint(data)
        print('', end='', flush=True)

        self._submit(data)

        with TicketedRemote() as r:
            r.recvuntil(b'?')
            r.send(b'3\n')
            data = r.recvall().decode('utf8').strip()

        print(f'[+] response: {data}')

    def launch_instance(self):
        return launch_instance()

    @abc.abstractmethod
    def _submit(self, challenge: ChallengeInstanceInfo):
        pass
