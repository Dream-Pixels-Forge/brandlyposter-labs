# BrandlyPoster-Labs — MCP-Controlled Poster Studio

Serious app version of L'ÉTOILE Studio, now controllable by any coding agent via MCP.

## Name
**BrandlyPoster-Labs** — Iconic movie posters featuring exact likeness, with systematic QA (earring symmetry fix).

## Architecture
Coding Agent (Claude/Cursor) -> MCP -> BrandlyPoster-Labs MCP Server -> Tools -> Image Generation -> 1440x900 Studio App

## MCP Tools Exposed

| Tool | What it does |
|------|--------------|
| brandly_list_genres | Lists 5 Hollywood presets |
| brandly_create_poster | Builds MASTER_PROMPT with earring fix enforced |
| brandly_fix_earrings | Standalone cast-sheet cleaner |
| brandly_export_specs | Returns print specs (27x40, 1440x900 deck, social) |

## How Coding Agent Controls It

### 1. Install
pip install mcp

### 2. Claude Desktop config
{
  "mcpServers": {
    "brandlyposter-labs": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}

### 3. Agent Workflow
User: "Make BADLAND poster romcom"
Agent:
1. brandly_list_genres -> gets romcom preset
2. brandly_create_poster(reference_image_path, genre=romcom, title=BADLAND, fix_earrings=true)
3. Gets master_prompt back
4. Calls image_gen with prompt + reference
5. Returns final poster + QA checklist

### Why MCP is Better
Before: Agent hallucinates prompt, forgets earring fix, crops feet
After: Server enforces preserve likeness, both gold hoops symmetrical, hero at 68% height, 2:3 ratio, genre palette locked

### Export Specs
- theatrical: 27x40 300dpi CMYK
- deck: 1440x900 sRGB (your requested studio display size)
- social: 2160x3240 2:3
- story: 1080x1920 9:16

### Integration with 1440x900 App
Web app exposes window.BrandlyPosterAPI = { createPoster, getPrompt, export }
MCP server can postMessage to iframe or write JSON to /mnt/data/brandlyposter-labs/projects/
