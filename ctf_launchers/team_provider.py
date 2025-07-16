import abc
import os
from os import environ

import requests


class TeamProviderError(Exception):
    """Custom exception for errors in team provider operations."""


CTFD_PUBLIC_URL: str = environ.get('CTFD_PUBLIC_URL', 'https://cr3c.tf/').rstrip('/')
CTFD_INTERNAL_URL: str = environ.get('CTFD_INTERNAL_URL', 'https://cr3c.tf/').rstrip('/')


class TeamProvider(abc.ABC):
    @abc.abstractmethod
    def get_team(self) -> str | None:
        pass


class CTFdTeamProvider(TeamProvider):
    def __init__(self) -> None:
        pass

    def get_team(self) -> str | None:
        team = self.get_team_by_ctfd_token(input(f'token? you can get one at {CTFD_PUBLIC_URL}/settings '))
        if not team:
            return None

        return str(team)

    @staticmethod
    def get_team_by_ctfd_token(ctfd_token: str) -> int | None:
        user_info = requests.get(
            f'{CTFD_INTERNAL_URL}/api/v1/users/me',
            headers={
                'User-Agent': 'paradigmctf.py',
                'Authorization': f'Token {ctfd_token}',
                'Content-Type': 'application/json',
            },
            timeout=5,
        ).json()
        if 'success' not in user_info or not user_info['success'] or 'data' not in user_info:
            return None
        if not isinstance(user_info['data'], dict) or 'team_id' not in user_info['data']:
            return None

        team_id: int = user_info['data']['team_id']
        if not isinstance(team_id, int):
            return None

        return team_id


class StaticTeamProvider(TeamProvider):
    def __init__(self, team_id: str, ticket: str) -> None:
        self.__team_id = team_id
        self.__ticket = ticket

    def get_team(self) -> str | None:
        ticket = input('ticket? ')

        if ticket != self.__ticket:
            return None

        return self.__team_id


class LocalTeamProvider(TeamProvider):
    def __init__(self, team_id: str) -> None:
        self.__team_id = team_id

    def get_team(self) -> str | None:
        return self.__team_id


def get_team_provider() -> TeamProvider:
    env = os.getenv('ENV', 'local')
    if env == 'local':
        return LocalTeamProvider(team_id='local')
    if env == 'dev':
        return StaticTeamProvider(team_id='dev', ticket='dev2023')
    if env == 'ctfd':
        return CTFdTeamProvider()
    msg = f'unknown team provider: {env}'
    raise TeamProviderError(msg)
