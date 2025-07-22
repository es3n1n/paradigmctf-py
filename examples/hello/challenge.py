#!/usr/bin/env python3
from ctf_launchers.pwn_launcher import PwnChallengeLauncher


class Launcher(PwnChallengeLauncher):
    pass


Launcher(project_location='/challenge/project').run()
