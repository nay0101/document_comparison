from typing import Literal, TypedDict, List, Optional
from io import BytesIO

Model = Literal[
    "chatgpt-4o-latest",
    "gpt-4o-mini",
    "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-latest",
    "gpt-4o-2024-11-20",
    "gpt-4o",
    "gpt-4.1",
    "o1",
    "o1-mini",
    "gemini-1.5-pro",
]

Engine = Literal["openai", "anthropic"]


class Exception(TypedDict):
    description: str
    issue_items: List[str]
    fix_recommendations: List[str]


class Deviation(TypedDict):
    guideline: str
    exceptions: List[Exception]


class DocSnippet(TypedDict):
    content: str


class Flag(TypedDict):
    types: List[str]
    doc1: DocSnippet
    doc2: DocSnippet
    explanation: str


class Mismatches(TypedDict):
    flags: List[Flag]


class GuidelineInfo(TypedDict):
    clause: str
    image_urls: List[str]
    title: str
