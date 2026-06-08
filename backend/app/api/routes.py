from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import DATA_DIR, get_settings
from app.core.database import get_db
from app.models.entities import Application, Artifact, Job, Profile, RunLog
from app.schemas.application import ApplicationRead, AutoApplyRequest, AutoApplyResponse, PrepareApplicationResponse
from app.schemas.artifact import ArtifactRead, GenerateArtifactsResponse
from app.schemas.dashboard import DashboardSummary
from app.schemas.job import DiscoveryRequest, DiscoveryResponse, JobListResponse, JobRead, JobStatusUpdate
from app.schemas.outreach import OutreachRead, SendOutreachResponse
from app.schemas.profile import ProfileRead, ProfileUpdate, ResumeParseResult
from app.services.applications import prepare_application
from app.services.artifacts import generate_application_artifacts
from app.services.auto_apply import auto_apply_available_jobs
from app.services.connectors.status import connector_status
from app.services.discovery import get_or_create_profile, run_discovery
from app.services.outreach import create_or_send_outreach
from app.services.resume_parser import build_profile_from_text, parse_resume


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/connectors")
def connectors() -> dict:
    return connector_status()


@router.get("/profile/current", response_model=ProfileRead)
def current_profile(db: Session = Depends(get_db)) -> Profile:
    return get_or_create_profile(db)


@router.put("/profile/current", response_model=ProfileRead)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)) -> Profile:
    profile = get_or_create_profile(db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    profile.profile_json = {**(profile.profile_json or {}), "manual_overrides": payload.model_dump(exclude_none=True)}
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/profile/resume", response_model=ResumeParseResult)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ResumeParseResult:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload a PDF resume.")

    resume_dir = DATA_DIR / "resumes"
    resume_dir.mkdir(parents=True, exist_ok=True)
    target = resume_dir / file.filename
    target.write_bytes(await file.read())
    structured = parse_resume(target)
    profile = get_or_create_profile(db)
    profile.name = structured["name"]
    profile.current_role = structured["current_role"]
    profile.experience_years = structured["experience_years"]
    profile.skills = structured["skills"]
    profile.preferred_roles = structured["preferred_roles"]
    profile.preferred_locations = structured["preferred_locations"]
    profile.resume_text = structured["resume_text"]
    profile.profile_json = structured
    profile.source_resume_path = str(target)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return ResumeParseResult(profile=profile, extracted_keywords=structured.get("keywords", []))


@router.post("/profile/resume/import-local", response_model=ResumeParseResult)
def import_local_resume(path: str = Query(default=str(DATA_DIR / "resumes" / "Amisha_Resume.pdf")), db: Session = Depends(get_db)) -> ResumeParseResult:
    resume_path = Path(path)
    if not resume_path.exists():
        raise HTTPException(status_code=404, detail=f"Resume not found: {resume_path}")
    structured = parse_resume(resume_path)
    profile = get_or_create_profile(db)
    profile.name = structured["name"]
    profile.current_role = structured["current_role"]
    profile.experience_years = structured["experience_years"]
    profile.skills = structured["skills"]
    profile.preferred_roles = structured["preferred_roles"]
    profile.preferred_locations = structured["preferred_locations"]
    profile.resume_text = structured["resume_text"]
    profile.profile_json = structured
    profile.source_resume_path = str(resume_path)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return ResumeParseResult(profile=profile, extracted_keywords=structured.get("keywords", []))


@router.post("/profile/resume/text", response_model=ResumeParseResult)
def parse_resume_text(text: str, db: Session = Depends(get_db)) -> ResumeParseResult:
    structured = build_profile_from_text(text)
    profile = get_or_create_profile(db)
    profile.name = structured["name"]
    profile.current_role = structured["current_role"]
    profile.experience_years = structured["experience_years"]
    profile.skills = structured["skills"]
    profile.preferred_roles = structured["preferred_roles"]
    profile.preferred_locations = structured["preferred_locations"]
    profile.resume_text = text
    profile.profile_json = structured
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return ResumeParseResult(profile=profile, extracted_keywords=structured.get("keywords", []))


