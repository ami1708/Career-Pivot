from datetime import datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Job, Profile, RunLog
from app.services.job_sources.company_pages import CompanyCareerPageSource
from app.services.job_sources.greenhouse import GreenhouseSource
from app.services.job_sources.lever import LeverSource
from app.services.job_sources.playwright_boards import PlaywrightBoardSource
from app.services.job_sources.public_apis import RemotiveSource, RemoteOKSource
from app.services.job_sources.sample import SampleSource
from app.services.scoring import score_job


def build_sources(selected: list[str] | None = None) -> list[Any]:
    settings = get_settings()
    selected_set = {item.lower() for item in selected or []}

    def wants(name: str) -> bool:
        return not selected_set or name in selected_set

    sources: list[Any] = []
    if settings.sample_jobs_enabled and wants("sample"):
        sources.append(SampleSource())
    if settings.public_job_apis_enabled and wants("remotive"):
        sources.append(RemotiveSource())
    if settings.public_job_apis_enabled and wants("remoteok"):
        sources.append(RemoteOKSource())
    greenhouse_companies = settings.greenhouse_companies or settings.default_greenhouse_companies
    lever_companies = settings.lever_companies or settings.default_lever_companies
    if greenhouse_companies and wants("greenhouse"):
        sources.append(GreenhouseSource(greenhouse_companies))
    if lever_companies and wants("lever"):
        sources.append(LeverSource(lever_companies))
    if settings.company_career_urls and wants("company_pages"):
        sources.append(CompanyCareerPageSource(settings.company_career_urls))
    include_browser_boards = settings.browser_job_boards_enabled or bool(selected_set)
    if include_browser_boards and wants("linkedin"):
        sources.append(PlaywrightBoardSource("linkedin", settings.linkedin_search_url))
    if include_browser_boards and wants("wellfound"):
        sources.append(PlaywrightBoardSource("wellfound", settings.wellfound_search_url))
    if include_browser_boards and wants("instahyre"):
        sources.append(PlaywrightBoardSource("instahyre", settings.instahyre_search_url))
    if include_browser_boards and wants("naukri"):
        sources.append(PlaywrightBoardSource("naukri", settings.naukri_search_url))
    if include_browser_boards and wants("indeed"):
        sources.append(PlaywrightBoardSource("indeed", settings.indeed_search_url))
    return sources


