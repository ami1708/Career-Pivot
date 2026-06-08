from types import SimpleNamespace

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.entities import Application, Artifact, Job, Profile
from app.services.auto_apply import auto_apply_available_jobs
from app.services.browser_automation import PrefillResult


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _settings(**overrides):
    defaults = {
        "min_match_score": 80,
        "preferred_salary_min_lpa": 20,
        "preferred_salary_max_lpa": 60,
        "salary_usd_to_inr": 83,
        "auto_apply_require_salary": False,
        "auto_apply_min_matched_skills": 3,
        "big_company_names": [],
        "auto_apply_enabled": False,
        "application_dry_run": True,
        "require_application_approval": True,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _profile(db):
    profile = Profile(
        name="Amisha Negi",
        current_role="SDE-2",
        experience_years=4,
        skills=["Python", "Django", "Redis"],
        preferred_roles=["Backend Engineer"],
        preferred_locations=["Remote India"],
        profile_json={},
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _job(
    db,
    *,
    score=91,
    source="greenhouse",
    url="https://boards.greenhouse.io/acme/jobs/1",
    company="Acme",
    description="Python Django Redis AWS",
):
    job = Job(
        source=source,
        external_id=url.rsplit("/", 1)[-1],
        url=url,
        title="Senior Backend Engineer",
        company=company,
        location="Remote India",
        remote=True,
        description=description,
        requirements=[],
        skills=["Python", "Django", "Redis"],
        seniority="senior",
        employment_type="full-time",
        score=score,
        score_breakdown={"matched_skills": ["python", "django", "redis"]},
        status="new",
        raw={},
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _fake_generate_artifacts(db, profile, job):
    artifacts = [
        Artifact(job_id=job.id, kind="tailored_resume", content="# Resume"),
        Artifact(job_id=job.id, kind="cover_letter", content="Hello"),
        Artifact(job_id=job.id, kind="application_answers", content='{"why_this_role": "Strong fit"}'),
    ]
    db.add_all(artifacts)
    db.commit()
    for artifact in artifacts:
        db.refresh(artifact)
    return artifacts


def test_auto_apply_safe_mode_prepares_only(monkeypatch) -> None:
    db = _session()
    _profile(db)
    high_score_job = _job(db)
    _job(db, score=70, url="https://boards.greenhouse.io/acme/jobs/2")
    settings = _settings()
    monkeypatch.setattr("app.services.auto_apply.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.applications.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.auto_apply.generate_application_artifacts", _fake_generate_artifacts)

    response = auto_apply_available_jobs(db, limit=10)

    assert response["processed"] == 1
    assert response["prepared"] == 1
    assert response["submitted"] == 0
    assert response["dry_run"] is True
    application = db.scalars(select(Application).where(Application.job_id == high_score_job.id)).one()
    assert application.status == "prepared"
    assert db.get(Job, high_score_job.id).status == "new"


def test_auto_apply_live_mode_marks_applied_after_browser_submit(monkeypatch) -> None:
    db = _session()
    _profile(db)
    job = _job(db)
    settings = _settings(auto_apply_enabled=True, application_dry_run=False, require_application_approval=False)
    monkeypatch.setattr("app.services.auto_apply.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.applications.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.auto_apply.generate_application_artifacts", _fake_generate_artifacts)
    monkeypatch.setattr(
        "app.services.auto_apply.prefill_application_form",
        lambda url, answers, resume_path=None: PrefillResult(url, False, True, "Form submitted."),
    )

    response = auto_apply_available_jobs(db, limit=10)

    assert response["processed"] == 1
    assert response["submitted"] == 1
    refreshed_job = db.get(Job, job.id)
    application = db.scalars(select(Application).where(Application.job_id == job.id)).one()
    assert refreshed_job.status == "applied"
    assert refreshed_job.applied_at is not None
    assert application.status == "submitted"
    assert application.submitted_at is not None


def test_auto_apply_skips_when_salary_bracket_is_missing(monkeypatch) -> None:
    db = _session()
    _profile(db)
    job = _job(db, description="Python Django Redis AWS. Salary 30-40 LPA.")
    settings = _settings(preferred_salary_min_lpa=None, preferred_salary_max_lpa=None, auto_apply_require_salary=True)
    monkeypatch.setattr("app.services.auto_apply.get_settings", lambda: settings)

    response = auto_apply_available_jobs(db, limit=10)

    assert response["skipped"] == 1
    refreshed_job = db.get(Job, job.id)
    assert refreshed_job.status == "skipped"
    assert "salary bracket is not configured" in refreshed_job.rejection_reason


def test_auto_apply_skips_salary_below_bracket(monkeypatch) -> None:
    db = _session()
    _profile(db)
    job = _job(db, description="Python Django Redis AWS. Salary 15-20 LPA.")
    settings = _settings(preferred_salary_min_lpa=30, preferred_salary_max_lpa=60, auto_apply_require_salary=True)
    monkeypatch.setattr("app.services.auto_apply.get_settings", lambda: settings)

    response = auto_apply_available_jobs(db, limit=10)

    assert response["skipped"] == 1
    refreshed_job = db.get(Job, job.id)
    assert refreshed_job.status == "skipped"
    assert "below desired minimum" in refreshed_job.rejection_reason


def test_auto_apply_prefers_big_company_when_eligible(monkeypatch) -> None:
    db = _session()
    _profile(db)
    _job(
        db,
        score=95,
        company="SmallCo",
        url="https://boards.greenhouse.io/smallco/jobs/1",
        description="Python Django Redis AWS. Salary 35-45 LPA.",
    )
    big_job = _job(
        db,
        score=82,
        company="Airbnb",
        url="https://boards.greenhouse.io/airbnb/jobs/2",
        description="Python Django Redis AWS. Salary 35-45 LPA.",
    )
    settings = _settings(
        auto_apply_enabled=True,
        application_dry_run=False,
        require_application_approval=False,
        auto_apply_require_salary=True,
        big_company_names=["airbnb"],
    )
    monkeypatch.setattr("app.services.auto_apply.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.applications.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.auto_apply.generate_application_artifacts", _fake_generate_artifacts)
    monkeypatch.setattr(
        "app.services.auto_apply.prefill_application_form",
        lambda url, answers, resume_path=None: PrefillResult(url, False, True, "Form submitted."),
    )

    response = auto_apply_available_jobs(db, limit=1)

    assert response["submitted"] == 1
    assert response["results"][0]["job_id"] == big_job.id
