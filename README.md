# paradigmctf.py

Slightly modified/refactored/fixed version of [paradigmctf.py](https://github.com/paradigmxyz/paradigm-ctf-infrastructure/)

### Docker hub

[`es3n1n/paradigmctf.py:latest`](https://hub.docker.com/repository/docker/es3n1n/paradigmctf.py/general)

### What's changed

- Fixed instance deletion
- A lot of refactoring for PEP8 (mypy, ruff now produce zero errors)
- Added print instance option for the challenge launchers
- Refactored error handling within challenge launchers, no more sensitive info leaks
- Fixed a few race conditions within backends
- Moved web services to uvicorn workers(5 workers per service, editable) for better performance
- Added possibility to deploy multiple contracts per challenge **(you must use [our forge-ctf](https://github.com/es3n1n/forge-ctf))**
- Completely rewrote websocket anvil proxy, now it preserves connection
- Some parts of solvers were rewritten
- Added CTFd integration
- Migrated to uv
- Other improvements, fixes

### Untested features

- KOTH challenges
- KOTH solvers
- SQLite database
- K8s backend

### Example deployments

There a few compose examples for deployments that are used for tests, you can reference them 
while deploying your own instance:

- [compose.yml](./compose.yml) - docker backend
- [compose-k8s.yml](./compose-k8s.yml) - k8s backend

### Running tests

To run tests, you will first need to deploy either of the example deployments.

### Todo

- Make database stuff async
- Get rid of blind exception catches
- Migrate from requests to aiohttp fully