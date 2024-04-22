import abc
import os
from dataclasses import dataclass
from os import environ
from typing import Optional

import requests


CTFD_PUBLIC_URL: str = environ.get('CTFD_PUBLIC_URL', 'https://cr3c.tf/').rstrip('/')
CTFD_INTERNAL_URL: str = environ.get('CTFD_INTERNAL_URL', 'https://cr3c.tf/').rstrip('/')


class TeamProvider(abc.ABC):
    @abc.abstractmethod
    def get_team(self) -> Optional[str]:
        pass


class TicketTeamProvider(TeamProvider):
    @dataclass
    class Ticket:
        challenge_id: str
        team_id: str

    def __init__(self, challenge_id):
        self.__challenge_id = challenge_id

    def get_team(self):
        ticket = self.__check_ticket(input('ticket? '))
        if not ticket:
            print('invalid ticket!')
            return None

        if ticket.challenge_id != self.__challenge_id:
            print('invalid ticket!')
            return None

        return ticket.team_id

    def __check_ticket(self, ticket: str) -> Optional[Ticket]:
        ticket_info = requests.post(
            'https://ctf.paradigm.xyz/api/internal/check-ticket',
            json={
                'ticket': ticket,
            },
        ).json()
        if not ticket_info['ok']:
            return None

        return TicketTeamProvider.Ticket(
            challenge_id=ticket_info['ticket']['challengeId'],
            team_id=ticket_info['ticket']['teamId'],
        )


class CTFdTeamProvider(TeamProvider):
    def __init__(self):
        pass

    def get_team(self) -> Optional[str]:
        team = self.get_team_by_ctfd_token(input(f'token? you can get one at {CTFD_PUBLIC_URL}/settings '))
        if not team:
            print('invalid token!')
            return None

        return str(team)

    def get_team_by_ctfd_token(self, ctfd_token: str) -> Optional[int]:
        user_info = requests.get(
            f'{CTFD_INTERNAL_URL}/api/v1/users/me',
            headers={
                'User-Agent': 'paradigmctf.py',
                'Authorization': f'Token {ctfd_token}',
                'Content-Type': 'application/json',
            }
        ).json()
        if 'success' not in user_info or not user_info['success'] or 'data' not in user_info:
            return None
        if not isinstance(user_info['data'], dict) or 'team_id' not in user_info['data']:
            return None

        team_id: int = user_info['data']['team_id']
        if not isinstance(team_id, int):
            return None

        print(f'nice, authorized as team with id {team_id}')
        return team_id


class StaticTeamProvider(TeamProvider):
    def __init__(self, team_id, ticket):
        self.__team_id = team_id
        self.__ticket = ticket

    def get_team(self) -> str | None:
        ticket = input('ticket? ')

        if ticket != self.__ticket:
            print('invalid ticket!')
            return None

        return self.__team_id


class LocalTeamProvider(TeamProvider):
    def __init__(self, team_id):
        self.__team_id = team_id

    def get_team(self):
        return self.__team_id


def get_team_provider() -> TeamProvider:
    env = os.getenv('ENV', 'local')
    if env == 'local':
        return LocalTeamProvider(team_id='local')
    elif env == 'dev':
        return StaticTeamProvider(team_id='dev', ticket='dev2023')
    elif env == 'ctfd':
        return CTFdTeamProvider()
    else:
        return TicketTeamProvider(challenge_id=os.getenv('CHALLENGE_ID'))
