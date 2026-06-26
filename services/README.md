# services/ - Backend Microservices

Per `backend-data-spec.md`, the following services are planned:
- `gateway/` - API gateway (auth, rate limiting, routing)
- `player/` - Player accounts, progression, quests
- `world/` - World state, regions, map
- `vote/` - Voting cycles, candidates, vote submissions (**first slice - initialized**)
- `generation/` - AI content generation orchestration
- `review/` - Content review workflow
- `content/` - Content packages, release, rollback
- `ops/` - Operations dashboard and admin APIs
