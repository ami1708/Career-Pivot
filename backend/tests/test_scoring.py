from dataclasses import dataclass

from app.services.job_sources.base import JobListing
from app.services.scoring import score_job


@dataclass
class ProfileLike:
    skills: list[str]
    preferred_roles: list[str]
    preferred_locations: list[str]
    experience_years: float


def test_score_job_accepts_strong_backend_match() -> None:
    profile = ProfileLike(
        skills=["Python", "Django", "AngularJS", "Elasticsearch", "Redis", "MySQL", "Celery", "AWS"],
        preferred_roles=["Senior Software Engineer", "Backend Engineer", "SDE-2"],
        preferred_locations=["Remote India", "Bangalore"],
        experience_years=4,
    )
    job = JobListing(
        source="test",
        external_id="1",
        url="https://example.com/job",
        title="Senior Backend Engineer",
        company="Example",
        location="Remote India",
        remote=True,
        description="Python Django Redis MySQL Celery AWS backend role. 4+ years required.",
        skills=["Python", "Django", "Redis", "MySQL", "Celery", "AWS"],
    ).normalized()

    result = score_job(profile, job)

    assert result.score >= 80
    assert "python" in result.breakdown["matched_skills"]
    assert result.breakdown["location_match"] == 20


def test_score_job_rejects_unrelated_location_and_stack() -> None:
    profile = ProfileLike(
        skills=["Python", "Django", "Redis", "MySQL", "AWS"],
        preferred_roles=["Backend Engineer"],
        preferred_locations=["Remote India", "Bangalore"],
        experience_years=4,
    )
    job = JobListing(
        source="test",
        external_id="2",
        url="https://example.com/ios",
        title="iOS Engineer",
        company="Example",
        location="Mumbai",
        remote=False,
        description="Swift UIKit iOS role. 7+ years required.",
        skills=["Swift", "iOS"],
    ).normalized()

    result = score_job(profile, job)

    assert result.score < 80
    assert result.breakdown["skill_overlap"] == 0
    assert result.breakdown["location_match"] == 4


def test_score_job_rejects_non_engineering_titles_even_with_python() -> None:
    profile = ProfileLike(
        skills=["Python", "Django", "Redis", "MySQL", "AWS"],
        preferred_roles=["Backend Engineer", "Software Engineer"],
        preferred_locations=["Remote India"],
        experience_years=4,
    )
    job = JobListing(
        source="test",
        external_id="3",
        url="https://example.com/video",
        title="Senior AI Video Editor",
        company="Example",
        location="Remote",
        remote=True,
        description="Python AI tooling. 3+ years required.",
        skills=["Python"],
    ).normalized()

    result = score_job(profile, job)

    assert result.score < 80
    assert result.breakdown["seniority_match"] == 0
