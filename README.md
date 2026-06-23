# OpenAD Zero

OpenAD Zero is a safe-by-design Windows / Active Directory pentest copilot MVP. V1 creates missions, validates an internal scope, runs a real Nmap discovery scan from the backend, streams logs through WebSocket, parses Nmap XML, and proposes non-executed next actions.

## V1 limits

Only Nmap safe discovery is implemented. NetExec, Nuclei, BloodHound CE, SharpHound, exploitation, credential collection, lateral movement, brute force, pass-the-hash, LSASS dump, DCSync, persistence, EDR bypass, reports and AI planning are intentionally not implemented.

## Quick start

```bash
cp .env.example .env
docker compose up --build
# or: docker-compose up --build
```

Open the UI at http://localhost:5173 and the API at http://localhost:8000. Example scope: `192.168.1.0/24`. Public ranges are refused unless `ALLOW_PUBLIC_SCANS=true` is set explicitly.

## Tests

```bash
make backend-test
make frontend-build
```

## API

- `GET /api/health`
- `POST /api/missions`
- `POST /api/missions/{mission_id}/start`
- `GET /api/missions/{mission_id}`
- `GET /api/missions`
- `WS /ws/missions/{mission_id}`

## Architecture

- `backend/app/core`: configuration, scope validation and command allowlist.
- `backend/app/jobs`: secure Nmap runner using argument lists, no shell.
- `backend/app/parsers`: Nmap XML parser.
- `backend/app/planner`: simple V1 findings and next actions.
- `frontend/src`: React cockpit with live console, hosts and actions.
- `evidence/`: stdout, stderr and XML per mission/job.

## Security

The frontend never submits shell commands. The backend builds Nmap commands from validated internal templates, refuses invalid/public/too-large scopes by default, stores evidence, logs command previews, handles missing Nmap, and only displays data from user missions, backend events and Nmap XML.

## Next steps

Step 2 NetExec safe enum, Step 3 Nuclei, Step 4 BloodHound CE / SharpHound, Step 5 React Flow graph, Step 6 reporting, Step 7 advanced planner.
