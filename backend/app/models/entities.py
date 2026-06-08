from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_role: Mapped[str | None] = mapped_column(String(255))
    experience_years: Mapped[float] = mapped_column(Float, default=0)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    resume_text: Mapped[str | None] = mapped_column(Text)
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source_resume_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_jobs_source_external_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255))
    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    seniority: Mapped[str | None] = mapped_column(String(100))
    employment_type: Mapped[str | None] = mapped_column(String(100))
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="new", index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    recruiter_name: Mapped[str | None] = mapped_column(String(255))
    recruiter_email: Mapped[str | None] = mapped_column(String(255))
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    artifacts: Mapped[list["Artifact"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    outreach_items: Mapped[list["Outreach"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    job: Mapped[Job] = relationship(back_populates="artifacts")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="prepared", index=True)
    answers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    resume_artifact_id: Mapped[int | None] = mapped_column(ForeignKey("artifacts.id"))
    cover_letter_artifact_id: Mapped[int | None] = mapped_column(ForeignKey("artifacts.id"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    job: Mapped[Job] = relationship(back_populates="applications")


class Outreach(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    recruiter_name: Mapped[str | None] = mapped_column(String(255))
    recruiter_email: Mapped[str | None] = mapped_column(String(255), index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    job: Mapped[Job] = relationship(back_populates="outreach_items")


class RunLog(Base):
    __tablename__ = "run_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kind: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)

