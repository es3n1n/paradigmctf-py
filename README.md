# paradigmctf.py

Slightly modified/refactored/fixed version of [paradigmctf.py](https://github.com/paradigmxyz/paradigm-ctf-infrastructure/)

### Docker hub

[`es3n1n/paradigmctf.py:latest`](https://hub.docker.com/repository/docker/es3n1n/paradigmctf.py/general)

### What's changed

- Fixed instance deletion
- A lot of refactoring for PEP8 (mypy, flake8 now produces zero errors)
- Added print instance option for the challenge launchers
- Refactored error handling within challenge launchers, no more sensitive info leaks
- Fixed a few race conditions within backends
- Moved web services to uvicorn workers(5 workers per service, editable) for better performance
- Added possibility to deploy multiple contracts per challenge **(you must use [our forge-ctf](https://github.com/es3n1n/forge-ctf))**
- Completely rewrote websocket anvil proxy, now it preserves connection
- Some parts of solvers were rewritten; I bet it doesn't even work with k8s(PR welcome)
- Added CTFd integration
- Migrated to uv
- Other improvements, fixes

### Notes

- I never really tested koth challs/koth solvers/sqlite db, so please create an issue if something's up with them 

### Todo

- Make database stuff async
- Get rid of blind exception catches
- Migrate from requests to aiohttp fully