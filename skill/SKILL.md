---
name: genie-ai-architect
description: "Phone a Friend" AI advisory package for Genie Code. Load this skill when the user types "ask ai" (with or without arch/dev/context/flush), or asks about the phone_a_friend package, load_project, ask_architect, review_code, review_sql, ProjectContext, or AI Gateway advisory calls.
---

# Genie AI Architect — Phone a Friend 

The `phone_a_friend` package lets Genie Code consult a stronger reasoning model
(Codex) through Databricks AI Gateway for architecture, code review, refactoring,
and documentation guidance. Genie Code remains the execution agent — the advisor
is reasoning-only.

## Package Location

The package lives at:
`/Workspace/Users/<USER>/codex-phone-a-friend/phone_a_friend/`

Replace `<USER>` with the current workspace user's email/username.

## Prerequisites

If a cold start hits `ModuleNotFoundError: databricks_openai`, run:
```python
%pip install -U databricks-openai "typing_extensions>=4.12.0"
dbutils.library.restartPython()
```

## Command Routing

When the user types `ask ai ...`, parse the message and route to one of
three commands:

### 1. `ask ai context /path/to/project`

Load (or replace) project context from the given workspace path.

Execution (via `executeCode`):
```python
import sys
sys.path.insert(0, "/Workspace/Users/<USER>/codex-phone-a-friend")
from phone_a_friend import load_project
project_ctx = load_project("/Workspace<path>")
```

Confirm what was loaded (section counts) and that the context is ready.

### 2. `ask ai flush`

Clear the loaded context.

Execution (via `executeCode`):
```python
project_ctx = None
print("Context flushed.")
```

Confirm context was cleared.

### 3. `ask ai [arch|dev] [question]`

Ask a question using the current `project_ctx`.

- `arch` — strategic mode (senior architect lens: design, tradeoffs, phased refactoring)
- `dev` — tactical mode (senior engineer lens: concrete code, implementation details)
- omitted — defaults to strategic

If no context has been loaded (or it was flushed), tell the user to load
context first with `ask ai context /path`.

Execution (via `executeCode`):
```python
import sys
sys.path.insert(0, "/Workspace/Users/<USER>/codex-phone-a-friend")
from phone_a_friend import ask_architect
print(ask_architect("<question>", context=project_ctx, mode="<strategic|tactical>"))
```

## Parsing Rules

1. Strip the `ask ai` prefix
2. Check the first token after the prefix:
   - `context` → load the path that follows
   - `flush` → clear context
   - `arch` → set mode to `strategic`, remainder is the question
   - `dev` → set mode to `tactical`, remainder is the question
   - anything else → mode is `strategic`, entire remainder is the question
3. Pass the question text **verbatim** — do NOT reword, massage, or restructure it

## Execution Rules

- Always use `executeCode` — do NOT modify notebook cells
- Add a timestamp comment at the top of every `executeCode` block
- If `project_ctx` was loaded in a prior `executeCode` call this session, reuse
  it — don't reload unless the user runs `ask ai context` again
- If cold start hits `ModuleNotFoundError`, install dependencies first (see Prerequisites), then retry

## 3 Layers of Access

The package provides three layers, each adding structure:

### Layer 1 — Raw AI Gateway call (`ask_ai`)
Bare wire — send any prompt, get text back. No system prompt, no context.
```python
from phone_a_friend import ask_ai
print(ask_ai("any question"))
# With metadata:
meta = ask_ai("question", return_metadata=True)
```

### Layer 2 — Structured advisory (`phone_a_friend`)
Adds a reasoning-only system prompt and structured request with modes.
```python
from phone_a_friend import phone_a_friend
advice = phone_a_friend("question", mode="architecture")
```
Modes: `general` (default), `architecture`, `refactor`, `code_review`, `documentation`.

### Layer 3 — Review functions + ProjectContext
Highest level — curated system prompts, optional codebase context.
```python
from phone_a_friend import load_project, ask_architect, review_code, review_sql
ctx = load_project("/Workspace/Users/me/my-project")
print(ask_architect("Where is the tech debt?", context=ctx))
print(review_code(my_code, mode="tactical"))
print(review_sql(my_sql, mode="tactical"))
```

| Function | Default mode | What you pass |
| --- | --- | --- |
| `ask_architect(question, ctx, mode)` | strategic | A question |
| `review_code(code, ctx, mode)` | tactical | Python/PySpark source |
| `review_sql(sql, ctx, mode)` | tactical | SQL source |
| `review_project(ctx)` | strategic | Full ProjectContext |
| `review_notebook_source(source, ctx)` | strategic | Raw notebook source |
| `review_documentation(text, ctx)` | N/A | Documentation text |

## Changing the Model

Default model: `databricks-gpt-5-3-codex`

```python
# Per-call override
ask_ai("...", model="databricks-meta-llama-3-1-70b-instruct")

# Session-wide override
import phone_a_friend.client as client
client.DEFAULT_MODEL = "your-endpoint-name"
```
