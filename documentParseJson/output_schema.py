from __future__ import annotations

from typing import List, Optional, Union, Tuple, Literal
from pydantic import BaseModel, Field, field_validator


class HeadingBlock(BaseModel):
    """A heading/title line within the document content hierarchy."""

    kind: Literal["heading"] = Field(
        "heading", description="Discriminator tag for this block type."
    )
    level: int = Field(
        ...,
        ge=1,
        le=6,
        description="Heading depth where 1 is the top-most level (e.g., H1) and 6 is the deepest (H6).",
    )
    text: str = Field(
        ..., description="Plain text content of the heading as it appears on the page."
    )


class ParagraphBlock(BaseModel):
    """A paragraph of running body text."""

    kind: Literal["paragraph"] = Field(
        "paragraph", description="Discriminator tag for this block type."
    )
    text: str = Field(
        ...,
        description="Plain text content of the paragraph, preserving reading order.",
    )


class ListBlock(BaseModel):
    """A list block containing ordered or unordered items."""

    kind: Literal["list"] = Field(
        "list", description="Discriminator tag for this block type."
    )
    ordered: bool = Field(
        ...,
        description="True for an ordered list (1., a., i.), False for an unordered list (bullets).",
    )
    items: List[str] = Field(
        default_factory=list,
        description="Each list item as plain text, in visual order.",
    )


class TableBlock(BaseModel):
    """A rectangular table represented as rows of cell text."""

    kind: Literal["table"] = Field(
        "table", description="Discriminator tag for this block type."
    )
    rows: List[List[str]] = Field(
        default_factory=list,
        description="2D array of table cells; each inner list is a row. All rows must have equal length.",
    )


class CodeBlock(BaseModel):
    """A fenced code block."""

    kind: Literal["code"] = Field(
        "code", description="Discriminator tag for this block type."
    )
    lang: Optional[str] = Field(
        default="",
        description="Optional language hint for syntax highlighting (e.g., 'python').",
    )
    code: str = Field(..., description="Raw code contents as monospaced text.")


class FigureBlock(BaseModel):
    """A figure or illustration with optional caption/alt text."""

    kind: Literal["figure"] = Field(
        "figure", description="Discriminator tag for this block type."
    )
    caption: str = Field(
        default="",
        description="Human-readable caption/legend shown near the figure.",
    )
    alt: str = Field(
        default="",
        description="Alternative text describing the figure's content for accessibility.",
    )


class FootnoteBlock(BaseModel):
    """A footnote definition mapping a reference marker to text."""

    kind: Literal["footnote"] = Field(
        "footnote", description="Discriminator tag for this block type."
    )
    ref: str = Field(
        ...,
        description="The footnote reference/marker (e.g., '1', '†') that appears in the main text.",
    )
    text: str = Field(
        ..., description="The full footnote text associated with the marker."
    )


class TOCBlock(BaseModel):
    """Table of contents block."""

    kind: Literal["toc"] = Field(
        "toc", description="Discriminator tag for this block type."
    )
    items: List[str] = Field(
        default_factory=list,
        description="Table of contents entry in visual order; strip dot leaders and page numbers.",
    )


# ANY-OF style union (no discriminator) -> exported JSON Schema uses `anyOf`
Block = Union[
    HeadingBlock,
    TOCBlock,
    ParagraphBlock,
    ListBlock,
    TableBlock,
    CodeBlock,
    FigureBlock,
    FootnoteBlock,
]


class Page(BaseModel):
    """A single page of the document with optional header/footer and main content blocks."""

    page_number: int = Field(
        ..., ge=1, description="1-based page index within the document."
    )
    header: str = Field(
        default_factory=str, description="Top-of-page region; empty if none."
    )
    footer: str = Field(
        default_factory=str, description="Bottom-of-page region; empty if none."
    )
    blocks: List[Block] = Field(
        default_factory=list,
        description="Main body content blocks for this page, in reading order, excluding header/footer.",
    )


class Document(BaseModel):
    """The full extracted document, organized by pages."""

    pages: List[Page] = Field(
        ..., min_length=1, description="List of pages in reading order."
    )
