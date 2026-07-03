# V2 Brand Identity

## Product name

The V2 product identity is **AD Mission Control**.

The repository remains **OpenAD-Zero**. Technical documentation can continue to refer to OpenAD-Zero when discussing the codebase, Docker stack, backend services, and safety model.

## Positioning

AD Mission Control is the V2 interface for persistent Active Directory audit operations. It presents scan lifecycle telemetry, persisted progress, realtime hints, and evidence-oriented operational state without turning the browser into a command launcher.

## Tagline

**Persistent Active Directory audit operations**

Short tagline: **Persistent AD audit ops**

## Short description

A safe-by-default mission control surface for persisted Active Directory audit workflows where PostgreSQL is the source of truth, Redis/RQ is asynchronous plumbing, and WebSocket updates are convenience hints.

## Logo concept

The local SVG logo combines the letters **AD** with a thin orbital radar path and a metallic orange orbital point. The orbital point represents an active scan signal. The logo is implemented as inline React SVG and does not use binary files, external images, or downloaded assets.

## Palette

| Token | Value |
| --- | --- |
| `--v2-bg` | `#FAF9F5` |
| `--v2-surface` | `#FFFFFF` |
| `--v2-text` | `#141413` |
| `--v2-text-muted` | `#6F6B63` |
| `--v2-border` | `#E8E6DC` |
| `--v2-gray` | `#B1ADA1` |
| `--v2-orange` | `#C15F3C` |
| `--v2-orange-light` | `#F28A4B` |
| `--v2-orange-dark` | `#8E3E26` |

## Components created

- `frontend/src/lib/v2Brand.ts` centralizes the V2 name, repository name, taglines, and domain candidates.
- `frontend/src/components/v2/V2Logo.tsx` provides the inline SVG logo with optional product text.
- `frontend/src/pages/V2BrandPage.tsx` documents the identity inside the application.
- `frontend/src/styles/v2-theme.css` provides scoped V2 tokens and reusable classes.

## Frontend routes

- `/v2-dashboard` — read-only AD Mission Control dashboard.
- `/scans` — persisted Scan Library with demo progress support.
- `/v2-brand` — brand/about page for the V2 identity.

## UX safety rules

- PostgreSQL is the source of truth.
- Redis/RQ remains asynchronous execution plumbing.
- WebSocket updates are realtime convenience hints only.
- The V2 dashboard is read-only.
- The frontend never sends raw commands.
- Demo progress remains a simulation-only worker.
- Human-approved operations stay explicit and policy-gated.
- Evidence-first workflows are preferred over browser-side execution controls.

## Domain candidates to verify

These are candidates to verify later; this document does not claim that any domain is available.

- `admissioncontrol.io`
- `admissioncontrol.dev`
- `admissioncontrol.app`
- `ad-control.io`
- `ad-orbit.io`

## Not done

- No domain reservation.
- No registrar availability check.
- No binary logo.
- No external logo asset.
- No NetExec catalog.
- No offensive automation.
- No frontend raw command capability.
