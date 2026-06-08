from __future__ import annotations

from typing import Any

import httpx

from app.services.job_sources.base import JobListing
from app.services.text import compact_whitespace, strip_html


class RemotiveSource:
    name = "remotive"

    def fetch(self, query: str, location: str, limit: int = 50) -> list[JobListing]:
        params = {"search": query}
        try:
            response = httpx.get("https://remotive.com/api/remote-jobs", params=params, timeout=20)
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        listings: list[JobListing] = []
        for item in response.json().get("jobs", []):
            if not _location_matches(item.get("candidate_required_location"), location):
                continue
            description = compact_whitespace(strip_html(item.get("description", "")))
            listings.append(
                JobListing(
                    source=self.name,
                    external_id=str(item.get("id")),
                    url=item.get("url") or item.get("job_url"),
                    title=item.get("title", ""),
                    company=item.get("company_name", ""),
                    location=item.get("candidate_required_location") or "Remote",
                    remote=True,
                    description=description,
                    employment_type=item.get("job_type"),
                    raw=item,
                ).normalized()
            )
            if len(listings) >= limit:
                break
        return [listing for listing in listings if listing.url and listing.title and listing.company]


class RemoteOKSource:
    name = "remoteok"

    def fetch(self, query: str, location: str, limit: int = 50) -> list[JobListing]:
        tag = _query_tag(query)
        try:
            response = httpx.get(f"https://remoteok.com/api?tag={tag}", headers={"User-Agent": "ai-job-search-agent/0.1"}, timeout=20)
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        listings: list[JobListing] = []
        payload = response.json()
        items = payload[1:] if payload and isinstance(payload[0], dict) and "legal" in payload[0] else payload
        for item in items:
            if not isinstance(item, dict):
                continue
            description = compact_whitespace(strip_html(item.get("description", "")))
            tags = item.get("tags") or []
            if not _query_matches(query, item.get("position", ""), description, tags):
                continue
            listings.append(
                JobListing(
                    source=self.name,
                    external_id=str(item.get("id")),
                    url=item.get("url") or item.get("apply_url"),
                    title=item.get("position", ""),
                    company=item.get("company", ""),
                    location=item.get("location") or "Remote",
                    remote=True,
                    description=description,
                    requirements=tags,
                    raw=item,
                ).normalized()
            )
            if len(listings) >= limit:
                break
        return [listing for listing in listings if listing.url and listing.title and listing.company]


def _location_matches(candidate_location: str | None, preferred_location: str) -> bool:
    if not candidate_location:
        return True
    normalized = candidate_location.lower()
    preferred = preferred_location.lower()
    return (
        "worldwide" in normalized
        or "anywhere" in normalized
        or "india" in normalized
        or preferred in normalized
        or "remote" in preferred
    )


def _query_tag(query: str) -> str:
    lowered = query.lower()
    if "backend" in lowered:
        return "backend"
    if "full" in lowered:
        return "fullstack"
    if "python" in lowered:
        return "python"
    return "software"


def _query_matches(query: str, title: str, description: str, tags: list[Any]) -> bool:
    haystack = f"{title} {description} {' '.join(str(tag) for tag in tags)}".lower()
    terms = [term for term in query.lower().replace("-", " ").split() if len(term) > 2]
    return any(term in haystack for term in terms) if terms else True
