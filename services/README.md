# services/ - Backend Microservices

> Document Status: active
> Applicable Stage: current
> Maintenance: keep in sync with `docs/20-specs/` and `docs/30-api/`

This directory is the backend service entry point for the monorepo. It summarizes which services exist, what each service owns, and where to find the authoritative specs and API references.

## Current Positioning

- `services/` is no longer a placeholder for future work. The repository already contains the planned backend service directories and their local README files.
- This README is an index, not the source of truth for contracts or state machines.
- Product, data, and engineering constraints remain authoritative in `docs/20-specs/`.
- API scopes, endpoint catalogs, and error-code references remain authoritative in `docs/30-api/`.

## Service Overview

- `gateway/` - Unified API gateway, authentication, rate limiting, tracing, and service routing
- `player/` - Player accounts, progression, quests, and unlocked region state
- `world/` - Regions, world skeleton snapshots, and world state queries
- `vote/` - Vote cycles, candidates, submissions, tally, and vote history
- `generation/` - AI generation requests, generated objects, and generation state transitions
- `review/` - Structured review workflow, risk decisions, and approval actions
- `content/` - Content packages, gray release, live release, rollback, and version archiving
- `ops/` - Operations dashboard, action history, and aggregated system status

## How To Read

1. Start with `docs/20-specs/backend-data-spec.md` for service boundaries, data rules, states, async tasks, and events.
2. Then read `docs/30-api/api-overview.md`, `docs/30-api/api-permissions.md`, and `docs/30-api/api-error-codes.md`.
3. Open the service-specific README under `services/<service>/README.md` for local startup, structure, and implementation notes.

## Governance Notes

- Keep this file aligned with root `README.md`, `docs/00-governance/project-status.md`, and `.trae/rules/52-documentation.md`.
- When a service is added, removed, or substantially renamed, update this file and the related specs in the same change.
- Service-level READMEs should link back to the relevant spec and API documents instead of duplicating full contracts.

## Related Docs

- `README.md` - Repository root entry
- `docs/README.md` - Documentation system entry
- `docs/00-governance/project-status.md` - Current project stage and risks
- `docs/20-specs/backend-data-spec.md` - Backend boundaries, data rules, and async/event contracts
- `docs/30-api/api-overview.md` - API catalog and service-facing interface map
- `.trae/rules/52-documentation.md` - Documentation synchronization rules
