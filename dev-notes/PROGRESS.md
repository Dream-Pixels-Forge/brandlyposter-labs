# Pipeline Progress

## Current State
- **Project:** BrandlyPoster-Labs — MCP-Controlled Poster Studio
- **Started:** 2025-11-01
- **Current Phase:** 3 (Implementation)
- **Status:** MCP server complete; Studio app complete

## Phase Completion
- [x] Phase 0: Bootstrap (git init, dev-notes/, .gitignore)
- [x] Phase 1: Brainstorm (BRAINSTORM.md)
- [x] Phase 2: Governance (GOAL.md + DECISIONS.md)
- [x] Phase 2: Next-Level Brainstorm (BRAINSTORM-NEXT-LEVEL.md)
- [x] Phase 2: Spec + Tasks (SPEC.md + TASKS.md)
- [x] Phase 3: MCP Server + Subject Vault + Vision QA (Sprint 1) — **COMPLETE**
  - 30+ MCP tools implemented
  - Subject vault with CLIP face embeddings
  - Vision QA: 11-category detection with scan animation
  - Batch export + client approval workflow
  - 61 tests passing
- [x] Phase 3: 1440x900 Studio App (Sprint 2) — **COMPLETE**
  - React + Vite + TanStack Router/Query + TypeScript + Tailwind CSS v4
  - BrandlyPosterAPI: createPoster, getPrompt, export, loadProject, setReferenceImage, onPosterUpdate
  - PosterStudio: 1440x900 deck preview with create form, QA, export
  - ProjectsList: gallery with detail modal, QA scores, variants
  - SettingsPanel: MCP config, data paths, export formats, API docs
  - MCP iframe postMessage bidirectional communication

## Active Tasks
None - both sprints complete

## Blockers
None

## Decisions Made
- 2025-11-01: Python FastMCP for MCP server
- 2025-11-01: React + Vite + TanStack for studio app (AGENTS.md TanStack First)
- 2025-11-01: Next-level direction = multi-agent studio