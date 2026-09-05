"""Databricks-native Codex 'phone a friend' helper.

This module lets Genie Code call a stronger reasoning model through AI Gateway
without changing Genie's execution-first workflow.  The helper is intentionally
reasoning-only: it returns recommendations, plans, and reviews, while Genie
remains the hands-on implementation agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .client import DEFAULT_MODEL, get_client

DEFAULT_SYSTEM_PROMPT = """
You are a reasoning-only advisor to Genie Code inside Databricks.

Your role:
- Help with architecture, refactoring strategy, code review, documentation, and design tradeoffs.
- Do not pretend to have run code, queried data, or edited assets.
- Do not output implementation claims such as 'I changed', 'I ran', or 'I verified'.
- Assume Genie Code will do the hands-on execution after reading your advice.

Response style:
- Be concise, concrete, and implementation-aware.
- Prefer structured bullets.
- Call out risks, assumptions, and recommended next steps.
""".strip()

ALLOWED_MODES = {
    "architecture",
    "refactor",
    "documentation",
    "code_review",
    "general",
}


@dataclass(slots=True)
class PhoneAFriendRequest:
    ask: str
    mode: str = "general"
    repo_context: str | None = None
    code_context: str | None = None
    constraints: Sequence[str] = field(default_factory=tuple)
    expected_output: str = (
        "Practical reasoning only. Genie Code will handle implementation."
    )

    def render(self) -> str:
        if self.mode not in ALLOWED_MODES:
            raise ValueError(
                f"Unsupported mode '{self.mode}'. Expected one of: {sorted(ALLOWED_MODES)}"
            )

        sections: list[str] = [
            "You are being used as Genie Code's 'phone a friend'.",
            f"Mode: {self.mode}",
            f"Primary request:\n{self.ask.strip()}",
        ]

        if self.repo_context:
            sections.append(f"Repository or workspace context:\n{self.repo_context.strip()}")

        if self.code_context:
            sections.append(f"Code or notebook context:\n{self.code_context.strip()}")

        if self.constraints:
            constraint_lines = "\n".join(f"- {item}" for item in self.constraints)
            sections.append(f"Constraints:\n{constraint_lines}")

        sections.append(f"Expected output:\n{self.expected_output.strip()}")
        return "\n\n".join(sections)


class PhoneAFriend:
    """Small wrapper around DatabricksOpenAI responses API."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self.model = model
        self.system_prompt = system_prompt

    def ask(self, request: PhoneAFriendRequest) -> str:
        prompt = f"System instructions:\n{self.system_prompt}\n\nUser request:\n{request.render()}"
        response = get_client().responses.create(model=self.model, input=prompt)
        return response.output_text.strip()


def phone_a_friend(
    ask: str,
    *,
    mode: str = "general",
    repo_context: str | None = None,
    code_context: str | None = None,
    constraints: Sequence[str] = (),
    expected_output: str = "Practical reasoning only. Genie Code will handle implementation.",
    model: str = DEFAULT_MODEL,
) -> str:
    """Convenience wrapper for one-shot advisory calls."""
    helper = PhoneAFriend(model=model)
    request = PhoneAFriendRequest(
        ask=ask,
        mode=mode,
        repo_context=repo_context,
        code_context=code_context,
        constraints=constraints,
        expected_output=expected_output,
    )
    return helper.ask(request)


def smoke_test() -> str:
    """Run the verified minimal model call."""
    response = get_client().responses.create(
        model=DEFAULT_MODEL,
        input="Reply with exactly: Hello from phone_a_friend",
    )
    return response.output_text.strip()
