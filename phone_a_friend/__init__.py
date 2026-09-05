"""phone_a_friend: Portable Databricks AI Gateway advisory package.

Drop this folder into any Databricks workspace to give notebooks a
"phone a friend" capability — consult a stronger reasoning model through
AI Gateway while Genie Code stays the execution engine.

Prerequisites:
    %pip install -U databricks-openai "typing_extensions>=4.12.0"

Quick start:
    import sys
    sys.path.insert(0, "/Workspace/Users/<you>/codex-phone-a-friend")

    from phone_a_friend import ask_ai, phone_a_friend, ProjectContext

    # Simple one-shot call
    print(ask_ai("What are best practices for Delta table partitioning?"))

    # Structured advisory call
    print(phone_a_friend("Review my pipeline architecture", mode="architecture"))
"""

from .client import DEFAULT_MODEL, ask_ai, get_client
from .context import ProjectContext
from .loader import load_project
from .advisor import PhoneAFriend, PhoneAFriendRequest, phone_a_friend, smoke_test
from .prompts import (
    ARCHITECT_PROMPT,
    DOCUMENTATION_PROMPT,
    SPARK_REVIEW_PROMPT,
    SQL_REVIEW_PROMPT,
    STANDARD_RESPONSE_FORMAT,
    STRATEGIC_ARCHITECT_PROMPT,
    TACTICAL_CODING_PROMPT,
    combine_prompt,
)
from .reviewer import (
    ask_architect,
    review_code,
    review_documentation,
    review_notebook_source,
    review_project,
    review_sql,
)

__all__ = [
    # Client
    "ask_ai",
    "get_client",
    "DEFAULT_MODEL",
    # Context
    "ProjectContext",
    "load_project",
    # Phone a Friend
    "PhoneAFriend",
    "PhoneAFriendRequest",
    "phone_a_friend",
    "smoke_test",
    # Prompts
    "ARCHITECT_PROMPT",
    "STRATEGIC_ARCHITECT_PROMPT",
    "TACTICAL_CODING_PROMPT",
    "SQL_REVIEW_PROMPT",
    "SPARK_REVIEW_PROMPT",
    "DOCUMENTATION_PROMPT",
    "STANDARD_RESPONSE_FORMAT",
    "combine_prompt",
    # Reviewer
    "ask_architect",
    "review_code",
    "review_sql",
    "review_project",
    "review_notebook_source",
    "review_documentation",
]
