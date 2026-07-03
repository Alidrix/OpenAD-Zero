# V2 Frontend Design System Foundation

## Objective

This document records the first small V2 design-system base for OpenAD-Zero. It is intentionally scoped to V2 scan pages only and does not replace the existing V1 Tailwind theme.

## Routes

- `/scans`: persisted V2 Scan Library with HTTP resynchronization and scan detail WebSocket hints.
- `/v2-dashboard`: read-only Mission Control dashboard for persisted scan counters and active progress.

## Safety model

- `Run demo progress` is a demo-only action that calls `POST /api/v2/scans/{scan_id}/enqueue-demo`.
- The frontend sends an empty JSON body for demo enqueue.
- The frontend never sends a raw command, target, offensive module, credential action, password spraying option, or dump option through this V2 demo flow.
- PostgreSQL remains the source of truth.
- Redis/RQ remains asynchronous execution plumbing.
- WebSocket messages are realtime hints only.
- HTTP resynchronization is mandatory after page reloads and during active scan polling.
- `/v2-dashboard` is read-only and does not enqueue, stop, delete, rename, or create scans.

## Token file

The V2 tokens live in:

```text
frontend/src/styles/v2-theme.css
```

## Tokens

```css
:root {
  --v2-bg: #FAF9F5;
  --v2-surface: #FFFFFF;
  --v2-text: #141413;
  --v2-text-muted: #6F6B63;
  --v2-border: #E8E6DC;
  --v2-gray: #B1ADA1;
  --v2-orange: #C15F3C;
  --v2-orange-light: #F28A4B;
  --v2-orange-dark: #8E3E26;
}
```

## Reusable classes

- `.v2-shell`: scoped off-white V2 page shell.
- `.v2-card`: white card surface with the V2 border and a light shadow.
- `.v2-orbit-dot`: small retro-spatial status dot.
- `.v2-counter`: dashboard counter typography.
- `.v2-progress`: neutral progress track.
- `.v2-progress-bar`: orange gradient progress fill.
- `.v2-safety-banner`: dark safety reminder panel.

## Current usage

The dashboard imports the token file directly and uses the reusable classes for Mission Control. The Scan Library imports the same token file so future V2-specific refinements can stay scoped to V2 pages.

## Next steps

- Add visual regression coverage when the frontend test stack is expanded.
- Consolidate repeated V2 primitives into shared React components if additional V2 pages adopt the same look.
- Keep the V2 design system isolated from V1 until the final branding decision is made.
