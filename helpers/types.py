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


class Result(TypedDict):
    clause: str
    isComplied: Literal["complied", "non-complied", "not-applicable"]
    reason: str


class Summary(TypedDict):
    compliant: List[str]
    nonComplied: List[str]
    notApplicable: List[str]


class Deviation(TypedDict):
    results: List[Result]
    summary: Summary


class DocSnippet(TypedDict):
    content: str


class Flag(TypedDict):
    types: List[str]
    doc1: DocSnippet
    doc2: DocSnippet
    explanation: str


class Mismatches(TypedDict):
    flags: List[Flag]


class InputType(TypedDict):
    images: List[str]
    text: str


class GuidelineInfo(TypedDict):
    clauses: List[InputType]
    attachments: List[InputType]
    title: str
