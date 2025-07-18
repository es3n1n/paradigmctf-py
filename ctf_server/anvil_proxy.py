import builtins
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import Any

import aiohttp
import websockets
from fastapi import FastAPI, Request, WebSocket
from loguru import logger
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.websockets import WebSocketDisconnect
from websockets import WebSocketException

from .databases import Database
from .loaders import load_database
from .utils import worker


ALLOWED_NAMESPACES = ['web3', 'eth', 'net']
DISALLOWED_METHODS = [
    'eth_sign',
    'eth_signTransaction',
    'eth_signTypedData',
    'eth_signTypedData_v3',
    'eth_signTypedData_v4',
    'eth_sendTransaction',
    'eth_sendUnsignedTransaction',
]


@dataclass
class Context:
    # note(es3n1n, 27.03.24): HACK: mypy won't know that we will initialize these within the lifespan
    session: aiohttp.ClientSession = None  # type: ignore[assignment]
    database: Database = None  # type: ignore[assignment]

    def setup(self) -> None:
        self.session = aiohttp.ClientSession()
        self.database = load_database()

    async def shutdown(self) -> None:
        if self.session is not None:
            await self.session.close()


context = Context()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    worker.setup('anvil_proxy')
    context.setup()
    yield
    await context.shutdown()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


def jsonrpc_fail(id_: str | int | None, code: int, message: str) -> dict[str, str | dict[str, str | int] | Any]:
    return {
        'jsonrpc': '2.0',
        'id': id_,
        'error': {
            'code': code,
            'message': message,
        },
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(jsonrpc_fail(None, -32600, exc.detail), status_code=exc.status_code)


@app.api_route('/', methods=['GET', 'POST'])
async def root() -> dict:
    return jsonrpc_fail(None, -32600, 'Please use the full node url')


def validate_request(request: dict) -> dict | None:
    if not isinstance(request, dict):
        return jsonrpc_fail(None, -32600, 'expected json object')

    request_id = request.get('id')
    request_method = request.get('method')

    if request_id is None:
        return jsonrpc_fail(None, -32600, 'invalid jsonrpc id')

    if not isinstance(request_method, str):
        return jsonrpc_fail(request['id'], -32600, 'invalid jsonrpc method')

    if request_method.split('_')[0] not in ALLOWED_NAMESPACES or request_method in DISALLOWED_METHODS:
        return jsonrpc_fail(request['id'], -32600, 'forbidden jsonrpc method')

    return None


async def proxy_request(
    external_id: str, anvil_id: str, request_id: str | None, body: dict | list | str | int | None
) -> dict | None:
    user_data = context.database.get_instance_by_external_id(external_id)
    if user_data is None:
        return jsonrpc_fail(request_id, -32602, 'invalid rpc url, instance not found')

    anvil_instance = user_data.get('anvil_instances', {}).get(anvil_id, None)
    if anvil_instance is None:
        return jsonrpc_fail(request_id, -32602, 'invalid rpc url, chain not found')

    instance_host = f'http://{anvil_instance["ip"]}:{anvil_instance["port"]}'
    try:
        async with context.session.post(instance_host, json=body) as resp:
            return await resp.json()
    except Exception as e:
        logger.opt(exception=e).error(f'failed to proxy anvil request to {external_id}/{anvil_id}')
        return jsonrpc_fail(request_id, -32602, str(e))


@app.post('/{external_id}/{anvil_id}')
async def http_rpc(external_id: str, anvil_id: str, request: Request) -> dict | list | None:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return jsonrpc_fail(None, -32600, 'expected json body')

    # special handling for batch requests
    if isinstance(body, list):
        responses = []
        for idx, req in enumerate(body):
            validation_error = validate_request(req)
            responses.append(validation_error)

            if validation_error is not None:
                # neuter the request
                body[idx] = {
                    'jsonrpc': '2.0',
                    'id': idx,
                    'method': 'web3_clientVersion',
                }

        upstream_responses = await proxy_request(external_id, anvil_id, None, body)

        for idx in range(len(responses)):
            if responses[idx] is None:
                if isinstance(upstream_responses, list):
                    responses[idx] = upstream_responses[idx]
                else:
                    responses[idx] = upstream_responses

        return responses

    validation_resp = validate_request(body)
    if validation_resp is not None:
        return validation_resp

    return await proxy_request(external_id, anvil_id, body['id'], body)


@app.websocket('/{external_id}/{anvil_id}/ws')
async def ws_rpc(external_id: str, anvil_id: str, client_ws: WebSocket) -> None:
    await client_ws.accept()

    user_data = context.database.get_instance_by_external_id(external_id)
    if user_data is None:
        await client_ws.send_json(jsonrpc_fail(None, -32602, 'invalid rpc url, instance not found'))
        return

    anvil_instance = user_data.get('anvil_instances', {}).get(anvil_id, None)
    if anvil_instance is None:
        await client_ws.send_json(jsonrpc_fail(None, -32602, 'invalid rpc url, chain not found'))
        return

    instance_host = f'ws://{anvil_instance["ip"]}:{anvil_instance["port"]}'

    try:
        async with websockets.connect(instance_host) as remote_ws:
            while True:
                message = await client_ws.receive_text()

                try:
                    json_msg = json.loads(message)
                except json.JSONDecodeError:
                    await client_ws.send_json(jsonrpc_fail(None, -32600, 'expected json body'))
                    continue

                if validation := validate_request(json_msg):
                    await client_ws.send_json(validation)
                    continue

                await remote_ws.send(message)

                response = await remote_ws.recv()
                if isinstance(response, str):
                    response = response.encode()
                await client_ws.send_bytes(response)
    except (WebSocketDisconnect, WebSocketException, KeyError):  # KeyError for empty messages
        # fixme(es3n1n, 28.03.24): ugly exception handling
        with suppress(builtins.BaseException):
            await remote_ws.close()
        with suppress(builtins.BaseException):
            await client_ws.close()
