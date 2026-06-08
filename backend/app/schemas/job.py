from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScoreBreakdown(BaseModel):
    skill_overlap: int = 0
    experience_match: int = 0
    location_match: int = 0
    seniority_match: int = 0
    tech_relevance: int = 0
    matched_skills: list[str] = Field(default_factory=list)
    missing_core_skills: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    external_id: str | None
    url: str
    title: str
    company: str
    location: str | None
    remote: bool
    description: str | None
    requirements: list[str]
    skills: list[str]
    seniority: str | None
    employment_type: str | None
    score: int
    score_breakdown: dict[str, Any]
    status: str
    rejection_reason: str | None
    recruiter_name: str | None
    recruiter_email: str | None
    discovered_at: datetime
    applied_at: datetime | None
    updated_at: datetime


class JobListResponse(BaseModel):
    jobs: list[JobRead]
    total: int


class JobStatusUpdate(BaseModel):
    status: str
    notes: str | None = None


class DiscoveryRequest(BaseModel):
    sources: list[str] | None = None
    limit: int = 50


class DiscoveryResponse(BaseModel):
    discovered: int
    accepted: int
    skipped: int
    run_id: int | None = None

