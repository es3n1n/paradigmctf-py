#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO
from pathlib import Path

from ctf_solvers.solver import launch_instance, get_pwn_flag
from cheb3 import Connection
from cheb3.utils import compile_file

HOST = '127.0.0.1'


def src_for(challenge: str, file: str) -> str:
    return str(Path(__file__).parent / challenge / 'project' / 'src' / file)


def solve_hello() -> str | None:
    instance = (HOST, 13371)
    data = launch_instance(*instance)

    contracts = compile_file(src_for('hello', 'Hello.sol'), solc_version='0.8.20')
    conn = Connection(data['http_endpoint'])
    acc = conn.account(data['private_key'])

    hello_abi, hello_bytecode = contracts['Hello']
    hello = conn.contract(signer=acc, address=data['contracts']['Hello'], abi=hello_abi, bytecode=hello_bytecode)
    hello.functions.solve().send_transaction()

    return get_pwn_flag(*instance)


if __name__ == '__main__':
    print('hello flag:', solve_hello())
