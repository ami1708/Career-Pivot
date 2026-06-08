from dataclasses import dataclass, field
from typing import Any, Protocol

from app.services.text import extract_email, extract_skills, infer_seniority


@dataclass
class JobListing:
    source: str
    external_id: str | None
    url: str
    title: str
    company: str
    location: str | None = None
    remote: bool = False
    description: str | None = None
    requirements: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    seniority: str | None = None
    employment_type: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> "JobListing":
        text = f"{self.title}\n{self.description or ''}\n{' '.join(self.requirements)}"
        if not self.skills:
            self.skills = extract_skills(text)
        if not self.seniority:
            self.seniority = infer_seniority(self.title)
        if not self.recruiter_email:
            self.recruiter_email = extract_email(self.description)
        if self.location and "remote" in self.location.lower():
            self.remote = True
        return self


class JobSource(Protocol):
    name: str

    def fetch(self, query: str, location: str, limit: int = 50) -> list[JobListing]:
        ...

