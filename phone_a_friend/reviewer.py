"""High-level review and advisory functions. 

Each function gathers optional context, builds a prompt, calls ask_ai(),
and returns structured markdown.
"""

from __future__ import annotations

from .client import ask_ai
from .context import ProjectContext
from .prompts import (
    ARCHITECT_PROMPT,
    DOCUMENTATION_PROMPT,
    SPARK_REVIEW_PROMPT,
    SQL_REVIEW_PROMPT,
    STRATEGIC_ARCHITECT_PROMPT,
    TACTICAL_CODING_PROMPT,
    combine_prompt,
)


def _render_context(context: ProjectContext | str | None) -> str | None:
    if context is None:
        return None
    if isinstance(context, ProjectContext):
        return context.render()
    return str(context).strip()


def _review(body: str, system_prompt: str, context: ProjectContext | str | None = None) -> str:
    prompt = combine_prompt(base_prompt=system_prompt, body=body, context=_render_context(context))
    return ask_ai(prompt=prompt)


def _pick_prompt(mode: str) -> str:
    """Return the system prompt for the given mode ('strategic' or 'tactical')."""
    if mode == "tactical":
        return TACTICAL_CODING_PROMPT
    return STRATEGIC_ARCHITECT_PROMPT


def review_code(code, context=None, mode="tactical"):
    return _review(
        body=f"Review the following code.\n\n```python\n{str(code).strip()}\n```",
        system_prompt=_pick_prompt(mode),
        context=context,
    )


def review_notebook_source(source, context=None, mode="strategic"):
    return _review(
        body=(
            "Review the following Databricks notebook source. Identify what should remain in notebooks, "
            "what should move into reusable Python modules, and where incremental refactoring would help."
            f"\n\n```python\n{str(source).strip()}\n```"
        ),
        system_prompt=_pick_prompt(mode),
        context=context,
    )


def review_sql(sql, context=None, mode="tactical"):
    return _review(
        body=f"Review the following SQL.\n\n```sql\n{str(sql).strip()}\n```",
        system_prompt=_pick_prompt(mode),
        context=context,
    )


def review_project(context):
    return _review(
        body=(
            "Review this project context and return the standard response format with emphasis on "
            "architecture, module boundaries, notebook responsibilities, and incremental refactoring."
        ),
        system_prompt=ARCHITECT_PROMPT,
        context=context,
    )


def ask_architect(question, context=None, mode="strategic"):
    return _review(
        body=f"Answer the following question:\n\n{str(question).strip()}",
        system_prompt=_pick_prompt(mode),
        context=context,
    )


def review_documentation(text, context=None):
    return _review(
        body=f"Review or improve the following documentation.\n\n{text}",
        system_prompt=DOCUMENTATION_PROMPT,
        context=context,
    )
