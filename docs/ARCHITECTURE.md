# Architecture (youtube_mcp)

This document describes the architecture of **youtube_mcp** at a high level.
It is designed for long-term maintainability and onboarding.

---

## 1) Overview

`youtube_mcp` is a Model Context Protocol (MCP) server that exposes YouTube tooling as **tools/actions** for AI agents.

Core goals:
- **Reliability**: bounded execution + clear errors.
- **Security**: strict endpoint allowlist; no API key leakage.
- **AI usability**: self-describing tools (rich docstrings) + structured JSON outputs.

---

## 2) Layers

### A) MCP layer (tool discovery + schemas)
- **`src/youtube_mcp/server.py`**
  - Creates the FastMCP server instance
  - Registers tools with `add_tool(..., description=fn.__doc__)`

- **`src/youtube_mcp/server_tools.py`**
  - Public wrappers with long docstrings (the contract an AI reads)

### B) Tool handler layer (env + budgets + domain calls)
Files named `mcp_tools_*.py`:
- read `YOUTUBE_API_KEY`
- apply pagination aliases (`page_token` vs `next_page_token`)
- create API client
- call domain functions
- return structured JSON

### C) Domain layer (pure-ish logic)
Examples:
- `channel_resolver.py`, `channel_inventory.py`, `playlist_videos.py`
- `channel_search.py` (Search API)
- `video_comments.py` (commentThreads)

Goal:
- keep domain testable with fake clients (no network)

### D) Infrastructure layer (HTTP client)
- `youtube_data_api_client.py`
  - fixed host/scheme/base path
  - endpoint allowlist
  - retries/backoff
  - gzip support

---

## 3) Pagination design

YouTube APIs return pages via `nextPageToken`.

To make LLM agents more successful, we expose **aliases**:
- output: `nextPageToken` and `next_page_token`
- input: `page_token` and `next_page_token`

This is a practical interoperability choice.

---

## 4) Quota model

Official reference:
- https://developers.google.com/youtube/v3/determine_quota_cost

Key note:
- `search.list` is expensive (100 units per page)

The project uses a **budget + estimator** approach (`quota_budgeter.py`) to avoid runaway calls.

---

## 5) Security posture

- Endpoint allowlist prevents SSRF-style abuse via user parameters.
- API key is never logged.
- Only public-data endpoints are used (API-key auth; no OAuth flows).

---

## 6) Extending the project

Common extension patterns:
- Add a domain module (pure logic)
- Add `mcp_tools_*.py` handler (env + budgeting)
- Add wrapper in `server_tools.py` (docstring matters)
- Register it in `server.py`
- Add unit tests using a fake client

