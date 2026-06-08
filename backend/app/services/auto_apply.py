from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Application, Artifact, Job, Profile, RunLog
from app.services.applications import prepare_application
from app.services.artifacts import generate_application_artifacts
from app.services.browser_automation import prefill_application_form
from app.services.discovery import get_or_create_profile
from app.services.job_fit import company_size_rank, evaluate_auto_apply_fit


REQUIRED_ARTIFACT_KINDS = {"tailored_resume", "cover_letter", "application_answers"}
AUTO_SUBMIT_URL_MARKERS = (
    "greenhouse.io",
    "job-boards.greenhouse.io",
    "boards.greenhouse.io",
    "jobs.lever.co",
    "lever.co",
    "ashbyhq.com",
    "workable.com",
    "breezy.hr",
    "smartrecruiters.com",
)


def auto_apply_available_jobs(db: Session, limit: int = 10) -> dict[str, Any]:
    settings = get_settings()
    profile = get_or_create_profile(db)
    run = RunLog(kind="auto_apply", status="running", started_at=datetime.utcnow())
    db.add(run)
    db.commit()
    db.refresh(run)

    can_submit = settings.auto_apply_enabled and not settings.application_dry_run and not settings.require_application_approval
    results: list[dict[str, Any]] = []
    counters = {"processed": 0, "submitted": 0, "prepared": 0, "skipped": 0, "failed": 0}

    candidate_limit = max(limit * 5, limit)
    candidates = db.scalars(
        select(Job)
        .where(Job.status == "new", Job.score >= settings.min_match_score)
        .order_by(Job.score.desc(), Job.discovered_at.desc())
        .limit(candidate_limit)
    ).all()
    jobs = sorted(candidates, key=lambda item: (company_size_rank(item, settings), item.score, item.discovered_at), reverse=True)[:limit]

    try:
        for job in jobs:
            counters["processed"] += 1
            try:
                fit = evaluate_auto_apply_fit(job, profile, settings)
                _store_fit_signals(job, fit.signals)
                if fit.reason:
                    job.status = "skipped"
                    job.rejection_reason = fit.reason
                    _record_attempt(job, "skipped", fit.reason, run.id)
                    db.add(job)
                    db.commit()
                    counters["skipped"] += 1
                    results.append(_result(job, None, "skipped", fit.reason, dry_run=not can_submit))
                    continue

                _ensure_application_artifacts(db, profile, job)
                application, _ = prepare_application(db, job)

                if not can_submit:
                    message = (
                        "Prepared automatically. Final browser submission is disabled until "
                        "AUTO_APPLY_ENABLED=true, APPLICATION_DRY_RUN=false, and REQUIRE_APPLICATION_APPROVAL=false."
                    )
                    application.status = "prepared"
                    application.notes = message
                    _record_attempt(job, "prepared", message, run.id)
                    db.add_all([job, application])
                    db.commit()
                    counters["prepared"] += 1
                    results.append(_result(job, application, "prepared", message, dry_run=True))
                    continue

                if not _is_auto_submit_supported(job):
                    message = "Application package prepared, but this job source needs manual review before browser submit."
                    application.status = "needs_review"
                    application.notes = message
                    _record_attempt(job, "needs_review", message, run.id)
                    db.add_all([job, application])
                    db.commit()
                    counters["prepared"] += 1
                    results.append(_result(job, application, "needs_review", message, dry_run=False))
                    continue

                browser_result = prefill_application_form(job.url, application.answers or {}, _resume_path(profile))
                if browser_result.submitted:
                    message = browser_result.message
                    job.status = "applied"
                    job.applied_at = datetime.utcnow()
                    application.status = "submitted"
                    application.submitted_at = datetime.utcnow()
                    application.notes = message
                    _record_attempt(job, "submitted", message, run.id)
                    db.add_all([job, application])
                    db.commit()
                    counters["submitted"] += 1
                    results.append(_result(job, application, "submitted", message, submitted=True, dry_run=False))
                else:
                    message = browser_result.message
                    application.status = "needs_review"
                    application.notes = message
                    _record_attempt(job, "needs_review", message, run.id)
                    db.add_all([job, application])
                    db.commit()
                    counters["prepared"] += 1
                    results.append(_result(job, application, "needs_review", message, dry_run=browser_result.dry_run))
            except Exception as exc:  # Browser/application sites are external and noisy; keep the batch moving.
                db.rollback()
                message = f"Auto-apply failed: {exc}"
                _record_attempt(job, "failed", message, run.id)
                db.add(job)
                db.commit()
                counters["failed"] += 1
                results.append(_result(job, None, "failed", message, dry_run=not can_submit))

        run.status = "success"
        run.summary = {**counters, "dry_run": not can_submit, "results": results}
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)
        run.summary = {**counters, "dry_run": not can_submit, "results": results}
        raise
    finally:
        run.finished_at = datetime.utcnow()
        db.add(run)
        db.commit()

    return {**counters, "dry_run": not can_submit, "run_id": run.id, "results": results}


def _ensure_application_artifacts(db: Session, profile: Profile, job: Job) -> None:
    by_kind = _artifacts_by_kind(db, job)
    if REQUIRED_ARTIFACT_KINDS.issubset(by_kind):
        return
    generate_application_artifacts(db, profile, job)


def _artifacts_by_kind(db: Session, job: Job) -> dict[str, Artifact]:
    artifacts = db.scalars(select(Artifact).where(Artifact.job_id == job.id).order_by(Artifact.created_at.asc())).all()
    return {artifact.kind: artifact for artifact in artifacts}


def _is_auto_submit_supported(job: Job) -> bool:
    url = job.url.lower()
    return job.source in {"greenhouse", "lever"} or any(marker in url for marker in AUTO_SUBMIT_URL_MARKERS)


def _resume_path(profile: Profile) -> str | None:
    if not profile.source_resume_path:
        return None
    path = Path(profile.source_resume_path).expanduser()
    return str(path) if path.exists() else None


def _store_fit_signals(job: Job, signals: dict[str, Any]) -> None:
    raw = dict(job.raw or {})
    raw["fit_signals"] = signals
    job.raw = raw


def _record_attempt(job: Job, status: str, message: str, run_id: int | None) -> None:
    entry = {
        "status": status,
        "message": message,
        "run_id": run_id,
        "attempted_at": datetime.utcnow().isoformat(),
    }
    raw = dict(job.raw or {})
    history = list(raw.get("auto_apply_history", []))[-9:]
    raw["last_auto_apply"] = entry
    raw["auto_apply_history"] = [*history, entry]
    job.raw = raw


def _result(
    job: Job,
    application: Application | None,
    status: str,
    message: str,
    *,
    submitted: bool = False,
    dry_run: bool = True,
) -> dict[str, Any]:
    return {
        "job_id": job.id,
        "title": job.title,
        "company": job.company,
        "source": job.source,
        "score": job.score,
        "application_id": application.id if application else None,
        "status": status,
        "submitted": submitted,
        "dry_run": dry_run,
        "message": message,
    }
