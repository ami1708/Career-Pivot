from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    status: str
    answers: dict[str, Any]
    resume_artifact_id: int | None
    cover_letter_artifact_id: int | None
    submitted_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PrepareApplicationResponse(BaseModel):
    application: ApplicationRead
    dry_run: bool
    message: str
    job_url: str
    answers: dict[str, Any]
    resume_path: str | None = None


class AutoApplyRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)


class AutoApplyJobResult(BaseModel):
    job_id: int
    title: str
    company: str
    source: str
    score: int
    application_id: int | None = None
    status: str
    submitted: bool
    dry_run: bool
    message: str


class AutoApplyResponse(BaseModel):
    processed: int
    submitted: int
    prepared: int
    skipped: int
    failed: int
    dry_run: bool
    run_id: int | None
    results: list[AutoApplyJobResult]
