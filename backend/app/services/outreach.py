from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Artifact, Job, Outreach
from app.services.connectors.email import EmailConnector, EmailResult


def create_or_send_outreach(db: Session, job: Job) -> tuple[Outreach, EmailResult]:
    recruiter_message = db.scalars(
        select(Artifact).where(Artifact.job_id == job.id, Artifact.kind == "recruiter_message").order_by(Artifact.id.desc())
    ).first()
    message = recruiter_message.content if recruiter_message else _fallback_message(job)
    outreach = db.scalars(select(Outreach).where(Outreach.job_id == job.id)).first()
    if not outreach:
        outreach = Outreach(job_id=job.id, recruiter_name=job.recruiter_name, recruiter_email=job.recruiter_email, message=message)
    else:
        outreach.message = message
        outreach.recruiter_name = job.recruiter_name
        outreach.recruiter_email = job.recruiter_email

    if not job.recruiter_email:
        outreach.status = "missing_contact"
        db.add(outreach)
        db.commit()
        db.refresh(outreach)
        return outreach, EmailResult(sent=False, dry_run=True, message="No recruiter email found for this job.")

    resume = db.scalars(
        select(Artifact).where(Artifact.job_id == job.id, Artifact.kind == "tailored_resume").order_by(Artifact.id.desc())
    ).first()
    result = EmailConnector().send(
        to_email=job.recruiter_email,
        subject=f"Interest in {job.title} at {job.company}",
        body=message,
        attachment_path=resume.file_path if resume else None,
    )
    outreach.status = "sent" if result.sent else "draft"
    outreach.sent_at = datetime.utcnow() if result.sent else None
    db.add(outreach)
    db.commit()
    db.refresh(outreach)
    return outreach, result


def _fallback_message(job: Job) -> str:
    return (
        f"Hi, I am interested in the {job.title} role at {job.company}. "
        "My background is in Python, Django, distributed backend systems, Redis, MySQL, Elasticsearch, Celery, and AWS. "
        "I would love to discuss whether my experience is a fit."
    )

