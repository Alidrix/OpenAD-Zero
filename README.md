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

V2 ajoute une intégration **NetExec SMB strictement contrôlée**. Après le scan Nmap, si SMB/445 est détecté, le planner propose des actions qui nécessitent une validation humaine avant exécution :

- `Énumération SMB contrôlée avec NetExec` (`netexec_smb_fingerprint`) pour enrichir hostname, domaine, OS, SMB signing et SMBv1 ;
- `Vérifier les hôtes sans SMB signing requis` (`netexec_smb_signing_check`) pour produire uniquement une liste défensive ;
- `Tester null session SMB` (`netexec_smb_null_session_check`) ;
- `Lister les partages accessibles anonymement` (`netexec_smb_null_session_shares`) seulement si une null session semble possible.

NetExec est exécuté côté backend uniquement. Le frontend envoie une approbation d’action, jamais une commande shell. Le backend reconstruit la commande depuis une allowlist, applique une politique de refus, lance `nxc` sans `shell=True`, streame les logs via WebSocket, parse les résultats et persiste les faits SMB, shares, findings et actions suivantes.

### Interdits V2

OpenAD Zero V2 bloque explicitement l’exécution distante, les modules NetExec, le password spraying, le bruteforce, pass-the-hash, les dumps SAM/LSA/NTDS/DPAPI/LSASS, DCSync, spidering, upload/download de fichiers et toute collecte de secrets. Aucune action relay n’est proposée ni exécutée ; le risque SMB signing est seulement documenté.

### Vérifier les outils

```bash
curl http://localhost:8000/api/health/tools
```

La réponse indique la disponibilité de `nmap` et `netexec` (`nxc`). Si NetExec n’est pas installé, la GUI affiche l’indisponibilité et les actions NetExec échouent proprement sans crash backend.

### Workflow NetExec

1. Lancer une mission sur `192.168.1.0/24`.
2. Attendre la fin de Nmap.
3. Aller dans `Actions`.
4. Autoriser `Énumération SMB contrôlée avec NetExec`.
5. Cocher les confirmations de scope autorisé et de journalisation.
6. Observer la console live avec les logs `[netexec]`.
7. Vérifier `Hosts` / SMB facts : domaine, OS, signing, SMBv1, null session et shares.
8. Vérifier les findings, notamment `SMB signing not required` si concerné.
9. Vérifier les prochaines actions proposées, dont BloodHound préparé mais non exécutable automatiquement en V2.

### Evidence NetExec

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

La V2 ne gère pas de credentials, ne lance pas BloodHound/SharpHound réel, ne lance pas de relay, ne télécharge rien et ne fait aucune exploitation. Elle se limite à une énumération SMB défensive, approuvée et journalisée.
