import abc
import random
import string
import time
from threading import Thread

from eth_account import Account
from eth_account.hdaccount import key_from_seed, seed_from_mnemonic
from eth_account.signers.local import LocalAccount
from loguru import logger
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
from foundry.anvil import anvil_set_balance


class InstanceExistsError(Exception):
    pass


class Backend(abc.ABC):
    def __init__(self, database: Database) -> None:
        self._database = database

        # We only want to run this thread for a single worker
        if worker.is_first:
            Thread(
                target=self.__instance_pruner_thread,
                name=f'{self.__class__.__name__} Anvil Pruner',
                daemon=True,
            ).start()

    def __instance_pruner_thread(self) -> None:
        @logger.catch
        def pruner() -> None:
            for instance in self._database.get_expired_instances():
                logger.info(f'pruning expired instance: {instance["instance_id"]}')
                self.kill_instance(instance['instance_id'])

        while True:
            pruner()
            time.sleep(1)

    def launch_instance(self, args: CreateInstanceRequest) -> UserData:
        if self._database.get_instance(args['instance_id']) is not None:
            raise InstanceExistsError

        try:
            user_data = self._launch_instance_impl(args)
            self._database.register_instance(args['instance_id'], user_data)
        except:
            self._cleanup_instance(args)
            raise
        else:
            return user_data

    @abc.abstractmethod
    def _launch_instance_impl(self, args: CreateInstanceRequest) -> UserData:
        pass

    @abc.abstractmethod
    def _cleanup_instance(self, args: CreateInstanceRequest) -> None:
        pass

    @abc.abstractmethod
    def kill_instance(self, instance_id: str) -> UserData | None:
        pass

    @staticmethod
    def _generate_rpc_id(length: int = 24) -> str:
        return ''.join(random.SystemRandom().choice(string.ascii_letters) for _ in range(length))

    @staticmethod
    def __derive_account(derivation_path: str, mnemonic: str, index: int) -> LocalAccount:
        seed = seed_from_mnemonic(mnemonic, '')
        private_key = key_from_seed(seed, f'{derivation_path}{index}')
        return Account.from_key(private_key)

    def _prepare_node(self, args: LaunchAnvilInstanceArgs, web3: Web3) -> None:
        while not web3.is_connected():
            time.sleep(0.1)
            continue

        for i in range(args.get('accounts', None) or DEFAULT_ACCOUNTS):
            anvil_set_balance(
                web3,
                self.__derive_account(
                    args.get('derivation_path', None) or DEFAULT_DERIVATION_PATH,
                    args.get('mnemonic', None) or DEFAULT_MNEMONIC,
                    i,
                ).address,
                hex(int(args.get('balance', None) or DEFAULT_BALANCE) * 10**18),
            )
