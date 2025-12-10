"""Pydantic schemas for the BLUX-cA API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReflectRequest(BaseModel):
    text: str = Field(..., description="User supplied text for reflection")
    depth: int = Field(3, ge=1, le=10)


class ReflectResponse(BaseModel):
    summary: str
    chain: list[str]


class VerdictResponse(BaseModel):
    decision: str
    score: float
    doctrine_refs: list[str]
    reason: str
