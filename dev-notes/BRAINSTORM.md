# BRAINSTORM.md — BrandlyPoster-Labs Idea + Architecture Vision

## Problem Statement
Before: coding agents hallucinate poster prompts, forget the earring symmetry fix, crop feet, and ignore genre palettes — producing off-brand, low-QA posters. There is no systematic, agent-controllable poster studio that enforces quality control.

## Proposed Solution
BrandlyPoster-Labs: an MCP server that any coding agent controls, enforcing preserve-likeness, symmetrical gold hoop earrings, hero at 68% height, 2:3 ratio, and genre-locked palettes. Returns a MASTER_PROMPT the agent feeds to an image generator, plus a 6-point QA checklist and print/social export specs.

## Architecture Vision
### Components
- **MCP Server (Python/FastMCP):** `server.py` — exposes brandly_* tools; builds master prompts, runs QA, returns export specs
- **Image Generation (external):** Agent calls image gen with master_prompt + reference image (provider-agnostic: Agnes/Midjourney/Flux/SD)
- **1440x900 Studio App (React + Vite + TanStack):** Web app exposing `window.BrandlyPosterAPI`; MCP can postMessage to iframe or write JSON to /mnt/data/brandlyposter-labs/projects/
- **QA Layer:** brandly_qa_check — 6/6 score gate before export

### Data Flow
1. Agent calls `brandly_list_genres` → picks genre preset
2. Agent calls `brandly_create_poster(reference_image_path, genre, title, ...)` → gets `master_prompt` + `qa` checklist
3. Agent calls external image gen with prompt + reference → gets poster image
4. Agent calls `brandly_qa_check` → 6/6 required before export
5. Agent calls `brandly_export_specs(format)` → theatrical/deck/social/animated specs
6. (Optional) Studio app renders the poster at 1440x900 deck size via BrandlyPosterAPI

### Agent Roles (if multi-agent)
- **Poster Director:** calls MCP tools, assembles master prompt, picks genre
- **QA Reviewer:** runs brandly_qa_check, gates export
- **Export Specialist:** applies export specs, writes project JSON / posts to iframe

## Framework Selection
- **MCP server:** Python + FastMCP (matches existing Server.py prototype, `pip install mcp`)
- **Studio app:** React 19 + Vite 6 + TanStack Router/Query/Form/Table (per AGENTS.md TanStack First; no Next.js)
- **Styling:** Tailwind CSS v4
- **Image gen provider:** provider-agnostic (Agnes default per brandly pipeline; agent swaps in)

## Open Questions
- Which image generation provider is default (Agnes vs Midjourney vs Flux)?
- Where does the studio app live (localhost iframe vs deployed)?
- How are reference images stored/referenced (paths vs URLs)?
- Does the MCP server need auth for multi-user studio access?
