# Genie Code Integration — `ask codex` Instructions

Copy the block below into your `.assistant_instructions.md` file to enable
the `ask codex` commands in Genie Code.

> **Before pasting:** replace `<YOUR_USERNAME>` with your Databricks workspace
> username (e.g. `lance@kytheralabs.com`).

---

## Copy from here ↓

```markdown
### Ask Codex — Phone a Friend

The `phone_a_friend` package is installed at:
`/Workspace/Users/<YOUR_USERNAME>/codex-phone-a-friend/phone_a_friend/`

Three command forms:

1. **`ask codex context /path/to/project`** — load (or replace) project context
   from the given workspace path. Runs `load_project(path)` and stores the
   result as `project_ctx`. Confirm what was loaded (section counts) and that
   the context is ready.

2. **`ask codex flush`** — clear the loaded context. Set `project_ctx = None`.
   Confirm context was cleared.

3. **`ask codex [arch|dev] [question]`** — ask a question using the current
   `project_ctx`.
   - `arch` — strategic mode (senior architect lens: design, tradeoffs, phased
     refactoring)
   - `dev` — tactical mode (senior engineer lens: concrete code, implementation
     details)
   - omitted — defaults to strategic
   - If no context has been loaded (or it was flushed), tell the user to load
     context first with `ask codex context /path`.

Examples:
- `ask codex context /Users/<YOUR_USERNAME>/my-project` → loads project context
- `ask codex what is the tech debt?` → strategic question against loaded context
- `ask codex dev review error handling` → tactical question against loaded context
- `ask codex flush` → clears context so a new project can be loaded
- `ask codex context /Users/<YOUR_USERNAME>/other-project` → replaces context

Parsing: strip "ask codex", then check first token: "context" → load path,
"flush" → clear, "arch"/"dev" → set mode + rest is question, otherwise →
strategic + entire remainder is question.

Pass the question text verbatim — do NOT reword, massage, or restructure it.

Do NOT modify any notebook cell. Use `executeCode` to run the call directly
and return the result in chat.

Execution patterns (always via executeCode):

- **Context load:**
  ```python
  import sys
  sys.path.insert(0, "/Workspace/Users/<YOUR_USERNAME>/codex-phone-a-friend")
  from phone_a_friend import load_project
  project_ctx = load_project("/Workspace<path>")
  ```

- **Flush:**
  ```python
  project_ctx = None
  print("Context flushed.")
  ```

- **Question:**
  ```python
  import sys
  sys.path.insert(0, "/Workspace/Users/<YOUR_USERNAME>/codex-phone-a-friend")
  from phone_a_friend import ask_architect
  print(ask_architect("<question>", context=project_ctx, mode="<strategic|tactical>"))
  ```

If `project_ctx` was loaded in a prior executeCode call this session, reuse
it — don't reload unless the user runs `ask codex context` again.

If cold start hits `ModuleNotFoundError: databricks_openai`, run
`%pip install -U databricks-openai "typing_extensions>=4.12.0"` first, then
`dbutils.library.restartPython()`, then retry.
```

## Copy to here ↑

---

## Setup Steps

1. Open your `.assistant_instructions.md` in Databricks
   (usually at `/Workspace/Users/<you>/.assistant_instructions.md`)
2. Paste the block above
3. Replace `<YOUR_USERNAME>` with your actual username
4. Save

Genie Code will pick up the instructions immediately in new chat sessions.
