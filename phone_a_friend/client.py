"""Databricks-native AI Gateway client.

Singleton DatabricksOpenAI client with notebook-native auth.
Single entry point for all AI calls through Databricks AI Gateway.

Prerequisites:
    %pip install -U databricks-openai "typing_extensions>=4.12.0"
"""

from __future__ import annotations

from threading import Lock
from time import perf_counter

from databricks_openai import DatabricksOpenAI

DEFAULT_MODEL = "databricks-gpt-5-3-codex"
_DEFAULT_MAX_OUTPUT_TOKENS = 3000
_EMPTY_RESPONSE_TEXT = "AI call completed but returned no text."

_client: DatabricksOpenAI | None = None
_client_lock = Lock()


def get_client() -> DatabricksOpenAI:
    """Return a singleton DatabricksOpenAI client using notebook-native auth."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = DatabricksOpenAI()
    return _client


def _build_input(prompt: str, system_prompt: str | None = None) -> str:
    if system_prompt:
        return f"System instructions:\n{system_prompt.strip()}\n\nUser request:\n{prompt.strip()}"
    return prompt.strip()


def _build_result(
    *,
    ok,
    text,
    model,
    started_at,
    prompt,
    error_type=None,
    error_message=None,
    response_id=None,
):
    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    return {
        "ok": ok,
        "text": text,
        "model": model,
        "duration_ms": duration_ms,
        "prompt_chars": len(prompt),
        "response_id": response_id,
        "error_type": error_type,
        "error_message": error_message,
    }


def ask_ai(
    prompt,
    system_prompt=None,
    model=DEFAULT_MODEL,
    max_output_tokens=_DEFAULT_MAX_OUTPUT_TOKENS,
    return_metadata=False,
):
    """Call Databricks AI Gateway through the Responses API.

    Returns plain text by default.  Pass return_metadata=True for a dict
    with ok, text, model, duration_ms, prompt_chars, response_id, and
    error details.
    """
    started_at = perf_counter()
    prompt_text = _build_input(prompt=prompt, system_prompt=system_prompt)

    if not prompt_text:
        result = _build_result(
            ok=False,
            text="AI call skipped because the prompt was empty.",
            model=model,
            started_at=started_at,
            prompt=prompt_text,
            error_type="ValueError",
            error_message="Prompt must not be empty.",
        )
        return result if return_metadata else result["text"]

    try:
        response = get_client().responses.create(
            model=model,
            input=prompt_text,
            max_output_tokens=max_output_tokens,
        )
        output_text = str(getattr(response, "output_text", "") or "").strip()
        result = _build_result(
            ok=bool(output_text),
            text=output_text or _EMPTY_RESPONSE_TEXT,
            model=model,
            started_at=started_at,
            prompt=prompt_text,
            response_id=getattr(response, "id", None),
        )
    except Exception as exc:
        result = _build_result(
            ok=False,
            text=f"AI call failed gracefully: {type(exc).__name__}: {exc}",
            model=model,
            started_at=started_at,
            prompt=prompt_text,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    return result if return_metadata else result["text"]
