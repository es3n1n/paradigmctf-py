#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List

from web3 import Web3

from ctf_launchers.pwn_launcher import PwnChallengeLauncher
from ctf_launchers.types import ChallengeContract


class Launcher(PwnChallengeLauncher):
    pass


Launcher(project_location='/challenge/project').run()
