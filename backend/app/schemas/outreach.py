from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OutreachRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    recruiter_name: str | None
    recruiter_email: str | None
    message: str
    status: str
    sent_at: datetime | None
    last_follow_up_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SendOutreachResponse(BaseModel):
    outreach: OutreachRead
    dry_run: bool
    message: str

