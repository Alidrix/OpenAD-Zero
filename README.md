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

## Étape 2 — NetExec safe SMB enum

OpenAD Zero intègre désormais NetExec uniquement en mode énumération SMB contrôlée. Après un scan Nmap, si un service SMB/445 est découvert, le planner propose des actions à validation humaine : fingerprint SMB/Windows, vérification défensive de SMB signing, test séparé de null session, puis listing des partages anonymes seulement si une null session semble possible.

NetExec est exécuté côté backend depuis des templates allowlistés (`command-catalog/netexec.yml`) : la GUI n’envoie jamais de commande libre. Une politique de refus bloque les options et mots-clés offensifs (`-x`, `--sam`, `--lsa`, `--ntds`, modules, dumping, spidering, bruteforce, exécution distante, etc.). La V2 n’ajoute pas de credentials, pas de password spraying, pas de pass-the-hash, pas de dump de secrets, pas de BloodHound réel et pas de relay.

### Vérifier les outils

- API : `GET /api/health`
- Outils backend : `GET /api/health/tools`
- La réponse inclut `nmap` et `netexec` avec `available` et `version`.
- Si `nxc` est absent, l’API et la GUI affichent proprement que NetExec est indisponible dans l’environnement backend.

### Workflow de test

1. Lancer une mission sur `192.168.1.0/24`.
2. Attendre la fin de Nmap.
3. Aller dans **Actions**.
4. Autoriser **Énumération SMB contrôlée avec NetExec**.
5. Observer la console live avec les lignes `[netexec]`.
6. Vérifier **Hosts / SMB facts** : domaine, OS, signing, SMBv1, null session, shares.
7. Vérifier **Findings**, notamment `SMB signing not required` si applicable.
8. Vérifier les prochaines actions proposées, par exemple préparation BloodHound non exécutable automatiquement en V2.

### Preuves

Chaque job NetExec écrit ses preuves dans :

```text
evidence/<mission_id>/jobs/<job_id>/
├── command.txt
├── stdout.log
├── stderr.log
├── netexec.log
├── parsed.json
└── findings.json
```

### Limites V2

Cette étape reste volontairement safe-by-design : elle ne réalise aucune exploitation, aucun dump, aucune exécution distante, aucun spidering de fichiers, aucun téléchargement/upload, aucune collecte BloodHound réelle et aucune attaque relay. Les actions de risque 3 sont préparées et affichées, mais l’exécution automatique est désactivée.
