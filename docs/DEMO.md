# OpenAD Zero Demo Guide

## Goal

This guide explains how to demonstrate OpenAD Zero safely in a local or controlled environment.

## Start the stack

```bash
cp .env.example .env
make up-build
make migrate
make smoke
```

## Demo flow

1. Open the UI.
2. Create a new mission with an internal lab scope.
3. Review scope validation.
4. Start Nmap discovery.
5. Open Jobs and observe queued/running/completed states.
6. Open Hosts and Services.
7. Open Actions and review approval-based actions.
8. Open Evidence.
9. Upload a harmless text file as evidence.
10. Generate a Markdown/HTML report.
11. Open Lab Operations.
12. Review progress score.
13. Open Timeline.
14. Open Capabilities.
15. Open Settings and System Health.

## Safety notes

- Only use internal lab ranges.
- Do not scan public IP ranges unless explicitly authorized.
- OpenAD Zero does not run exploitation workflows.
- BloodHound / SharpHound collection is manual and optional.
