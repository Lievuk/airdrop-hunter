"""Domain types for hunter."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Source(str, Enum):
    GALXE = "galxe"
    LAYER3 = "layer3"
    ZEALY = "zealy"
    TWITTER = "twitter"
    MANUAL = "manual"


class Step(BaseModel):
    order: int
    action: str  # e.g. "navigate", "connect_wallet", "sign_message", "swap"
    target: str  # url or contract or handle
    params: dict = Field(default_factory=dict)
    estimated_seconds: int


class Candidate(BaseModel):
    source: Source
    project_name: str
    campaign_id: str
    title: str
    summary: str
    url: str
    deadline_utc: Optional[datetime] = None
    requires_deposit_usd: float = 0.0
    requires_kyc: bool = False
    chain: Optional[str] = None
    raw: dict = Field(default_factory=dict)


class Score(BaseModel):
    candidate: Candidate
    roi_estimate_usd: float
    effort_minutes: int
    risk_score: float  # 0..10
    sybil_resistance: float  # 0..10, higher = harder to sybil
    confidence: float  # 0..1
    rationale: str
    steps: List[Step] = Field(default_factory=list)
