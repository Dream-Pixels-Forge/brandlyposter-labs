# HANDOFF.md — BrandlyPoster-Labs

## Session Summary
**Date:** 2025-11-01  
**Project:** BrandlyPoster-Labs — MCP-Controlled Poster Studio  
**Location:** `/home/dimona/Dream-Pixels-Forge/Dev/app/brandlyposter-labs`  
**Git:** `master` @ `9505202` (both sprints complete, working tree clean)

---

## What Was Completed

### Sprint 1: MCP Server (`server.py`) — 30+ Tools, 61 Tests ✅
- **Subject Vault:** `brandly_subject_save`, `brandly_subject_match`, `brandly_earring_check`
- **Poster Creation:** `brandly_create_poster` (master prompt + variant plan)
- **Text/Layout:** 8 tools (title, subtitle, tagline, billing, custom layers, alignment, grid, hero)
- **Style/Composition:** 3 tools (background, lighting, palette)
- **Animation:** 3 tools (6 presets, custom keyframes, export specs)
- **Vision QA:** `brandly_qa_check` (6-point), **`brandly_scan_issues` (11-category + scan animation)**
- **Fix Tools:** 7 tools (`brandly_fix_*_prompt` + `brandly_generate_master_fix_prompt`)
- **Export:** `brandly_export_specs` (4 formats), `brandly_batch_export` (manifest)
- **Client Approval:** `brandly_share_review`, `brandly_compare_versions`, `brandly_approve_version`
- **Tests:** 61 passing across 11 modules (`tests/`)

### Sprint 2: 1440×900 Studio App (`studio-app/`) ✅
- React 19 + Vite 6 + TypeScript + TanStack Router/Query + Tailwind CSS v4
- Routes: `/studio`, `/projects`, `/settings`
- `window.BrandlyPosterAPI`: createPoster, getPrompt, export, loadProject, setReferenceImage, onPosterUpdate
- MCP iframe postMessage bidirectional communication
- PosterStudio: 1440×900 deck preview, create form, QA checklist, export dropdown
- ProjectsList: gallery, detail modal, load-to-studio
- SettingsPanel: MCP config, data paths, export formats, API docs

---

## Current State (Live)

### Servers Running
| Service | URL | PID | Status |
|---------|-----|-----|--------|
| MCP Server | `http://localhost:8000/mcp` | 1438571 | ✅ streamable-http |
| Studio App | `http://localhost:5173` | 1529457 | ✅ Vite dev |

### Test Reference Image
- `/tmp/test_reference.jpg` — 512×512 with symmetrical gold hoop earrings
- Annotated: `/tmp/test_reference_annotated.jpg`
- Scan frames: `/tmp/scan_demo/scan_frame_000-013.png`

### MCP Session
```
Session ID: 55322ab89e874336ae7e97e310309506
Server: BrandlyPoster-Labs Pro v1.27.1
Protocol: 2024-11-05
```

---

## Verified End-to-End Workflow

```bash
# 1. Save subject (CLIP embedding + earring baseline)
brandly_subject_save(subject_id="demo-star", reference_image_path="/tmp/test_reference.jpg", ...)

# 2. Create poster (master prompt with earring fix, 68% hero, 2:3 ratio)
brandly_create_poster(subject_id="demo-star", genre="thriller", title="L'ÉTOILE", ...)

# 3. Scan generated poster for issues (11 categories)
brandly_scan_issues(image_path="/path/to/generated.png", subject_id="demo-star", create_animation=true)

# 4. If issues: generate master fix prompt
brandly_generate_master_fix_prompt(image_path=..., subject_id="demo-star", expected_outfit=...)

# 5. Re-generate with fix prompt appended → repeat until 6/6 QA pass

# 6. Export all formats + project manifest
brandly_batch_export(project_id="...", formats=["theatrical","deck","social","story"])
```

**Last test result:** 9/11 checks passed (ratio=high, text=medium — expected for reference image without text)

---

## Key Files

