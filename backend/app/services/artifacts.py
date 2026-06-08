import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import DATA_DIR
from app.models.entities import Artifact, Job, Profile
from app.services.ai import AIService, job_payload, profile_payload


SYSTEM_PROMPT = (
    "You are an expert technical job application assistant. "
    "Write concise, specific, truthful material. Do not invent experience. "
    "Use the candidate's actual skills and align them to the job."
)


def generate_application_artifacts(db: Session, profile: Profile, job: Job) -> list[Artifact]:
    ai = AIService()
    context = json.dumps({"profile": profile_payload(profile), "job": job_payload(job)}, indent=2)
    prompts = {
        "tailored_resume": (
            "Create a tailored resume version in Markdown. Keep it ATS-friendly, factual, "
            "and emphasize backend/full-stack impact using the provided profile and job.\n\n"
            f"{context}"
        ),
        "cover_letter": (
            "Write a cover letter under 260 words. Make it specific to the company and role. "
            "Avoid generic hype.\n\n"
            f"{context}"
        ),
        "recruiter_message": (
            "Write a concise recruiter outreach message under 120 words. "
            "Mention the strongest role fit and ask for a conversation.\n\n"
            f"{context}"
        ),
        "application_answers": (
            "Generate JSON with answers for common application questions: why_this_role, "
            "relevant_experience, notice_period, work_authorization, salary_expectation_note. "
            "Use null when unknown.\n\n"
            f"{context}"
        ),
    }

    artifacts = []
    for kind, prompt in prompts.items():
        content = ai.generate_text(SYSTEM_PROMPT, prompt) if ai.available() else local_artifact(kind, profile, job)
        file_path = write_artifact_file(job.id, kind, content)
        artifact = Artifact(job_id=job.id, kind=kind, content=content, file_path=str(file_path))
        db.add(artifact)
        artifacts.append(artifact)
    db.commit()
    for artifact in artifacts:
        db.refresh(artifact)
    return artifacts


def write_artifact_file(job_id: int, kind: str, content: str) -> Path:
    output_dir = DATA_DIR / "generated" / f"job-{job_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    extension = "json" if kind == "application_answers" else "md"
    path = output_dir / f"{kind}.{extension}"
    path.write_text(content, encoding="utf-8")
    return path


def local_artifact(kind: str, profile: Profile, job: Job) -> str:
    matched = ", ".join(job.score_breakdown.get("matched_skills", [])[:8]) if job.score_breakdown else ", ".join(job.skills[:8])
    core_skills = ", ".join(profile.skills[:10])
    if kind == "tailored_resume":
        return f"""# {profile.name}

{profile.current_role or "Software Engineer"} with {profile.experience_years:g}+ years of experience building backend and full-stack systems.

## Target Role

{job.title} at {job.company}

## Core Skills

{core_skills}

## Relevant Experience

- Built and maintained Python/Django backend services with production data stores and asynchronous workflows.
- Worked across Redis, MySQL, Elasticsearch, Celery, and AWS-backed systems.
- Contributed to full-stack product work with AngularJS and JavaScript where needed.
- Strong fit for this role based on matched skills: {matched or "backend engineering, APIs, and distributed systems"}.

## Selected Projects

- Redis clone in Python using TCP sockets, concurrency, and persistence concepts.
- Sales and lead-intelligence systems involving scoring, search, and workflow automation.
"""
    if kind == "cover_letter":
        return (
            f"Hi {job.company} team,\n\n"
            f"I am excited to apply for the {job.title} role. I am currently an {profile.current_role or 'SDE-2'} "
            f"with {profile.experience_years:g}+ years of experience across Python, Django, Redis, MySQL, "
            "Elasticsearch, Celery, AWS, and full-stack product work.\n\n"
            f"The role stands out because it maps closely to my backend experience and the stack overlap is strong: "
            f"{matched or ', '.join(job.skills[:6])}. I would bring hands-on ownership of APIs, data-backed systems, "
            "debugging, and pragmatic product delivery.\n\n"
            "Thank you for considering my application.\n\n"
            f"Best,\n{profile.name}\n"
        )
    if kind == "recruiter_message":
        return (
            f"Hi, I am {profile.name}, currently {profile.current_role or 'a software engineer'} with "
            f"{profile.experience_years:g}+ years of experience in Python/Django backend systems, Redis, MySQL, "
            f"Elasticsearch, Celery, and AWS. I found the {job.title} role at {job.company} and the match looks strong "
            f"against my experience ({matched or 'backend systems and APIs'}). Could we connect for a quick conversation?"
        )
    if kind == "application_answers":
        return json.dumps(
            {
                "why_this_role": f"The {job.title} role aligns with my Python/Django backend experience and preferred role path.",
                "relevant_experience": (
                    f"{profile.experience_years:g}+ years as {profile.current_role or 'a software engineer'} working with "
                    f"{core_skills}."
                ),
                "notice_period": None,
                "work_authorization": "Authorized to work in India",
                "salary_expectation_note": None,
            },
            indent=2,
        )
    return ""
