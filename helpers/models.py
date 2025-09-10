from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ComplianceStatus(str, Enum):
    """Allowed compliance outcomes for a single clause."""

    COMPLIED = "complied"
    NON_COMPLIED = "non-complied"
    NOT_APPLICABLE = "not-applicable"


class ClauseResult(BaseModel):
    """Result of comparing one guideline clause against the document."""

    clause: str = Field(
        ...,
        description="Full clause text starting with its identifier, e.g., 'S 16.1 …' or 'G 16.2 …'.",
    )
    isComplied: ComplianceStatus = Field(
        ..., description="Outcome: 'complied' | 'non-complied' | 'not-applicable'."
    )
    reason: str = Field(
        "",
        description="If isComplied != 'complied', brief concrete reason; otherwise empty string.",
    )


class Summary(BaseModel):
    """
    Roll-up summary listing clause identifiers by outcome.
    """

    complied: List[str] = Field(
        default_factory=list,
        description="Clause IDs that are complied (e.g., ['S 16.1', 'G 16.2']).",
    )
    nonComplied: List[str] = Field(
        default_factory=list,
        description="Clause IDs that are non-complied, in guideline order.",
    )
    notApplicable: List[str] = Field(
        default_factory=list,
        description="Clause IDs that are not-applicable, in guideline order.",
    )


class ClauseComparisonReport(BaseModel):
    """Top-level wrapper for Structured Outputs (object schema with an array field)."""

    model_config = ConfigDict(
        title="ClauseComparisonReport",
        description="Container for per-clause compliance results, in guideline order.",
    )
    results: List[ClauseResult] = Field(
        ...,
        description="Ordered list of per-clause results aligned to the guideline clauses.",
    )
    summary: Optional[Summary] = Field(
        None,
        description="Summary lists of clause IDs by outcome. If omitted, it will be auto-generated from 'results'.",
    )
