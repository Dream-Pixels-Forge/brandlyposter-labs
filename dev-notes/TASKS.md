# TASKS.md — BrandlyPoster-Labs Task Breakdown

## Epic: MCP Server + Subject Vault + Vision QA (Phase 3, Sprint 1)

### Task 1: Scaffold MCP server package
- **Issue:** #1
- **Branch:** feature/1-mcp-server-scaffold
- **Status:** pending
- **Subagent:** yes
- **Files:** `server.py`, `requirements.txt`, `pyproject.toml`, `README.md`
- **Tests:** `tests/test_server_imports.py` — server imports, FastMCP instance created

### Task 2: Subject vault — save + match
- **Issue:** #2
- **Branch:** feature/2-subject-vault
- **Status:** pending
- **Subagent:** yes
- **Files:** `server.py` (subject tools), `subjects/` storage
- **Tests:** `tests/test_subject_vault.py` — save profile, match scoring, threshold

### Task 3: Vision QA — 6-point check
- **Issue:** #3
- **Branch:** feature/3-vision-qa
- **Status:** pending
- **Subagent:** yes
- **Files:** `server.py` (qa tools)
- **Tests:** `tests/test_vision_qa.py` — each of 6 checks, score computation, pass/fail

### Task 4: Earring symmetry check
- **Issue:** #4
- **Branch:** feature/4-earring-check
- **Status:** pending
- **Subagent:** yes
- **Files:** `server.py` (earring tool)
- **Tests:** `tests/test_earring_check.py` — symmetry pass/fail, offset delta

### Task 5: Export specs + batch export
- **Issue:** #5
- **Branch:** feature/5-export
- **Status:** pending
- **Subagent:** yes
- **Files:** `server.py` (export tools), `projects/` storage
- **Tests:** `tests/test_export.py` — spec correctness per format, manifest structure

### Task 6: Core poster creation tool
- **Issue:** #6
- **Branch:** feature/6-create-poster
- **Status:** pending
- **Subagent:** yes
- **Files:** `server.py` (create_poster)
- **Tests:** `tests/test_create_poster.py` — master_prompt generation, earring fix enforced

### Task 7: Text & layout tools
- **Issue:** #7
- **Branch:** feature/7-text-layout
- **Status:** pending
- **Subagent:** yes
- **Files:** `server.py` (text tools)
- **Tests:** `tests/test_text_tools.py` — title/subtitle/tagline/billing/layer output

### Task 8: Animation tools
- **Issue:** #8
- **Branch:** feature/8-animation
- **Status:** pending
- **Subagent:** yes
- **Files:** `server.py` (animation tools)
- **Tests:** `tests/test_animation.py` — keyframes, export specs

### Task 9: Client approval tools
- **Issue:** #9
- **Branch:** feature/9-client-approval
- **Status:** pending
- **Subagent:** yes
- **Files:** `server.py` (share/compare/approve tools)
- **Tests:** `tests/test_client_approval.py` — review URL, compare, approve lock

### Task 10: Integration + CLI smoke test
- **Issue:** #10
- **Branch:** feature/10-integration
- **Status:** pending
- **Subagent:** no
- **Files:** `server.py` full, `tests/test_integration.py`
- **Tests:** end-to-end: subject → poster → QA → export → approve

## Epic: 1440x900 Studio App (Phase 3, Sprint 2 — deferred)
- React + Vite + TanStack app exposing `window.BrandlyPosterAPI`
- MCP iframe postMessage + project JSON loading
- Deferred until MCP server is complete and tested

## Definition of Done (per task)
- [ ] Code written and committed on feature branch
- [ ] Tests pass (`pytest`)
- [ ] Type-checked (`mypy` or equivalent)
- [ ] PR opened and reviewed
- [ ] Squash-merged into master
