# BRAINSTORM-NEXT-LEVEL.md — BrandlyPoster-Labs Phase 2 Vision

## From "MCP tool prototype" → "Multi-agent poster studio"

Current state: one Python FastMCP server that builds text prompts + a 6-point QA checklist.
Next level: an agent-operable studio where multiple specialized agents collaborate end-to-end — subject vault, vision QA, batch/animated export, client approval — all still MCP-controllable so any coding agent can drive it.

## Problem being solved at next level
Today an agent generates one poster, trusts the QA checklist, and hopes the earrings are symmetrical. At scale you need:
- **Identity locking:** the same star across 3 genre variants must look like the same person
- **Real QA:** not a self-reported checklist but actual pixel-level checks (earring symmetry, face match, cropped feet, text legibility)
- **Batch export:** theatrical + deck + social + story from one approval
- **Client sign-off:** shareable review + version compare + approval, not "here's an image, trust me"

## Architecture vision (Phase 2)

### Agents (roles)
| Agent | Responsibility | MCP tools owned |
|-------|---------------|-----------------|
| **Subject Curator** | Ingest reference images, build subject vault, run likeness scoring | `brandly_subject_save`, `brandly_subject_match`, `brandly_earring_check` |
| **Poster Director** | Pick genre, compose master prompt, iterate on variants | `brandly_create_poster`, `brandly_set_*`, `brandly_animate_poster` |
| **QA Reviewer** | Run vision QA, gate export, reject/iterate | `brandly_qa_check` (vision-backed), `brandly_compare_versions` |
| **Export Specialist** | Render all formats, write project JSON, post to studio app iframe | `brandly_export_specs`, `brandly_batch_export`, `brandly_export_animation` |
| **Client Liaison** | Generate review links, version comparison, capture approval | `brandly_share_review`, `brandly_approve_version` |

### Data flow (next level)
1. **Subject in:** Agent uploads reference photo(s) → `brandly_subject_save` stores + embeds face/likeness signature in subject vault (`/mnt/data/brandlyposter-labs/subjects/<id>/`)
2. **Director:** picks genre + title → `brandly_create_poster(subject_id, genre, ...)` → master_prompt + variant plan
3. **Image gen (external):** agent renders poster + variants (Agnes/Midjourney/Flux/SD, provider-agnostic)
4. **QA Reviewer:** `brandly_qa_check` runs vision-backed checks — face match vs subject, earring symmetry pixel-check, no cropped feet/hands, 2:3 ratio, text legible. Score must be 6/6 **and** pass likeness threshold before export
5. **Export Specialist:** `brandly_batch_export` renders theatrical/deck/social/story + optional animated variant; writes project JSON + posts to 1440x900 studio app iframe via `window.BrandlyPosterAPI`
6. **Client Liaison:** `brandly_share_review` → review page with before/after + version compare → `brandly_approve_version` locks final

### Subject vault (identity locking)
- Each subject: `subject_id`, reference images, face embedding, likeness threshold, earring baseline (left/right gold hoop pixel coords)
- `brandly_subject_match(generated_image, subject_id)` → similarity score 0–1; blocks export below threshold
- `brandly_earring_check(image)` → pixel-level symmetry check on gold hoops; returns pass/fail + offset delta

### Vision QA (replaces self-reported checklist)
`brandly_qa_check` now actually inspects the generated image:
1. Likeness preserved — face match vs subject vault ≥ threshold
2. Both earrings symmetrical — pixel-check gold hoops, identical size/position
3. No cropped hands/feet — subject fully within 2:3 frame
4. Ratio 2:3 — canvas dimension check
5. Eyes sharp — focus/blur metric on eye region
6. Text legible — OCR-confirmed title/tagline at bottom
Score: 6/6 + likeness threshold required before export

### Batch & animated export
- `brandly_batch_export(subject_id, poster_id, formats=[theatrical,deck,social,story])` → one call, all specs + files
- `brandly_export_animation(animation_type=parallax|ken_burns|title_reveal|full_cinematic, duration=6s)` → mp4/gif/webm at 1080x1920 or 1440x900
- Outputs written to `/mnt/data/brandlyposter-labs/projects/<project_id>/` + project JSON manifest

### Client approval portal
- `brandly_share_review(project_id)` → shareable URL with poster + variants + QA scorecard
- `brandly_compare_versions(variant_a, variant_b)` → side-by-side with diff highlights
- `brandly_approve_version(project_id, version_id, client_signature)` → locks final, triggers export

## Framework selection (next level)
| Layer | Choice | Reason |
|-------|--------|--------|
| MCP server | Python + FastMCP | Already prototyped; `pip install mcp`; agent-native |
| Subject vault | Local JSON + face embeddings | No new infra; subject files under `/mnt/data/...` |
| Vision QA | Agnes/gpt-image-2 vision or local CLIP | Provider-agnostic; agent picks vision model |
| Studio app | React 19 + Vite 6 + TanStack (Router/Query/Form/Table) | AGENTS.md TanStack First; no Next.js |
| Styling | Tailwind CSS v4 | Per AGENTS.md standard |
| Image gen | Provider-agnostic (Agnes default) | MCP returns prompts; agent swaps provider |

## Open questions (next level)
- Default vision QA provider: Agnes vision vs local model vs gpt-image-2?
- Subject vault storage: local `/mnt/data` vs cloud (S3/R2) for multi-agent access?
- Client review portal: static HTML + JSON vs full Next.js auth app (avoid — keep simple HTML)?
- How many poster variants per subject before QA gates kick in?
- Version retention policy (how many rejected variants to keep)?

## Non-goals (next level)
- Multi-user auth / teams / billing (keep single-agent-operable)
- Real-time collaboration (MCP is request/response; fine)
- Native mobile app (studio app is web/iframe)
- Video beyond animated posters (6s mp4/gif max)

## Immediate next step
Convert the Phase 2 vision into `dev-notes/SPEC.md` + `dev-notes/TASKS.md`, then implement starting with: subject vault + vision QA (the highest-leverage next-level features).
