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

    clauseId: str = Field(
        ...,
        description="Identifier of the clause, e.g., 'S 16.1' or 'G 16.2'.",
    )
    clause: str = Field(
        ...,
        description="Full clause text starting with its identifier, e.g., 'S 16.1 …' or 'G 16.2 …'.",
    )
    isComplied: ComplianceStatus = Field(
        ..., description="Outcome: 'complied' | 'non-complied' | 'not-applicable'."
    )
    reason: str = Field(
        "",
        description="If isComplied = 'non-complied', detailed reasoning of what is missing/contradicted/not in required order (point out every sentence or paragraph), or if 'complied', a brief description of why it is complied (reference where the document aligns), or if 'not-applicable', state why it cannot be assessed or why it does not apply.",
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="If isComplied = 'non-complied', clear and actionable suggestions on how the document can be modified to comply",
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
    # summary: Optional[Summary] = Field(
    #     None,
    #     description="Summary lists of clause IDs by outcome. If omitted, it will be auto-generated from 'results'.",
    # )


class FinalClauseResult(BaseModel):
    snippet: str = Field(
        ...,
        description="Text snippet from the document relevant to the clause.",
    )
    isComplied: ComplianceStatus = Field(
        ..., description="Outcome: 'complied' | 'non-complied' | 'not-applicable'."
    )
    reason: str = Field(
        "",
        description="If isComplied = 'non-complied', detailed reasoning of what is missing/contradicted/not in required order (point out every sentence or paragraph), or if 'complied', a brief description of why it is complied (reference where the document aligns), or if 'not-applicable', state why it cannot be assessed or why it does not apply.",
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="If isComplied = 'non-complied', clear and actionable suggestions on how the document can be modified to comply",
    )


class FinalComparisonReport(BaseModel):
    clauseId: str = Field(
        ...,
        description="Identifier of the clause, e.g., 'S 16.1' or 'G 16.2'.",
    )
    clause: str = Field(
        ...,
        description="Full clause text starting with its identifier, e.g., 'S 16.1 …' or 'G 16.2 …'.",
    )
    results: List[FinalClauseResult] = Field(
        ...,
        description="List of comparison results for the clause.",
    )


class FinalComparisonResult(BaseModel):
    section: str = Field(
        ...,
        description="Title of the guideline section.",
    )
    comparisons: List[FinalComparisonReport] = Field(
        ...,
        description="List of clause comparison reports for the section.",
    )
