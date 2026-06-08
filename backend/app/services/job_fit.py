from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.models.entities import Job, Profile
from app.services.text import normalize_token


PREFERRED_TITLE_TERMS = ("software engineer", "backend engineer", "full stack", "full-stack", "sde", "python engineer")
BLOCKED_TITLE_TERMS = ("engineering manager", "manager,", "director", "head of", "staff engineer", "intern")
BLOCKED_LOCATION_TERMS = (
    "beijing",
    "china",
    "united states",
    "usa",
    "u.s.",
    "us -",
    "us remote",
    "north america",
    "canada",
    "registered entity",
)
INDIA_LOCATION_TERMS = (
    "india",
    "remote india",
    "bangalore",
    "bengaluru",
    "delhi",
    "ncr",
    "gurgaon",
    "gurugram",
    "noida",
    "hyderabad",
    "pune",
    "worldwide",
    "anywhere",
    "global",
)
DEFAULT_BIG_COMPANY_NAMES = {
    "airbnb",
    "amazon",
    "atlassian",
    "databricks",
    "google",
    "hashicorp",
    "meta",
    "microsoft",
    "mongodb",
    "netflix",
    "postman",
    "salesforce",
    "stripe",
    "uber",
    "vercel",
    "walmart",
}


@dataclass(frozen=True)
class SalaryRange:
    min_lpa: float | None
    max_lpa: float | None
    source: str


@dataclass(frozen=True)
class FitDecision:
    ok: bool
    reason: str | None = None
    signals: dict[str, Any] = field(default_factory=dict)


def evaluate_auto_apply_fit(job: Job, profile: Profile, settings: Any) -> FitDecision:
    title = job.title.lower()
    location_text = f"{job.location or ''} {job.description or ''}".lower()
    matched_skills = _matched_skills(job)
    min_matched_skills = int(getattr(settings, "auto_apply_min_matched_skills", 3))
    salary = extract_salary_lpa(job, settings)
    required_years = extract_required_years(job.description or "")
    company_rank = company_size_rank(job, settings)
    signals = {
        "matched_skills": matched_skills,
        "matched_skill_count": len(matched_skills),
        "required_years": required_years,
        "profile_years": profile.experience_years,
        "salary_lpa": None if salary is None else {"min": salary.min_lpa, "max": salary.max_lpa, "source": salary.source},
        "company_size_rank": company_rank,
    }

    if any(term in title for term in BLOCKED_TITLE_TERMS):
        return FitDecision(False, "Auto-apply skipped: title appears outside preferred IC software/backend/full-stack roles.", signals)
    if not any(term in title for term in PREFERRED_TITLE_TERMS):
        return FitDecision(False, "Auto-apply skipped: title does not match preferred software/backend/full-stack roles.", signals)
    if any(term in location_text for term in BLOCKED_LOCATION_TERMS):
        return FitDecision(False, "Auto-apply skipped: role appears restricted outside India/Remote India preferences.", signals)
    if not (job.remote and not job.location) and not any(term in location_text for term in INDIA_LOCATION_TERMS):
        return FitDecision(
            False,
            "Auto-apply skipped: location does not match Remote India, Delhi NCR, Bangalore, Hyderabad, or Pune.",
            signals,
        )
    if len(matched_skills) < min_matched_skills:
        return FitDecision(
            False,
            f"Auto-apply skipped: only {len(matched_skills)} matched skills; needs at least {min_matched_skills}.",
            signals,
        )
    if required_years is not None and profile.experience_years < required_years:
        return FitDecision(
            False,
            f"Auto-apply skipped: requires {required_years:g}+ years; profile has {profile.experience_years:g}+ years.",
            signals,
        )

    salary_issue = _salary_issue(salary, settings)
    if salary_issue:
        return FitDecision(False, salary_issue, signals)

    return FitDecision(True, None, signals)


def extract_salary_lpa(job: Job, settings: Any) -> SalaryRange | None:
    raw = job.raw or {}
    usd_to_inr = float(getattr(settings, "salary_usd_to_inr", 83.0))
    numeric_min = _first_number(raw, ("salary_min", "salaryMin", "min_salary", "minimum_salary"))
    numeric_max = _first_number(raw, ("salary_max", "salaryMax", "max_salary", "maximum_salary"))
    if numeric_min or numeric_max:
        return SalaryRange(_salary_number_to_lpa(numeric_min, usd_to_inr), _salary_number_to_lpa(numeric_max, usd_to_inr), "raw")

    salary_text = " ".join(
        str(value)
        for value in (
            raw.get("salary"),
            raw.get("compensation"),
            raw.get("pay"),
            raw.get("payRange"),
            job.description,
        )
        if value
    )
    return _parse_salary_text(salary_text, usd_to_inr)


