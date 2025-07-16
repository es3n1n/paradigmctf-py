import shutil
import subprocess

from web3 import Web3


class ForgeFailedError(Exception):
    """Exception raised when the forge command fails to execute."""


def solve(
    web3: Web3,
    project_location: str,
    player_key: str,
    challenge_addr: str,
    solve_script: str = 'script/Solve.s.sol:Solve',
) -> None:
    forge_location = shutil.which('forge')
    if forge_location is None:
        forge_location = '/opt/foundry/bin/forge'

    proc = subprocess.Popen(
        args=[
            forge_location,
            'script',
            '--rpc-url',
            web3.provider.endpoint_uri,  # type: ignore[attr-defined]
            '--slow',
            '-vvvvv',
            '--broadcast',
            solve_script,
        ],
        env={
            'PLAYER': player_key,
            'CHALLENGE': challenge_addr,
        },
        cwd=project_location,
        text=True,
        encoding='utf8',
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()

    if proc.returncode != 0:
        msg = f'forge failed to run: {stdout!r}, {stderr!r}'
        raise ForgeFailedError(msg)
