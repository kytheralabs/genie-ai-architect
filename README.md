# genie-ai-architect

A portable Databricks-native package that gives Genie Code a "phone a friend"
capability — consult a stronger reasoning model through AI Gateway while
Genie Code stays the hands-on execution engine.

## What it does

```
Developer → Genie Code → phone_a_friend (Codex via AI Gateway) → Genie Code continues
```

The advisory helper is **reasoning-only**: it returns architecture guidance,
code reviews, refactoring plans, and documentation — never claims to have
executed code or edited assets.  Genie Code remains the implementation agent.

## Architecture: 3 Layers of Access

The package provides three layers, each adding structure on top of the one below.
Pick the layer that matches your use case.

### Layer 1 — Raw AI Gateway call (`ask_ai`)

The bare wire.  Send any prompt to Codex and get text back.  No system prompt,
no mode, no context assembly.

```python
from phone_a_friend import ask_ai

# Plain text
print(ask_ai("What are best practices for Delta partitioning?"))

# With metadata (timing, model, response ID)
meta = ask_ai("Explain medallion architecture", return_metadata=True)
print(f"{meta['model']}  {meta['duration_ms']}ms  ok={meta['ok']}")
```

**When to use:** Quick one-shot questions, smoke tests, custom prompts where
you want full control.

### Layer 2 — Structured advisory (`phone_a_friend`)

Wraps the call in a `PhoneAFriendRequest` that injects a reasoning-only system
prompt and structures your ask with a mode, repo context, code context, and
constraints.

```python
from phone_a_friend import phone_a_friend

advice = phone_a_friend(
    "Review my pipeline architecture for brittleness",
    mode="architecture",
    repo_context="ETL pipeline: bronze → silver → gold with 20 notebooks",
    constraints=["Must stay on Databricks", "No autonomous agents"],
)
```

Available modes: `general` (default), `architecture`, `refactor`,
`code_review`, `documentation`.

**When to use:** You want the advisory system prompt and structured request
format, but don't need the prompt library or ProjectContext.

### Layer 3 — Review functions (`reviewer` + `ProjectContext`)

The highest-level entry points.  Each function picks a system prompt from the
prompt library, wraps your input in a review-specific frame, optionally renders
a `ProjectContext`, and calls `ask_ai`.

```python
from phone_a_friend import load_project, ask_architect, review_code

# Auto-discover an entire project — one call
ctx = load_project("/Workspace/Users/me/my-project")

# Then ask anything about it
print(ask_architect("Where is the highest-priority tech debt?", context=ctx))

# Quick code review (no project context needed)
print(review_code(my_code, mode="tactical"))
```

| Function | Default system prompt | What you pass |
| --- | --- | --- |
| `ask_architect(question, ctx, mode)` | Strategic Architect | A question |
| `review_code(code, ctx, mode)` | Tactical Engineer | Python/PySpark source |
| `review_sql(sql, ctx, mode)` | Tactical Engineer | SQL source |
| `review_project(ctx)` | Strategic Architect | Full ProjectContext |
| `review_notebook_source(source, ctx)` | Strategic Architect | Raw notebook source |
| `review_documentation(text, ctx)` | Documentation | Documentation text |

The `mode` parameter switches between two system prompts:
- **`"strategic"`** — senior architect lens (design, tradeoffs, phased refactoring)
- **`"tactical"`** — senior engineer lens (concrete code, implementation details)

**When to use:** Code reviews, SQL reviews, architecture questions, project
audits — anything where you want the curated prompts and optional
`ProjectContext` to ground the model in your codebase.

## Prerequisites

1. **Databricks workspace** with AI Gateway access
2. **AI Gateway endpoint** serving a model (default: `databricks-gpt-5-3-codex`)
3. **Python package**: `databricks-openai`

No PATs.  No secrets.  No manual base URLs.  Authentication is automatic
via notebook-native Databricks auth.

## Installation on a new workspace

### Step 1: Copy the folder

Copy the entire `codex-phone-a-friend/` folder to the target workspace:

```
/Workspace/Users/<you>/codex-phone-a-friend/
├── README.md
├── genie_setup.md           ← manual instructions template (alternative to skill)
├── skill/
│   └── SKILL.md              ← Genie Code skill (auto-loaded, recommended)
└── phone_a_friend/          ← importable Python package
    ├── __init__.py
    ├── client.py             ← singleton AI Gateway client + ask_ai()
    ├── prompts.py            ← system prompt library
    ├── context.py            ← ProjectContext for building context
    ├── loader.py             ← load_project() auto-discovery
    ├── reviewer.py           ← ask_architect, review_code, review_sql, etc.
    └── advisor.py            ← PhoneAFriend class + phone_a_friend()
```

### Step 2: Install the dependency

In your notebook:

```python
%pip install -U databricks-openai "typing_extensions>=4.12.0"
dbutils.library.restartPython()
```

### Step 3: Add to Python path and import

```python
import sys
sys.path.insert(0, "/Workspace/Users/<you>/codex-phone-a-friend")

from phone_a_friend import ask_ai, phone_a_friend, ProjectContext, ask_architect
```

### Step 4: Verify

```python
from phone_a_friend import smoke_test
print(smoke_test())  # → "Hello from phone_a_friend"
```

## Quick start

### Simple one-shot call

```python
from phone_a_friend import ask_ai

print(ask_ai("What are best practices for Delta table partitioning?"))
```

### With metadata (timing, model, response ID)

```python
result = ask_ai("Explain medallion architecture", return_metadata=True)
print(f"OK: {result['ok']}  Model: {result['model']}  Duration: {result['duration_ms']}ms")
print(result["text"])
```

### Structured advisory call

