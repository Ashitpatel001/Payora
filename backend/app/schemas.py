"""Strict Pydantic schemas for LLM output validation.

Every field that the LLM produces is constrained to known-good values.
If the LLM hallucinates an unknown enum member, Pydantic raises
ValidationError and the system falls back to deterministic rules.
"""
from enum import Enum
from pydantic import BaseModel, Field


class RootCauseCategory(str, Enum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    BANK_TIMEOUT = "bank_timeout"
    EXPIRED_MANDATE = "expired_mandate"
    RISK_DECLINE = "risk_decline"
    INVOICE_OVERDUE = "invoice_overdue"
    STRATEGIC_DEFAULTER = "strategic_defaulter"
    UNKNOWN = "unknown"


class RiskQuadrant(str, Enum):
    TECHNICAL = "technical"
    HARDSHIP = "hardship"
    SERIAL_NON_PAYER = "serial_non_payer"
    HIGH_VALUE = "high_value"


class DiagnosisResult(BaseModel):
    """Validated LLM diagnosis output.

    confidence is clamped to [0.0, 1.0].
    root_cause_category and risk_quadrant MUST be one of the
    enum values — anything else raises ValidationError.
    """
    root_cause_category: RootCauseCategory
    risk_quadrant: RiskQuadrant
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1)
