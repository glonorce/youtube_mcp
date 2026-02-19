# Developer Guide — youtube_mcp

This is the **single source of truth** for maintainers.

Goal: a new contributor (or another AI) should be able to understand the system
*without reading every file*.

---

## 0) Project identity

- GitHub repo: `glonorce/youtube_mcp`
- PyPI distribution name: `glonorce-youtube-mcp`
- Python import/package name: `youtube_mcp`
- Server entrypoint:
  - `python -m youtube_mcp.server`
  - installed CLI: `youtube_mcp`

---

## 1) What this project does

`youtube_mcp` is a **Model Context Protocol (MCP)** server that exposes tools (actions)
for YouTube **data extraction** and **inventory listing**.

It is designed to be:
- **AI-friendly**: rich docstrings are sent to MCP hosts for tool discovery.
- **Safe-by-default**: bounded execution + strict URL/endpoint allowlists.
- **Deterministic**: consistent structured JSON outputs for most tools.

---

## 2) End-user mental model

A typical AI workflow looks like:

1) User pastes a YouTube URL or channel handle.
2) AI chooses the correct tool:
   - For a single video: `get_yt_video_info`
   - For channel resolution: `resolve_youtube_channel`
   - For inventory pagination: `list_youtube_channel_videos` / playlists / playlist videos
   - For keyword search inside a channel: `search_youtube_channel_videos` (expensive)
   - For comments: `list_youtube_video_comments`
3) If a tool returns `nextPageToken` / `next_page_token`, AI calls the same tool again
   passing the token.

---

## 3) Tool discovery & wrapper strategy (CRITICAL)

### Why wrappers exist

MCP hosts display tools based on what the server registers. In practice:
- we want **stable tool names**
- we want **rich docstrings** in the MCP client UI
- we want the server bootstrap file to stay small

Therefore:
- `server.py` registers tools using `FastMCP.add_tool(fn, description=fn.__doc__)`
- `server_tools.py` contains the wrapper functions with the **long docstrings**
- `mcp_tools_*.py` contains the implementation handlers that:
  - read env vars
  - construct the API client
  - enforce budgets / validate
  - return structured output

### Pagination alias design

Some LLM agents fail to connect:
- output `nextPageToken` (camelCase)
- input `page_token` (snake_case)

To make pagination robust across hosts/agents:
- responses include both `nextPageToken` and `next_page_token`
- requests accept both `page_token` and `next_page_token`

This is implemented in the **tool handler layer** and also reflected in wrapper
function signatures so schemas show the alias.

---

## 4) Repository layout

```
.
├─ src/
│  └─ youtube_mcp/
│     ├─ server.py                 # MCP bootstrap + tool registration
│     ├─ server_tools.py           # wrappers + docstrings (tool contracts)
│     ├─ youtube_data_api_client.py
│     ├─ youtube_client_protocol.py
│     ├─ youtube_data_api_constants.py
│     ├─ quota_budgeter.py
│     ├─ channel_resolver.py / channel_ref.py
│     ├─ channel_inventory.py      # uploads playlist strategy
│     ├─ channel_playlists.py
│     ├─ playlist_videos.py
│     ├─ channel_search.py         # Search API (keyword search)
│     ├─ video_comments.py         # commentThreads
│     ├─ youtube_url.py            # URL → video_id helper
│     └─ mcp_tools_*.py            # tool handlers (env + budgets + domain call)
├─ tests/
└─ docs/
```

---

## 5) YouTube Data API client design (security & resilience)

### Fixed host / SSRF guardrails
The HTTP client:
- uses a fixed scheme/host/base path
- rejects non-allowlisted endpoints

Allowlist lives in:
- `youtube_data_api_constants.py` → `YOUTUBE_DATA_API_ALLOWED_ENDPOINTS`

### Retry/backoff
`YouTubeDataApiClient` implements:
- bounded retries
- exponential backoff for transient failures (429/5xx/network)

### Gzip handling
Some responses are gzip-compressed. The client:
- checks `Content-Encoding: gzip` and/or gzip magic bytes
- decompresses before JSON decoding

---

## 6) Quota model (best-effort)

The project uses a **quota estimator + enforcement** layer.

File:
- `quota_budgeter.py`

Key points:
- It is an estimator, not a billing engine.
- It exists to prevent accidental huge runs.

Official quota reference:
- https://developers.google.com/youtube/v3/determine_quota_cost

Important costs:
- `search.list` ~100 units per page (expensive)
- most `*.list` reads are ~1 unit per page

---

## 7) Sorting / ordering capabilities

### What we can do cheaply
- Uploads playlist listing is cheap and complete.

### What we can do with bounded local sorting
`order_strategy=local_sort`:
- fetches a bounded subset (max_videos + max_pages)
- hydrates stats via `videos.list`
- sorts locally by:
  - `viewCount`, `likeCount`, `commentCount`, `duration`

Notes:
- Not paginated
- Not guaranteed to find the global maximum if the channel is huge (because bounded)

### What we can do via Search API
- `search_youtube_channel_videos` supports keyword search and Search ordering.

Notes:
- Expensive quota
- API behavior can cap results

---

## 8) Comments tool notes

- Uses `commentThreads.list`
- Supports pagination (`pageToken`)
- `maxResults` allows up to **100**
- Comments may be disabled → 403 with reason `commentsDisabled`

---

## 9) URL handling

The tool `get_yt_video_info` accepts:
- raw video id
- full YouTube URL

Helper:
- `youtube_url.extract_video_id()`

---

## 10) Documentation responsibilities

- `README.md` is user-facing.
- `docs/TOOLS.md` is the canonical list of tools + params + pagination + quota.
- `docs/PACKAGING_PYPI.md` is the operational packaging checklist.

---

## 11) Testing (run commands)

### IMPORTANT rule
Always run pytest through the intended interpreter to avoid global/venv mismatch:

```powershell
# inside venv (recommended)
.\.venv\Scripts\python.exe -m pytest -q

# or generic
python -m pytest -q
```

### Common dev dependencies

```powershell
python -m pip install -U pytest pytest-asyncio
```
