from __future__ import annotations

from typing import List, Optional, Union, Literal, Annotated
from pydantic import BaseModel, Field, field_validator


# ---------- Block variants ----------


class HeadingBlock(BaseModel):
    kind: Literal["heading"] = "heading"
    level: int = Field(ge=1, le=6)
    text: str


class ParagraphBlock(BaseModel):
    kind: Literal["paragraph"] = "paragraph"
    text: str


class ListBlock(BaseModel):
    kind: Literal["list"] = "list"
    ordered: bool
    items: List[str] = Field(default_factory=list)


class TableBlock(BaseModel):
    kind: Literal["table"] = "table"
    rows: List[List[str]] = Field(default_factory=list)

    @field_validator("rows")
    @classmethod
    def _rows_non_jagged(cls, v: List[List[str]]) -> List[List[str]]:
        if not v:
            return v
        width = len(v[0])
        for idx, row in enumerate(v, start=1):
            if len(row) != width:
                raise ValueError(
                    f"table rows must have equal length (row {idx} has {len(row)}, expected {width})"
                )
        return v


class CodeBlock(BaseModel):
    kind: Literal["code"] = "code"
    lang: Optional[str] = ""  # keep empty string if unknown
    code: str


class FigureBlock(BaseModel):
    kind: Literal["figure"] = "figure"
    caption: Optional[str] = None
    alt: Optional[str] = None


class FootnoteBlock(BaseModel):
    kind: Literal["footnote"] = "footnote"
    ref: str
    text: str


# Discriminated union on the `kind` field
Block = Union[
    HeadingBlock,
    ParagraphBlock,
    ListBlock,
    TableBlock,
    CodeBlock,
    FigureBlock,
    FootnoteBlock,
]


# ---------- Page & Document ----------


class Page(BaseModel):
    page_number: int = Field(ge=1)
    blocks: List[Block] = Field(default_factory=list)


class Document(BaseModel):
    pages: List[Page] = Field(min_length=1)
