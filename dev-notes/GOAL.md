# GOAL.md — BrandlyPoster-Labs

## Project Vision
An MCP-controlled poster studio that lets any coding agent generate iconic movie posters with exact likeness, systematic QA (earring symmetry fix), and print/social export specs — controllable end-to-end via MCP tools from Claude/Cursor/any agent.

## Verification Gates
- [ ] Gate 1: MCP server exposes all core tools (list_genres, create_poster, fix_earrings, export_specs, qa_check) and returns valid JSON
- [ ] Gate 2: `brandly_create_poster` enforces both gold hoop earrings symmetrical + hero at 68% height + 2:3 ratio + genre palette locked
- [ ] Gate 3: `brandly_qa_check` returns 6/6 score (likeness, earrings, hands, ratio, eyes, text legibility)
- [ ] Gate 4: `brandly_export_specs` returns correct specs for theatrical/deck/social/animated formats
- [ ] Gate 5: 1440x900 studio app exposes `window.BrandlyPosterAPI` (createPoster, getPrompt, export)
- [ ] Gate 6: MCP server can postMessage to iframe or write project JSON to /mnt/data/brandlyposter-labs/projects/

## Acceptance Criteria
### Feature: MCP poster creation tools
- [ ] brandly_list_genres returns 5+ Hollywood genre presets with palette/backgrounds/lighting
- [ ] brandly_create_poster builds a MASTER_PROMPT with earring fix enforced when fix_earrings=true
- [ ] brandly_fix_earrings is a standalone cast-sheet cleaner
- [ ] brandly_export_specs returns print specs per format

### Feature: QA gate
- [ ] brandly_qa_check validates likeness preserved, both earrings symmetrical, no cropped hands, 2:3 ratio, sharp eyes, legible text

### Feature: 1440x900 studio app
- [ ] App renders at 1440x900 sRGB deck size
- [ ] window.BrandlyPosterAPI exposes createPoster, getPrompt, export
- [ ] MCP can drive the app via iframe postMessage or JSON project files

## Non-Goals
- Image generation itself (MCP returns prompts; agent calls external image gen)
- Video/animation export beyond animated poster specs
- User auth / multi-tenancy
- Payment or billing
