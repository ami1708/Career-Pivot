from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProfileBase(BaseModel):
    name: str
    current_role: str | None = None
    experience_years: float
    skills: list[str]
    preferred_roles: list[str]
    preferred_locations: list[str]


class ProfileUpdate(BaseModel):
    name: str | None = None
    current_role: str | None = None
    experience_years: float | None = None
    skills: list[str] | None = None
    preferred_roles: list[str] | None = None
    preferred_locations: list[str] | None = None


class ProfileRead(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_text: str | None = None
    profile_json: dict[str, Any]
    source_resume_path: str | None = None
    created_at: datetime
    updated_at: datetime


class ResumeParseResult(BaseModel):
    profile: ProfileRead
    extracted_keywords: list[str]
