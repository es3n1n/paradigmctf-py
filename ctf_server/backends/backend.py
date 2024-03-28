import abc
import logging
import random
import string
import time
from threading import Thread
from typing import Optional

from eth_account import Account
from eth_account.hdaccount import key_from_seed, seed_from_mnemonic
from eth_account.signers.local import LocalAccount
from web3 import Web3

from ctf_server.databases.database import Database
from ctf_server.types import (
    DEFAULT_ACCOUNTS,
    DEFAULT_BALANCE,
    DEFAULT_DERIVATION_PATH,
    DEFAULT_MNEMONIC,
    CreateInstanceRequest,
    LaunchAnvilInstanceArgs,
    UserData,
)
from ctf_server.utils import worker
from foundry.anvil import anvil_setBalance


class InstanceExists(Exception):
    pass


class Backend(abc.ABC):
    def __init__(self, database: Database):
        self._database = database

        # We only want to run this thread for a single worker
        if worker.is_first:
            Thread(
                target=self.__instance_pruner_thread,
                name=f'{self.__class__.__name__} Anvil Pruner',
                daemon=True,
            ).start()

    def __instance_pruner_thread(self):
        while True:
            try:
                for instance in self._database.get_expired_instances():
                    logging.info(
                        'pruning expired instance: %s', instance['instance_id']
                    )

                    self.kill_instance(instance['instance_id'])
            except Exception as e:
                logging.error('failed to prune instances', exc_info=e)
            time.sleep(1)

    def launch_instance(self, args: CreateInstanceRequest) -> UserData:
        if self._database.get_instance(args['instance_id']) is not None:
            raise InstanceExists()

        try:
            user_data = self._launch_instance_impl(args)
            self._database.register_instance(args['instance_id'], user_data)
            return user_data
        except:  # noqa
            self._cleanup_instance(args)
            raise

    @abc.abstractmethod
    def _launch_instance_impl(self, args: CreateInstanceRequest) -> UserData:
        pass

    def _cleanup_instance(self, args: CreateInstanceRequest):
        pass

    @abc.abstractmethod
    def kill_instance(self, id: str) -> Optional[UserData]:
        pass

    def _generate_rpc_id(self, N: int = 24) -> str:
        return ''.join(
            random.SystemRandom().choice(string.ascii_letters) for _ in range(N)
        )

    def __derive_account(self, derivation_path: str, mnemonic: str, index: int) -> LocalAccount:
        seed = seed_from_mnemonic(mnemonic, '')
        private_key = key_from_seed(seed, f'{derivation_path}{index}')

        return Account.from_key(private_key)

    def _prepare_node(self, args: LaunchAnvilInstanceArgs, web3: Web3):
        while not web3.is_connected():
            time.sleep(0.1)
            continue

        for i in range(args.get('accounts', None) or DEFAULT_ACCOUNTS):
            anvil_setBalance(
                web3,
                self.__derive_account(
                    args.get('derivation_path', None) or DEFAULT_DERIVATION_PATH,
                    args.get('mnemonic', None) or DEFAULT_MNEMONIC,
                    i,
                ).address,
                hex(int(args.get('balance', None) or DEFAULT_BALANCE) * 10**18),
            )
