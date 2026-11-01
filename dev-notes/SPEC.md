# SPEC.md — BrandlyPoster-Labs Architecture Specs (Phase 2)

## System Architecture

### Layers
1. **MCP Server (Python + FastMCP)** — `server.py` — exposes all `brandly_*` tools; builds master prompts, runs subject vault + vision QA, returns export specs
2. **Subject Vault** — local JSON + face embeddings under `/mnt/data/brandlyposter-labs/subjects/<subject_id>/` — identity locking across variants
3. **Vision QA** — provider-agnostic vision model (Agnes default) — pixel-level checks on generated images
4. **Image Generation (external)** — agent calls with master_prompt + reference; provider-agnostic (Agnes/Midjourney/Flux/SD)
5. **Studio App (React + Vite + TanStack)** — 1440x900 deck; `window.BrandlyPosterAPI`; MCP drives via iframe postMessage or project JSON
6. **Project Store** — `/mnt/data/brandlyposter-labs/projects/<project_id>/` — project JSON manifest + exported assets

### Data Flow
```
Subject In → Subject Vault (embed + store)
   ↓
Director picks genre → brandly_create_poster(subject_id, genre, ...) → master_prompt + variant plan
   ↓
External image gen renders poster + variants
   ↓
QA Reviewer → brandly_qa_check(image, subject_id) → 6/6 + likeness threshold → gate
   ↓
Export Specialist → brandly_batch_export(project_id, formats) → all specs + files + project JSON
   ↓
Client Liaison → brandly_share_review → compare → brandly_approve_version → locked final
```

## Module Specifications

### Module: subject_vault
- **Responsibility:** Store subject profiles, embed reference faces, track earring baseline
- **Interface:**
  - `brandly_subject_save(subject_id, reference_image_path, name, ...)` → subject profile JSON
  - `brandly_subject_match(generated_image, subject_id)` → similarity score 0–1
  - `brandly_earring_check(image)` → {pass: bool, offset_delta: px, left_ear: coords, right_ear: coords}
- **Dependencies:** vision model for face embedding; local filesystem
- **Tests:** unit tests for embedding extraction, match scoring, earring symmetry detection

### Module: mcp_server (server.py)
- **Responsibility:** Expose all `brandly_*` MCP tools; orchestrate subject vault + QA + export
- **Interface:** FastMCP tools listed in API Specifications below
- **Dependencies:** subject_vault, vision_qa, export_specs
- **Tests:** tool-level tests — each tool returns valid JSON, correct fields, error handling

### Module: vision_qa
- **Responsibility:** Run 6-point QA on generated images using vision model
- **Interface:** `brandly_qa_check(image_path, subject_id)` → {score: "6/6", checks: {...}, pass: bool}
- **Dependencies:** vision model provider (Agnes default, agent-swappable)
- **Tests:** mock vision model; test each of 6 checks independently

### Module: export_specs
- **Responsibility:** Return print/digital specs per format; batch export orchestration
- **Interface:** `brandly_export_specs(format)` → specs; `brandly_batch_export(project_id, formats)` → manifest
- **Dependencies:** none (pure config + file writing)
- **Tests:** spec correctness per format; manifest structure validation

## API Specifications (MCP Tools)

### Genre & presets
- `brandly_list_genres()` → {genres: {...}}
- `brandly_list_fonts()` → {fonts: {...}}

### Subject vault
- `brandly_subject_save(subject_id, reference_image_path, name, story, outfit, ...)` → {subject_id, profile, embedding_stored: bool}
- `brandly_subject_match(generated_image, subject_id)` → {subject_id, similarity: 0-1, pass: bool, threshold}
- `brandly_earring_check(image_path)` → {pass: bool, offset_delta_px, symmetrical: bool}

### Poster creation
- `brandly_create_poster(subject_id, genre, title, subtitle, tagline, story, outfit, fix_earrings=true, resolution="2:3")` → {master_prompt, genre_config, qa_checklist, subject_id, variant_plan}

### Text & layout
- `brandly_set_title(...)`, `brandly_set_subtitle(...)`, `brandly_set_tagline(...)`, `brandly_set_billing_block(...)`, `brandly_add_text_layer(...)`
- `brandly_align_text(...)`, `brandly_place_element(...)`, `brandly_distribute_layers(...)`, `brandly_set_grid(...)`, `brandly_set_hero_placement(...)`

### Style & composition
- `brandly_set_background(...)`, `brandly_set_lighting(...)`, `brandly_set_color_palette(...)`

### Animation
- `brandly_animate_poster(animation_type, duration, fps, loop)` → {animation_type, keyframes}
- `brandly_set_animation_keyframes(layer_id, keyframes)`
- `brandly_export_animation(format, resolution, fps, duration, codec)` → {file, specs}

### QA & export
- `brandly_qa_check(image_path, subject_id)` → {score: "6/6", checks: {6 checks}, pass: bool}
- `brandly_export_specs(format)` → specs
- `brandly_batch_export(project_id, formats)` → {manifest, files: [...]}
- `brandly_share_review(project_id)` → {review_url, version_id}
- `brandly_compare_versions(variant_a, variant_b)` → {side_by_side, diff_highlights}
- `brandly_approve_version(project_id, version_id, client_signature)` → {locked: bool, final_version}

## Database Schema (local JSON)

### subjects/<subject_id>/profile.json
```json
{
  "subject_id": "string",
  "name": "string",
  "reference_images": ["path"],
  "face_embedding": [float],
  "likeness_threshold": 0.85,
  "earring_baseline": {"left_ear": [x,y], "right_ear": [x,y], "gold_hoop": true},
  "story": "string",
  "outfit": "string",
  "created_at": "iso"
}
```

### projects/<project_id>/manifest.json
```json
{
  "project_id": "string",
  "subject_id": "string",
  "poster_id": "string",
  "genre": "string",
  "master_prompt": "string",
  "qa_score": "6/6",
  "qa_passed": true,
  "variants": [{"format": "...", "file": "...", "specs": {...}}],
  "approved": false,
  "created_at": "iso"
}
```

## Non-Goals
- Multi-user auth / teams / billing
- Real-time collaboration
- Native mobile app
- Video beyond animated posters (6s mp4/gif max)