@router.post("/jobs/discover", response_model=DiscoveryResponse)
def discover_jobs(payload: DiscoveryRequest, db: Session = Depends(get_db)) -> dict:
    return run_discovery(db, selected_sources=payload.sources, limit=payload.limit)


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    status: str | None = None,
    min_score: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> JobListResponse:
    statement = select(Job)
    count_statement = select(func.count()).select_from(Job)
    if status:
        statement = statement.where(Job.status == status)
        count_statement = count_statement.where(Job.status == status)
    if min_score is not None:
        statement = statement.where(Job.score >= min_score)
        count_statement = count_statement.where(Job.score >= min_score)
    jobs = db.scalars(statement.order_by(Job.score.desc(), Job.discovered_at.desc()).offset(offset).limit(limit)).all()
    total = db.scalar(count_statement) or 0
    return JobListResponse(jobs=list(jobs), total=total)


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)) -> Job:
    return _get_job_or_404(db, job_id)


@router.patch("/jobs/{job_id}/status", response_model=JobRead)
def update_job_status(job_id: int, payload: JobStatusUpdate, db: Session = Depends(get_db)) -> Job:
    job = _get_job_or_404(db, job_id)
    job.status = payload.status
    if payload.notes:
        job.raw = {**(job.raw or {}), "status_note": payload.notes}
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs/{job_id}/artifacts", response_model=list[ArtifactRead])
def list_artifacts(job_id: int, db: Session = Depends(get_db)) -> list[Artifact]:
    _get_job_or_404(db, job_id)
    return list(db.scalars(select(Artifact).where(Artifact.job_id == job_id).order_by(Artifact.created_at.desc())).all())


@router.post("/jobs/{job_id}/generate-artifacts", response_model=GenerateArtifactsResponse)
def generate_artifacts(job_id: int, db: Session = Depends(get_db)) -> GenerateArtifactsResponse:
    profile = get_or_create_profile(db)
    job = _get_job_or_404(db, job_id)
    artifacts = generate_application_artifacts(db, profile, job)
    return GenerateArtifactsResponse(artifacts=artifacts)


@router.post("/jobs/{job_id}/apply/prepare", response_model=PrepareApplicationResponse)
def prepare_job_application(job_id: int, db: Session = Depends(get_db)) -> PrepareApplicationResponse:
    settings = get_settings()
    job = _get_job_or_404(db, job_id)
    application, message = prepare_application(db, job)
    return PrepareApplicationResponse(application=application, dry_run=settings.application_dry_run, message=message)


@router.post("/jobs/{job_id}/outreach/send", response_model=SendOutreachResponse)
def send_outreach(job_id: int, db: Session = Depends(get_db)) -> SendOutreachResponse:
    job = _get_job_or_404(db, job_id)
    outreach, result = create_or_send_outreach(db, job)
    return SendOutreachResponse(outreach=outreach, dry_run=result.dry_run, message=result.message)


@router.get("/outreach", response_model=list[OutreachRead])
def list_outreach(db: Session = Depends(get_db)) -> list:
    from app.models.entities import Outreach

    return list(db.scalars(select(Outreach).order_by(Outreach.updated_at.desc())).all())


@router.get("/applications", response_model=list[ApplicationRead])
def list_applications(db: Session = Depends(get_db)) -> list[Application]:
    return list(db.scalars(select(Application).order_by(Application.updated_at.desc())).all())


@router.post("/applications/auto-apply", response_model=AutoApplyResponse)
def auto_apply_jobs(payload: AutoApplyRequest = AutoApplyRequest(), db: Session = Depends(get_db)) -> dict:
    return auto_apply_available_jobs(db, limit=payload.limit)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    def count_status(status: str) -> int:
        return db.scalar(select(func.count()).select_from(Job).where(Job.status == status)) or 0

    avg_score = db.scalar(select(func.avg(Job.score))) or 0
    settings = get_settings()
    return DashboardSummary(
        new_jobs=count_status("new"),
        applied=count_status("applied"),
        interviewing=count_status("interviewing"),
        rejected=count_status("rejected"),
        offers=count_status("offers"),
        follow_ups=count_status("follow_up"),
        skipped=count_status("skipped"),
        average_score=round(float(avg_score), 1),
        high_score_jobs=db.scalar(
            select(func.count()).select_from(Job).where(Job.score >= settings.min_match_score, Job.status != "skipped")
        )
        or 0,
    )


@router.get("/runs")
def list_runs(db: Session = Depends(get_db)) -> list[dict]:
    runs = db.scalars(select(RunLog).order_by(RunLog.started_at.desc()).limit(50)).all()
    return [
        {
            "id": run.id,
            "kind": run.kind,
            "status": run.status,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "summary": run.summary,
            "error": run.error,
        }
        for run in runs
    ]


def _get_job_or_404(db: Session, job_id: int) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job
