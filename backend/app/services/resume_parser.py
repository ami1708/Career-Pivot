import re
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.services.text import canonicalize_skills, compact_whitespace, extract_skills


SECTION_MARKERS = {
    "experience": ["experience", "work experience", "professional experience"],
    "projects": ["projects", "selected projects", "key projects"],
    "education": ["education", "academics"],
}


def parse_pdf_text(path: str | Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def extract_years(text: str, fallback: float) -> float:
    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s*(?:of)?\s*(?:experience|exp)?",
        r"experience\s*[:|-]?\s*(\d+(?:\.\d+)?)\+?",
    ]
    candidates = [fallback]
    for pattern in patterns:
        candidates.extend(float(match) for match in re.findall(pattern, text, flags=re.IGNORECASE))
    return max(candidates)


def collect_section_lines(text: str, section_name: str) -> list[str]:
    markers = SECTION_MARKERS[section_name]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    capture = False
    collected: list[str] = []
    all_markers = {marker for values in SECTION_MARKERS.values() for marker in values}
    for line in lines:
        normalized = line.lower().strip(": ")
        if normalized in markers:
            capture = True
            continue
        if capture and normalized in all_markers:
            break
        if capture:
            collected.append(line)
    return collected[:20]


def extract_companies(text: str) -> list[str]:
    companies = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean or len(clean) > 90:
            continue
        if re.search(r"(private limited|pvt|technologies|labs|systems|solutions|instahyre|paytm|amazon|microsoft)", clean, re.I):
            companies.append(clean)
    return list(dict.fromkeys(companies))[:10]


def extract_education(text: str) -> list[str]:
    education_lines = []
    for line in text.splitlines():
        clean = line.strip()
        if re.search(r"(university|institute|college|b\.?tech|bachelor|master|degree)", clean, re.I):
            education_lines.append(clean)
    return list(dict.fromkeys(education_lines))[:10]


def build_profile_from_text(text: str, resume_path: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    detected_skills = extract_skills(text)
    merged_skills = canonicalize_skills(settings.default_skills + detected_skills)
    keywords = canonicalize_skills(detected_skills + re.findall(r"\b[A-Z][A-Za-z0-9+.#/-]{2,}\b", text)[:50])
    profile_json: dict[str, Any] = {
        "name": settings.default_name,
        "current_role": settings.default_current_role,
        "experience_years": extract_years(text, settings.default_experience_years),
        "skills": merged_skills,
        "preferred_roles": settings.default_preferred_roles,
        "preferred_locations": settings.default_preferred_locations,
        "companies": extract_companies(text),
        "projects": collect_section_lines(text, "projects"),
        "education": extract_education(text) or collect_section_lines(text, "education"),
        "keywords": keywords,
        "resume_summary": compact_whitespace(text[:1600]),
    }
    if resume_path:
        profile_json["source_resume_path"] = resume_path
    return profile_json


def parse_resume(path: str | Path) -> dict[str, Any]:
    text = parse_pdf_text(path)
    structured = build_profile_from_text(text, str(path))
    structured["resume_text"] = text
    return structured
