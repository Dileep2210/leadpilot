from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


class LeadRequest(BaseModel):
    raw_text: str = Field(..., min_length=5, max_length=6000)


class StructuredLead(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    contact: Optional[str] = None
    need: Optional[str] = None
    urgency: Literal["hot", "warm", "cold", "unknown"] = "unknown"
    budget_hint: Optional[str] = None


class SheetResult(BaseModel):
    mode: Literal["live", "mock"]
    row_number: Optional[int] = None
    sheet_url: Optional[str] = None
    note: Optional[str] = None


class SlackResult(BaseModel):
    mode: Literal["live", "mock"]
    posted: bool
    message: str
    note: Optional[str] = None


class LeadResult(BaseModel):
    structured: StructuredLead
    sheet: SheetResult
    draft_reply: str
    slack: SlackResult
