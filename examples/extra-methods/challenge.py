#!/usr/bin/env python3
from ctf_launchers.pwn_launcher import PwnChallengeLauncher
from ctf_server.types import LaunchAnvilInstanceArgs


class Launcher(PwnChallengeLauncher):
    def get_anvil_instances(self) -> dict[str, LaunchAnvilInstanceArgs]:
        return {
            'main': self.get_anvil_instance(
                image='ghcr.io/es3n1n/foundry:latest',
                extra_allowed_methods=['debug_getRawReceipts'],
            ),
        }


Launcher(project_location='/challenge/project').run()
