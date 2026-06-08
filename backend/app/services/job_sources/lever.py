from __future__ import annotations

import httpx

from app.services.job_sources.base import JobListing
from app.services.text import compact_whitespace, strip_html


class LeverSource:
    name = "lever"

    def __init__(self, companies: list[str]):
        self.companies = companies

    def fetch(self, query: str, location: str, limit: int = 50) -> list[JobListing]:
        listings: list[JobListing] = []
        for company in self.companies:
            url = f"https://api.lever.co/v0/postings/{company}?mode=json"
            try:
                response = httpx.get(url, timeout=15)
                response.raise_for_status()
            except httpx.HTTPError:
                continue
            for item in response.json():
                title = item.get("text", "")
                categories = item.get("categories", {}) or {}
                job_location = categories.get("location")
                content = compact_whitespace(strip_html(" ".join([
                    item.get("descriptionPlain", ""),
                    item.get("additionalPlain", ""),
                    item.get("lists", [{}])[0].get("content", "") if item.get("lists") else "",
                ])))
                if not _matches(title, content, query, location, job_location):
                    continue
                listings.append(
                    JobListing(
                        source=self.name,
                        external_id=item.get("id"),
                        url=item.get("hostedUrl") or item.get("applyUrl") or url,
                        title=title,
                        company=company,
                        location=job_location,
                        remote="remote" in (job_location or "").lower() or "remote" in content.lower(),
                        description=content,
                        employment_type=categories.get("commitment"),
                        raw=item,
                    ).normalized()
                )
                if len(listings) >= limit:
                    return listings
        return listings


def _matches(title: str, content: str, query: str, location: str, job_location: str | None) -> bool:
    haystack = f"{title} {content} {job_location or ''}".lower()
    query_terms = [term for term in query.lower().replace("-", " ").split() if len(term) > 2]
    query_ok = any(term in haystack for term in query_terms) if query_terms else True
    location_ok = location.lower() in haystack or "remote" in haystack or not location
    return query_ok and location_ok