def get_or_create_profile(db: Session) -> Profile:
    settings = get_settings()
    profile = db.scalars(select(Profile).order_by(Profile.id.desc())).first()
    if profile:
        return profile
    profile = Profile(
        name=settings.default_name,
        current_role=settings.default_current_role,
        experience_years=settings.default_experience_years,
        skills=settings.default_skills,
        preferred_roles=settings.default_preferred_roles,
        preferred_locations=settings.default_preferred_locations,
        profile_json={
            "source": "defaults",
            "keywords": settings.default_skills,
        },
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def run_discovery(db: Session, selected_sources: list[str] | None = None, limit: int = 50) -> dict[str, Any]:
    settings = get_settings()
    profile = get_or_create_profile(db)
    run = RunLog(kind="discovery", status="running", started_at=datetime.utcnow())
    db.add(run)
    db.commit()
    db.refresh(run)

    discovered = 0
    accepted = 0
    skipped = 0
    errors: list[str] = []
    source_stats: dict[str, dict[str, Any]] = {}

    try:
        sources = build_sources(selected_sources)
        if not sources:
            errors.append("No discovery sources are enabled. Turn on public APIs, configure company sources, or select a browser board.")
        queries = profile.preferred_roles[:3] or ["Backend Engineer"]
        locations = profile.preferred_locations[:3] or ["Remote India"]
        per_source_limit = max(1, limit // max(len(sources), 1))
        for source in sources:
            source_key = _source_key(source)
            stats = source_stats.setdefault(
                source_key,
                {"attempts": 0, "discovered": 0, "accepted": 0, "skipped": 0, "errors": []},
            )
            source_queries = queries[:1] if isinstance(source, PlaywrightBoardSource) else queries
            source_locations = locations[:1] if isinstance(source, PlaywrightBoardSource) else locations
            for query in source_queries:
                for location in source_locations:
                    stats["attempts"] += 1
                    try:
                        listings = source.fetch(query=query, location=location, limit=per_source_limit)
                    except Exception as exc:  # External job sites are noisy; log and keep moving.
                        message = f"{source_key}: {exc}"
                        errors.append(message)
                        stats["errors"].append(str(exc))
                        continue
                    stats["discovered"] += len(listings)
                    for listing in listings:
                        discovered += 1
                        job = upsert_job(db, profile, listing)
                        if job.score >= settings.min_match_score:
                            accepted += 1
                            stats["accepted"] += 1
                        else:
                            skipped += 1
                            stats["skipped"] += 1
        rescore_existing_jobs(db, profile)
        run.status = "success"
        run.summary = {
            "discovered": discovered,
            "accepted": accepted,
            "skipped": skipped,
            "errors": errors,
            "sources": source_stats,
        }
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)
        run.summary = {
            "discovered": discovered,
            "accepted": accepted,
            "skipped": skipped,
            "errors": errors,
            "sources": source_stats,
        }
        raise
    finally:
        run.finished_at = datetime.utcnow()
        db.add(run)
        db.commit()

    return {"discovered": discovered, "accepted": accepted, "skipped": skipped, "run_id": run.id, "errors": errors, "sources": source_stats}


def rescore_existing_jobs(db: Session, profile: Profile) -> None:
    settings = get_settings()
    jobs = db.scalars(select(Job)).all()
    for job in jobs:
        score_result = score_job(profile, job)
        job.score = score_result.score
        job.score_breakdown = score_result.breakdown
        if job.source == "sample":
            job.status = "skipped"
            job.rejection_reason = "Demo job hidden after live discovery was enabled."
        elif job.status in {"new", "skipped"}:
            if _was_auto_apply_skipped(job):
                job.status = "skipped"
            elif score_result.score >= settings.min_match_score:
                job.status = "new"
                job.rejection_reason = None
            else:
                job.status = "skipped"
                job.rejection_reason = f"Score {score_result.score} is below threshold {settings.min_match_score}."
        db.add(job)
    db.commit()


def upsert_job(db: Session, profile: Profile, listing: Any) -> Job:
    settings = get_settings()
    existing = db.scalars(
        select(Job).where(
            or_(
                Job.url == listing.url,
                (Job.source == listing.source) & (Job.external_id == listing.external_id),
            )
        )
    ).first()
    score_result = score_job(profile, listing)
    status = "new" if score_result.score >= settings.min_match_score else "skipped"
    rejection_reason = None if status == "new" else f"Score {score_result.score} is below threshold {settings.min_match_score}."

    if existing:
        existing.title = listing.title
        existing.company = listing.company
        existing.location = listing.location
        existing.remote = listing.remote
        existing.description = listing.description
        existing.requirements = listing.requirements
        existing.skills = listing.skills
        existing.seniority = listing.seniority
        existing.employment_type = listing.employment_type
        existing.score = score_result.score
        existing.score_breakdown = score_result.breakdown
        existing.recruiter_name = listing.recruiter_name
        existing.recruiter_email = listing.recruiter_email
        existing.raw = listing.raw
        if existing.status in {"new", "skipped"}:
            if _was_auto_apply_skipped(existing):
                existing.status = "skipped"
            else:
                existing.status = status
                existing.rejection_reason = rejection_reason
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    job = Job(
        source=listing.source,
        external_id=listing.external_id,
        url=listing.url,
        title=listing.title,
        company=listing.company,
        location=listing.location,
        remote=listing.remote,
        description=listing.description,
        requirements=listing.requirements,
        skills=listing.skills,
        seniority=listing.seniority,
        employment_type=listing.employment_type,
        score=score_result.score,
        score_breakdown=score_result.breakdown,
        status=status,
        rejection_reason=rejection_reason,
        recruiter_name=listing.recruiter_name,
        recruiter_email=listing.recruiter_email,
        raw=listing.raw,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _was_auto_apply_skipped(job: Job) -> bool:
    last_attempt = (job.raw or {}).get("last_auto_apply", {})
    return last_attempt.get("status") == "skipped" and (job.rejection_reason or "").startswith("Auto-apply skipped")


def _source_key(source: Any) -> str:
    name = getattr(source, "name", source.__class__.__name__)
    board = getattr(source, "board", None)
    return f"{name}:{board}" if board else str(name)
