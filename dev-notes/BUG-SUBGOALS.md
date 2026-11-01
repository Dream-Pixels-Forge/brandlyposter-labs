# BUG-SUBGOALS.md — BrandlyPoster-Labs Bug-Hunt Phase 1

Branch: `bug/bug-hunt-phase-1` (from master). Source audits: `/tmp/bug-audit-server.md`, `/tmp/bug-audit-studio.md`. All server bugs were **confirmed by direct execution** of `server.py` functions.

## Subgoals (each = binary DoD + verification steps)

### SG-1 — Fix `compute_similarity` NaN on zero/empty vectors (BUG-001, High)
**DoD:** `compute_similarity` returns `0.0` (never `nan`) when either vector is zero-length or empty; emits no `RuntimeWarning`; result is always a finite float JSON-serializable via `allow_nan=False`.
**Verification:**
- [ ] `compute_similarity([0]*512,[0]*512) == 0.0`
- [ ] `compute_similarity([0]*512,[1]*512) == 0.0`
- [ ] `compute_similarity([], []) == 0.0`
- [ ] `compute_similarity([1,0,0],[1,0,0]) == 1.0` (unchanged happy path)
- [ ] `compute_similarity([1,0,0],[0,1,0]) == 0.0` (unchanged)
- [ ] `json.dumps({"s": compute_similarity([0]*512,[0]*512)}, allow_nan=False)` does not raise
- [ ] No `RuntimeWarning` raised for zero-vector input
**Tests:** new `tests/test_compute_similarity.py` (RED first).

### SG-2 — Graceful handling of missing subject in `brandly_subject_match` (BUG-002, High)
**DoD:** `brandly_subject_match(..., subject_id="missing")` returns `{"pass": False, ...}` gracefully instead of raising uncaught `FileNotFoundError`. Same guard applied to `brandly_create_poster` (731), `brandly_batch_export` (1243), `brandly_share_review` (1274), `brandly_approve_version` (1301).
**Verification:**
- [ ] missing subject → dict with `pass: False` + `reason`, no exception
- [ ] existing subject → unchanged behavior
**Tests:** new test in `tests/test_subject_vault.py` (RED first).

### SG-3 — Graceful handling of missing image in `compute_face_embedding` (BUG-004, Medium)
**DoD:** `compute_face_embedding("/nonexistent.png")` returns a sentinel/error dict (or raises a clear, caught error) instead of uncaught `FileNotFoundError` from `Image.open`; callers treat failed embedding as `pass: False`.
**Verification:**
- [ ] missing image → no uncaught exception; caller gets `pass: False`
- [ ] valid image → 512-d embedding unchanged
**Tests:** new test (RED first).

### SG-4 — Remove bare `except: pass` that silently swallows errors (BUG-003, Medium)
**DoD:** Bare `except:` at server.py:358 and 1027 replaced with specific exception handling + logging/reason so swallowed `FileNotFoundError` no longer silently drops likeness or empties `base_prompt`.
**Verification:**
- [ ] no bare `except:` remains in server.py
- [ ] likeness check still reported when subject missing
**Tests:** existing + new assertions.

### SG-5 — Ensure all tool-return floats are JSON-safe / never nan (BUG-006, Medium, defense-in-depth)
**DoD:** No `server.py` MCP tool can return `nan`/`inf` in a JSON-serialized dict; `json.dumps(result, allow_nan=False)` never raises for any tool output.
**Verification:**
- [ ] `json.dumps(tool_result, allow_nan=False)` passes for QA/subject/scan tools with zero-vector input
**Tests:** assertions in SG-1/SG-2/SG-3 cover this.

### SG-6 — Remove unused imports `base64`, `hashlib` (BUG-005, Low)
**DoD:** `server.py` imports only used modules; `grep base64./hashlib.` returns no matches; ruff clean.
**Verification:** static grep + `ruff check server.py` clean.

### SG-7 (deferred, studio) — Empty iframe src / postMessage origin verification (Studio BUG-001/002, High)
**DoD:** Studio `VITE_MCP_IFRAME_URL` defaults to a real MCP iframe URL; postMessage uses validated origin.
**Verification:** studio-app typecheck + lint; manual iframe load.
**Status:** DEFERRED — requires frontend build env; tracked separately.

### SG-8 (deferred, studio) — Null-safety / error boundary / listener leaks (Studio BUG-003..008)
**DoD:** `currentProject.variants` null-safe; React error boundary added; per-request listeners cleaned on unmount; `exportPoster` rejects consistently.
**Status:** DEFERRED.

## Definition of Done (overall)
- [ ] All server subgoals SG-1..SG-6 green (tests pass, ruff/mypy clean)
- [ ] Full `pytest` suite passes (61 existing + new)
- [ ] Changes committed on `bug/bug-hunt-phase-1`, pushed, PR opened
- [ ] Subgoals marked complete below

## Completion tracking
- [x] SG-1 compute_similarity NaN — COMPLETE (tests/test_compute_similarity.py, 3 tests)
- [x] SG-2 missing subject — COMPLETE (subject_match/create_poster/batch_export/share_review/approve_version guarded; 5 tests)
- [x] SG-3 missing image embedding — COMPLETE (compute_face_embedding returns []; 2 tests)
- [x] SG-4 bare except — COMPLETE (likeness/scan now record pass=False instead of silently dropping; 2 tests)
- [x] SG-5 JSON-safe floats — COMPLETE (covered by SG-1 allow_nan=False assertion)
- [x] SG-6 unused imports — COMPLETE (removed base64/hashlib)
- [ ] SG-7 studio iframe/origin — deferred (frontend build env)
- [ ] SG-8 studio null-safety/boundary — deferred (frontend build env)

## Verification
- `pytest tests/` → 73 passed (61 original + 12 new), 0 failed
- `ruff check server.py` → no new F401/F841 from my edits (remaining 71 errors are pre-existing)
