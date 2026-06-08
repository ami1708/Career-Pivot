import re
from dataclasses import dataclass
from typing import Any

from app.services.text import extract_skills, infer_seniority, normalize_token


@dataclass(frozen=True)
class ScoreResult:
    score: int
    breakdown: dict[str, Any]


def _normalized_set(values: list[str]) -> set[str]:
    return {normalize_token(value) for value in values if value}


def _experience_score(description: str, profile_years: float) -> tuple[int, str]:
    matches = re.findall(r"(\d+)\+?\s*(?:years|yrs)", description, re.I)
    if not matches:
        return 14, "No explicit years requirement found."
    required = min(int(value) for value in matches)
    if profile_years >= required:
        return 20, f"Profile meets {required}+ years requirement."
    if profile_years + 1 >= required:
        return 14, f"Profile is close to {required}+ years requirement."
    return 4, f"Requires {required}+ years; profile has {profile_years:g}+ years."


def _location_score(job_location: str | None, remote: bool, preferred_locations: list[str]) -> tuple[int, str]:
    if remote:
        return 20, "Remote role matches Remote India preference."
    if not job_location:
        return 8, "Location is not specified."
    job_norm = normalize_token(job_location)
    for location in preferred_locations:
        loc_norm = normalize_token(location)
        if loc_norm in job_norm or job_norm in loc_norm:
            return 20, f"Location matches {location}."
    metro_aliases = {
        "delhi ncr": ["delhi", "gurgaon", "gurugram", "noida", "faridabad"],
        "bangalore": ["bengaluru", "bangalore"],
    }
    for preferred in preferred_locations:
        preferred_norm = normalize_token(preferred)
        for alias in metro_aliases.get(preferred_norm, []):
            if alias in job_norm:
                return 20, f"Location matches {preferred}."
    return 4, f"Location {job_location} is outside preferred locations."


def _seniority_score(title: str, preferred_roles: list[str]) -> tuple[int, str]:
    title_norm = normalize_token(title)
    for role in preferred_roles:
        role_norm = normalize_token(role)
        if role_norm in title_norm or title_norm in role_norm:
            return 15, f"Title matches preferred role {role}."
    role_markers = [
        "engineer",
        "engineering",
        "developer",
        "backend",
        "back end",
        "full stack",
        "fullstack",
        "software",
        "sde",
    ]
    if not any(marker in title_norm for marker in role_markers):
        return 0, "Title does not match the target engineering roles."
    seniority = infer_seniority(title)
    if seniority in {"mid-senior", "senior", "lead"}:
        return 12, f"Seniority inferred as {seniority}."
    if seniority == "mid":
        return 9, "Mid-level role is acceptable for SDE-2 target."
    return 3, f"Seniority inferred as {seniority}."


def score_job(profile: Any, job: Any) -> ScoreResult:
    profile_skills = profile.skills if hasattr(profile, "skills") else profile["skills"]
    profile_roles = profile.preferred_roles if hasattr(profile, "preferred_roles") else profile["preferred_roles"]
    preferred_locations = profile.preferred_locations if hasattr(profile, "preferred_locations") else profile["preferred_locations"]
    experience_years = profile.experience_years if hasattr(profile, "experience_years") else profile["experience_years"]

    title = job.title if hasattr(job, "title") else job["title"]
    description = job.description if hasattr(job, "description") else job.get("description", "")
    location = job.location if hasattr(job, "location") else job.get("location")
    remote = job.remote if hasattr(job, "remote") else job.get("remote", False)
    job_skills = job.skills if hasattr(job, "skills") else job.get("skills", [])
    if not job_skills:
        job_skills = extract_skills(f"{title}\n{description or ''}")

    profile_skill_set = _normalized_set(profile_skills)
    job_skill_set = _normalized_set(job_skills)
    matched = sorted(profile_skill_set & job_skill_set)
    missing = sorted(profile_skill_set - job_skill_set)
    profile_ratio = len(matched) / max(min(len(profile_skill_set), 8), 1)
    job_ratio = len(matched) / max(len(job_skill_set), 1)
    skill_score = min(35, round(max(profile_ratio, job_ratio) * 35))

    exp_score, exp_note = _experience_score(description or "", float(experience_years))
    loc_score, loc_note = _location_score(location, bool(remote), preferred_locations)
    seniority_score, seniority_note = _seniority_score(title, profile_roles)

    tech_relevance = 10 if {"python", "django"} & job_skill_set else 6 if {"redis", "mysql", "aws", "elasticsearch"} & job_skill_set else 2
    if "backend" in normalize_token(title):
        tech_relevance = min(10, tech_relevance + 2)

    score = min(100, skill_score + exp_score + loc_score + seniority_score + tech_relevance)
    if seniority_score == 0:
        score = min(score, 59)
    breakdown = {
        "skill_overlap": skill_score,
        "experience_match": exp_score,
        "location_match": loc_score,
        "seniority_match": seniority_score,
        "tech_relevance": tech_relevance,
        "matched_skills": matched,
        "missing_core_skills": missing,
        "notes": [exp_note, loc_note, seniority_note],
    }
    return ScoreResult(score=score, breakdown=breakdown)
