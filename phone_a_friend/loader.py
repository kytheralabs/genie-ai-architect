"""Auto-discover and load project context from a workspace path.

One call replaces the manual add_directory / add_workspace_notebook ceremony:

    from phone_a_friend import load_project, ask_architect

    ctx = load_project("/Workspace/Users/me/my-project")
    print(ask_architect("Where is the tech debt?", context=ctx))
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .context import ProjectContext

_DEFAULT_CODE_PATTERNS: tuple[str, ...] = ("*.py",)
_DEFAULT_DOC_PATTERNS: tuple[str, ...] = ("*.md", "*.toml", "*.yaml", "*.yml", "*.txt")


def load_project(
    path: str,
    *,
    name: str | None = None,
    code_patterns: Sequence[str] = _DEFAULT_CODE_PATTERNS,
    doc_patterns: Sequence[str] = _DEFAULT_DOC_PATTERNS,
    include_notebooks: bool = True,
    max_depth: int = 10,
    verbose: bool = True,
) -> ProjectContext:
    """Auto-discover and load project context from a workspace path.

    Scans the given path for:
      - Source code files (``*.py`` by default)
      - Documentation / config files (``*.md``, ``*.toml``, ``*.yaml``, etc.)
      - Databricks workspace notebooks (via SDK export)

    Args:
        path: Workspace path to the project root.
              Accepts ``/Workspace/Users/...`` or ``/Users/...`` formats.
        name: Project name for the context header.  Defaults to the folder name.
        code_patterns: Glob patterns for source code (passed to ``rglob``).
        doc_patterns: Glob patterns for docs / config.
        include_notebooks: Whether to discover and load workspace notebooks.
        max_depth: Maximum directory depth for notebook discovery (0 = root only).
        verbose: Print a summary when loading completes.

    Returns:
        A populated :class:`ProjectContext` ready for ``ask_architect``, etc.
    """
    # ── Normalize paths ──────────────────────────────────────────────────────
    ws_path = path.rstrip("/")
    if ws_path.startswith("/Workspace"):
        fs_path = Path(ws_path)
        api_path = ws_path[len("/Workspace"):]
    else:
        fs_path = Path(f"/Workspace{ws_path}")
        api_path = ws_path

    project_name = name or fs_path.name
    ctx = ProjectContext(project_name)

    # ── Source code ──────────────────────────────────────────────────────────
    code_count = 0
    for pattern in code_patterns:
        before = len(ctx.sections)
        ctx.add_directory(fs_path, pattern=pattern, label_relative_to=fs_path)
        code_count += len(ctx.sections) - before

    # ── Documentation / config ───────────────────────────────────────────────
    doc_count = 0
    for pattern in doc_patterns:
        before = len(ctx.sections)
        ctx.add_directory(fs_path, pattern=pattern, label_relative_to=fs_path)
        doc_count += len(ctx.sections) - before

    # ── Workspace notebooks ──────────────────────────────────────────────────
    nb_count = 0
    if include_notebooks:
        nb_count = _discover_notebooks(ctx, api_path, max_depth, verbose)

    if verbose:
        print(
            f"load_project ready \u2014 {len(ctx.sections)} sections total\n"
            f"  {code_count:>3} source files     ({', '.join(code_patterns)})\n"
            f"  {doc_count:>3} docs / config     ({', '.join(doc_patterns)})\n"
            f"  {nb_count:>3} notebooks         (workspace SDK)\n"
            f"from {fs_path}"
        )

    return ctx


def _discover_notebooks(
    ctx: ProjectContext,
    api_path: str,
    max_depth: int,
    verbose: bool,
) -> int:
    """Recursively discover workspace notebooks under *api_path* via SDK."""
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.workspace import ObjectType

    w = WorkspaceClient()
    count = 0
    skipped: list[str] = []

    def _walk(dir_path: str, depth: int) -> None:
        nonlocal count
        if depth > max_depth:
            return
        try:
            for obj in w.workspace.list(dir_path):
                if obj.object_type == ObjectType.NOTEBOOK:
                    label = (obj.path or "")[len(api_path):].lstrip("/")
                    try:
                        ctx.add_workspace_notebook(obj.path, label=label or obj.path)
                        count += 1
                    except Exception as exc:
                        skipped.append(f"{label}: {exc}")
                elif obj.object_type == ObjectType.DIRECTORY:
                    _walk(obj.path, depth + 1)
        except Exception as exc:
            skipped.append(f"{dir_path}: {exc}")

    _walk(api_path, 0)

    if verbose and skipped:
        print(f"  skipped {len(skipped)} notebook(s):")
        for s in skipped[:5]:
            print(f"    {s}")
        if len(skipped) > 5:
            print(f"    ... and {len(skipped) - 5} more")

    return count
