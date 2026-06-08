from __future__ import annotations

import httpx

from app.services.job_sources.base import JobListing
from app.services.text import compact_whitespace, strip_html


class GreenhouseSource:
    name = "greenhouse"

    def __init__(self, companies: list[str]):
        self.companies = companies

    def fetch(self, query: str, location: str, limit: int = 50) -> list[JobListing]:
        listings: list[JobListing] = []
        for company in self.companies:
            url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
            try:
                response = httpx.get(url, timeout=15)
                response.raise_for_status()
            except httpx.HTTPError:
                continue
            for item in response.json().get("jobs", []):
                offices = ", ".join(office.get("name", "") for office in item.get("offices", []) if office.get("name"))
                departments = [dept.get("name", "") for dept in item.get("departments", []) if dept.get("name")]
                content = compact_whitespace(strip_html(item.get("content", "")))
                title = item.get("title", "")
                if not _matches(title, content, query, location, offices):
                    continue
                listings.append(
                    JobListing(
                        source=self.name,
                        external_id=str(item.get("id")),
                        url=item.get("absolute_url") or url,
                        title=title,
                        company=company,
                        location=offices or None,
                        remote="remote" in offices.lower() or "remote" in content.lower(),
                        description=content,
                        requirements=departments,
                        raw=item,
                    ).normalized()
                )
                if len(listings) >= limit:
                    return listings
        return listings


def _matches(title: str, content: str, query: str, location: str, offices: str) -> bool:
    haystack = f"{title} {content} {offices}".lower()
    query_terms = [term for term in query.lower().replace("-", " ").split() if len(term) > 2]
    query_ok = any(term in haystack for term in query_terms) if query_terms else True
    location_ok = location.lower() in haystack or "remote" in haystack or not location
    return query_ok and location_ok