```python
from phone_a_friend import phone_a_friend

advice = phone_a_friend(
    "Review my pipeline architecture for brittleness",
    mode="architecture",
    repo_context="ETL pipeline: bronze → silver → gold with 20 notebooks",
    constraints=["Must stay on Databricks", "No autonomous agents"],
)
print(advice)
```

### Code review

```python
from phone_a_friend import review_code

feedback = review_code('''
def process_batch(df):
    results = df.collect()
    for row in results:
        spark.sql(f"INSERT INTO target VALUES ('{row.id}', '{row.value}')")
''', mode="tactical")
print(feedback)
```

### Project-wide architectural review

```python
from phone_a_friend import ProjectContext, ask_architect

ctx = ProjectContext("my-project")
ctx.add_directory("/Workspace/Users/me/my-project/src", pattern="*.py")
ctx.add_text("Pipeline: ingest → transform → publish", label="Architecture")

print(ask_architect("Where is the highest-priority technical debt?", context=ctx))
```

### Load workspace notebooks into context

```python
ctx = ProjectContext("my-pipeline")
ctx.add_workspace_notebook("/Users/me/notebooks/etl_main", label="ETL Main")
ctx.add_workspace_notebook("/Users/me/notebooks/data_quality", label="DQ Checks")

print(ask_architect("What should move from notebooks into Python modules?", context=ctx))
```

## API Reference

### Project Loading

```python
ctx = load_project(
    "/Workspace/Users/me/my-project",
    name="my-project",              # defaults to folder name
    code_patterns=("*.py",),         # source code globs
    doc_patterns=("*.md", "*.toml"), # documentation globs
    include_notebooks=True,          # auto-discover workspace notebooks via SDK
    max_depth=10,                    # max directory depth for notebook scan
    verbose=True,                    # print summary on completion
)
```

`load_project` auto-discovers source files, documentation, and workspace
notebooks under the given path.  It returns a `ProjectContext` ready to pass
into any review function.  No manual file listing required.

### Core

| Function | Description |
| --- | --- |
| `ask_ai(prompt, system_prompt=None, model=DEFAULT_MODEL, return_metadata=False)` | Single AI Gateway call.  Returns text or metadata dict. |
| `get_client()` | Singleton DatabricksOpenAI client. |
| `DEFAULT_MODEL` | Currently `"databricks-gpt-5-3-codex"`. |

### Advisory

| Function | Description |
| --- | --- |
| `phone_a_friend(ask, mode, repo_context, code_context, constraints)` | One-shot advisory call with structured request. |
| `PhoneAFriend(model, system_prompt)` | Class for repeated calls with custom config. |
| `PhoneAFriendRequest(ask, mode, ...)` | Structured request dataclass. |

### Review

| Function | Description |
| --- | --- |
| `ask_architect(question, context=None, mode="strategic")` | Architecture/design questions. |
| `review_code(code, context=None, mode="tactical")` | Python/PySpark code review. |
| `review_sql(sql, context=None, mode="tactical")` | SQL review (Databricks-first). |
| `review_project(context)` | Full project architectural review. |
| `review_notebook_source(source, context=None)` | Notebook module-boundary analysis. |
| `review_documentation(text, context=None)` | Documentation review/drafting. |

### Context

| Method | Description |
| --- | --- |
| `ProjectContext(name)` | Create a new context collector. |
| `.add_code(code, label)` | Add Python code. |
| `.add_sql(sql, label)` | Add SQL. |
| `.add_text(text, label)` | Add free-form text. |
| `.add_schema(text, label)` | Add schema description. |
| `.add_directory(path, pattern)` | Recursively load files. |
| `.add_workspace_notebook(path, label)` | Export + add a Databricks notebook. |
| `.add_notebook_file(path, label)` | Add a local .ipynb file. |
| `.render()` | Render all sections as markdown. |

### Modes

**Reviewer modes** (`ask_architect`, `review_code`, `review_sql`):
- `"strategic"` — senior architect lens: design, tradeoffs, phased refactoring
- `"tactical"` — senior engineer lens: concrete code, implementation details

**Advisory modes** (`phone_a_friend`):
- `"architecture"` — system design and boundaries
- `"refactor"` — refactoring strategy
- `"code_review"` — code quality
- `"documentation"` — docs review
- `"general"` — open-ended questions

## Genie Code Integration

The package ships with a **Genie Code skill** that automatically enables
`ask ai` commands:

```
ask ai context /Users/me/my-project    ← load project context
ask ai what is the tech debt?           ← ask a question (strategic)
ask ai dev review error handling        ← ask a question (tactical)
ask ai flush                            ← clear context
```

### Option A: Install the skill (recommended)

Copy the `skill/SKILL.md` file to your Genie Code skills directory:

```
/Workspace/Users/<you>/.assistant/skills/genie-ai-architect/SKILL.md
```

Genie Code auto-discovers skills and loads them when relevant — no manual
pasting required. The skill activates whenever you type `ask ai`.

### Option B: Manual instructions (alternative)

If you prefer, see **[genie_setup.md](genie_setup.md)** for a copy-paste
template to add to your `.assistant_instructions.md`.

## Changing the model

To use a different AI Gateway endpoint:

```python
from phone_a_friend import ask_ai

# Per-call override
result = ask_ai("...", model="databricks-meta-llama-3-1-70b-instruct")

# Or change the default for the session
import phone_a_friend.client as client
client.DEFAULT_MODEL = "your-endpoint-name"
```

## Design philosophy

This is **not** another coding agent.  It does not replace Genie Code.
It does not execute code, edit notebooks, or manage state.

It is a reasoning-only advisor that answers:
- Where is the technical debt?
- What should become Python modules?
- What responsibilities belong in notebooks?
- What architectural improvements are highest priority?
- How should this project evolve?

The emphasis is always on practical incremental improvements.