def extract_required_years(description: str) -> float | None:
    matches = re.findall(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)", description, re.I)
    if not matches:
        return None
    values = [float(match) for match in matches if float(match) < 20]
    return min(values) if values else None


def company_size_rank(job: Job, settings: Any) -> int:
    configured = {normalize_token(name) for name in getattr(settings, "big_company_names", [])}
    known_big = configured | {normalize_token(name) for name in DEFAULT_BIG_COMPANY_NAMES}
    company = normalize_token(job.company)
    description = (job.description or "").lower()
    raw_text = str(job.raw or {}).lower()
    if company in known_big:
        return 3
    if any(term in description or term in raw_text for term in ("fortune 500", "fortune 1000", "global enterprise", "public company")):
        return 2
    if re.search(r"(\d{1,3}(?:,\d{3})+|\d{4,})\+?\s+(?:employees|team members|people)", description):
        return 2
    if any(term in description for term in ("millions of users", "global customers", "enterprise customers", "worldwide")):
        return 1
    return 0


def _matched_skills(job: Job) -> list[str]:
    matched = (job.score_breakdown or {}).get("matched_skills") or []
    if matched:
        return sorted({normalize_token(skill) for skill in matched if skill})
    profile_relevant = {"python", "django", "angularjs", "elasticsearch", "redis", "mysql", "celery", "aws"}
    return sorted(profile_relevant & {normalize_token(skill) for skill in job.skills or []})


def _salary_issue(salary: SalaryRange | None, settings: Any) -> str | None:
    require_salary = bool(getattr(settings, "auto_apply_require_salary", True))
    desired_min = getattr(settings, "preferred_salary_min_lpa", None)
    desired_max = getattr(settings, "preferred_salary_max_lpa", None)
    if desired_min is None and desired_max is None:
        return "Auto-apply skipped: salary bracket is not configured."
    if salary is None:
        return "Auto-apply skipped: salary is not listed." if require_salary else None

    min_lpa = salary.min_lpa
    max_lpa = salary.max_lpa
    if desired_min is not None and max_lpa is not None and max_lpa < float(desired_min):
        return f"Auto-apply skipped: salary max {max_lpa:g} LPA is below desired minimum {float(desired_min):g} LPA."
    if desired_max is not None and min_lpa is not None and min_lpa > float(desired_max):
        return f"Auto-apply skipped: salary min {min_lpa:g} LPA is above desired maximum {float(desired_max):g} LPA."
    return None


def _first_number(raw: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = raw.get(key)
        if value in (None, ""):
            continue
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            continue
    return None


def _salary_number_to_lpa(value: float | None, usd_to_inr: float) -> float | None:
    if value is None:
        return None
    if value > 1000:
        return round(value * usd_to_inr / 100000, 2)
    return round(value, 2)


def _parse_salary_text(text: str, usd_to_inr: float) -> SalaryRange | None:
    if not text:
        return None
    normalized = text.replace(",", "")
    lpa = re.search(
        r"(?P<min>\d+(?:\.\d+)?)\s*(?:-|to|–|—)\s*(?P<max>\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lacs?)",
        normalized,
        re.I,
    )
    if lpa:
        return SalaryRange(float(lpa.group("min")), float(lpa.group("max")), "text_lpa")

    inr = re.search(
        r"(?:₹|rs\.?|inr)\s*(?P<min>\d+(?:\.\d+)?)\s*(?:-|to|–|—)\s*(?:₹|rs\.?|inr)?\s*(?P<max>\d+(?:\.\d+)?)\s*(?P<unit>lpa|lakhs?|lacs?)?",
        normalized,
        re.I,
    )
    if inr:
        unit = (inr.group("unit") or "").lower()
        scale = 1 if unit else 0.00001
        return SalaryRange(round(float(inr.group("min")) * scale, 2), round(float(inr.group("max")) * scale, 2), "text_inr")

    usd = re.search(
        r"\$\s*(?P<min>\d+(?:\.\d+)?)\s*(?:-|to|–|—)\s*\$?\s*(?P<max>\d+(?:\.\d+)?)\s*(?:usd|annually|per year)?",
        normalized,
        re.I,
    )
    if usd:
        return SalaryRange(
            round(float(usd.group("min")) * usd_to_inr / 100000, 2),
            round(float(usd.group("max")) * usd_to_inr / 100000, 2),
            "text_usd",
        )
    return None
