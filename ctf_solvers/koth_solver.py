import abc

from ctf_solvers.types import ChallengeInstanceInfo


class KothChallengeSolver(abc.ABC):
    def start(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _submit(self, challenge: ChallengeInstanceInfo) -> None:
        pass
