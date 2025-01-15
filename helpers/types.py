from typing import Literal


Model = Literal[
    "chatgpt-4o-latest",
    "gpt-4o-mini",
    "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-latest",
    "gpt-4o-2024-11-20",
    "gpt-4o",
    "gemini-1.5-pro",
]

Engine = Literal["openai", "anthropic"]
