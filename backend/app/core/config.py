from functools import lru_cache
import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR if (BACKEND_DIR / "data").exists() else BACKEND_DIR.parent
IS_VERCEL = os.getenv("VERCEL") == "1"
DATA_DIR = Path(os.getenv("CAREER_PIVOT_DATA_DIR", "/tmp/career-pivot/data" if IS_VERCEL else str(PROJECT_DIR / "data")))
DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:////tmp/career-pivot/job_agent.db" if IS_VERCEL else f"sqlite:///{BACKEND_DIR / 'job_agent.db'}",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    backend_cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    database_url: str = DEFAULT_DATABASE_URL

    min_match_score: int = 80
    preferred_salary_min_lpa: float | None = None
    preferred_salary_max_lpa: float | None = None
    salary_usd_to_inr: float = 83.0
    auto_apply_require_salary: bool = True
    auto_apply_min_matched_skills: int = 3
    big_company_names: list[str] = []
    scheduler_timezone: str = "Asia/Kolkata"
    daily_discovery_hour: int = 8
    daily_discovery_minute: int = 0
    run_scheduler: bool = False
    daily_auto_apply_enabled: bool = True
    daily_auto_apply_limit: int = 10
    auto_discover_on_empty: bool = IS_VERCEL and not os.getenv("DATABASE_URL")
    sample_jobs_enabled: bool = False
    public_job_apis_enabled: bool = True
    browser_job_boards_enabled: bool = False

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"
    openai_reasoning_effort: str = "low"

    greenhouse_companies: list[str] = []
    lever_companies: list[str] = []
    company_career_urls: list[str] = []
    default_greenhouse_companies: list[str] = [
        "airbnb",
        "stripe",
        "databricks",
        "mongodb",
        "hashicorp",
    ]
    default_lever_companies: list[str] = [
        "postman",
        "netlify",
        "vercel",
    ]

    playwright_headless: bool = True
    linkedin_search_url: str = "https://www.linkedin.com/jobs/search/?keywords={query}&location={location}"
    wellfound_search_url: str = "https://wellfound.com/jobs"
    instahyre_search_url: str = "https://www.instahyre.com/search-jobs/"
    naukri_search_url: str = "https://www.naukri.com/{query}-jobs-in-{location}"
    indeed_search_url: str = "https://in.indeed.com/jobs?q={query}&l={location}"

    auto_apply_enabled: bool = False
    require_application_approval: bool = True
    application_dry_run: bool = True

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    outreach_dry_run: bool = True

    google_service_account_json: str | None = None
    google_sheets_spreadsheet_id: str | None = None
    google_calendar_id: str = "primary"

    default_name: str = "Amisha Negi"
    default_current_role: str = "SDE-2"
    default_experience_years: float = 4.0
    default_skills: list[str] = [
        "Python",
        "Django",
        "AngularJS",
        "Elasticsearch",
        "Redis",
        "MySQL",
        "Celery",
        "AWS",
    ]
    default_preferred_roles: list[str] = [
        "Senior Software Engineer",
        "Backend Engineer",
        "Software Engineer",
        "Full Stack Engineer",
        "SDE-2",
    ]
    default_preferred_locations: list[str] = [
        "Remote India",
        "Delhi NCR",
        "Bangalore",
        "Hyderabad",
        "Pune",
    ]

    @field_validator(
        "backend_cors_origins",
        "greenhouse_companies",
        "lever_companies",
        "company_career_urls",
        "big_company_names",
        "default_greenhouse_companies",
        "default_lever_companies",
        mode="before",
    )
    @classmethod
    def split_csv(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
