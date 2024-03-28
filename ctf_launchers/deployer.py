import os
import subprocess
from json import loads
from typing import Dict, List

from web3 import Web3

from foundry.anvil import anvil_autoImpersonateAccount

from .types import ChallengeContract


def _deserialize_deploy_response(response: str) -> List[ChallengeContract]:
    result: List[ChallengeContract] = list()

    for line in response.splitlines():
        if len(line) == 0:
            continue

        item = loads(line)
        result.append({
            'name': item[0],
            'address': item[1]
        })

    return result


def deploy(
        web3: Web3,
        project_location: str,
        mnemonic: str,
        deploy_script: str = 'script/Deploy.s.sol:Deploy',
        env: Dict = {},
) -> List[ChallengeContract]:
    anvil_autoImpersonateAccount(web3, True)

    rfd, wfd = os.pipe2(os.O_NONBLOCK)  # type: ignore

    proc = subprocess.Popen(
        args=[
            '/opt/foundry/bin/forge',
            'script',
            '--rpc-url',
            web3.provider.endpoint_uri,  # type: ignore
            '--out',
            '/artifacts/out',
            '--cache-path',
            '/artifacts/cache',
            '--broadcast',
            '--unlocked',
            '--sender',
            '0x0000000000000000000000000000000000000000',
            deploy_script,
        ],
        env={
            'PATH': '/opt/huff/bin:/opt/foundry/bin:/usr/bin:' + os.getenv('PATH', '/fake'),
            'MNEMONIC': mnemonic,
            'OUTPUT_FILE': f'/proc/self/fd/{wfd}',
        } | env,
        pass_fds=[wfd],
        cwd=project_location,
        text=True,
        encoding='utf8',
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()

    anvil_autoImpersonateAccount(web3, False)

    if proc.returncode != 0:
        print(stdout)
        print(stderr)
        raise Exception('forge failed to run')

    result = os.read(rfd, 1024).decode('utf8')

    os.close(rfd)
    os.close(wfd)

    return _deserialize_deploy_response(result)