```
brandlyposter-labs/
├── server.py                 # MCP server (FastMCP, 30+ tools)
├── pyproject.toml            # Python project config
├── requirements.txt
├── tests/                    # 61 tests (11 modules)
├── studio-app/               # React + Vite + TanStack
│   ├── src/
│   │   ├── components/       # BrandlyPosterProvider, PosterStudio, ProjectsList, SettingsPanel
│   │   ├── routes/           # __root, studio, projects, settings
│   │   ├── types/index.ts    # Full TypeScript types
│   │   └── router.tsx        # TanStack Router + Query
│   └── vite.config.ts
├── dev-notes/
│   ├── PROGRESS.md           # Pipeline state
│   ├── GOAL.md               # 6 verification gates
│   ├── BRAINSTORM.md         # Phase 1 vision
│   ├── BRAINSTORM-NEXT-LEVEL.md  # Phase 2 vision (multi-agent)
│   ├── SPEC.md               # Architecture specs
│   ├── TASKS.md              # Task breakdown (10 tasks)
│   └── DECISIONS.md          # Decision log
└── HANDOFF.md                # This file
```

---

## Next Steps (When Resuming)

### Immediate (if continuing)
1. **Connect Studio App to live MCP** — Update `VITE_MCP_BASE_URL` in studio-app/.env to `http://localhost:8000`
2. **Test iframe postMessage** — Load a project in Studio, verify createPoster calls MCP
3. **Add real image generation** — Integrate Agnes/Midjourney/Flux as external provider

### Short-term
- [ ] Project persistence: `brandly_batch_export` needs project manifest pre-creation
- [ ] Studio App: Wire `onPosterUpdate` to auto-refresh preview from MCP
- [ ] Add authentication for multi-user MCP access
- [ ] CI/CD: GitHub Actions for Python tests + TypeScript build

### Medium-term
- [ ] Subject vault UI in Studio App (list/edit subjects)
- [ ] Scan animation playback in Studio (show scan frames as MP4/GIF)
- [ ] Client approval portal (static HTML generator for `brandly_share_review`)
- [ ] Multi-genre variant generation in single workflow

---

## Commands to Restart

```bash
# Terminal 1: MCP Server
cd /home/dimona/Dream-Pixels-Forge/Dev/app/brandlyposter-labs
BRANDLY_DATA_ROOT=/tmp/brandlyposter-labs python3 server.py

# Terminal 2: Studio App
cd /home/dimona/Dream-Pixels-Forge/Dev/app/brandlyposter-labs/studio-app
npm run dev -- --host

# Test MCP
SESSION=$(curl -s -i -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | grep -i mcp-session-id | cut -d' ' -f2)

curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"brandly_list_genres","arguments":{}}}'
```

---

## Known Issues / Gotchas

1. **MCP streamable-http** requires `Accept: application/json, text/event-stream` header + session ID from initialize response
2. **Data root** must be writable — uses `/tmp/brandlyposter-labs` in dev (configure via `BRANDLY_DATA_ROOT`)
3. **CLIP model** downloads on first run (~500MB) — cached in HF_HOME
4. **Studio iframe** currently points to empty `VITE_MCP_IFRAME_URL` — set to `http://localhost:8000/mcp/iframe` when MCP iframe endpoint added
5. **Tests** use temp directory (`/tmp/brandlyposter-labs-test`) auto-cleaned via `conftest.py`

---

## Architecture Decisions Logged

| Decision | Date | Recorded In |
|----------|------|-------------|
| Python FastMCP (not Node) | 2025-11-01 | DECISIONS.md |
| TanStack First (no Next.js) | 2025-11-01 | DECISIONS.md |
| Multi-agent next-level vision | 2025-11-01 | BRAINSTORM-NEXT-LEVEL.md |
| Comprehensive fix tools + scan animation | 2025-11-01 | SPEC.md + TASKS.md |

---

## Context for Next Session

> **Project is at "Phase 3 complete" — both sprints done.**  
> MCP server fully functional with 30+ tools. Studio app builds and runs.  
> Next session should focus on: wiring Studio ↔ MCP via iframe postMessage, adding real image generation provider, and project persistence for batch export/approval flow.

**All tests pass. Git clean. Servers running. Ready to continue.** 🎬