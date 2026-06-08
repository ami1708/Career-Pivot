from pydantic import BaseModel


class DashboardSummary(BaseModel):
    new_jobs: int
    applied: int
    interviewing: int
    rejected: int
    offers: int
    follow_ups: int
    skipped: int
    average_score: float
    high_score_jobs: int

