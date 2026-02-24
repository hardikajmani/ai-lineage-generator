from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class EdgeStatus(str, Enum):
    AI_SUGGESTED    = "AI_SUGGESTED"
    HUMAN_ATTESTED  = "HUMAN_ATTESTED"
    FLAGGED         = "NEEDS_HUMAN_REVIEW"


class ConfidenceLevel(str, Enum):
    HIGH   = "HIGH"    # Both AST/SQL parser + LLM agree
    MEDIUM = "MEDIUM"  # One parser + LLM confirmed
    LOW    = "LOW"     # LLM only, no static parse evidence


class LineageNode(BaseModel):
    node_id:     str                      # e.g. "transactions", "fees"
    node_type:   str                      # "source" | "intermediate" | "output"
    description: Optional[str] = None    # AI-generated description
    is_high_risk: bool = False            # True if feeds a regulatory report


class LineageEdge(BaseModel):
    edge_id:          str                          # "{source}__{target}__{file}"
    source:           str                          # source table/field name
    target:           str                          # target table/field name
    transformation:   str                          # raw code snippet or SQL fragment
    explanation:      Optional[str] = None         # AI plain-English explanation
    confidence:       ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    source_file:      str                          # which file this edge came from
    line_number:      Optional[int] = None         # line in source file
    status:           EdgeStatus = EdgeStatus.AI_SUGGESTED
    attested_by:      Optional[str] = None         # reviewer name on attestation
    attested_at:      Optional[str] = None         # ISO timestamp


class ParseResult(BaseModel):
    file_name:  str
    file_type:  str          # "python" | "sql"
    edges:      list[LineageEdge]
    nodes:      list[LineageNode]
    parse_errors: list[str] = []
