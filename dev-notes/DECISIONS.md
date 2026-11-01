# DECISIONS.md — Decision Log

## 2025-11-01: Bootstrap project structure
- **Decision:** git init + dev-notes/ + .gitignore; Python FastMCP server + React/Vite/TanStack studio app
- **Rationale:** Matches AGENTS.md mandatory rules (git-driven, TanStack First) and existing Server.py prototype
- **Alternatives considered:** npm/Next.js stack (rejected — AGENTS.md forbids new Next.js projects)
- **Impact:** Sets up governance artifacts; implementation still pending
- **Decided by:** pipeline-orchestrator (ponytail mode)

## 2025-11-01: Scope limited to goals + brainstorming
- **Decision:** Only bootstrap governance (GOAL.md, BRAINSTORM.md, PROGRESS.md, DECISIONS.md); defer CI/CD, SECURITY.md, SPEC.md, DESIGN.md
- **Rationale:** User asked to "set the goals, brainstorm, etc" — no implementation requested yet; avoids "for later" boilerplate per ponytail
- **Alternatives considered:** Full project-init with all governance artifacts (rejected — over-engineering for current ask)
- **Impact:** Implementation phase (Phase 3) remains to be done when user requests it
- **Decided by:** pipeline-orchestrator (ponytail mode)

## 2025-11-01: Next-level direction (Phase 2 vision)
- **Decision:** Expand beyond single MCP tool prototype into multi-agent poster studio: subject vault (identity locking), vision-backed QA (pixel-level earring symmetry + face match), batch + animated export, client approval portal
- **Rationale:** "Push to next level" — a one-poster text-prompt tool is a toy; a studio with QA gates and client sign-off is a product
- **Alternatives considered:** Just build the MCP server as-is (rejected — too thin; no real QA, no identity locking, no client workflow)
- **Impact:** Raises implementation scope; next concrete deliverable is SPEC.md + TASKS.md then subject vault + vision QA first
- **Decided by:** pipeline-orchestrator (ponytail mode)
