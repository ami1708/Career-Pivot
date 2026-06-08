import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Application, Artifact, Job


def prepare_application(db: Session, job: Job) -> tuple[Application, str]:
    settings = get_settings()
    artifacts = db.scalars(select(Artifact).where(Artifact.job_id == job.id).order_by(Artifact.created_at.asc())).all()
    by_kind = {artifact.kind: artifact for artifact in artifacts}
    answers = _parse_answers(by_kind.get("application_answers"))
    application = db.scalars(select(Application).where(Application.job_id == job.id)).first()
    if not application:
        application = Application(job_id=job.id)
    application.status = "prepared"
    application.answers = answers
    application.resume_artifact_id = by_kind.get("tailored_resume").id if by_kind.get("tailored_resume") else None
    application.cover_letter_artifact_id = by_kind.get("cover_letter").id if by_kind.get("cover_letter") else None
    application.notes = "Prepared by Career Pivot."
    db.add(application)
    db.commit()
    db.refresh(application)

    if settings.application_dry_run or settings.require_application_approval or not settings.auto_apply_enabled:
        return application, "Application package prepared. Browser submission is in dry-run/approval mode."

    return application, "Application package prepared. The auto-apply runner handles browser submission."


def _parse_answers(artifact: Artifact | None) -> dict:
    if not artifact:
        return {}
    try:
        return json.loads(artifact.content)
    except json.JSONDecodeError:
        return {"raw": artifact.content}
