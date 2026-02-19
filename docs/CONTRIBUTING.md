# Contributing (youtube_mcp)

This document describes how to contribute safely and consistently.

---

## 1) Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e .
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

---

## 2) Coding guidelines

- Prefer **small, explicit** functions.
- Keep the HTTP client safe:
  - do not add new endpoints without updating the allowlist in `youtube_data_api_constants.py`
- Tool wrappers (`server_tools.py`) must have **high-quality docstrings**:
  - explain inputs
  - explain pagination
  - explain quota implications
  - include common failure cases

---

## 3) Adding a new tool (checklist)

1) Domain function
2) Tool handler (`mcp_tools_*.py`)
3) Wrapper (`server_tools.py` docstring)
4) Register tool in `server.py`
5) Unit tests (fake client)
6) Update `docs/TOOLS.md`

---

## 4) Notes for AI-assisted development

If you use another AI to extend this project, point it to:
- `docs/ARCHITECTURE.md`
- `docs/TOOLS.md`

And ask it to:
- keep outputs structured
- respect quota budgets
- preserve endpoint allowlists
